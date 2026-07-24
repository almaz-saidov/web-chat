import uuid
from math import inf, sqrt

from fastapi import Depends

from core.config import settings
from database.repositories.signature_template_repository import (
    SignatureTemplateRepository,
)
from schemas.signature import (
    SignaturePointSchema,
    SignatureSampleSchema,
    SignatureTemplateCreateSchema,
    SignatureTemplateDataSchema,
    SignatureTemplateSchema,
)
from services.db_service import DatabaseService


class SignatureService(DatabaseService[SignatureTemplateRepository]):
    async def create_template(
        self,
        user_id: uuid.UUID,
        signature_samples: list[SignatureSampleSchema],
    ) -> SignatureTemplateSchema:
        template_data = self._build_template(signature_samples=signature_samples)
        signature_template_create_data = SignatureTemplateCreateSchema(
            user_id=user_id,
            template_data=template_data,
        )

        return await self._repository.create(
            signature_template_create_data=signature_template_create_data
        )

    async def verify_signature(
        self, user_id: uuid.UUID, signature_sample: SignatureSampleSchema
    ) -> bool:
        signature_template = await self._repository.get_by_user_id(user_id=user_id)
        if not signature_template:
            return False

        current_template_data = self._normalize_sample_data(
            signature_sample=signature_sample
        )
        score = self._calculate_score(
            reference_template_data=signature_template.template_data,
            current_template_data=current_template_data,
        )

        return score >= settings.SIGNATURE_MATCH_THRESHOLD

    def _build_template(
        self, signature_samples: list[SignatureSampleSchema]
    ) -> SignatureTemplateDataSchema:
        if len(signature_samples) != settings.SIGNATURE_SAMPLE_COUNT:
            raise ValueError(
                f"Signature template requires exactly {settings.SIGNATURE_SAMPLE_COUNT} samples"
            )

        normalized_samples = [
            self._normalize_sample_data(signature_sample=signature_sample)
            for signature_sample in signature_samples
        ]

        averaged_points = [
            self._average_points(
                points=[sample.points[point_index] for sample in normalized_samples]
            )
            for point_index in range(settings.SIGNATURE_NORMALIZED_POINT_COUNT)
        ]

        return SignatureTemplateDataSchema(
            points=averaged_points,
            duration_ms=self._average(
                values=[sample.duration_ms for sample in normalized_samples]
            ),
            break_count=self._average(
                values=[sample.break_count for sample in normalized_samples]
            ),
        )

    def _normalize_sample_data(
        self, signature_sample: SignatureSampleSchema
    ) -> SignatureTemplateDataSchema:
        centered_points = self._center_and_scale_points(points=signature_sample.points)
        normalized_time_points = self._normalize_time(
            points=centered_points, duration_ms=signature_sample.duration_ms
        )
        resampled_points = self._resample_points(
            points=normalized_time_points,
            point_count=settings.SIGNATURE_NORMALIZED_POINT_COUNT,
        )
        smoothed_points = self._smooth_points(points=resampled_points)

        return SignatureTemplateDataSchema(
            points=smoothed_points,
            duration_ms=signature_sample.duration_ms,
            break_count=float(signature_sample.break_count),
        )

    def _center_and_scale_points(
        self, points: list[SignaturePointSchema]
    ) -> list[SignaturePointSchema]:
        min_x = min(point.x for point in points)
        max_x = max(point.x for point in points)
        min_y = min(point.y for point in points)
        max_y = max(point.y for point in points)

        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        scale = max(max_x - min_x, max_y - min_y, 1.0)

        return [
            point.model_copy(
                update={
                    "x": (point.x - center_x) / scale,
                    "y": (point.y - center_y) / scale,
                }
            )
            for point in points
        ]

    def _normalize_time(
        self, points: list[SignaturePointSchema], duration_ms: float
    ) -> list[SignaturePointSchema]:
        return [
            point.model_copy(update={"time_ms": point.time_ms / duration_ms})
            for point in points
        ]

    def _resample_points(
        self,
        points: list[SignaturePointSchema],
        point_count: int,
    ) -> list[SignaturePointSchema]:
        distances = self._get_cumulative_distances(points=points)
        total_distance = distances[-1]
        if total_distance == 0:
            return [points[0].model_copy() for _ in range(point_count)]

        resampled_points: list[SignaturePointSchema] = []
        source_index = 1

        for point_index in range(point_count):
            target_distance = total_distance * point_index / (point_count - 1)
            while (
                source_index < len(distances) - 1
                and distances[source_index] < target_distance
            ):
                source_index += 1

            previous_distance = distances[source_index - 1]
            next_distance = distances[source_index]
            ratio = self._get_interpolation_ratio(
                target_distance=target_distance,
                previous_distance=previous_distance,
                next_distance=next_distance,
            )
            resampled_points.append(
                self._interpolate_points(
                    first_point=points[source_index - 1],
                    second_point=points[source_index],
                    ratio=ratio,
                )
            )

        return resampled_points

    def _get_cumulative_distances(
        self, points: list[SignaturePointSchema]
    ) -> list[float]:
        distances = [0.0]
        for point_index in range(1, len(points)):
            distances.append(
                distances[-1]
                + self._calculate_coordinate_distance(
                    first_point=points[point_index - 1],
                    second_point=points[point_index],
                )
            )

        if distances[-1] > 0:
            return distances

        time_distances = [point.time_ms - points[0].time_ms for point in points]
        if time_distances[-1] > 0:
            return time_distances

        return [float(point_index) for point_index in range(len(points))]

    def _smooth_points(
        self, points: list[SignaturePointSchema]
    ) -> list[SignaturePointSchema]:
        smoothed_points: list[SignaturePointSchema] = []

        for point_index in range(len(points)):
            window_start = max(point_index - 1, 0)
            window_end = min(point_index + 2, len(points))
            smoothed_points.append(
                self._average_points(points=points[window_start:window_end])
            )

        return smoothed_points

    def _calculate_score(
        self,
        reference_template_data: SignatureTemplateDataSchema,
        current_template_data: SignatureTemplateDataSchema,
    ) -> float:
        dtw_distance = self._calculate_dtw_distance(
            reference_points=reference_template_data.points,
            current_points=current_template_data.points,
        )
        duration_penalty = self._calculate_duration_penalty(
            reference_duration_ms=reference_template_data.duration_ms,
            current_duration_ms=current_template_data.duration_ms,
        )
        break_count_penalty = abs(
            reference_template_data.break_count - current_template_data.break_count
        )

        return 1 / (
            1
            + dtw_distance
            + duration_penalty
            + break_count_penalty * settings.SIGNATURE_BREAK_COUNT_WEIGHT
        )

    def _calculate_dtw_distance(
        self,
        reference_points: list[SignaturePointSchema],
        current_points: list[SignaturePointSchema],
    ) -> float:
        previous_distances = [inf] * (len(reference_points) + 1)
        previous_distances[0] = 0

        for current_point in current_points:
            current_distances = [inf] * (len(reference_points) + 1)

            for reference_index, reference_point in enumerate(
                reference_points, start=1
            ):
                point_distance = self._calculate_point_distance(
                    reference_point=reference_point,
                    current_point=current_point,
                )
                current_distances[reference_index] = point_distance + min(
                    current_distances[reference_index - 1],
                    previous_distances[reference_index],
                    previous_distances[reference_index - 1],
                )

            previous_distances = current_distances

        return previous_distances[-1] / (len(reference_points) + len(current_points))

    def _calculate_point_distance(
        self,
        reference_point: SignaturePointSchema,
        current_point: SignaturePointSchema,
    ) -> float:
        coordinate_distance = self._calculate_coordinate_distance(
            first_point=reference_point,
            second_point=current_point,
        )
        pressure_distance = abs(reference_point.pressure - current_point.pressure)
        tilt_distance = (
            abs(reference_point.tilt_x - current_point.tilt_x)
            + abs(reference_point.tilt_y - current_point.tilt_y)
        ) / 180
        time_distance = abs(reference_point.time_ms - current_point.time_ms)

        return sqrt(
            (coordinate_distance * settings.SIGNATURE_COORDINATE_WEIGHT) ** 2
            + (pressure_distance * settings.SIGNATURE_PRESSURE_WEIGHT) ** 2
            + (tilt_distance * settings.SIGNATURE_TILT_WEIGHT) ** 2
            + (time_distance * settings.SIGNATURE_TIME_WEIGHT) ** 2
        )

    def _calculate_coordinate_distance(
        self,
        first_point: SignaturePointSchema,
        second_point: SignaturePointSchema,
    ) -> float:
        return sqrt(
            (first_point.x - second_point.x) ** 2
            + (first_point.y - second_point.y) ** 2
        )

    def _calculate_duration_penalty(
        self, reference_duration_ms: float, current_duration_ms: float
    ) -> float:
        duration_ratio = abs(reference_duration_ms - current_duration_ms) / max(
            reference_duration_ms, 1
        )
        return (
            min(duration_ratio, settings.SIGNATURE_MAX_DURATION_PENALTY_RATIO)
            * settings.SIGNATURE_DURATION_WEIGHT
        )

    def _interpolate_points(
        self,
        first_point: SignaturePointSchema,
        second_point: SignaturePointSchema,
        ratio: float,
    ) -> SignaturePointSchema:
        return SignaturePointSchema(
            x=self._interpolate(first_point.x, second_point.x, ratio),
            y=self._interpolate(first_point.y, second_point.y, ratio),
            pressure=self._interpolate(
                first_point.pressure, second_point.pressure, ratio
            ),
            tilt_x=self._interpolate(first_point.tilt_x, second_point.tilt_x, ratio),
            tilt_y=self._interpolate(first_point.tilt_y, second_point.tilt_y, ratio),
            time_ms=self._interpolate(first_point.time_ms, second_point.time_ms, ratio),
        )

    def _average_points(
        self, points: list[SignaturePointSchema]
    ) -> SignaturePointSchema:
        return SignaturePointSchema(
            x=self._average(values=[point.x for point in points]),
            y=self._average(values=[point.y for point in points]),
            pressure=self._average(values=[point.pressure for point in points]),
            tilt_x=self._average(values=[point.tilt_x for point in points]),
            tilt_y=self._average(values=[point.tilt_y for point in points]),
            time_ms=self._average(values=[point.time_ms for point in points]),
        )

    def _get_interpolation_ratio(
        self, target_distance: float, previous_distance: float, next_distance: float
    ) -> float:
        if next_distance == previous_distance:
            return 0

        return (target_distance - previous_distance) / (
            next_distance - previous_distance
        )

    def _interpolate(
        self, first_value: float, second_value: float, ratio: float
    ) -> float:
        return first_value + (second_value - first_value) * ratio

    def _average(self, values: list[float]) -> float:
        return sum(values) / len(values)


def get_signature_service(
    repository: SignatureTemplateRepository = Depends(),
) -> SignatureService:
    return SignatureService(repository=repository)

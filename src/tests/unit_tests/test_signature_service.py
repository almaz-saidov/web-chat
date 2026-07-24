import uuid
from collections.abc import Sequence
from datetime import datetime, timezone
from typing import cast
from unittest.mock import AsyncMock, Mock

import pytest

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
from services.signature_service import SignatureService

DEFAULT_COORDINATES = (
    (0.0, 0.0),
    (1.0, 1.0),
    (2.0, 1.0),
    (3.0, 2.0),
    (4.0, 3.0),
)


@pytest.fixture(autouse=True)
def compact_signature_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "SIGNATURE_SAMPLE_COUNT", 5)
    monkeypatch.setattr(settings, "SIGNATURE_NORMALIZED_POINT_COUNT", 5)
    monkeypatch.setattr(settings, "SIGNATURE_MATCH_THRESHOLD", 0.85)


def make_repository() -> Mock:
    return Mock(spec=SignatureTemplateRepository)


def make_service(repository: Mock) -> SignatureService:
    return SignatureService(repository=cast(SignatureTemplateRepository, repository))


def make_signature_sample(
    coordinates: Sequence[tuple[float, float]] = DEFAULT_COORDINATES,
    duration_ms: float = 400,
    break_count: int = 0,
    pressure: float = 0.5,
) -> SignatureSampleSchema:
    return SignatureSampleSchema(
        points=[
            SignaturePointSchema(
                x=x,
                y=y,
                pressure=pressure,
                tilt_x=0,
                tilt_y=0,
                time_ms=duration_ms * point_index / (len(coordinates) - 1),
            )
            for point_index, (x, y) in enumerate(coordinates)
        ],
        duration_ms=duration_ms,
        break_count=break_count,
    )


def make_signature_samples(
    duration_values: Sequence[float] = (400, 400, 400, 400, 400),
    break_count_values: Sequence[int] = (0, 0, 0, 0, 0),
) -> list[SignatureSampleSchema]:
    return [
        make_signature_sample(duration_ms=duration_ms, break_count=break_count)
        for duration_ms, break_count in zip(
            duration_values, break_count_values, strict=True
        )
    ]


def make_template_data() -> SignatureTemplateDataSchema:
    return SignatureTemplateDataSchema(
        points=make_signature_sample().points,
        duration_ms=400,
        break_count=0,
    )


def make_signature_template_schema(
    user_id: uuid.UUID,
    template_data: SignatureTemplateDataSchema,
) -> SignatureTemplateSchema:
    return SignatureTemplateSchema(
        id=uuid.uuid4(),
        user_id=user_id,
        template_data=template_data,
        created_at=datetime.now(timezone.utc),
    )


def assert_points_are_close(
    actual_points: Sequence[SignaturePointSchema],
    expected_points: Sequence[SignaturePointSchema],
) -> None:
    assert len(actual_points) == len(expected_points), (
        "Compared point collections must have the same length"
    )

    for point_index, (actual_point, expected_point) in enumerate(
        zip(actual_points, expected_points, strict=True)
    ):
        assert actual_point.x == pytest.approx(expected_point.x), (
            f"Point {point_index} x coordinate must match"
        )
        assert actual_point.y == pytest.approx(expected_point.y), (
            f"Point {point_index} y coordinate must match"
        )
        assert actual_point.pressure == pytest.approx(expected_point.pressure), (
            f"Point {point_index} pressure must match"
        )
        assert actual_point.tilt_x == pytest.approx(expected_point.tilt_x), (
            f"Point {point_index} tilt_x must match"
        )
        assert actual_point.tilt_y == pytest.approx(expected_point.tilt_y), (
            f"Point {point_index} tilt_y must match"
        )
        assert actual_point.time_ms == pytest.approx(expected_point.time_ms), (
            f"Point {point_index} time must match"
        )


async def test_create_template_builds_template_and_returns_repository_result() -> None:
    user_id = uuid.uuid4()
    repository = make_repository()
    created_template = make_signature_template_schema(
        user_id=user_id, template_data=make_template_data()
    )
    repository.create = AsyncMock(return_value=created_template)
    service = make_service(repository=repository)
    signature_samples = make_signature_samples()

    result = await service.create_template(
        user_id=user_id, signature_samples=signature_samples
    )

    assert result == created_template, (
        "SignatureService.create_template must return repository result"
    )
    repository.create.assert_awaited_once()
    create_data = repository.create.await_args.kwargs["signature_template_create_data"]
    assert isinstance(create_data, SignatureTemplateCreateSchema), (
        "SignatureService.create_template must pass create schema to repository"
    )
    assert create_data.user_id == user_id, (
        "Signature template create schema must keep target user id"
    )
    assert (
        len(create_data.template_data.points)
        == settings.SIGNATURE_NORMALIZED_POINT_COUNT
    ), "Signature template must use configured normalized point count"
    assert create_data.template_data.duration_ms == pytest.approx(400), (
        "Signature template must store average sample duration"
    )
    assert create_data.template_data.break_count == pytest.approx(0), (
        "Signature template must store average sample break count"
    )


async def test_verify_signature_returns_false_when_template_does_not_exist() -> None:
    user_id = uuid.uuid4()
    repository = make_repository()
    repository.get_by_user_id = AsyncMock(return_value=None)
    service = make_service(repository=repository)

    result = await service.verify_signature(
        user_id=user_id, signature_sample=make_signature_sample()
    )

    assert result is False, (
        "SignatureService.verify_signature must reject user without signature template"
    )
    repository.get_by_user_id.assert_awaited_once_with(user_id=user_id)


async def test_verify_signature_returns_true_for_matching_signature() -> None:
    user_id = uuid.uuid4()
    repository = make_repository()
    service = make_service(repository=repository)
    signature_sample = make_signature_sample()
    template_data = service._build_template(
        signature_samples=[signature_sample for _ in range(5)]
    )
    signature_template = make_signature_template_schema(
        user_id=user_id, template_data=template_data
    )
    repository.get_by_user_id = AsyncMock(return_value=signature_template)

    result = await service.verify_signature(
        user_id=user_id, signature_sample=signature_sample
    )

    assert result is True, (
        "SignatureService.verify_signature must accept matching signature sample"
    )
    repository.get_by_user_id.assert_awaited_once_with(user_id=user_id)


async def test_verify_signature_returns_false_for_different_signature() -> None:
    user_id = uuid.uuid4()
    repository = make_repository()
    service = make_service(repository=repository)
    reference_sample = make_signature_sample()
    wrong_signature_sample = make_signature_sample(
        coordinates=((0, 3), (1, 0), (2, 3), (3, 0), (4, 3)),
        duration_ms=1200,
        break_count=3,
        pressure=1,
    )
    template_data = service._build_template(
        signature_samples=[reference_sample for _ in range(5)]
    )
    signature_template = make_signature_template_schema(
        user_id=user_id, template_data=template_data
    )
    repository.get_by_user_id = AsyncMock(return_value=signature_template)

    result = await service.verify_signature(
        user_id=user_id, signature_sample=wrong_signature_sample
    )

    assert result is False, (
        "SignatureService.verify_signature must reject a different signature sample"
    )
    repository.get_by_user_id.assert_awaited_once_with(user_id=user_id)


def test_build_template_averages_duration_and_break_count() -> None:
    repository = make_repository()
    service = make_service(repository=repository)
    duration_values = (300.0, 400.0, 500.0, 600.0, 700.0)
    break_count_values = (0, 1, 2, 3, 4)

    result = service._build_template(
        signature_samples=make_signature_samples(
            duration_values=duration_values,
            break_count_values=break_count_values,
        )
    )

    assert len(result.points) == settings.SIGNATURE_NORMALIZED_POINT_COUNT, (
        "Signature template builder must normalize point count"
    )
    assert result.duration_ms == pytest.approx(500), (
        "Signature template builder must average sample durations"
    )
    assert result.break_count == pytest.approx(2), (
        "Signature template builder must average sample break counts"
    )


def test_normalize_sample_data_makes_translated_and_scaled_samples_equivalent() -> None:
    repository = make_repository()
    service = make_service(repository=repository)
    base_sample = make_signature_sample()
    transformed_sample = make_signature_sample(
        coordinates=[(x * 10 + 100, y * 10 - 50) for x, y in DEFAULT_COORDINATES],
    )

    base_template_data = service._normalize_sample_data(signature_sample=base_sample)
    transformed_template_data = service._normalize_sample_data(
        signature_sample=transformed_sample
    )

    assert base_template_data.duration_ms == transformed_template_data.duration_ms, (
        "Signature normalization must preserve original duration"
    )
    assert base_template_data.break_count == transformed_template_data.break_count, (
        "Signature normalization must preserve break count"
    )
    assert_points_are_close(
        actual_points=transformed_template_data.points,
        expected_points=base_template_data.points,
    )


def test_calculate_score_returns_one_for_identical_templates() -> None:
    repository = make_repository()
    service = make_service(repository=repository)
    template_data = service._normalize_sample_data(
        signature_sample=make_signature_sample()
    )

    result = service._calculate_score(
        reference_template_data=template_data,
        current_template_data=template_data,
    )

    assert result == pytest.approx(1), (
        "Signature score must be perfect for identical templates"
    )

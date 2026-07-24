function createSignaturePad({canvasId, clearButtonId, errorElementId, onChange}) {
    const canvas = document.getElementById(canvasId);
    const context = canvas.getContext('2d');
    const clearButton = document.getElementById(clearButtonId);
    const errorElement = document.getElementById(errorElementId);

    let points = [];
    let activePointerId = null;
    let strokeStartedAt = 0;
    let touchDurationMs = 0;
    let breakCount = 0;
    let lastDrawPoint = null;

    context.lineCap = 'round';
    context.lineJoin = 'round';
    context.lineWidth = 2;
    context.strokeStyle = '#4a5568';
    context.fillStyle = '#4a5568';

    function notifyChange() {
        if (onChange) {
            onChange();
        }
    }

    function showError(message) {
        if (!errorElement) {
            return;
        }

        errorElement.style.display = 'block';
        errorElement.textContent = message;
    }

    function clamp(value, min, max) {
        return Math.min(Math.max(value, min), max);
    }

    function getPointerValue(value, fallback) {
        return Number.isFinite(value) ? value : fallback;
    }

    function getCanvasPoint(event) {
        const rect = canvas.getBoundingClientRect();
        const scaleX = canvas.width / rect.width;
        const scaleY = canvas.height / rect.height;
        const timeMs = touchDurationMs + Math.max(event.timeStamp - strokeStartedAt, 0);

        return {
            x: (event.clientX - rect.left) * scaleX,
            y: (event.clientY - rect.top) * scaleY,
            pressure: clamp(getPointerValue(event.pressure, 0), 0, 1),
            tilt_x: clamp(getPointerValue(event.tiltX, 0), -90, 90),
            tilt_y: clamp(getPointerValue(event.tiltY, 0), -90, 90),
            time_ms: timeMs
        };
    }

    function drawPoint(point) {
        if (!lastDrawPoint) {
            context.beginPath();
            context.arc(point.x, point.y, 1.5, 0, Math.PI * 2);
            context.fill();
            lastDrawPoint = point;
            return;
        }

        context.beginPath();
        context.moveTo(lastDrawPoint.x, lastDrawPoint.y);
        context.lineTo(point.x, point.y);
        context.stroke();
        lastDrawPoint = point;
    }

    function addPoint(event) {
        const point = getCanvasPoint(event);
        points.push(point);
        drawPoint(point);
    }

    function finishStroke(event) {
        touchDurationMs += Math.max(event.timeStamp - strokeStartedAt, 0);
        activePointerId = null;
        lastDrawPoint = null;
        notifyChange();
    }

    canvas.addEventListener('pointerdown', function(event) {
        if (event.pointerType !== 'pen') {
            showError('Signature requires a pen input');
            return;
        }

        if (activePointerId !== null) {
            return;
        }

        event.preventDefault();

        if (points.length > 0) {
            breakCount += 1;
        }

        activePointerId = event.pointerId;
        strokeStartedAt = event.timeStamp;
        lastDrawPoint = null;
        canvas.setPointerCapture(event.pointerId);
        addPoint(event);
        notifyChange();
    });

    canvas.addEventListener('pointermove', function(event) {
        if (event.pointerId !== activePointerId) {
            return;
        }

        event.preventDefault();
        addPoint(event);
        notifyChange();
    });

    canvas.addEventListener('pointerup', function(event) {
        if (event.pointerId !== activePointerId) {
            return;
        }

        event.preventDefault();
        canvas.releasePointerCapture(event.pointerId);
        finishStroke(event);
    });

    canvas.addEventListener('pointercancel', function(event) {
        if (event.pointerId !== activePointerId) {
            return;
        }

        canvas.releasePointerCapture(event.pointerId);
        finishStroke(event);
    });

    clearButton.addEventListener('click', function() {
        points = [];
        activePointerId = null;
        strokeStartedAt = 0;
        touchDurationMs = 0;
        breakCount = 0;
        lastDrawPoint = null;
        context.clearRect(0, 0, canvas.width, canvas.height);
        notifyChange();
    });

    return {
        clear() {
            clearButton.click();
        },
        getPointCount() {
            return points.length;
        },
        getSample() {
            if (activePointerId !== null || points.length < 5 || touchDurationMs <= 0) {
                return null;
            }

            return {
                points: points.map(point => ({...point})),
                duration_ms: touchDurationMs,
                break_count: breakCount
            };
        }
    };
}

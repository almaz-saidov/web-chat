from fastapi import HTTPException, WebSocketException, status


class UserNotFoundHTTPException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )


class InvalidTokenHTTPException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


class UserAlreadyExistsHTTPException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail="The user with this username already exists",
        )


class WrongUsernameOrPasswordHTTPException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong username or password",
        )


class AccessTokenExpiredHTTPException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token expired",
        )


class RefreshTokenExpiredHTTPException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired",
        )


class RefreshTokenCookieIsMissingHTTPException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token cookie is missing",
        )


class InvalidRefreshTokenFormatHTTPException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token format",
        )


class WrongRefreshTokenHTTPException(HTTPException):
    def __init__(self) -> None:
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Wrong refresh token",
        )


class TokenIsRequiredWebSocketException(WebSocketException):
    def __init__(self) -> None:
        super().__init__(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Token is required",
        )


class TokenIsInvalidOrExpiredWebSocketException(WebSocketException):
    def __init__(self) -> None:
        super().__init__(
            code=status.WS_1008_POLICY_VIOLATION,
            reason="Invalid or expired token",
        )

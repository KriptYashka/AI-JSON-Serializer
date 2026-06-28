class OpenRouterError(Exception):
    pass


class AuthenticationError(OpenRouterError):
    pass


class RateLimitError(OpenRouterError):
    pass


class BadRequestError(OpenRouterError):
    pass


class ServerError(OpenRouterError):
    pass


ERROR_MAP: dict[int, type[OpenRouterError]] = {
    401: AuthenticationError,
    402: AuthenticationError,
    403: AuthenticationError,
    429: RateLimitError,
    422: BadRequestError,
    400: BadRequestError,
    500: ServerError,
    502: ServerError,
    503: ServerError,
}

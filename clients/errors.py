class ExternalServiceError(Exception):
    pass


class NotFoundError(Exception):
    pass


class InvalidResponseError(ExternalServiceError):
    pass

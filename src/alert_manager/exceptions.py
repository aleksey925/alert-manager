class ServiceException(Exception):  # noqa: N818
    pass


class UnauthorizedRequestError(ServiceException):
    pass

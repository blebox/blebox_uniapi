class Error(RuntimeError):
    pass


class TimeoutError(Error):
    pass


class ClientError(Error):
    pass


class HttpError(Error):
    pass

class Error(RuntimeError):
    pass


# Basic http client errors:


class TimeoutError(Error):
    pass


class ClientError(Error):
    pass


class HttpError(Error):
    pass


# api errors


class BoxError(Error):
    pass


class UnsupportedBoxResponse(BoxError):
    pass


class UnsupportedBoxVersion(BoxError):
    pass


class UnsupportedAppVersion(BoxError):
    pass


# TODO: not used yet
# class OutdatedBoxVersion(BoxError):
#     pass


class JPathFailed(BoxError):
    def __init__(self, message, path, data):
        self._message = message
        self._path = path
        self._data = data

    def __str__(self):
        return f"{self._message} at '{self._path}' within '''{self._data}'''"


class BadFieldExceedsMax(BoxError):
    def __init__(self, dev_name, field, value, max_value):
        self._dev_name = dev_name
        self._field = field
        self._value = value
        self._max_value = max_value

    def __str__(self):
        return f"{self._dev_name}.{self._field} is {self._value} which exceeds max ({self._max_value})"


class BadFieldLessThanMin(BoxError):
    def __init__(self, dev_name, field, value, min_value):
        self._dev_name = dev_name
        self._field = field
        self._value = value
        self._min_value = min_value

    def __str__(self):
        return f"{self._dev_name}.{self._field} is {self._value} which is less than minimum ({self._min_value})"


class BadFieldMissing(BoxError):
    def __init__(self, dev_name, field):
        self._dev_name = dev_name
        self._field = field

    def __str__(self):
        return f"{self._dev_name}.{self._field} is missing"


class BadFieldNotANumber(BoxError):
    def __init__(self, dev_name, field, value):
        self._dev_name = dev_name
        self._field = field
        self._value = value

    def __str__(self):
        return (
            f"{self._dev_name}.{self._field} is '{self._value}' which is not a number"
        )


class BadFieldNotAString(BoxError):
    def __init__(self, dev_name, field, value):
        self._dev_name = dev_name
        self._field = field
        self._value = value

    def __str__(self):
        return f"{self._dev_name}.{self._field} is {self._value} which is not a string"


class BadFieldNotRGBW(BoxError):
    def __init__(self, dev_name, field, value):
        self._dev_name = dev_name
        self._field = field
        self._value = value

    def __str__(self):
        return f"{self._dev_name}.{self._field} is {self._value} which is not a rgbw string"


# API command errors


class BadOnValueError(BoxError):
    pass


# misc errors


class MisconfiguredDevice(BoxError):
    pass


class DeviceStateNotAvailable(BoxError):
    def __str__(self):
        return "device state not available yet"

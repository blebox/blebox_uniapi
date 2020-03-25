from blebox_uniapi.error import (
    Error,
    TemporaryError,
    ConnectionError,
    TimeoutError,
    ClientError,
    HttpError,
    BoxError,
)

ALL = set([Error, ConnectionError, TimeoutError, ClientError, HttpError, BoxError])


def assert_is_a(subject, errors):
    for error in errors:
        assert issubclass(subject, error)

    remaining = ALL - set(errors) - set([subject])
    for error in remaining:
        assert not issubclass(subject, error)


def test_error():
    assert_is_a(Error, (Error,))


def test_temporary_error():
    assert_is_a(TemporaryError, (Error,))


def test_connection_error():
    assert_is_a(ConnectionError, (Error, TemporaryError))


def test_timeout_error():
    assert_is_a(TimeoutError, (Error, ConnectionError, TemporaryError))


def test_client_error():
    assert_is_a(ClientError, (Error,))


def test_http_error():
    assert_is_a(HttpError, (Error, ClientError))


def test_box_error():
    assert_is_a(BoxError, (Error,))

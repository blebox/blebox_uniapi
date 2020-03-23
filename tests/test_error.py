from blebox_uniapi import error


def test_error_hierarchy():
    assert issubclass(error.TimeoutError, error.Error)
    assert issubclass(error.ClientError, error.Error)
    assert issubclass(error.HttpError, error.Error)

    assert issubclass(error.BoxError, error.Error)

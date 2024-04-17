from typing import Any

import jmespath


def follow(data: dict | list, path: str) -> Any:
    if data is None:
        raise RuntimeError(f"bad argument: data {data}")  # pragma: no cover

    expression = jmespath.compile(path)
    return expression.search(data)

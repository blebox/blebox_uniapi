from typing import Any, Union

import jmespath


def follow(data: Union[dict, list], path: str) -> Any:
    if data is None:
        raise RuntimeError(f"bad argument: data {data}")  # pragma: no cover

    expression = jmespath.compile(path)
    return expression.search(data)

"""Type stubs for pytest."""

from typing import Any, Optional, Union

class ApproxBase:
    def __eq__(self, other: Any) -> bool: ...

def approx(
    expected: Union[float, int],
    rel: Optional[Union[float, int]] = None,
    abs: Optional[Union[float, int]] = None,
    nan_ok: bool = False,
) -> ApproxBase: ...
def raises(exception: type[BaseException], *args: Any, **kwargs: Any) -> Any: ...
def skip(reason: str = "") -> Any: ...

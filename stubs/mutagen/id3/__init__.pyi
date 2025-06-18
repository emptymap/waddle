"""Type stubs for mutagen.id3."""

from pathlib import Path
from typing import Any, List, Optional, Union

class ID3:
    def __init__(self, filename: Optional[Union[str, Path]] = None) -> None: ...
    def add(self, frame: Any) -> None: ...
    def save(
        self,
        filething: Optional[Union[str, Path]] = None,
        v1: int = 1,
        v2_version: int = 4,
        v23_sep: str = "/",
        padding: Optional[Any] = None,
    ) -> None: ...
    def getall(self, key: str) -> List[Any]: ...
    def pprint(self) -> str: ...

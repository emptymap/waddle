"""Type stubs for mutagen.id3._frames."""

from typing import Any, List, Optional

class CHAP:
    def __init__(
        self,
        element_id: str,
        start_time: int,
        end_time: int,
        sub_frames: Optional[List[Any]] = None,
        **kwargs: Any,
    ) -> None: ...

class CTOC:
    def __init__(
        self,
        element_id: str,
        flags: int,
        child_element_ids: List[str],
        **kwargs: Any,
    ) -> None: ...

class TIT2:
    def __init__(self, text: str, **kwargs: Any) -> None: ...

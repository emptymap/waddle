"""Type stubs for soundfile."""

from pathlib import Path
from typing import Any, Optional, Union

import numpy as np

def write(
    file: Union[str, Path],
    data: np.ndarray[Any, Any],
    samplerate: int,
    subtype: Optional[str] = None,
    endian: Optional[str] = None,
    format: Optional[str] = None,
    closefd: bool = True,
) -> None: ...

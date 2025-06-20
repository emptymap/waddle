"""Type stubs for librosa."""

from pathlib import Path
from typing import Any, Optional, Tuple, Union

import numpy as np

def load(
    path: Union[str, int, Path, Any],
    *,
    sr: Optional[float] = 22050,
    mono: bool = True,
    offset: float = 0,
    duration: Optional[float] = None,
    dtype: Any = np.float32,
    res_type: str = "soxr_hq",
) -> Tuple[np.ndarray[Any, np.dtype[np.float32]], Union[int, float]]: ...

"""Type stubs for scipy."""

from typing import Any

import numpy as np

class signal:
    @staticmethod
    def correlate(
        in1: np.ndarray[Any, Any],
        in2: np.ndarray[Any, Any],
        mode: str = "full",
        method: str = "auto",
    ) -> np.ndarray[Any, np.dtype[np.float64]]: ...

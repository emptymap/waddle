"""Type stubs for scipy.io."""

from pathlib import Path
from typing import Any, Tuple, Union

import numpy as np

class wavfile:
    @staticmethod
    def write(filename: Union[str, Path], rate: int, data: np.ndarray[Any, Any]) -> None: ...
    @staticmethod
    def read(
        filename: Union[str, Path], mmap: bool = False
    ) -> Tuple[int, np.ndarray[Any, Any]]: ...

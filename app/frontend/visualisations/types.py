from __future__ import annotations

from collections.abc import Callable

import pandas as pd

Renderer = Callable[[pd.DataFrame], None]

"""V55: East China Sea pressure d14 shear/ws3 probe.

V53 promoted the pressure-physics feature family for ECS pressure d7, while
v54 showed the same direct replacement does not transfer blindly to North Sea.
V55 keeps the expansion inside the validated ECS pressure family and tests d14
only, using the closest available HRES forecast stack (d10) plus selected d1/d7
signals.

Scope:
- base: v53
- changed rows: grid / east_china_sea / pressure levels / horizon d14
- changed columns: q05, q50, q95 only
"""

from __future__ import annotations

from src.data.paths import LOGS_DIR
from src.experiments import pressure_shear_v53 as runner


runner.VERSION = "v55"
runner.BASE_VERSION = "v53"
runner.EXPECTED_BASE_FILE = "predictions_v53.csv"
runner.REGION = "east_china_sea"
runner.TARGET_HORIZONS = [14]
runner.OUT_DIR = LOGS_DIR / "pressure_shear_v55"


def generate_v55() -> None:
    runner.generate_v53()


if __name__ == "__main__":
    generate_v55()

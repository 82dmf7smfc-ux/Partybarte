"""Make the alarm_pareto package importable when running pytest from the root.

This file sits at the project root. pytest loads it before collecting tests.
Adding the root folder to the import path means the tests can simply write
'from alarm_pareto import ...' no matter how pytest was launched.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

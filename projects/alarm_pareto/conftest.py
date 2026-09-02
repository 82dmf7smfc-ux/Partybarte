"""Make the alarm_pareto package importable when running pytest.

This file sits at the top of the alarm_pareto project folder. pytest loads it
before collecting any test underneath it. Adding this folder to the import path
means the tests can simply write 'from alarm_pareto import ...' no matter where
pytest was launched from, and no matter whether the project is being run inside
this repository or from the downloaded zip package, where this file sits beside
the alarm_pareto folder in the same way.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

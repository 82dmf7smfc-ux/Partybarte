"""Make the fab_drivers package importable when running pytest.

This file sits at the top of the fab_drivers project folder. pytest loads it
before collecting any test underneath it. Adding this folder to the import path
means the tests can simply write 'from fab_drivers import ...' no matter where
pytest was launched from.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

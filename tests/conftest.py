"""pytest 公共配置：让 tests/ 下的测试可以直接 `from src.core.xxx import ...`。

（A 地基工提供的骨架便利，B/C/D 写自己的测试时同样受益。）
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

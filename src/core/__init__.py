"""核心逻辑包（core）。

模块归属（见 docs/ARCHITECTURE.md 第 1 节）：
- models.py     ← A 地基工：公共数据模型（其他人只读）
- safety.py     ← A 地基工：安全红线层
- scanner.py    ← B 分析师：文件扫描
- classifier.py ← B 分析师：分类规则
- executor.py   ← C 搬运工：执行移动/删除
- undo.py       ← C 搬运工：撤销栈 + 日志

本文件故意不 import 任何子模块，避免并行开发时产生循环依赖。
调用方请按需显式导入，例如：from src.core.models import FileItem
"""

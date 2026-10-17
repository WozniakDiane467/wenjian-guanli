# ARCHITECTURE — 架构与接口契约

> 本文件是 4 个 agent 协作的「合同」。接口一经冻结，任何人改接口必须先改这里，并在 STATUS.md 说明、等总统筹裁决。**所有 agent 开工前必读。**

## 1. 模块划分

```
src/
├── core/
│   ├── models.py        ← A：公共数据模型 FileItem
│   ├── safety.py        ← A：安全红线层
│   ├── scanner.py       ← B：文件扫描
│   ├── classifier.py    ← B：分类规则
│   ├── executor.py      ← C：批量执行
│   └── undo.py          ← C：撤销 + 日志
├── gui/
│   └── main_window.py   ← D：主窗口界面
└── main.py              ← D：入口，集成全部
```

## 2. 数据流

```
B.scan_directory(目录)  →  产出 list[FileItem]
        ↓
B.classify(item)        →  给每个 item 打 category + suggested_path
        ↓
D 展示清单，用户勾选
        ↓
C.execute(勾选的 items) →  内部调 A 的 safe_move / move_to_trash
        ↓
C.undo() / C.get_log()  →  撤销 / 日志
```

## 3. 公共数据模型（A 负责，其他人只读）

### FileItem（dataclass）

| 字段 | 类型 | 含义 |
|---|---|---|
| path | str | 文件绝对路径（原始） |
| name | str | 文件名 |
| size | int | 字节数 |
| category | str | 分类（7 类之一） |
| suggested_path | str | 建议归入的目标路径（含新文件名） |
| action | str | "move"（移动）或 "trash"（进回收站） |

> 分类标签统一为：`文档 / 图片 / 视频 / 音频 / 压缩包 / 安装包 / 其他`。

## 4. 接口契约（函数名 / 签名已冻结）

### A 地基工 — safety.py

```python
SAFE_EXCLUDE_DIRS: set[str]
    # 受保护目录黑名单（Windows / Program Files / AppData / System32 等）

def is_safe(path: str) -> bool:
    # 判断该路径是否允许操作：不在黑名单内、不在系统盘根目录

def move_to_trash(path: str) -> bool:
    # 用 send2trash 把文件/文件夹移进回收站，返回是否成功

def safe_move(src: str, dst: str) -> str:
    # 安全移动：先 is_safe 检查，处理重名（自动加后缀），返回最终路径
```

### B 分析师 — scanner.py / classifier.py

```python
def scan_directory(root: str) -> list[FileItem]:
    # 递归扫描 root 下所有文件，跳过受保护目录，返回 FileItem 列表

def classify(item: FileItem) -> FileItem:
    # 按扩展名打 category，并生成 suggested_path，返回更新后的 item

CATEGORY_RULES: dict[str, str]
    # 扩展名 → 分类 的映射表（可配置）
```

### C 搬运工 — executor.py / undo.py

```python
def execute(items: list[FileItem]) -> dict:
    # 批量执行：action=move 调 safe_move，action=trash 调 move_to_trash
    # 每条压入撤销栈并写日志；单条失败不中断整批
    # 返回 {"moved": N, "trashed": N, "failed": [..]}

def undo() -> bool:
    # 撤销上一步（弹出撤销栈，反向操作），返回是否成功

def get_log() -> list[str]:
    # 返回操作日志列表
```

### D 总装师 — gui/main_window.py / main.py

```python
class MainWindow(QMainWindow):
    # 选目录 → 扫描 → 清单表格(勾选) → 确认弹窗 → 执行 → 撤销 → 日志区
```

## 5. 依赖关系与并行策略

- **A 是地基**：models.py + safety.py 是公共依赖，B/C/D 都引用它。
- **接口已冻结**：B/C/D 不必等 A 写完，按本契约开发，最后 D 集成。
- 建议开工顺序：A 先产出 models.py + safety.py；B、C 可立即并行；D 可先用假数据跑通界面，最后替换成真实调用。
- 集成顺序：A+B+C 就绪 → D 集成 → 总统筹验收。

## 6. 环境与依赖

- 用系统可用的 Python 3.11+；建议在项目目录建 venv。
- 依赖（A 写进 requirements.txt）：`PySide6`、`send2trash`、`pytest`。

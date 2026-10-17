# 电脑桌面管理 — 项目总览与协作规范

> 桌面端文件自动整理工具：把散乱的文件自动归类到规范文件夹，先出清单、你点头才动手，删/移一律进回收站、可撤销。

## 一句话定位

电脑里的「桌面 / 下载 / 文档」越堆越乱？这个工具帮你走完一条闭环：**扫描 → 分类 → 出清单 → 你确认 → 自动整理 → 可撤销**，全程安全。

## 技术栈

- Python 3.11+
- 图形界面：PySide6
- 进回收站：send2trash
- 打包（可选）：PyInstaller
- 测试：pytest

## 团队分工

| 代号 | 角色 | 负责模块 | 产出文件 | 工作记录 |
|---|---|---|---|---|
| A | 地基工 | 项目骨架 + 公共数据模型 + 安全红线层 | src/core/models.py、safety.py | docs/records/A-地基工-工作记录.md |
| B | 分析师 | 文件扫描 + 分类规则 | src/core/scanner.py、classifier.py | docs/records/B-分析师-工作记录.md |
| C | 搬运工 | 执行 + 撤销 + 日志 | src/core/executor.py、undo.py | docs/records/C-搬运工-工作记录.md |
| D | 总装师 | 图形界面 + 集成 | src/gui/*、src/main.py | docs/records/D-总装师-工作记录.md |

> 总统筹（阿管）只做三件事：**调度、验收、裁决**，不代工写代码。

## 协作规范（每个 agent 必读）

1. **各写各的模块**：只在自己的文件里写代码，不碰别人的模块。
2. **接口以 ARCHITECTURE.md 为准**：函数名/签名已冻结，想改必须先改 `docs/ARCHITECTURE.md` 并写进 STATUS.md 说明，等总统筹裁决。
3. **双重留痕**（这是给总统筹验收用的）：
   - `docs/STATUS.md` —— 总白板，只写**一行状态**（开工/完工/卡点），总统筹快速巡查用。
   - `docs/records/` 你自己的那份工作记录 —— 详细日志（做了什么、遇到什么问题、怎么解决、交付了哪些文件、自检结果），总统筹验收时细看。
4. **先读再干**：开工前先读 `docs/README.md`、`docs/PRD.md`、`docs/ARCHITECTURE.md`、`docs/STATUS.md`。

## 目录结构

```
电脑桌面管理/
├── docs/
│   ├── README.md            ← 本文件（总览 + 规范）
│   ├── PRD.md               ← 需求文档
│   ├── ARCHITECTURE.md      ← 架构 + 接口契约（最重要）
│   ├── STATUS.md            ← 总白板（总统筹巡查）
│   ├── DECISIONS.md         ← 决策记录
│   ├── records/             ← 4 份 agent 工作记录（总统筹验收）
│   └── prompts/             ← 4 份开工提示词
├── src/
│   ├── core/                ← 核心逻辑（A/B/C 的模块）
│   ├── gui/                 ← 界面（D）
│   └── main.py              ← 入口（D）
└── tests/                   ← 测试
```

## 如何启动（D 集成完成后）

```bash
python src/main.py
```

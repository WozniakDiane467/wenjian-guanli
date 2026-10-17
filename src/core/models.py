"""公共数据模型（A 地基工）。

契约来源：docs/ARCHITECTURE.md 第 3 节。字段名已冻结，任何改动必须先改文档
并在 docs/STATUS.md 说明；B/C/D 只读本模块，不要改字段名。

用法：
    from src.core.models import FileItem
    item = FileItem(path=r"C:\\Users\\me\\Desktop\\报告.docx", name="报告.docx")
"""

from __future__ import annotations

from dataclasses import asdict, dataclass

__all__ = ["CATEGORIES", "ACTIONS", "FileItem"]

#: category 的合法取值（7 大类，见 PRD.md 第 4 节）
CATEGORIES: tuple[str, ...] = ("文档", "图片", "视频", "音频", "压缩包", "安装包", "其他")

#: action 的合法取值
ACTIONS: tuple[str, ...] = ("move", "trash")


@dataclass
class FileItem:
    """一个待整理的文件。

    path          文件绝对路径
    name          文件名（含扩展名）
    size          字节大小
    category      分类标签，取值见 CATEGORIES
    suggested_path 建议归入的完整目标路径（含文件名）
    action        "move"（移动归档）或 "trash"（移进回收站）
    """

    path: str
    name: str
    size: int = 0
    category: str = "其他"
    suggested_path: str = ""
    action: str = "move"

    @property
    def extension(self) -> str:
        """小写扩展名（不含点）。无扩展名返回空串。"""
        idx = self.name.rfind(".")
        if idx <= 0:  # 没有点，或形如 ".gitignore" 的隐藏文件
            return ""
        return self.name[idx + 1 :].lower()

    def is_valid(self) -> bool:
        """自检：字段是否满足契约。D 集成时可用它做验收。"""
        return (
            bool(self.path)
            and bool(self.name)
            and isinstance(self.size, int)
            and not isinstance(self.size, bool)
            and self.size >= 0
            and self.category in CATEGORIES
            and self.action in ACTIONS
        )

    def to_dict(self) -> dict:
        """转成普通字典（界面表格 / 日志用）。"""
        return asdict(self)

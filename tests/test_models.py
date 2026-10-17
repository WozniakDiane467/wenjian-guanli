"""models.py 契约测试（A 地基工）。

这些测试是「防改名守卫」：ARCHITECTURE.md 冻结的字段名一旦被误改，这里立刻红。
"""

from __future__ import annotations

import pytest

from src.core.models import ACTIONS, CATEGORIES, FileItem

CONTRACT_FIELDS = ["path", "name", "size", "category", "suggested_path", "action"]


def test_字段名与契约完全一致():
    assert list(FileItem.__dataclass_fields__) == CONTRACT_FIELDS


def test_默认值符合契约():
    item = FileItem(path="C:\\Users\\me\\Desktop\\a.txt", name="a.txt")
    assert item.size == 0
    assert item.category == "其他"
    assert item.suggested_path == ""
    assert item.action == "move"


def test_分类与动作取值符合契约():
    assert CATEGORIES == ("文档", "图片", "视频", "音频", "压缩包", "安装包", "其他")
    assert ACTIONS == ("move", "trash")


@pytest.mark.parametrize(
    "name,expected",
    [("报告.DOCX", "docx"), ("包.tar.gz", "gz"), ("无扩展名", ""), (".gitignore", "")],
)
def test_扩展名解析(name, expected):
    assert FileItem(path="x", name=name).extension == expected


def test_is_valid():
    assert FileItem(path="C:\\a.txt", name="a.txt", size=3, category="文档", action="trash").is_valid() is True
    assert FileItem(path="", name="a.txt").is_valid() is False
    assert FileItem(path="C:\\a.txt", name="a.txt", category="未知分类").is_valid() is False
    assert FileItem(path="C:\\a.txt", name="a.txt", action="delete").is_valid() is False


def test_to_dict():
    item = FileItem(path="C:\\a.txt", name="a.txt", size=1, category="图片", suggested_path="C:\\图片\\a.txt")
    assert item.to_dict() == {
        "path": "C:\\a.txt",
        "name": "a.txt",
        "size": 1,
        "category": "图片",
        "suggested_path": "C:\\图片\\a.txt",
        "action": "move",
    }


def test_实例之间互不影响():
    a = FileItem(path="C:\\a", name="a")
    b = FileItem(path="C:\\b", name="b")
    a.category = "文档"
    assert b.category == "其他"

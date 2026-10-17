"""safety.py 验收测试（A 地基工）。

原则：涉及「破坏性」的断言一律只在临时目录里做实验；
真实的桌面/下载/文档/系统目录只做**只读**判断，绝不真去动它们。
"""

from __future__ import annotations

import os
import sys

import pytest

from src.core import safety
from src.core.safety import (
    NEVER_DELETE_ROOTS,
    SAFE_EXCLUDE_DIRS,
    is_deletable,
    is_protected_root,
    is_safe,
    move_to_trash,
    safe_move,
)

WINDOWS = sys.platform.startswith("win")
HOME = os.path.expanduser("~")
DESKTOP = os.path.join(HOME, "Desktop")


def _make(folder, name, text="x"):
    """在临时目录里造一个文件，返回路径对象。"""
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(str(folder), name)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)
    return path


# --------------------------------------------------------------------------- #
# 黑名单本身
# --------------------------------------------------------------------------- #

def test_黑名单覆盖契约要求的系统目录():
    normalized = {p.rstrip("\\").lower() for p in SAFE_EXCLUDE_DIRS}
    for required in ("c:\\windows", "c:\\program files", "c:\\program files (x86)", "c:\\programdata"):
        assert required in normalized, f"黑名单缺少 {required}"
    assert "c:" in normalized, "黑名单缺少系统盘根目录 C:\\"


def test_黑名单里都是绝对路径():
    for entry in SAFE_EXCLUDE_DIRS:
        assert os.path.isabs(entry), f"{entry} 不是绝对路径"


# --------------------------------------------------------------------------- #
# is_safe
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "path",
    [
        r"C:\Windows",
        r"C:\Windows\System32\drivers\etc\hosts",
        r"C:\Program Files\SomeApp\app.exe",
        r"C:\Program Files (x86)\OldApp\old.exe",
        r"C:\ProgramData\Microsoft\data.bin",
    ],
)
def test_系统目录一律不放行(path):
    assert is_safe(path) is False


def test_大小写不敏感():
    assert is_safe("c:\\wInDoWs\\SyStEm32") is False
    assert is_safe("C:\\pRoGrAm FiLeS\\x.exe") is False


def test_系统盘根目录不放行():
    assert is_safe("C:\\") is False
    assert is_safe("c:/") is False


def test_盘符根目录不会误伤整盘(tmp_path):
    """C:\\ 只保护它自己；C: 盘下的普通目录必须仍然可用。"""
    assert is_safe(str(tmp_path)) is True


def test_普通用户文件放行(tmp_path):
    sample = _make(tmp_path / "in", "报告.docx")
    assert is_safe(sample) is True
    assert is_safe(str(tmp_path)) is True
    assert is_safe(DESKTOP) is True


def test_非法输入一律不放行():
    assert is_safe("") is False
    assert is_safe("   ") is False
    assert is_safe(None) is False
    assert is_safe(123) is False


# --------------------------------------------------------------------------- #
# 受保护根目录（红线：绝不删/搬「桌面、下载、文档」本身）
# --------------------------------------------------------------------------- #

def test_桌面下载文档本身受保护():
    for name in ("Desktop", "Downloads", "Documents"):
        target = os.path.join(HOME, name)
        assert is_protected_root(target) is True
        assert is_deletable(target) is False


def test_主目录与盘根受保护():
    assert is_protected_root(HOME) is True
    assert is_deletable(HOME) is False
    assert is_deletable("C:\\") is False
    assert is_deletable(r"C:\Windows") is False


def test_桌面里的文件照常可整理():
    """红线只保护目录本身，里面的具体文件是正常可整理的。"""
    inside = os.path.join(DESKTOP, "旧截图.png")
    assert is_protected_root(inside) is False
    assert is_deletable(inside) is True


def test_永不删除集合包含黑名单():
    assert set(SAFE_EXCLUDE_DIRS).issubset(NEVER_DELETE_ROOTS)


# --------------------------------------------------------------------------- #
# move_to_trash
# --------------------------------------------------------------------------- #

def test_受保护目录拒绝进回收站():
    assert move_to_trash("C:\\") is False
    assert move_to_trash(r"C:\Windows") is False
    assert move_to_trash(HOME) is False
    assert move_to_trash(DESKTOP) is False


def test_不存在的文件与非法输入返回失败():
    assert move_to_trash(os.path.join(DESKTOP, "__A地基工测试用_不存在__.tmp")) is False
    assert move_to_trash("") is False
    assert move_to_trash(None) is False


@pytest.mark.skipif(not WINDOWS, reason="回收站行为只在 Windows 上验证")
def test_真实文件进回收站(tmp_path):
    victim = _make(tmp_path / "in", "待回收.txt", "bye")
    assert move_to_trash(victim) is True
    assert os.path.exists(victim) is False


@pytest.mark.skipif(not WINDOWS, reason="回收站行为只在 Windows 上验证")
def test_真实文件夹进回收站(tmp_path):
    folder = tmp_path / "待回收文件夹"
    _make(folder, "inside.txt")
    assert move_to_trash(str(folder)) is True
    assert folder.exists() is False


# --------------------------------------------------------------------------- #
# safe_move
# --------------------------------------------------------------------------- #

def test_基本移动并自动建目录(tmp_path):
    src = _make(tmp_path / "in", "报告.docx", "hello")
    dst = tmp_path / "文档" / "报告.docx"

    final = safe_move(src, str(dst))

    assert isinstance(final, str)
    assert os.path.exists(final) is True
    assert os.path.exists(src) is False
    assert os.path.basename(final) == "报告.docx"
    assert os.path.dirname(final) == str(tmp_path / "文档")
    with open(final, encoding="utf-8") as handle:
        assert handle.read() == "hello"


def test_同名不覆盖而是加后缀(tmp_path):
    target_dir = tmp_path / "文档"
    os.makedirs(target_dir, exist_ok=True)
    with open(target_dir / "报告.docx", "w", encoding="utf-8") as handle:
        handle.write("老文件")

    first = safe_move(_make(tmp_path / "in1", "报告.docx", "新1"), str(target_dir / "报告.docx"))
    second = safe_move(_make(tmp_path / "in2", "报告.docx", "新2"), str(target_dir / "报告.docx"))

    assert os.path.basename(first) == "报告 (1).docx"
    assert os.path.basename(second) == "报告 (2).docx"
    with open(target_dir / "报告.docx", encoding="utf-8") as handle:
        assert handle.read() == "老文件", "原文件被覆盖了，违反安全红线"
    with open(second, encoding="utf-8") as handle:
        assert handle.read() == "新2"


def test_目标受保护时拒绝移动(tmp_path):
    src = _make(tmp_path / "in", "a.txt")
    with pytest.raises(PermissionError):
        safe_move(src, r"C:\Windows\a.txt")
    assert os.path.exists(src) is True
    assert os.path.exists(r"C:\Windows\a.txt") is False


def test_源受保护时拒绝移动(tmp_path):
    with pytest.raises(PermissionError):
        safe_move(r"C:\Windows\notepad.exe", str(tmp_path / "notepad.exe"))


def test_绝不会把受保护根目录整体搬走(tmp_path, monkeypatch):
    """用「假桌面」验证逻辑，绝不拿真桌面做实验。"""
    fake_root = tmp_path / "假桌面"
    os.makedirs(fake_root, exist_ok=True)
    monkeypatch.setattr(safety, "NEVER_DELETE_ROOTS", set(safety.NEVER_DELETE_ROOTS) | {str(fake_root)})

    with pytest.raises(PermissionError):
        safe_move(str(fake_root), str(tmp_path / "搬走后"))
    assert os.path.exists(fake_root) is True


def test_源不存在时报错(tmp_path):
    with pytest.raises(FileNotFoundError):
        safe_move(str(tmp_path / "没有这个文件.txt"), str(tmp_path / "out.txt"))


def test_源与目标相同报错(tmp_path):
    src = _make(tmp_path / "in", "a.txt")
    with pytest.raises(ValueError):
        safe_move(src, src)
    assert os.path.exists(src) is True


def test_不能把文件夹搬进自己的子目录(tmp_path):
    folder = tmp_path / "袋子"
    os.makedirs(folder / "子目录", exist_ok=True)
    with pytest.raises(ValueError):
        safe_move(str(folder), str(folder / "子目录" / "袋子"))
    assert os.path.exists(folder) is True


def test_移动文件夹(tmp_path):
    folder = tmp_path / "相册"
    _make(folder, "1.png")
    target = tmp_path / "图片" / "相册"

    final = safe_move(str(folder), str(target))

    assert os.path.exists(os.path.join(final, "1.png")) is True
    assert os.path.exists(folder) is False

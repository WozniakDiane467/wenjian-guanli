"""安全红线层（A 地基工）——全项目唯一允许「动文件」的出口。

契约来源：docs/ARCHITECTURE.md 第 4.1 节；红线定义见 docs/PRD.md 第 5 节。

四条硬约束（本模块负责在代码层兜底，调用方忘了校验也不会出事）：
1. 绝不删除/清空「桌面、下载、文档」根目录本身（也含用户主目录、各盘根目录）；
2. 绝不触碰系统目录（Windows / Program Files / ProgramData / 系统盘根目录 …）；
3. 所有删除必须走 move_to_trash（进回收站）；本模块没有任何永久删除代码；
4. 移动前必须校验源和目标安全，同名自动加后缀 (1)/(2) 而不是覆盖。

用法：
    from src.core.safety import is_safe, safe_move, move_to_trash
"""

from __future__ import annotations

import os
import shutil

try:  # 缺失时模块仍可被 import（B/C/D 不会因此崩），只是删除动作会返回 False
    from send2trash import send2trash as _send2trash
except ImportError:  # pragma: no cover - 取决于环境
    _send2trash = None

__all__ = [
    "SAFE_EXCLUDE_DIRS",
    "NEVER_DELETE_ROOTS",
    "is_safe",
    "is_protected_root",
    "is_deletable",
    "move_to_trash",
    "safe_move",
]

# --------------------------------------------------------------------------- #
# 路径归一化
# --------------------------------------------------------------------------- #

def _norm(path: object) -> str:
    """把路径归一成「大小写不敏感 + 无尾分隔符 + 展开 ~ + 解析链接」的绝对形式。

    盘符根目录保留 ``c:\\`` 这种带尾分隔符的写法，便于识别。
    传入不可处理的值时抛 TypeError/ValueError，由调用方决定怎么兜底。
    """
    text = os.fspath(path)  # 非路径类型在这里抛 TypeError
    if isinstance(text, bytes):
        text = text.decode("utf-8", "surrogateescape")
    if not text.strip():
        raise ValueError("空路径")
    text = os.path.expanduser(text)
    text = os.path.abspath(text)
    try:
        text = os.path.realpath(text)  # 解析符号链接/目录联接，防止绕道进系统目录
    except OSError:  # pragma: no cover - 一般不会发生
        pass
    text = os.path.normcase(os.path.normpath(text))
    if len(text) == 2 and text[1] == ":":  # "c:" -> "c:\\"
        text += "\\"
    return text


def _is_drive_root(normalized: str) -> bool:
    """是否是盘符根目录（如 c:\\）。根目录只匹配它自己，不牵连整盘。"""
    return len(normalized) == 3 and normalized[1] == ":" and normalized[2] == "\\"


# --------------------------------------------------------------------------- #
# 受保护目录黑名单
# --------------------------------------------------------------------------- #

def _env(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


_SYSTEM_DRIVE = _env("SystemDrive") or "C:"
_SYSTEM_ROOT = _env("SystemRoot", "windir") or _SYSTEM_DRIVE + "\\Windows"
_PROGRAM_FILES = _env("ProgramFiles") or _SYSTEM_DRIVE + "\\Program Files"
_PROGRAM_FILES_X86 = _env("ProgramFiles(x86)", "ProgramFiles(x86)") or _SYSTEM_DRIVE + "\\Program Files (x86)"
_PROGRAM_DATA = _env("ProgramData") or _SYSTEM_DRIVE + "\\ProgramData"

_RAW_EXCLUDES: list[str] = [
    _SYSTEM_DRIVE + "\\",           # 系统盘根目录本身
    _SYSTEM_ROOT,                   # C:\Windows
    _SYSTEM_ROOT + "\\System32",    # 显式列出，读代码时一眼可见
    _SYSTEM_ROOT + "\\SysWOW64",
    _PROGRAM_FILES,
    _PROGRAM_FILES_X86,
    _PROGRAM_DATA,
]

# 其他盘（D:\ E:\ …）的根目录也不允许整个动。Python 3.12+ 才有 os.listdrives，
# 取不到就跳过，不影响功能（老版本仍有系统盘根目录兜底）。
for _drive in getattr(os, "listdrives", lambda: [])():
    _RAW_EXCLUDES.append(_drive if _drive.endswith("\\") else _drive + "\\")

#: 受保护目录黑名单（原始绝对路径，供其他模块读取/展示）。
#: 判定时大小写不敏感；这里是「黑名单树」，落在其中的路径一律不放行。
SAFE_EXCLUDE_DIRS: set[str] = {d for d in _RAW_EXCLUDES if d}

# --------------------------------------------------------------------------- #
# 永不删除的根目录（桌面/下载/文档本身、用户主目录、各盘根、系统目录）
# --------------------------------------------------------------------------- #

_HOME = os.path.expanduser("~")
_USER_ROOT_CANDIDATES = [
    _HOME,
    os.path.join(_HOME, "Desktop"),
    os.path.join(_HOME, "Downloads"),
    os.path.join(_HOME, "Documents"),
    os.path.join(_HOME, "OneDrive", "Desktop"),
    os.path.join(_HOME, "OneDrive", "Downloads"),
    os.path.join(_HOME, "OneDrive", "Documents"),
]

#: 「只允许整理里面的文件，绝不允许动它本身」的根目录集合。
NEVER_DELETE_ROOTS: set[str] = set(_USER_ROOT_CANDIDATES) | set(SAFE_EXCLUDE_DIRS)


# --------------------------------------------------------------------------- #
# 对外的三个判定 + 两个动作
# --------------------------------------------------------------------------- #

def is_safe(path: str) -> bool:
    """判断路径是否允许操作（不在黑名单内）。

    供 B 扫描、C 执行时调用。
    - 路径本身或它的任一级父目录落在 SAFE_EXCLUDE_DIRS 内 → False；
    - 盘符根目录（C:\\ D:\\ …）只保护它自己，不会误伤整盘里的文件；
    - 传空值/非法值一律 False（宁可不做，不可做错）。
    """
    try:
        target = _norm(path)
    except (TypeError, ValueError):
        return False
    for blocked in SAFE_EXCLUDE_DIRS:
        try:
            blocked_norm = _norm(blocked)
        except (TypeError, ValueError):
            continue
        if _is_drive_root(blocked_norm):
            if target == blocked_norm:
                return False
            continue
        if target == blocked_norm or target.startswith(blocked_norm + "\\"):
            return False
    return True


def is_protected_root(path: str) -> bool:
    """路径是否**本身就是**那个不能被删/被挪走的根目录（精确匹配）。"""
    try:
        target = _norm(path)
    except (TypeError, ValueError):
        return True  # 判不出来就当它是受保护的，安全优先
    for root in NEVER_DELETE_ROOTS:
        try:
            if target == _norm(root):
                return True
        except (TypeError, ValueError):
            continue
    return False


def is_deletable(path: str) -> bool:
    """能否把这个路径送进回收站：既不在黑名单里，也不是受保护的根目录本身。"""
    return is_safe(path) and not is_protected_root(path)


def move_to_trash(path: str) -> bool:
    """把文件/文件夹移进回收站（用 send2trash），返回是否成功。

    受保护目录、非法路径、文件不存在、send2trash 不可用 → 返回 False。
    本函数永远不会永久删除：没有任何 os.remove / shutil.rmtree 调用。
    """
    if _send2trash is None:
        return False
    if not is_deletable(path):
        return False
    try:
        target = os.path.abspath(os.path.expanduser(os.fspath(path)))
    except (TypeError, ValueError):
        return False
    if not os.path.lexists(target):
        return False
    try:
        _send2trash(target)
        return True
    except Exception:  # 回收站不可用/被占用等，一律视为失败，绝不降级为永久删除
        return False


def _unique_path(destination: str) -> str:
    """目标已存在时，自动追加 (1)/(2)/… 直到不冲突，返回可用路径。"""
    if not os.path.exists(destination):
        return destination
    stem, ext = os.path.splitext(destination)
    index = 1
    while True:
        candidate = f"{stem} ({index}){ext}"
        if not os.path.exists(candidate):
            return candidate
        index += 1
        if index > 9999:  # pragma: no cover - 极端情况兜底
            raise OSError(f"同名文件过多，无法为 {destination} 生成新名字")


def safe_move(src: str, dst: str) -> str:
    """安全移动：先 is_safe 校验，遇到同名自动加后缀 (1)/(2)，返回最终路径；失败抛异常。

    抛出：PermissionError（源/目标不安全、或源是受保护根目录本身）、
          FileNotFoundError（源不存在）、ValueError（路径为空/源目标相同/目标在源内部）、
          OSError（磁盘层面的失败，如跨盘复制出错）。
    """
    try:
        src_abs = os.path.abspath(os.path.expanduser(os.fspath(src)))
        dst_abs = os.path.abspath(os.path.expanduser(os.fspath(dst)))
    except (TypeError, ValueError) as exc:
        raise ValueError(f"路径非法：src={src!r} dst={dst!r}") from exc

    if not is_safe(src_abs):
        raise PermissionError(f"源路径位于受保护目录内，已拒绝移动：{src_abs}")
    if not is_safe(dst_abs):
        raise PermissionError(f"目标路径位于受保护目录内，已拒绝移动：{dst_abs}")
    if is_protected_root(src_abs):
        raise PermissionError(f"受保护目录本身不允许移动：{src_abs}")
    if not os.path.exists(src_abs):
        raise FileNotFoundError(f"源文件不存在：{src_abs}")

    src_norm, dst_norm = _norm(src_abs), _norm(dst_abs)
    if src_norm == dst_norm:
        raise ValueError(f"源路径与目标路径相同，无需移动：{src_abs}")
    if dst_norm.startswith(src_norm + "\\"):
        raise ValueError(f"不能把文件夹移动到它自己的子目录里：{src_abs} -> {dst_abs}")

    parent = os.path.dirname(dst_abs)
    if parent:
        os.makedirs(parent, exist_ok=True)

    final_path = _unique_path(dst_abs)
    shutil.move(src_abs, final_path)
    return final_path

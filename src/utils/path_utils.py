"""路径工具函数。"""

from pathlib import Path
from typing import Union


def resolve_path(base_dir: Union[str, Path], file_path: str) -> str:
    """解析文件路径。"""
    base_path = Path(base_dir)
    file_path_obj = Path(file_path)
    
    # 如果是绝对路径且存在，直接返回
    if file_path_obj.is_absolute() and file_path_obj.exists():
        return str(file_path_obj)
    
    # 如果是绝对路径但不存在，回退到 base_dir + 去掉前导分隔符的拼接
    if file_path_obj.is_absolute():
        file_path = str(file_path_obj.relative_to(file_path_obj.anchor))
    
    # 相对路径，与 base_dir 拼接
    resolved_path = base_path / file_path
    
    # 如果拼接后的路径存在，返回它
    if resolved_path.exists():
        return str(resolved_path)
    
    # 如果拼接后的路径不存在，尝试直接使用原路径
    if file_path_obj.exists():
        return str(file_path_obj)
    
    # 最后返回拼接后的路径（即使不存在）
    return str(resolved_path)


def ensure_dir(dir_path: Union[str, Path]) -> None:
    """确保目录存在。"""
    Path(dir_path).mkdir(parents=True, exist_ok=True)

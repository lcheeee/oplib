"""端口占用检测与进程终止工具。

优先使用 psutil 实现跨平台端口占用检测和进程终止；
在 Windows 上如果未安装 psutil，则回退到 netstat/taskkill；
在 Linux/macOS 上如果未安装 psutil，则回退到 lsof/kill。
"""

from __future__ import annotations

import subprocess
import sys
from typing import List, Optional


def _is_windows() -> bool:
    return sys.platform.startswith("win")


def find_pids_by_port(port: int) -> List[int]:
    """查找占用指定端口的进程PID列表。"""
    try:
        import psutil  # type: ignore
        pids: List[int] = []
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and getattr(conn.laddr, "port", None) == port:
                if conn.pid is not None and conn.pid > 0:
                    pids.append(conn.pid)
        return sorted(list(set(pids)))
    except Exception:
        # 回退实现
        if _is_windows():
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                f"(Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue) | Select-Object -ExpandProperty OwningProcess"
            ]
            try:
                output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            except Exception:
                # 进一步回退 netstat
                cmd = ["netstat", "-ano"]
                output = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL)
            pids: List[int] = []
            for line in output.splitlines():
                line = line.strip()
                if not line:
                    continue
                if f":{port} " in line or line.endswith(f":{port}"):
                    try:
                        pid = int(line.split()[-1])
                        if pid > 0:
                            pids.append(pid)
                    except Exception:
                        continue
            return sorted(list(set(pids)))
        else:
            # 尝试 lsof
            try:
                output = subprocess.check_output(["lsof", f"-i:{port}", "-sTCP:LISTEN", "-n", "-P"], text=True)
                pids: List[int] = []
                for line in output.splitlines()[1:]:
                    parts = line.split()
                    if len(parts) > 1:
                        try:
                            pids.append(int(parts[1]))
                        except Exception:
                            pass
                return sorted(list(set(pids)))
            except Exception:
                # 尝试 ss
                try:
                    output = subprocess.check_output(["ss", "-ltnp"], text=True)
                    pids: List[int] = []
                    for line in output.splitlines():
                        if f":{port} " in line or line.endswith(f":{port}"):
                            # 解析 pid=1234
                            if "pid=" in line:
                                try:
                                    seg = line.split("pid=")[1]
                                    pid_str = seg.split(",")[0].strip()
                                    pids.append(int(pid_str))
                                except Exception:
                                    pass
                    return sorted(list(set(pids)))
                except Exception:
                    return []


def kill_process(pid: int, force: bool = True) -> bool:
    """根据 PID 终止进程。返回是否成功。"""
    try:
        import psutil  # type: ignore
        proc = psutil.Process(pid)
        if force:
            proc.kill()
        else:
            proc.terminate()
        return True
    except Exception:
        # 回退到系统命令
        try:
            if _is_windows():
                cmd = ["taskkill", "/PID", str(pid), "/F" if force else "/T"]
            else:
                cmd = ["kill", "-9" if force else "-15", str(pid)]
            subprocess.check_call(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return True
        except Exception:
            return False


def ensure_port_available(port: int, auto_kill: bool = False) -> Optional[List[int]]:
    """确保端口可用。如果被占用：
    - auto_kill=False: 返回占用该端口的PID列表（非空表示被占用）
    - auto_kill=True: 尝试终止占用该端口的所有进程；返回被终止的PID列表（可能为空）
    """
    pids = find_pids_by_port(port)
    if not pids:
        return []
    if not auto_kill:
        return pids
    killed: List[int] = []
    for pid in pids:
        if kill_process(pid, force=True):
            killed.append(pid)
    return killed



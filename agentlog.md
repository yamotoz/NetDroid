# NetDroid — Agent Log (Diário de Bordo Técnico)

## Sessão: 2026-04-26

### Contexto
Construção completa do `NetDroid.py` — script single-file de análise de redes WiFi, nível profissional, para execução no Termux (Android) sem root.

---

### Arquitetura Implementada

O script é composto por **12 classes** em um único arquivo (`NetDroid.py`, ~1690 linhas):

| Classe | Responsabilidade |
|---|---|
| `TerminalUI` | Interface terminal cyberpunk via `rich`. Banner ASCII, tabelas, progress bars, logging colorido, consent prompts. Graceful fallback para print() se rich indisponível. |
| `NetworkDetector` | Auto-detecção de gateway/subnet/local IP/SSID. Métodos: `ip route`, socket probe, `termux-wifi-connectioninfo`, `iwgetid`, `nmcli`. Cria pasta de output com nome do SSID. |
| `HostDiscovery` | Descoberta de hosts: lê `/proc/net/arp` (sem root), ping sweep asyncio paralelo, TCP probe em hosts silenciosos (portas 80,443,22,8080,8443), TTL fingerprint (Linux/Windows/iOS), MAC vendor lookup offline (100+ prefixos). |
| `PortScanner` | TCP connect scan 100% asyncio. 3 modos: `normal` (top 20), `insane` (1-65535), `stealth` (top 100, delays random). Banner grabbing em portas abertas. Service fingerprint por porta + banner. |
| `LatencyMonitor` | Thread daemon que faz ping contínuo ao gateway durante stress tests. Mede baseline, avg, min, max, packet loss. |
| `StressEngine` | Orquestrador de stress: TCP connection flood (escalas crescentes), UDP storm (broadcast, payload 65507 bytes), HTTP storm (aiohttp, requisições crescentes). Modo `overflow` com iperf3 (TCP/UDP, throughput, jitter, loss). |
| `GodMode` | Modo agressivo: UDP broadcast sweep, SSDP M-SEARCH, NetBIOS name query, HTTP deep probe, API endpoint discovery, RTSP discovery. Ataques avançados em IoT: ONVIF WS-Discovery, HTTP Slowloris, RTSP Connection Exhaustion, Mirai Telnet/SSH Brute-force. |
| `ReportEngine` | Gera relatório HTML cyberpunk (tema escuro, cards com borda vermelha, SVG topology map, tabelas de hosts/serviços/credenciais) e resumo executivo TXT. |
| `Upgrader` | Auto-update do GitHub: compara versão, faz backup, substitui automaticamente. |

---

### Decisões Técnicas

1. **Zero dependência de root**: Todo o scan é TCP connect via asyncio (não usa raw sockets). ARP cache lido de `/proc/net/arp` (disponível sem root no Linux/Termux/Windows).

2. **Cross-Platform nativo**: Funciona em Linux/Termux e Windows. O script ajusta dinamicamente `ping` (`-c` vs `-n`), roteamento (`ip route` vs `ipconfig`) e leitura de cache MAC (`/proc/net/arp` vs `arp -a`).

3. **Dependências mínimas**: Removidos `scapy`, `python-nmap`, `netifaces`, `mac-vendor-lookup` do requirements. O script resolve tudo nativamente.

4. **Asyncio puro**: Ping sweep, TCP scan, banner grabbing, HTTP probes — tudo assíncrono com semáforos para controle de concorrência (`CONCURRENT_LIMIT = 500`).

5. **Ataques IoT não-privilegiados**: Os ataques `--slowloris`, `--rtsp-kill` e `--mirai` operam inteiramente na camada 7 (aplicação), permitindo travar dispositivos e descobrir credenciais sem raw sockets.

---

### CLI — Flags e Combinações

```
--auto          Auto-detect gateway/subnet
--t TARGET      Alvo manual (IP ou subnet CIDR)
--discover      Descoberta completa de hosts
--normal        Scan top 20 portas
--Insane        Scan 1-65535 (velocidade máxima)
--stealth       Scan top 100 (furtivo)
--ports P,P,P   Portas customizadas
--overfull      Stress pesado (TCP+UDP+HTTP flood)
--overflow      Stress profissional (iperf3)
--god           God Mode (broadcast+NetBIOS+HTTP probe)
--slowloris     [GOD] HTTP Slowloris attack (Esgota conexões web de IoT)
--rtsp-kill     [GOD] RTSP Connection exhaustion (Trava câmeras IP)
--onvif         [GOD] ONVIF WS-Discovery (Detecta câmeras IP em multicast)
--mirai         [GOD] Mirai botnet brute-force (Telnet/SSH senhas padrão)
--upgrade       Auto-update do GitHub
--version       Versão atual
```

**Ordem de execução**: NetworkDetector → HostDiscovery → PortScanner → StressEngine → GodMode → ReportEngine

**Combinações**: Flags são aditivas. `--auto --discover --Insane --god` executa discover + scan insane + god mode em sequência.

---

### Estrutura de Output

```
{SSID}/
├── report_YYYY-MM-DD_HHhMM.html   ← relatório cyberpunk completo
└── {SSID}_YYYY-MM-DD.txt           ← resumo executivo texto
```

---

### Databases Embutidos

- **MAC Vendors**: 100+ prefixos (Apple, Samsung, TP-Link, Hikvision, Dahua, ASUS, MikroTik, Cisco, Intel, Huawei, Raspberry Pi, etc.)
- **Default Credentials**: 10 fabricantes × múltiplas combinações (generic, dahua, hikvision, tp-link, asus, mikrotik, d-link, linksys, cisco, huawei)
- **Service Map**: 70+ portas mapeadas para nomes de serviço
- **RTSP Paths**: 12 paths comuns de câmeras IP
- **API Endpoints**: 11 endpoints comuns de dispositivos IoT/roteadores
- **Device Fingerprints**: 18 assinaturas de fabricantes por análise de título/body/server HTTP

---

### Instalação no Termux

```bash
pkg update && pkg upgrade
pkg install python iperf3
pip install -r requirements.txt
python NetDroid.py --version
```

Opcionais: `pkg install nmap` (para OS detection avançado)

---

### Notas para Agentes Futuros

- O arquivo é **single-file** por design. Não fragmentar.
- Todas as constantes editáveis estão no topo do arquivo (VERSION, URLs, NETBIOS_MESSAGE, etc.)
- `HAS_RICH`, `HAS_AIOHTTP`, etc. são flags de graceful degradation — o script funciona mesmo sem dependências opcionais.
- O `TerminalUI` tem fallback completo para `print()` quando `rich` não está instalado.
- Para adicionar novos fabricantes de MAC: editar `MAC_VENDORS` dict.
- Para adicionar novas credenciais padrão: editar `DEFAULT_CREDS` dict.
- O relatório HTML é gerado com f-strings puras (sem Jinja2) para eliminar dependência.
- `asyncio.run()` é o entry point — compatível com Python 3.7+.

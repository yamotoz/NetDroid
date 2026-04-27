md# NetDroid — Plano Completo de Engenharia

## Visão geral

Script Python single-file de análise de redes WiFi, nível profissional.
Temática cyberpunk, terminal elegante com rich, sem necessidade de root.

**Arquivos do projeto:**
- `NetDroid.py` — script principal (arquivo único)
- `requirements.txt` — dependências Python
- `agentlog.md` — memória de sessões para agentes IA
- `README.md` — documentação

**Output gerado automaticamente:**
- Pasta com nome da rede Wi-Fi detectada
- `report_YYYY-MM-DD_HHhMM.html` — relatório cyberpunk com gráficos
- `NomeDaRede_YYYY-MM-DD.txt` — resumo executivo

---

## Módulos

### 1. discover — Descoberta de hosts
python NetDroid.py --discover
python NetDroid.py --t 192.168.0.0/24 --discover

**Features:**
- ARP cache reader — lê /proc/net/arp sem root
- Ping sweep asyncio — ICMP paralelo com gráfico de latência no terminal
- TCP probe discovery — confirm hosts que não respondem ICMP (portas 80,443,22,8080,8443)
- MAC vendor lookup — identifica fabricante offline (Apple, Samsung, TP-Link, Hikvision...)
- OS fingerprint por TTL — TTL64=Linux/Android, TTL128=Windows, TTL255=iOS/Cisco
- Auto-detect subnet e gateway via ip route + socket (zero config)

---

### 2. scan — Port Scanning & Serviços
python NetDroid.py --mode normal
python NetDroid.py --mode Insane
python NetDroid.py --mode stealth
python NetDroid.py --t 192.168.1.5 Insane
python NetDroid.py --ports 80,443,8080,8443

**Modos:**
- `--normal` — top 20 portas mais usadas, balanceado
- `--Insane` — 1-65535 completo (equivalente ao -p- do nmap), máxima velocidade
- `--stealth` — top 100 portas, delays randomizados, evasão de detecção

**Features:**
- TCP connect scan 100% asyncio Python puro (sem root)
- nmap integration quando disponível (OS detection avançado, -sV -O)
- Banner grabbing — SSH version, HTTP Server, FTP banner, Telnet prompt
- Service fingerprint — identifica serviço por porta + banner
- IoT/câmera profile — portas 554 (RTSP), 8000, 8080, 37777, 34567, 8888
- Web server enum — GET /, coleta title, server header, formulários de login
- SMB/NetBIOS detect — porta 445 e 139, NetBIOS name query

---

### 3. stress — Teste de Carga (rede própria)
python NetDroid.py --overfull 
python NetDroid.py --overfull 
python NetDroid.py --overflow

**Modo --overfull (pesado — testar limites reais):**
- TCP connection flood — asyncio abre conexões simultâneas crescentes (100→500→1000→...) até colapso
- UDP storm — socket sendto() paralelo com payloads de 65507 bytes para gateway e broadcast
- HTTP storm — aiohttp dispara requisições crescentes contra painel admin do roteador
- Detecta ponto exato de colapso com timestamp preciso
- Flag --confirm obrigatória para evitar execução acidental

**Modo --overflow (profissional com métricas):**
- iperf3 TCP e UDP — mede throughput real, jitter, packet loss
- Gera curva de saturação progressiva
- Relatório com percentis de latência

**Monitor paralelo (ambos os modos):**
- Thread separada faz ping contínuo durante o stress
- Mede latência baseline vs pico em tempo real
- Detecta degradação e tempo de recuperação

---

### 4. --god — God Mode (interação em massa)
python NetDroid.py --god


**Sub-módulo: UDP Broadcast**
- Payload UDP de 65507 bytes (máximo IPv4) enviado para broadcast da subnet
- Multi-port sweep: portas 9, 7, 1900 (UPnP/SSDP), 5353 (mDNS), 137 (NetBIOS)
- Listener paralelo — coleta respostas e identifica serviços ocultos
- SSDP M-SEARCH para 239.255.255.250:1900 — descobre Smart TVs, consoles, impressoras

**Sub-módulo: NetBIOS Popup**
- NetBIOS name query broadcast (porta 137) — lista todos os hosts Windows
- Envia mensagem "O relogio bate as 4" via NetBIOS datagram para cada host Windows
- Fallback SMB via porta 445

**Sub-módulo: HTTP Deep Probe**
- Crawl paralelo (aiohttp) em todos os hosts com porta web aberta
- Coleta: title, server, headers, cookies, formulários, links, comentários HTML
- Device fingerprint por assinatura de página (TP-LINK, DAHUA, Hikvision, ASUS, MikroTik...)
- Login form detection — detecta campos type=password
- Default credential audit — testa credenciais padrão por fabricante:
  - Genérico: admin/admin, admin/1234, admin/password, root/root, user/user
  - DAHUA: admin/admin
  - Hikvision: admin/12345
  - TP-Link: admin/admin, admin/(vazio)
  - ASUS: admin/admin
  - MikroTik: admin/(vazio)
- API endpoint discovery — testa /api/, /cgi-bin/, /admin/, /login, /status, /config.xml
- RTSP stream discovery — testa rtsp://ip/live, /stream, /ch01, /video1, /cam/realmonitor
- Relatório dedicado com credentials encontradas em destaque

---

### 5. --upgrade
python NetDroid.py --upgrade
- Compara versão local com GitHub raw (URL configurável no topo do arquivo como constante)
- Faz backup do arquivo atual antes de substituir
- Baixa e aplica nova versão automaticamente

---

# NetDroid — CLI Atualizado

---

## Flags principais
--auto          detecta IP/subnet do roteador automaticamente
--t             define alvo manual (IP ou subnet)  ex: --t 192.168.1.5
--discover      realiza descoberta completa de hosts
--normal        port scan top 20 portas, balanceado
--Insane        port scan 1-65535 completo, máxima velocidade
--stealth       port scan top 100, furtivo, delays randomizados
--ports         portas customizadas  ex: --ports 80,443,8080
--overfull      stress pesado (TCP flood + UDP storm + HTTP storm)
--overflow      stress profissional com métricas (iperf3)
--god           god mode básico (broadcast + NetBIOS + HTTP deep probe)
--slowloris     [God Mode] HTTP Slowloris attack (derruba webservers IoT)
--rtsp-kill     [God Mode] RTSP Connection exhaustion (trava/reinicia câmeras)
--onvif         [God Mode] ONVIF WS-Discovery (enumera câmeras via multicast)
--mirai         [God Mode] Mirai botnet brute-force (testa credenciais Telnet/SSH)
--upgrade       atualiza o script do GitHub
--version       exibe versão atual

---

## Exemplos de uso

```bash
# Só descoberta automática
python NetDroid.py --auto --discover

# Descoberta + scan normal
python NetDroid.py --auto --discover --normal

# Descoberta + scan insano
python NetDroid.py --auto --discover --Insane

# Descoberta + stress pesado
python NetDroid.py --auto --discover --overfull

# Descoberta + stress pesado no modo insano
python NetDroid.py --auto --discover --overfull --Insane

# Descoberta + god mode
python NetDroid.py --auto --discover --god

# Tudo junto — o combo completo
python NetDroid.py --auto --discover --god --overfull --Insane

# Alvo manual
python NetDroid.py --t 192.168.1.5 --Insane
python NetDroid.py --t 192.168.0.0/24 --discover --normal

# Portas customizadas
python NetDroid.py --auto --ports 80,443,8080,8443

# Utilitários
python NetDroid.py --upgrade
python NetDroid.py --version
```

---

## Lógica de combinação de flags
--auto           → detecta gateway/subnet sozinho
--t              → sobrescreve o --auto se usado junto
--discover       → sempre roda antes de qualquer outra operação
--normal         → scan após discover (se --discover presente)
--Insane         → modifica velocidade do scan OU do stress
--stealth        → modifica comportamento para furtivo
--overfull       → roda stress pesado após scan (se scan presente)
--overflow       → roda stress profissional
--god            → roda broadcast + NetBIOS + HTTP deep probe
flags combinadas → executadas em sequência: discover → scan → stress → god

---

## Ordem de execução quando combinadas

NetworkDetector  (--auto ou --t) --t eu vou dizer o ip logo em seguida e --auto não irei
HostDiscovery    (--discover)
PortScanner      (--normal / --Insane / --stealth / --ports)
StressEngine     (--overfull / --overflow)
GodMode          (--god)
ReportEngine     (HTML + TXT gerados sempre ao final)


---

## Observações

- `--god` já engloba broadcast + NetBIOS popup + HTTP deep probe (não precisa de subflags)
- `--Insane` modifica tanto o scan (velocidade máxima) quanto o stress (sem limites)
- `--discover` pode rodar sozinho ou como pré-requisito de qualquer outro módulo
- Todo output vai para pasta `{nome-da-rede}/` criada automaticamente
- `--auto` é recomendado sempre — só use `--t` se quiser sobrescrever

---

## Arquitetura interna (NetDroid.py)
NetDroidCore          — argparse, banner, consent, roteamento
NetworkDetector       — auto-detect subnet/gateway/SSID, cria pasta output
HostDiscovery         — ARP cache, ping sweep, TCP probe, TTL, MAC vendor
PortScanner           — asyncio TCP scan, modos, integração nmap
ServiceFingerprint    — banner grabbing, service dict, IoT profile, web enum, SMB
StressEngine          — orchestrador
TCPFloodWorker      — asyncio connection flood
UDPStormWorker      — socket UDP flood
HTTPStormWorker     — aiohttp request storm
BandwidthTester     — iperf3 wrapper
LatencyMonitor      — ping paralelo durante stress
GodMode               — orchestrador god
BroadcastEngine     — UDP broadcast + SSDP
NetBIOSMessenger    — popup Windows
HTTPDeepProbe       — crawl + fingerprint
DefaultCredAuditor  — audit de credenciais padrão
RTSPDiscovery       — descoberta de streams
ReportEngine          — HTML Jinja2 + .txt executivo
TerminalUI            — rich: tabelas, progress, live, cores cyberpunk
Upgrader              — auto-update do GitHub

---

## requirements.txt
rich>=13.0
colorama>=0.4
aiohttp>=3.9
requests>=2.31
scapy>=2.5
beautifulsoup4>=4.12
lxml>=4.9
python-nmap>=0.7
netifaces>=0.11
mac-vendor-lookup>=0.1
jinja2>=3.1

---

## Instalação no Termux

```bash
pkg update && pkg upgrade
pkg install python nmap iperf3
pip install -r requirements.txt
python NetDroid.py --version
```

---

## Tema visual (terminal)

- Background: #0a0a0a (preto profundo)
- Texto principal: #ffffff
- Destaque / alertas: #cc0000 (vermelho sangue)
- Sucesso / hosts ativos: #00ff41 (verde terminal)
- Avisos: #ffcc00 (amarelo)
- Fonte: monospace via rich
- Banner ASCII do NetDroid no topo de cada execução
- Tabelas com bordas finas, progress bars animadas, spinners

---

## Tema HTML report

- Background: #0a0a0a
- Cards com borda #cc0000
- Texto branco
- Gráficos SVG inline (latência, banda, hosts)
- Tabela de hosts com colunas: IP, MAC, Fabricante, OS, Portas, Serviços
- Seção de credenciais encontradas em vermelho com destaque
- Mapa de topologia SVG (roteador no centro, hosts em volta)

---

## Ordem de desenvolvimento (fases)
Fase 1 — Core + TerminalUI + NetworkDetector + Upgrader
Fase 2 — HostDiscovery (discover completo)
Fase 3 — PortScanner + ServiceFingerprint (scan completo)
Fase 4 — StressEngine (stress --overfull e --overflow)
Fase 5 — GodMode (broadcast + NetBIOS + HTTP deep probe)
Fase 6 — ReportEngine (HTML cyberpunk + .txt executivo)

---

## Constantes editáveis no topo do arquivo

```python
VERSION = "1.0.0"
GITHUB_RAW_URL = "https://raw.githubusercontent.com/SEU_USER/SEU_REPO/main/NetDroid.py"
GITHUB_VERSION_URL = "https://raw.githubusercontent.com/SEU_USER/SEU_REPO/main/VERSION"
NETBIOS_MESSAGE = "O relogio bate as 4"
DEFAULT_SCAN_MODE = "normal"
STRESS_MAX_DURATION = 300  # segundos máximos para --overfull
```

---

*NetDroid — desenvolvido para auditoria de redes sob autorização do responsável.*
*Use apenas em redes de sua propriedade ou com permissão explícita.*
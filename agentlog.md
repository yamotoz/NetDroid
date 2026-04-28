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

## Sessão: 2026-04-27

### Diário de bordo (análise inicial do repo)

Contexto: revisão do projeto no workspace `C:\Users\diluc\Desktop\NetDroid` para entender a arquitetura real (código) vs documentação.

Arquivos no root:
- `NetDroid.py` (script único, ~2.1k linhas)
- `README.md` (uso e flags)
- `ideia.md` (plano/engenharia; parece conter partes antigas e/ou mais extensas do que o requirements atual)
- `requirements.txt` (dependências: rich, colorama, aiohttp, requests, bs4, lxml)
- `agentlog.md` (este arquivo)

O que o código realmente tem (NetDroid.py):
- 9 classes: `TerminalUI`, `NetworkDetector`, `HostDiscovery`, `PortScanner`, `LatencyMonitor`, `StressEngine`, `GodMode`, `ReportEngine`, `Upgrader`.
- Flags no parser: `--auto`, `--t`, `--discover`, `--normal`, `--Insane`, `--stealth`, `--ports`, `--overfull`, `--overflow`, `--flood`, `--god`, `--slowloris`, `--rtsp-kill`, `--onvif`, `--mirai`, `--upgrade`, `--version`.
- Orquestração: detect/rede → (opcional) discover → (opcional) scan → (opcional) stress → (opcional) god → report (exceto quando `--flood`).
- Há prompts de consentimento para operações de risco (stress pesado e rotinas do `GodMode`).

Pontos importantes (ética/segurança):
- Existem rotinas explicitamente destrutivas/invasivas no `GodMode` (ex.: DoS por slowloris/rtsp exhaustion e brute-force estilo “mirai”).
- Mesmo com prompts de consentimento, isso aumenta o risco de uso indevido. Para manter o projeto estritamente “ético”, faz sentido separar bem “auditoria passiva” vs “ação ativa” e endurecer guardrails (ex.: exigir flag extra + aviso + log de autorização, ou remover por padrão).

Próximos passos de análise:
1) Mapear o dataflow completo (dados por host: ip/mac/vendor/os/latência/portas/serviços) e onde cada módulo escreve/consome.
2) Revisar a geração de relatórios (campos, sanitização, persistência em disco).
3) Revisar a superfície de risco (funções ativas) e propor modo “safe by default” para auditoria/autorização.

### Atualização de implementação (2026-04-27)

Mudanças aplicadas no `NetDroid.py` para orientar o fluxo a auditoria defensiva:

- Adicionada a flag `--godfall` como modo de resiliência controlado (não-destrutivo), com métricas por host.
- `--god` remodelado para auditoria profunda: inventário, exposição web/API/RTSP/ONVIF e scoring de risco por host.
- Rotinas ofensivas (`--mirai`, `--slowloris`, `--rtsp-kill`) mantidas apenas como flags legadas com aviso de desativação.
- `_audit_default_creds` removido do fluxo e substituído por avaliação passiva de superfície de login (`_evaluate_login_surface`).
- Adicionado motor de risco (`_assess_risks`) com findings estruturados (`risk_findings`).
- Fluxo principal atualizado para incluir `--godfall` em `has_action`, execução no `StressEngine` e inclusão de riscos em `god_data`.
- Relatório HTML revisado para melhor responsividade (desktop/mobile), tabela com scroll, cards e seções novas:
  - `Risk Findings`
  - `Godfall Resilience`
  - `Latency During Stress`
- Relatório TXT revisado para formato executivo enxuto com:
  - resumo geral
  - risco por host
  - top findings
  - bloco de resiliência do Godfall
- NetBIOS em modo inventário: envio ativo de mensagem desativado.

Validação:
- `python -m py_compile NetDroid.py` executado com sucesso.
- `python NetDroid.py --version` executado com sucesso.

### Iteração adicional do Godfall (2026-04-27)

Reforço aplicado no `--godfall` sem sair do escopo de resiliência controlada:

- O fluxo deixou de ser sweep simples e virou benchmark em fases:
  - `VANGUARD`
  - `SIEGE`
  - `OVERDRIVE`
- Cada fase agora tem:
  - multiplicador de tentativas por host
  - concorrência própria
  - delay próprio entre operações
  - snapshot de latência
- O benchmark usa mix de operações por serviço:
  - `tcp-connect`
  - `http-head`
  - `http-get`
- Hosts são priorizados com gateway primeiro para leitura operacional mais útil.
- Resultado do Godfall agora registra:
  - `phases`
  - `per_host`
  - `avg_success_rate`
  - métricas médias por host
- Relatórios HTML/TXT atualizados para exibir as fases e ranking de resiliência.
- Godfall ganhou telemetria de fase e safety rails:
  - taxa de sucesso global por fase
  - abort automático por degradação (latência/loss/sucesso) com motivo registrado
  - janela de recuperação (tempo até a latência voltar ao alvo)
  - reutilização de sessão HTTP por fase quando `aiohttp` está disponível (mais realista e eficiente)

Validação pós-reforço:
- `python -m py_compile NetDroid.py` executado com sucesso.

### Godfall apex / TITANFALL (2026-04-27)

Reforço exponencial do `--godfall` para colocá-lo no mesmo patamar (ou acima) do `--flood`, mantendo a estética em fases e os safety rails:

- Constantes recalibradas em `NetDroid.py`:
  - `GODFALL_ATTEMPTS` 30 → 160
  - `GODFALL_ATTEMPTS_INSANE` 80 → 420
  - Concorrência por fase elevada (96 / 160 / 256 / 384 no normal; até 512 no insane)
  - Abort thresholds afrouxados para permitir saturação real:
    - `GODFALL_ABORT_LOSS_PCT` 60 → 92
    - `GODFALL_ABORT_LATENCY_MULT` 3 → 8
    - `GODFALL_ABORT_SUCCESS_PCT` 35 → 4
  - Janela de recovery estendida (60s → 90s, alvo 1.3x → 1.5x baseline)
- Nova fase apex **TITANFALL** adicionada ao final de `GODFALL_PHASES` e `GODFALL_PHASES_INSANE` (multiplier 3.5x / 5.0x, delay 0).
- Cada fase agora tem campo `barrage` (tier 0-4) que dispara, **em paralelo** ao benchmark assíncrono por host:
  - `GODFALL_BARRAGE_THREADS_PER_TIER = 28` threads UDP raw (payloads 65507 / 4096 / 512 alternados, 14 portas-chave + porta randômica, broadcast habilitado)
  - `GODFALL_TCP_SWARM_PER_TIER = 64` threads de TCP connect-and-close
  - Coordenação via `threading.Event` para parada limpa ao final de cada fase
  - Contador global `barrage_pkt_counter` agregando pacotes UDP enviados
- `run_host_phase` reescrito de loop sequencial (com `await sleep` serializando) para batch via `asyncio.gather`, saturando de fato a concorrência da fase.
- Telemetria nova no `results["godfall"]`:
  - `barrage_tier` e `barrage_packets` por fase
  - `barrage_packets_total` agregado
- `--godfall` no argparse atualizado descrevendo as 4 fases e a barragem multi-vetorial.

No tier 4 (TITANFALL insane): 112 threads UDP + 256 threads TCP rodando concorrentemente com até 512 conexões assíncronas por host — supera os 100 threads UDP do `--flood` e ainda preserva métricas por host, abort automático, recovery window e relatórios HTML/TXT.

Validação:
- `python -m py_compile NetDroid.py` executado com sucesso.
- `python NetDroid.py --version` executado com sucesso.

### Upgrade Colossal — v1.1.0 (2026-04-27)

Refatoração ampla seguindo o plano `claudinho-meu-lindo-me-wiggly-zephyr.md`. Foco: deixar `--discover`, `--Insane`, `--god`, `--godfall` em nível militar, consolidar todo DOS dentro de `--godfall`, corrigir URL do upgrade, manter código em PT-BR.

**Constantes / capabilities**
- `VERSION` 1.0.0 → **1.1.0**.
- `GITHUB_RAW_URL` / `GITHUB_VERSION_URL` → `github.com/yamotoz/NetDroid`.
- Nova flag `HAS_NMAP_BIN = bool(shutil.which("nmap"))` (separada do módulo python-nmap).

**Bancos globais expandidos**
- `MAC_VENDORS`: 48 → **140+** prefixos (Xiaomi, Tenda, ZTE, Google/Nest, Amazon, Sony, LG, Netgear, Aruba, Ruckus, Ubiquiti, Roku, Sonos, Wyze, Eufy, Synology, QNAP, impressoras HP/Epson/Brother/Canon/Kyocera, câmeras Axis/Foscam/Reolink/Amcrest, Grandstream).
- `SERVICE_MAP`: 43 → **110+** (Modbus 502, BACnet 47808, DICOM 104, EthernetIP 44818, CoAP 5683, MQTTS 8883, jogos 25565/27015, infra industrial, IoT, NAS, Kubernetes 6443, Vault 8200, Consul 8500, Cassandra 9042, etc.).
- `DEFAULT_CREDS`: 10 → **15+** vendors (Xiaomi, Tenda, ZTE, Ubiquiti, Axis, Foscam, Reolink, Amcrest, Netgear, Synology, QNAP, Intelbras, Fortinet).
- `RTSP_PATHS`: 12 → **35+** (Hikvision, Dahua, Axis, Ubiquiti, Foscam, Amcrest, Reolink, ONVIF).
- `API_ENDPOINTS`: 10 → **30+** (Swagger/GraphQL/ISAPI/PSIA/axis-cgi/Synology/QNAP/HNAP1, .git, .env, /manager/html).
- Novo `DEVICE_FINGERPRINTS`: lista global com **50+ assinaturas** (vendor + marker + tipo) — usada por `HostDiscovery._classificar_dispositivo` e `GodMode._fingerprint_device`.
- Novo `VULN_DB`: dict porta → list[{servico, regex, dica, severidade}] com 30+ portas e ~80 assinaturas (severidades `critica`/`alta`/`media`/`info`).
- Novo `DEVICE_HEURISTICS`: regras ordenadas para classificação `roteador|camera_ip|impressora|nas|voip|windows_pc|linux_servidor|mobile|iot_generico|desconhecido`.

**Upgrader**
- Método `_fetch()` com até 3 tentativas + backoff e User-Agent.
- Validação pré-overwrite: tamanho mínimo (10 KB) + checagem de strings `NetDroid` e `def main_async`.
- Mensagens em PT-BR.

**HostDiscovery (--discover militar)**
- Novos métodos: `_consultar_mdns`, `_consultar_netbios`, `_sondar_ssdp`, `_banner_smb`, `_coletar_http`, `_nmap_os`, `_ler_dhcp_leases`, `_classificar_dispositivo`, `_calcular_confianca`, `_enriquecer_hosts` / `_enriquecer_host_unico`.
- Modelo de host expandido: `hostname`, `device_type`, `fontes` (lista de origens: arp/ttl/mdns/netbios/ssdp/smb/http/nmap/dhcp), `confiancas` (dict 0–100 por campo), `vulns`, `extra` (metadata SSDP/HTTP/SMB).
- Fluxo: ARP → ping → TCP probe → enriquecimento paralelo → classificação → score de confiança.
- Tabela CLI nova com colunas `Hostname, Tipo, Conf.`.

**PortScanner (--Insane com avaliação de vulns)**
- Novo método `_avaliar_vulns(host)` chamado automaticamente quando `insane=True`.
- Helpers: `_auditar_headers_http` (ausência de X-Frame-Options/CSP/HSTS/X-Content-Type-Options/Referrer-Policy + cookies suspeitos + servidor antigo), `_verificar_ssh_versao` (CVE-2018-15473 e correções 8.5+), `_telnet_ftp_banner` (ProFTPD 1.3.3c, vsftpd 2.3.4).
- Output: nova tabela "Vulnerabilidades Identificadas (Insane)" com severidade.

**GodMode (--god aprofundado)**
- `_fingerprint_device` agora consome `DEVICE_FINGERPRINTS` global (50+).
- Novos probes: `_sondar_servicos_amplificacao` (SNMP `public` GetRequest, NTP monlist mode 7, DNS `version.bind` CHAOS) e `_sondar_paths_default` (phpmyadmin, wp-admin, manager/html, .git/config, .env, server-status, HNAP1).
- `_assess_risks` ampliado com SNMP/DNS/NTP/Redis/Mongo/Elastic/Docker, paths default, amplificação e absorção de vulns do PortScanner. Mensagens em PT-BR.

**StressEngine (consolidação --godfall)**
- Removidos do parser: `--overfull`, `--overflow`, `--flood`, `--slowloris`, `--rtsp-kill`, `--mirai`.
- Removidos do código: `run_overfull`, `run_flood`, `run_overflow` (helpers `_tcp_flood`/`_udp_storm`/`_http_storm`/`_run_iperf` mantidos como utilitários internos do godfall).
- `--godfall` ganhou:
  - **RECON iperf3** baseline (TCP+UDP) absorvido do antigo overflow.
  - Novo argumento de ctor `infinito` (vindo de `--infinite`).
  - **Modo eterno**: quando `--infinite` é combinado com `--godfall`, a fase TITANFALL roda em loop até `KeyboardInterrupt`/`CancelledError`, com contador de ciclos e pacotes em tempo real.
  - `results["godfall"]` ganha `modo` ("infinito"/"fases") e `baseline_iperf`.

**Parser & main_async**
- `has_action` reduzido a `[discover, normal, Insane, stealth, ports, god, godfall, onvif]`.
- Helper `_host_vazio()` cria host com modelo expandido para casos sem `--discover`.
- Help/argparse 100% em PT-BR; exemplos atualizados.

**ReportEngine**
- HTML: tabela de hosts ganhou `Hostname`, `Tipo` (badge colorido por tipo), `Conf.`, `Risk`, `Fontes`. Novo card `Vulnerabilidades` com badges de severidade. Card `Godfall` mostra modo, baseline iperf3, barragem por fase + total. CSS expandido com classes `.badge.tipo-*` e `.badge.sev-*`.
- TXT: blocos `Hostname`, `Tipo`, `Fontes`, `Vuln [SEV]` por host; novas seções `=== VULNERABILIDADES ===`, `=== TOP RISCOS ===`, `=== GODFALL TITAN SWEEP (modo) ===` e `=== RANKING DE RESILIÊNCIA ===`.

**Validação final**
- `python -m py_compile NetDroid.py` ok.
- `python NetDroid.py --version` ok (imprime `v1.1.0`).
- `python NetDroid.py --help` ok (parser limpo, sem flags removidas, com `--infinite`).

### Apex Privilege + Kamikase — v1.2.0 (2026-04-27)

Implementação completa do plano `claudinho-meu-lindo-me-wiggly-zephyr.md` (sessão de privilégio). Foco: explodir capacidade exponencialmente quando `--root` ativo, e adicionar módulo dedicado de stress 802.11 (`--kamikase`).

**Decisões fechadas (confirmadas pelo usuário antes da implementação):**
- Uma única flag `--root` que auto-detecta SO (Windows Admin / Linux root / Termux su). Sem flags separadas.
- Scapy é **opcional** (try-import); fallback para subprocess `aireplay-ng`/`mdk4`/`tcpdump`/`iw`/`netsh`.
- `--kamikase` no Windows é implementado com NPCAP+scapy + warning honesto sobre instabilidade do monitor mode.

**Constantes / capabilities adicionadas:**
- `VERSION` 1.1.0 → **1.2.0**.
- `HAS_SCAPY` (try-import scapy + 802.11 layers).
- `IS_TERMUX` e `IS_LINUX`.
- 11 capability flags em runtime: `HAS_AIREPLAY`, `HAS_AIRMON`, `HAS_MDK4`, `HAS_TCPDUMP`, `HAS_IW`, `HAS_IWCONFIG`, `HAS_ARPSCAN`, `HAS_IPTABLES`, `HAS_NETSH`, `HAS_PKTMON`, `HAS_POWERSHELL`, `HAS_SU`.
- `GODFALL_PHASES_ROOT` e `GODFALL_PHASES_ROOT_INSANE` — multipliers de até 8.0x e concorrência até 1024.
- `CONCURRENT_LIMIT_ROOT = 2048` (vs 500 user-space).
- `THERMAL_LIMITE_REDUZIR = 70°C`, `THERMAL_LIMITE_ABORTAR = 80°C` (Termux).
- `SNMP_COMMUNITIES_ROOT` com 40+ entradas (vs 13 padrão).

**Classe nova `ContextoPrivilegio`:**
- `detectar_e_validar(ui)` retorna instância ativa ou None.
- Validação por motor: `ctypes IsUserAnAdmin()` (Windows), `os.geteuid()==0` + raw socket test (Linux), `su -c id` retornando uid=0 (Termux).
- `_descobrir_capabilities()` preenche set com base em binários disponíveis e plataforma.
- Banner de boot mostra plataforma, motor, capabilities, e dicas de instalação para o que falta.
- Helpers globais `priv_ativo()` e `tem_cap(c)` consultam variável global `ctx_priv`.
- `temperatura_cpu()` lê `/sys/class/thermal/thermal_zone0/temp` para thermal guard.

**`HostDiscovery` boost root:**
- `_enriquecer_root(host)` chamado adicionalmente a `_enriquecer_host_unico` quando `priv_ativo()`.
- `_raw_icmp_echo`: socket raw ICMP type 8 com checksum Internet, mede TTL e RTT.
- `_inferir_os_por_ttl`: TTL ≤ 64 = Linux/Android, ≤ 128 = Windows, > 128 = Network device.
- `_raw_arp_probe`: scapy `srp(Ether/ARP)` para ARP active probe.
- `_syn_fingerprint`: scapy `IP/TCP(flags="S")` com análise TTL+window+MSS para palpite refinado de OS.

**`PortScanner` boost root:**
- `_tcp_scan` agora roteia para `_tcp_scan_raw_syn` quando `priv_ativo() and tem_cap("scapy")`.
- `_tcp_scan_raw_syn`: scapy SYN scan stealth (sem 3-way handshake), em chunks de 1024 portas via executor, com RST após SYN/ACK para fechar limpo.
- `CONCURRENT_LIMIT_ROOT` (2048) usado em vez de 500 quando root.
- Batch elevado para 1024 (vs 500) sob root.
- Thermal guard em Termux: reduz para 256 com >70°C, aborta com >80°C.

**`GodMode` boost root:**
- `_upgrade_root()` chamado de `run()` antes de `_assess_risks` quando `priv_ativo()`.
- `_snmp_mass`: testa `SNMP_COMMUNITIES_ROOT` (40+) e grava em `host["snmp_creds"]` + `host["root_findings"]`.
- `_dns_cache_snoop`: query DNS RD=0 em domínios populares (google.com, facebook.com, youtube.com, etc.); ANCOUNT>0 = cacheado.
- `_sniff_lldp_cdp`: scapy sniff filtrando frames `01:80:c2:00:00:0e` (LLDP) e `01:00:0c:cc:cc:cc` (CDP) por 15s.
- `_tcpdump_arp_spoof`: subprocess tcpdump por 10s, detecta IPs com mais de um MAC.
- `_assess_risks` ampliado para absorver `root_findings` com pesos (alta=25, media=12, info=5).

**`StressEngine` boost root:**
- `run_godfall` usa `GODFALL_PHASES_ROOT*` quando `priv_ativo()`, com `base_attempts × 1.6`.
- `_spawn_titan_flood_raw`: SYN flood scapy com IPs source aleatórios, threads adicionais à barragem UDP/TCP existente, ativado para tier ≥ 2.

**Classe nova `KamikaseEngine` (~520 linhas):**
- `_validar_pre_requisitos`: detecta interface WiFi (netsh / iw / wlan0), exige aireplay/mdk4/scapy disponível, warning honesto no Windows.
- `_consent_duplo`: banner vermelho + aviso legal (Lei 12.737/2012, CFAA) + prompt EXIGE digitação literal "EU AUTORIZO".
- `_descobrir_aps`: motor híbrido — `netsh wlan show networks mode=bssid` (Windows), `iw dev <iface> scan` (Linux), `termux-wifi-scaninfo` (Termux), fallback scapy Beacon sniff 8s.
- `_setup_monitor`: `airmon-ng start` (Kali), `iw set type monitor` (Termux), no-op no Windows (NPCAP injeta direto).
- `_atacar_bssid`: thread por BSSID rodando `aireplay-ng -0 0 -a BSSID`, parse stdout para contar deauths; fallback scapy `Dot11Deauth` em loop.
- Contador thread-safe (`threading.Lock`) — global e por BSSID.
- `_loop_ui_live`: print no mesmo lugar a cada 1s mostrando tempo, total, PPS, BSSIDs ativos.
- `_encerrar_limpo`: terminate subprocess + join threads + restaurar `airmon-ng stop` ou `iw set type managed` + audit log final.
- `kamikase_audit.log` append-only no `output_dir`: timestamp ISO, plataforma, motor, interface, BSSIDs alvos, comando completo, total de pacotes, motivo do encerramento.

**Parser e `main_async`:**
- Novas flags `--root` e `--kamikase` com helps detalhados em PT-BR.
- `--kamikase` sem `--root` → erro.
- `--kamikase` sozinho não exige target (opera no chip WiFi local); criação de output dir fallback se `detector.detect()` falhar.
- `has_action` inclui `args.kamikase`.
- Branch `if args.root: ctx_priv = ContextoPrivilegio.detectar_e_validar(ui)` antes de discover.
- Branch `if args.kamikase: KamikaseEngine(ui, ctx_priv, detector).run()` antes do report.

**`ReportEngine` v1.2:**
- `__init__` aceita `kamikase_data` e `ctx_priv` como kwargs.
- Novo card HTML `Privilege Mode — Apex Militar` no topo (após topology) — plataforma, motor, capabilities como badges, didática expandível.
- Novo card HTML `⚡ Kamikase Death Toll ⚡` ao lado do godfall — totais, PPS médio, motivo encerramento, audit log path, tabela ESSID/BSSID/Canal/RSSI/Pacotes, didática expandível.
- Ordem: privilege → vuln → cred → risk → godfall → kamikase → lat.
- TXT: nova seção `=== PRIVILEGE MODE — MOTOR ===` e `=== ⚡ KAMIKASE DEATH TOLL ⚡ ===` antes do glossário.
- 5 entradas novas em `EXPLICACOES`: `privilegio_root`, `arp_spoofing_detect`, `lldp_cdp`, `dns_snooping`, `kamikase` — cada uma com resumo, como_validar, impacto.
- `_coletar_chaves_explicacao` detecta `root_findings` por tipo e adiciona ao glossário só os que apareceram.

**README v1.2:**
- Banner atualizado para v1.2.0 + badge "Root: Optional (Apex Mode)".
- Nova seção "🔥 Modo Root (--root) — Apex Militar" com matriz de motor por SO, boosts por módulo, lista de capabilities opcionais e comandos de instalação.
- Nova seção "⚡ --kamikase — Deauth Flood 802.11" com **aviso legal destacado** (Lei 12.737/2012, CFAA, GDPR), uso autorizado, fluxo (consent duplo + audit log), exemplos e limitações honestas por SO.

**Validação:**
- `python -m py_compile NetDroid.py` ok.
- `python NetDroid.py --version` retorna `v1.2.0`.
- `python NetDroid.py --help` mostra `--root` e `--kamikase` com helps PT-BR + 2 exemplos novos.
- Smoke test report engine completo com `ctx_priv` + `kamikase_data` simulados: HTML 13.7 KB com cards Privilege Mode e Kamikase Death Toll; TXT 10 KB com seções dedicadas e glossário ampliado (`arp_spoofing_detect`, `lldp_cdp`, `dns_snooping`, `kamikase`, `privilegio_root`).

### Simplificação Cirúrgica — v1.3.0 (2026-04-27)

Reorganização major do CLI seguindo pedido do usuário: **3 modos apenas** (`--god`, `--godfall`, `--kamikase`) + booster `--root`. Todas as flags antigas de scan/discovery foram absorvidas.

**Decisão arquitetural:**
- Filosofia "uma flag, um verbo" — usuário não precisa saber quais sub-flags combinar.
- `--god` é o pacote completo de **reconhecimento** (descoberta + scan total + auditoria).
- `--godfall` é o pacote completo de **ataque** (subnet inteira ou hosts descobertos pelo --god).
- `--kamikase` é o pacote completo de **deauth WiFi** (já era dedicado).

**Removidas do parser:**
- `--discover` → absorvida pelo `--god` (Fase 1/3 automática).
- `--Insane` → absorvida pelo `--god` (Fase 2/3 sempre em modo insane).
- `--normal` → removida (era redundante com Insane absorvida).
- `--stealth` → removida (caso de uso muito específico, baixa demanda).
- `--ports` → removida (sem necessidade real fora de pentest cirúrgico).
- `--onvif` → absorvida pelo `--god` (já era parte do GodMode.run()).

**CLI final (apenas 8 flags):**
```
--auto, --t TARGET    (alvo)
--god                 (reconhecimento total — 3 fases)
--godfall [--infinite] (ataque colossal a todos os hosts)
--kamikase            (deauth WiFi — exige --root)
--root                (booster apex)
--upgrade, --version  (utilidades)
```

**Mudanças no `main_async`:**
- `has_action = any([args.god, args.godfall, args.kamikase])` (vs antes: 9 flags).
- `if args.god:` agora roda em sequência: `HostDiscovery` → `PortScanner(insane=True)` → `GodMode.run()`. Cada fase com seu `ui.section("FASE N/3 — ...")` para feedback claro.
- `if args.godfall and not args.god`: usa fallback de subnet inteira (254 IPs) para spray colossal.
- `if args.godfall and args.god`: ataca apenas os hosts vivos descobertos.
- `args.Insane` removido como condicional separada — sempre `True` quando `--god` ativo.

**Estado dos cards/relatórios:**
- HTML/TXT inalterados em estrutura — todos os cards (`Privilege Mode`, `Inventário`, `Vulnerabilidades`, `Credential Hunting`, `Risk Findings`, `Godfall`, `Kamikase`, `Latência`) continuam aparecendo conforme o modo executado.
- O glossário didático continua se adaptando ao que foi encontrado.

**README v1.3.0:**
- Reescrito do zero com seção "Filosofia" (3 verbos), tabela de fases do `--god`, descrição do ataque colossal do `--godfall` (subnet inteira sem `--god` vs hosts vivos com `--god`), comportamento do `--kamikase` por SO.
- Aviso legal mantido em quote blocks para `--godfall` e `--kamikase`.

**Validação:**
- `python -m py_compile NetDroid.py` ok.
- `python NetDroid.py --version` → `v1.3.0`.
- `python NetDroid.py --help` mostra apenas 8 flags com helps PT-BR + 7 exemplos.
- `python NetDroid.py` (sem args) → mensagem clara listando os 3 modos disponíveis.

### Dashboard C2 Live — v1.4.0 (2026-04-28)

Implementação completa do painel web em tempo real (`--live`) para `--god` e `--kamikase`. Foco em uso autorizado em Kali Linux.

**Arquitetura:**
- Flask + Flask-SocketIO em thread daemon, host fixo `127.0.0.1:5556`.
- Templates HTML embutidos como strings Python (mantém single-file): `TEMPLATE_GOD` e `TEMPLATE_KAMIKASE`.
- TailwindCSS + Chart.js + SortableJS via CDN para visual luxuoso sem build step.
- Tema cyberpunk preto/vermelho/branco, modo escuro padrão, glass morphism, scan lines, pulse glow nos cards de ataque.
- Browser abre automaticamente via `webbrowser.open()`.

**Classes novas (~900 linhas adicionadas):**
- `EventBus` (singleton global `event_bus`) — desacopla módulos do canal de transporte; queue de 500 eventos pré-conexão; helper `emitir(nome, **dados)`.
- `WifiSecurityAuditor` — score 0–100 + achados estruturados: detecta WPS, WEP/TKIP legacy, beacon interval anômalo, RSSI excessivo (vazamento de perímetro).
- `PMKIDCapture` — primário hcxdumptool focado (25s), fallback airodump+aireplay (deauth burst para forçar handshake).
- `HashcatWorker` — fila thread única, converte pcapng→22000 via hcxpcapngtool, roda hashcat com perfis (low/medium/high/nuclear), parse de progress + ETA em tempo real, emite `hashcat_start`/`progress`/`done`.
- `LiveDashboard` — Flask app, rotas `/`, `/api/estado`, `/api/wordlists`, `/api/perfis_hashcat`, handler `mover_zona` para drag-drop.
- `PDFReport` — reportlab, gerado ao final de `--god`/`--kamikase` com tema vermelho/preto, tabelas de hosts/vulns/kamikase.

**Capabilities/constants novas:**
- `HAS_FLASK`, `HAS_REPORTLAB`, `HAS_HCXDUMPTOOL`, `HAS_HCXPCAPNGTOOL`, `HAS_HASHCAT`, `HAS_AIRODUMP`.
- `DASHBOARD_HOST = 127.0.0.1`, `DASHBOARD_PORT = 5556`, `DASHBOARD_SECRET`.
- `WORDLIST_DIR = Path("WordList")`, `HANDSHAKE_DIR = Path("handshakes")`.
- `HASHCAT_PROFILES`: low/medium/high/nuclear com workload 1-4.

**Hooks `--god --live`:**
- `HostDiscovery.discover()` emite `fase` no início, `host_found` por host descoberto, `host_update` após enriquecimento.
- `PortScanner.scan_all()` emite `fase` no início.
- `PortScanner.scan_host()` emite `host_update` após scan, `vuln_found` por vulnerabilidade detectada.
- `GodMode.run()` emite `fase`. Sob `--live`, pula consent (já dado pela escolha de modo).

**Hooks `--kamikase --live`:**
- `KamikaseEngine.__init__` ganha `live: bool` + estado de zonas (`verde`/`vermelha`/`azul`), `deauth_threads`/`deauth_stops` por BSSID, `hashcat_worker`, `pmkid`.
- `KamikaseEngine.run()` roteia para `_run_live()` se `live=True`.
- `_run_live()`: descobre APs → audita cada um (WifiSecurityAuditor) → popula zona verde → emite `ap_descoberto` → setup monitor mode → loop heartbeat emitindo `pacotes_total`.
- `mover_para_zona(bssid, destino, perfil, wordlist)`:
  - Se entra na vermelha: spawna thread `_loop_deauth_zona` que envia 1 frame deauth a cada 0.5s (aireplay-ng primário, scapy fallback) e incrementa contadores.
  - Se sai da vermelha: seta stop_event, thread encerra graciosamente.
  - Se entra na azul: spawna captura assíncrona PMKID → enfileira no HashcatWorker.

**Templates HTML:**
- `TEMPLATE_GOD` (~280 linhas): header com logo "NETDROID" + tag "GOD · C2 LIVE" pulsante, 4 stat cards, inventário de hosts expansíveis, 2 pie charts (tipos + severidades), feed de vulns colorido, log em tempo real.
- `TEMPLATE_KAMIKASE` (~310 linhas): header com tag "KAMIKASE · C2 LIVE", contador global + PPS, 3 zonas drag-and-drop com SortableJS, modal de configuração de crack (perfil + wordlist), pie chart das 3 zonas, log em tempo real. Cards animados (pulse-red para deauth, pulse-blue para crack).

**Pasta `WordList/`:**
- Criada com `comum.txt` (28 senhas frequentes em PT-BR para teste em rede própria).
- Dashboard lista automaticamente todos os `.txt` da pasta no modal de crack.

**Arquivos novos:**
- `requirementskali.txt` — dependências Python + lista de pacotes APT (`aircrack-ng mdk4 hcxdumptool hcxtools hashcat tcpdump arp-scan iw nmap iperf3 iptables`) + comandos de verificação.
- `WordList/comum.txt` — wordlist default em PT-BR.

**`requirements.txt` reescrito:**
- Adicionadas: `scapy`, `python-nmap`, `flask`, `flask-socketio`, `python-socketio`, `python-engineio`, `simple-websocket`, `reportlab` (todas obrigatórias).

**Parser:**
- Nova flag `--live`. Validação: só funciona com `--god` ou `--kamikase` (erro caso contrário).

**main_async:**
- Após validar privilégio, instancia `LiveDashboard(modo)` se `--live` presente.
- Quando `--kamikase --live`: injeta `kami` no `dashboard.kami_engine` para callbacks de drag-drop funcionarem.
- PDF executivo gerado ao final automaticamente.
- Modo `--god --live` (sem kamikase): aguarda Ctrl+C para manter dashboard ativo após scan terminar.

**Validação:**
- `python -m py_compile NetDroid.py` ok.
- `python NetDroid.py --version` → `v1.4.0`.
- `python NetDroid.py --help` mostra 9 flags incluindo `--live`.

### Iteração v1.4.0 — Wordlist Contextual + Bulk Move + Visual Kill (2026-04-28)

Refinamento do dashboard `--kamikase --live` após review do usuário:

**Perfis hashcat renomeados:**
- `nuclear` → `insane` (label "🔴 INSANE — 100% GPU descontrolado")
- `high` → `hard` (label "🟠 HARD — pesado, ~90% GPU")
- Mantidos: `low` (🟢) e `medium` (🟡). Total: low/medium/hard/insane.

**Nova classe `WordlistContextual`:**
- Estática, gera 500-1000 variações por ESSID com filtro WPA2-PSK (8-63 chars).
- Bases: original + lowercase + UPPERCASE + Capitalize + leet speak (a/e/i/o/s/t).
- Detecta camelCase via regex (`[A-Z]?[a-z]+|[A-Z]+|\d+`) e expande partes individuais.
- Combinatorial: bases × {41 sufixos numéricos, 17 anos 2010-2026, 25 símbolos, 11 prefixos genéricos}.
- Variações extras: reverso, duplicado.
- Ordena por probabilidade: 8-12 chars primeiro (mais comum em residencial), depois 13-16, depois 17+.
- `WordlistContextual.gerar_arquivo(essid, base_wordlist)` cria `./WordList/_contextual_<essid>.txt` com header de metadata + variações + wordlist base concatenada.
- Validado: `Casa01` → 1000 variações geradas (incluindo `c45401` leet, `casa01@2024`, etc.).

**HashcatWorker integrado:**
- `enfileirar` aceita `contextual: bool = True` (default ON).
- `_processar` chama `WordlistContextual.gerar_arquivo` e usa o arquivo combinado como `wordlist` final do hashcat.
- Item da fila ganha `contextual_count` (qtde de variações geradas) e `wordlist_efetiva` (nome do arquivo `_contextual_*`) para exibir no card.

**KamikaseEngine + LiveDashboard:**
- `mover_para_zona(bssid, destino, perfil, wordlist, contextual)` aceita flag.
- Handler `on_mover` do SocketIO repassa `contextual`.
- `_iniciar_crack_async` aceita e propaga.

**Template kamikase.html — melhorias massivas (~600 linhas):**
- **Animação `morph-to-red` 3s**: card recém-movido para vermelha morpha visualmente verde→amarelo→laranja→vermelho com `transform:scale` (1→1.03→0.98→1) simulando "morte progressiva". Após 3s vira `pulse-red` permanente.
- **Animação `crystallizing` 1.5s** ao entrar na azul: gradient verde→ciano.
- **Multi-select com checkbox** em cada card (anti-conflito com SortableJS via `filter:"input[type=checkbox]"`). Toolbar amarela aparece no topo quando há seleção: "Ação em massa nos selecionados" com botões para cada zona destino.
- **Bulk move por zona**: cada zona tem 3 botões na header (`→ todos vermelha`, `→ todos azul`, `selecionar tudo`).
- **Sidebar `📚 Wordlists Disponíveis`** atualizando a cada 10s via `/api/wordlists`. Marca arquivos `_contextual_*` como `(contextual)`.
- **Modal de crack expandido**: mostra ESSID, perfil emoji-coded, wordlist dropdown, checkbox "prepend variações contextuais" (default ON). Suporta lote: se múltiplos APs movidos juntos, modal aplica config a todos.
- **Card azul ampliado**: mostra status, %, ETA, **contador de variações contextuais** (`📚 1000 variações prepended`), senha quebrada em badge verde com `<code>`.
- Stat de selecionados no header.

**Validação final:**
- `python -m py_compile NetDroid.py` ok.
- `WordlistContextual.gerar_variacoes('Casa01')` retorna 1000 variações ordenadas por probabilidade.
- Templates: GOD 11.6 KB / KAMIKASE **23 KB** (cresceu ~9 KB com toolbar bulk + sidebar + animations + modal expandido).

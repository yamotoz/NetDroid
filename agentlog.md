# NetDroid — Agent Handover Log

> Documento vivo de contexto para qualquer agente de IA que pegar o projeto. Lê isso e o `NetDroid.py` em paralelo. Tudo aqui é verdade no commit atual; coisas que mudarem precisam ser refletidas aqui.

---

## 1. O que é o NetDroid

Single-file Python (`NetDroid.py`, ~10.6k linhas, **v1.5.2**) — toolkit de auditoria/ataque WiFi com dashboard web em tempo real (Flask + SocketIO). Roda em **Kali/Linux** (full power), **Termux com root** (Android), e **Windows** (modos limitados, sem 802.11 raw).

Linguagem dos comentários e UI: **PT-BR**. Arquitetura: deliberadamente single-file (não dividir em módulos sem instrução explícita do usuário).

### Modos principais (CLI)
- `--auto` — varredura automática da rede local (host discovery + port scan + latency)
- `--god` — auditoria profunda + relatório PDF (`GodMode` class)
- `--godfall` — ataque colossal a TODOS os hosts (incluindo gateway)
- `--kamikase` — ataque WiFi 802.11 (deauth/handshake/crack) com 3 zonas drag-drop
- `--live` — habilita dashboard C2 em http://127.0.0.1:5556 (combina com `--god` ou `--kamikase`)
- `--root` — força capabilities elevadas (necessário para `--kamikase`)

### Comando alvo do usuário
```bash
sudo -E python NetDroid.py --root --kamikase --live
```

---

## 2. Layout de pastas (criadas em runtime)

| Path | Função |
|---|---|
| `./WordList/` | wordlists `.txt` consumidas pelo hashcat |
| `./memoria/db.json` | persistência cross-session (APs vistos, histórico) |
| `./memoria/handshakes/` | `.cap`/`.pcapng` capturados |
| `./Pass/senhas.txt` | append-only `ESSID:BSSID:senha:wordlist:data` |
| `./imports/` | exports PDF+TXT por zona |
| `./venv/` | ambiente Python isolado (Kali) |
| `./agentlog.md` | este arquivo |
| `./README.md` | doc do usuário final |
| `./requirements.txt` | deps Python cross-platform |
| `./requirementskali.txt` | comando 1-line de setup completo no Kali |

---

## 3. Constantes globais relevantes ([NetDroid.py:117-202](NetDroid.py#L117))

```python
VERSION = "1.5.2"
DASHBOARD_HOST = "127.0.0.1"
DASHBOARD_PORT = 5556
WORDLIST_DIR = Path("WordList")
HANDSHAKE_DIR = Path("handshakes")
PASS_DIR = Path("Pass")
IMPORTS_DIR = Path("imports")
DEAUTH_THREAD_LIMIT = 8              # semáforo anti-explosion
CONTINUOUS_SCAN_INTERVAL_SEC = 6     # cadência do scan contínuo
CHANNEL_HOP_INTERVAL_MS = 250        # tempo em cada canal
HANDSHAKE_RETRY_FOREVER = True       # captura handshake nunca desiste
```

### Capability flags (detectadas via `shutil.which`)
`HAS_AIREPLAY`, `HAS_AIRMON`, `HAS_AIRODUMP`, `HAS_AIRCRACK`, `HAS_HCXDUMPTOOL`, `HAS_HCXPCAPNGTOOL`, `HAS_HASHCAT`, `HAS_MDK4`, `HAS_TCPDUMP`, `HAS_IW`, `HAS_IWCONFIG`, `HAS_ARPSCAN`, `HAS_IPTABLES`, `HAS_NETSH`, `HAS_PKTMON`, `HAS_POWERSHELL`, `HAS_SU`, `HAS_SCAPY`.

### Lookup tables 802.11 ([NetDroid.py:182-198](NetDroid.py#L182))
`CHANNEL_TO_FREQ_24/_5/_6/_ALL`, `FREQ_TO_CHANNEL_ALL` — usadas em `_normalizar_ap` para cross-fill canal↔freq quando uma fonte só tem um lado. Elimina campos `?` em runtime.

---

## 4. Classes e responsabilidades

| Classe | Linha | O que faz |
|---|---|---|
| `ContextoPrivilegio` | 1300 | Decide motor (`adm` Win, `root-kali`, `root-termux`) e capabilities |
| `TerminalUI` | 1492 | Banner cyberpunk + log colorido (rich) |
| `NetworkDetector` | 1623 | Identifica iface, gateway, ASN, OUI |
| `HostDiscovery` | 1802 | ARP scan / ping sweep |
| `PortScanner` | 2514 | Async TCP/SYN + nmap fallback |
| `LatencyMonitor` | 2904 | iperf3 + jitter |
| `StressEngine` | 2969 | SYN/ARP/UDP flood (`--godfall`) |
| **`KamikaseEngine`** | **3576** | **Coração do `--kamikase --live`** — vê seção 5 |
| `EventBus` | 5271 | Wrapper para SocketIO emit thread-safe |
| `WifiSecurityAuditor` | 5317 | Score 0-100 + achados (WEP/TKIP/WPS/RSSI alto) |
| **`PMKIDCapture`** | **5376** | **Captura handshake** — vê seção 6 |
| `MemoriaPersistente` | 5616 | JSON-based local storage cross-session |
| `WordlistContextual` | 5843 | Gera variações baseadas em ESSID/BSSID/data |
| `HashcatWorker` | 5973 | Fila + processo hashcat com parser de progresso |
| **`LiveDashboard`** | **6307** | **Flask + SocketIO** — endpoints e templates |
| `ZonaExporter` | 8286 | Export PDF+TXT por zona |
| `PDFReport` | 8490 | Relatório executivo via reportlab |
| `GodMode` | 8595 | Pipeline auditoria + relatório (`--god`) |
| `ReportEngine` | 9536 | Markdown report final |
| `Upgrader` | 10286 | Auto-update via git pull |

---

## 5. KamikaseEngine — fluxo do `--kamikase --live`

Construtor em [NetDroid.py:3580](NetDroid.py#L3580). Estado relevante:
- `self.alvos: List[Dict]` — APs descobertos (1 por BSSID, normalizado uppercase)
- `self.zonas: Dict[str, List[str]]` — `verde` (descobertas), `vermelha` (deauth ativo), `azul` (handshake+crack)
- `self.zonas_lock`, `self.contador_lock` — mutexes
- `self.deauth_threads: Dict[bssid, Thread]`, `self.deauth_stops: Dict[bssid, Event]`
- `self.deauth_semaforo = BoundedSemaphore(8)` — anti-explosion (8 threads max)
- **`self.capture_stops: Dict[bssid, Event]`** — controle das capturas de handshake
- `self.scan_continuo_*` — controla thread de scan e channel hopper
- `self.iface_orig` / `self.iface_monitor` — antes/depois do airmon-ng

### Boot do `--live` ([_run_live](NetDroid.py#L3663))
1. Carrega memória (cross-session APs, senhas)
2. **`_setup_monitor()` ANTES do scan** (crítico: sem monitor, scan só vê ~25% das redes)
3. `_descobrir_aps()` — varredura inicial via nmcli/iw/scapy
4. Audita cada AP, restaura senha/handshake da memória, joga na zona verde
5. **`iniciar_scan_continuo()`** — auto-inicia loop de scan + channel hopper
6. Inicia `HashcatWorker` e `PMKIDCapture` em standby
7. Heartbeat: emite `pacotes_total` 1×/s

### Setup monitor ([_setup_monitor](NetDroid.py#L4900))
1. `airmon-ng check kill` (mata NetworkManager/wpa_supplicant)
2. `airmon-ng start <iface>`
3. Detecta nome real via `iw dev` → grep `type monitor`
4. Valida com `/sys/class/net/<iface>` antes de aceitar
5. Fallback: `iw dev <iface> set type monitor` + `ip link set up`

### Scan contínuo ([_loop_scan_continuo](NetDroid.py#L3877))
- Roda `remapear_redes()` a cada `CONTINUOUS_SCAN_INTERVAL_SEC` (6s)
- `remapear_redes` ([3743](NetDroid.py#L3743)) tenta nmcli → iw → scapy nessa ordem, mescla via `_mesclar_aps`, dedup absoluto por BSSID
- **Channel hopper paralelo** ([_loop_channel_hopper](NetDroid.py#L3893)): `iw set channel` rotacionando 1-13 + 36/40/44/48/52/56/60/64/100-140/149-165 a cada 250ms. **Pausa quando há captura ativa** (`capture_stops` não-vazio) para não tirar a iface do canal do AP-alvo da zona azul.

### Movimentar AP entre zonas ([mover_para_zona](NetDroid.py#L3915))
Disparado pelo websocket `mover_zona`:
- Sai da `vermelha` → seta `deauth_stops[bssid]`, join, pop
- Sai da `azul` → seta `capture_stops[bssid]` (cancela handshake limpo)
- Entra `vermelha` → valida `iface_monitor`, spawna `_loop_deauth_zona` com semáforo
- Entra `azul` → chama `_iniciar_crack_async` (captura handshake → enfileira hashcat)

### Loop deauth ([_loop_deauth_zona](NetDroid.py#L3989))
- Adquire semáforo (timeout 5s, desiste se cheio)
- Loop while not stop_event:
  - `aireplay-ng -0 1 -a <bssid> <iface_monitor>` (1 pkt)
  - Fallback scapy `RadioTap()/Dot11()/Dot11Deauth(reason=7)` se aireplay timeout
  - Incrementa contadores, emite `ap_update`
  - **`stop_event.wait(0.2)`** — 200ms entre frames (5 pkt/s sustentado por BSSID)
- Finally: termina subprocess, libera semáforo

---

## 6. PMKIDCapture — captura cirúrgica de handshake

Versão atual ([NetDroid.py:5461-5615](NetDroid.py#L5461)) usa **estratégia única**, escolha do usuário:

### `capturar_infinito(bssid, canal, stop_event, on_tentativa)`
1. **Trava canal** via `iw dev <iface> set channel <canal>` (sem isso o channel hopper sabota)
2. Sobe `airodump-ng --bssid <BSSID> --channel <C> -w <arq> --output-format cap <iface>` em background (Popen) — **escuta contínua**, não derruba entre tentativas
3. Loop até stop_event ou pegar:
   - Burst `aireplay-ng -0 30 -a <BSSID> <iface>` (30 deauths broadcast)
   - Sleep 8s (tempo do cliente reconectar e aparecer EAPOL)
   - `_cap_tem_handshake(cap_file, bssid)`:
     - Tenta `aircrack-ng -a2 -w /dev/null -b <BSSID> <cap>` → regex `(\d+) handshake` ≥ 1
     - Fallback scapy: `rdpcap` + conta EAPOL com `bssid in (addr1,addr2,addr3)` ≥ 2
     - Final: `cap_size > 24KB` heurística
4. Finally: termina airodump

**Cancelamento limpo**: `stop_event` é setado por `mover_para_zona` quando AP sai da azul.

⚠️ Estratégias antigas (hcxdumptool focado/broadcast, scapy puro, airodump-burst-curto) foram **removidas em v1.5.2** porque o usuário preferiu uma única estratégia bem afinada. NÃO reintroduzir sem instrução explícita.

---

## 7. Dashboard Live — endpoints

Em `LiveDashboard` ([NetDroid.py:6307](NetDroid.py#L6307)). Templates HTML são strings r"""...""" no final do arquivo: `TEMPLATE_GOD` (~6378), `TEMPLATE_KAMIKASE` (~6777).

### REST
| Rota | Método | Função |
|---|---|---|
| `/` | GET | renderiza template (god ou kamikase) |
| `/api/estado` | GET | snapshot de `dash.estado` |
| `/api/wordlists` | GET | lista `./WordList/*.txt` |
| `/api/perfis_hashcat` | GET | low/medium/high/extreme |
| `/api/rescan` | POST | `remapear_redes(profundo)` síncrono |
| `/api/rescan_start` | POST | inicia thread de scan contínuo |
| `/api/rescan_stop` | POST | para scan contínuo |
| `/api/rescan_exec` | POST | uma iteração de scan (chamado pelo frontend) |
| `/api/scan_nmcli` | POST | nmcli + merge sem duplicar |
| `/api/scan_scapy` | POST | sniff scapy + merge sem duplicar |
| `/api/exportar?zona=X` | GET | gera PDF+TXT em `imports/` |
| `/api/memoria/stats` | GET | resumo da memória |
| `/api/memoria/limpar` | POST | reset (opcional `?handshakes=1`) |
| `/api/ap/<bssid>` | GET | detalhe completo do AP |

### WebSocket (server → client)
- `estado_inicial` (on connect)
- `ap_descoberto`, `ap_update` — frontend dedupa por `aps[bssid]`
- `pacotes_total{total}` — heartbeat 1Hz
- `hashcat_start/progress/done`
- `monitor_failed{iface,motivo}` — frontend mostra warning vermelho
- `handshake_tentativa{bssid,estrategia,n}` — UI mostra contador
- `handshake_capturado{bssid,pcap}`
- `scan_continuo_status{ativo,modo}`

### WebSocket (client → server)
- `mover_zona{bssid,destino,perfil,wordlists,contextual,stop_on_crack}`
- `reset_deauth{bssid}`, `reset_crack{bssid,recapturar}`

---

## 8. Frontend (TEMPLATE_KAMIKASE)

3 zonas em `<section>` `col-span-12 md:col-span-6 lg:col-span-4`:

### Zona Verde (saudáveis / descobertas)
Header: `🔄 Mapear Contínuo` · `🔓 Cadeado` · `📡 NMCLI` · `🦂 Scapy`
- **Cadeado** ([NetDroid.py:7747](NetDroid.py#L7747)): toggle global. Travado → todas as varreduras são bloqueadas (frontend e backend); botões mostram toast `🔒 ... bloqueado — destrave o cadeado primeiro`. Default destravado.
- **Mapear Contínuo**: alterna scan automático
- **NMCLI**: `_scan_aps_nmcli` síncrono, idempotente
- **Scapy**: `_scan_aps_scapy` síncrono (pode ter campos faltando — nmcli é mais completo)

### Zona Vermelha (deauth)
Drag/drop de cards verdes pra cá → dispara `mover_zona`. Mostra `pacotes` (contador) e botão reset. Indicador `1 pkt / 0.2s · ∞`.

### Zona Azul (crack)
Drag pra cá → captura handshake (loop infinito airodump+aireplay) → enfileira hashcat com wordlists escolhidas. Card mostra estágio: `capturing` (com tentativa#), `queued`, `running` (progresso+ETA), `cracked` (com animação `morph-to-green` 2s + `glow-victory` 4s) ou `failed/exhausted`.

### Render perf
`renderZonas()` debounce 80ms ([NetDroid.py:7572](NetDroid.py#L7572)) para não estourar reflows com 50+ APs.

---

## 9. Filtros e dedup absoluto

### ESSID `?` — bloqueado
[NetDroid.py:4574-4577](NetDroid.py#L4574) — `_normalizar_ap` retorna `None` se `essid.strip() == "?"` ou vazio. `<oculto>` é mantido (informação válida — rede com SSID broadcast desligado).

### Dedup por BSSID
- `_normalizar_bssid` ([4424](NetDroid.py#L4424)) sempre uppercase, formato `AA:BB:CC:DD:EE:FF`
- `_mesclar_aps` ([4589](NetDroid.py#L4589)) — merge inteligente:
  - RSSI: pega o mais forte (menos negativo)
  - security: pega a string mais detalhada
  - essid: prefere não-`<oculto>`
  - canal/freq: cross-fill via lookup table
- `_adicionar_ou_mesclar_ap` ([4640](NetDroid.py#L4640)) — usado pelos endpoints de scan manual; idempotente (clicar 100× não duplica)

---

## 10. Persistência

### `MemoriaPersistente` ([NetDroid.py:5616](NetDroid.py#L5616))
- `memoria/db.json`: `{version, criado_em, atualizado_em, aps: {bssid: {...}}}`
- `memoria/handshakes/`: arquivos `.cap`/`.pcapng` movidos para cá após captura
- Métodos: `registrar_ap`, `registrar_zona`, `registrar_handshake`, `registrar_senha`, `obter_ap`, `stats`, `limpar`
- `registrar_senha` também faz append em `Pass/senhas.txt` (formato `ESSID:BSSID:senha:wordlist:ISO_data`), idempotente

### `ZonaExporter` ([NetDroid.py:8286](NetDroid.py#L8286))
Gera 2 arquivos em `imports/zona_<X>_<timestamp>.{txt,pdf}`. PDF via reportlab (`PDFReport`).

---

## 11. Convenções de código (NÃO violar)

- **Single-file**: nunca dividir em módulos sem instrução explícita
- **PT-BR**: todas as strings de UI/log/comentário em português
- **Sem emojis** em código novo a menos que já existam (UI usa, lógica não)
- **Graceful degradation**: cada `HAS_*` flag deve ser checado antes de usar a ferramenta; nunca `raise` se ferramenta ausente
- **Exceptions em loops**: `try/except` amplo dentro do loop; **nunca** propagar de threads daemon ou de loops infinitos
- **Threads**: sempre `daemon=True` + `name=...` + `stop_event`
- **BSSID**: sempre normalizado uppercase antes de armazenar/comparar
- **Dedup**: passar tudo por `_adicionar_ou_mesclar_ap` ou `_mesclar_aps` — nunca `self.alvos.append(ap)` direto sem checar BSSID
- **Captura handshake**: NÃO reintroduzir hcxdumptool/scapy puro como estratégia. Manter só airodump+aireplay.

---

## 12. Histórico de versões

### v1.5.4 (2026-04-29)
- **`--kamikase` implica `--live`**: dashboard ativa automaticamente. Comando alvo do usuário simplificado para `sudo -E python NetDroid.py --root --kamikase`. Help text atualizado.

### v1.5.3 (2026-04-29)
- **Lazy monitor mode**: airmon-ng NÃO é mais ativado no boot. Iface fica em managed mode e nmcli funciona livremente. Monitor é ativado on-demand via `_garantir_monitor_ativo()` quando o primeiro AP entra em vermelha/azul. Após isso, nmcli volta vazio (esperado).
- **Scan inicial 3× nmcli**: novo `_scan_inicial_nmcli_triplo()` roda nmcli 3 vezes com 1.5s de pausa, mescla via `_mesclar_aps`, dedupa por BSSID. Substitui o caminho que caía em scapy.
- **Continuous scan**: `remapear_redes` agora usa **só nmcli** (sem fallback iw/scapy). Se nmcli vier vazio em monitor mode, log informa "esperado".
- **Channel hopper**: agora gated por `monitor_ativo` E pausa quando há `capture_stops` ou `deauth_procs` ativos.
- **Zona vermelha refatorada**: substituído loop Python `aireplay -0 1 a cada 200ms` (5 pkt/s) por **um único `aireplay-ng --deauth 0 -a <BSSID> --ignore-negative-one <iface>` infinito** que roda como subprocess persistente (~64 pkt/s broadcast). Trava canal antes via `iw set channel`. Thread só monitora processo, atualiza contador aproximado (+64/s) e reinicia se cair. `self.deauth_procs: Dict[bssid, [Popen]]` rastreia.
- **Botão `🔄 recapturar handshake`**: cancela captura atual, limpa handshake antigo, re-dispara `_iniciar_crack_async` do zero. Novo socket event `recapturar_handshake` + método `KamikaseEngine.recapturar_handshake`.
- **Contador de tentativas grande no card azul**: durante `status==="capturing"`, mostra `🎯 #N` em fonte 3xl com glow ciano.
- Bump VERSION="1.5.3".

### v1.5.2 (2026-04-29)
- **Cadeado** na zona verde substituindo botão `🔍 Profundo`. Trava todas as varreduras (frontend + backend).
- **Botão `🦂 Scapy`** novo + endpoint `/api/scan_scapy` (sniff passivo, idempotente).
- **Filtro absoluto** de ESSID `?` em `_normalizar_ap` (retorna None).
- **Handshake refatorado**: 4 estratégias antigas removidas. Estratégia única — airodump escutando contínuo + bursts de 30 deauths via aireplay-ng a cada ~8s + detecção via aircrack-ng/scapy. Channel hopper pausa enquanto captura ativa.
- **Deauth interval `0.5s → 0.2s`** em `_loop_deauth_zona` (5 pkt/s sustentado).
- Constante `HAS_AIRCRACK` adicionada.
- Bump VERSION="1.5.2".

### v1.5.1 (2026-04-29)
- Auto-monitor no boot do `--live` (antes do scan inicial — crítico p/ varredura completa).
- Scan contínuo + channel hopper paralelo (1-13 + 5GHz comuns).
- Cross-fill canal↔freq via lookup table 802.11.
- Botão `📡 NMCLI` + endpoint `/api/scan_nmcli`.
- (Versão anterior) captura handshake com retry infinito 4 estratégias — substituída em v1.5.2.

### v1.5.0
- Pasta `Pass/senhas.txt` append-only.
- Pasta `imports/` + endpoints export PDF+TXT.
- Animação `morph-to-green` + `glow-victory` ao crack ter sucesso.
- 9 bugs corrigidos: thread explosion (semáforo), monitor não-validado, dedup quebrado, ETA hashcat, render perf, senha persistida não-renderizada, race condition em cancel, log frontend cap, listeners órfãos.

### v1.4.0 e anteriores
Construção inicial: classes `KamikaseEngine`, `LiveDashboard`, `GodMode`, `MemoriaPersistente`. Modos `--auto`/`--god`/`--godfall`/`--kamikase` consolidados (flag `--normal` removida).

---

## 13. Cheat-sheet pro próximo agente

### Como navegar o arquivo gigante
```python
# Achar uma classe
Grep(pattern=r"^class KamikaseEngine", path="NetDroid.py")

# Achar todos endpoints
Grep(pattern=r"@app\.route", path="NetDroid.py")

# Achar todos os emit
Grep(pattern=r"emitir\(", path="NetDroid.py")
```

### Verificações antes de claim "pronto"
```bash
python -m py_compile NetDroid.py             # syntax
python NetDroid.py --version                 # banner com versão correta
sudo -E python NetDroid.py --root --kamikase --live   # smoke real (Kali)
```

### Pegadinhas comuns
1. **`sudo` sem `-E`** quebra o venv → sempre `sudo -E python ...`
2. **Channel hopper roda em paralelo** — se você adicionar nova feature que precisa de canal fixo, registre algo no `capture_stops` ou crie flag análoga, senão o hopper sabota
3. **Frontend dedupa por `aps[bssid]`** — sempre emite com `bssid` válido uppercase, ou JS quebra
4. **`emitir()` é thread-safe** mas argumentos não podem ter chave `nome` (kwarg conflita com SocketIO `name`)
5. **HasattribuTar em `KamikaseEngine`**: alguns dicts (`capture_stops`) inicializados no `__init__` mas o código também faz `if not hasattr(self, "capture_stops")` defensivamente — é proposital para suportar reload
6. **`HANDSHAKE_RETRY_FOREVER = True`** controla se o loop de captura é infinito; se mudar para False, há fallback de 30 tentativas

### O que perguntar ao usuário antes de mexer
- Mudanças no template HTML/JS — ele tem opinião forte sobre UX
- Estratégias de captura/ataque — ele testa em Kali real e prefere coisas simples e previsíveis
- Auto-comportamentos (auto-iniciar X, auto-fechar Y) — sempre confirma
- Adicionar dependências em `requirements.txt` — pergunta primeiro

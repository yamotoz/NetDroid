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
DEAUTH_THREAD_LIMIT = 100            # teto de threads (carrossel + reserva)
CONTINUOUS_SCAN_INTERVAL_SEC = 6     # cadência do scan contínuo
CHANNEL_HOP_INTERVAL_MS = 250        # tempo em cada canal (channel hopper geral)
HANDSHAKE_RETRY_FOREVER = True       # captura handshake nunca desiste
CARROSSEL_SLOT_VERMELHA_S = 15       # tempo por canal quando só há vermelha
CARROSSEL_SLOT_AZUL_S = 20           # tempo por canal quando há azul
CARROSSEL_AIRODUMP_BOOT_S = 1.5      # pausa entre airodump up e aireplay
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
| **`CarrosselCanal`** | **5764** | **Orquestrador único de canais** — vê seção 5b |
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

### Movimentar AP entre zonas ([mover_para_zona](NetDroid.py#L3970))
Disparado pelo websocket `mover_zona`. **A partir da v1.5.6 não spawna threads per-AP** — apenas registra na zona, ativa monitor lazy, garante carrossel rodando:
- Sai da `vermelha`/`azul` → AP simplesmente some do agrupamento na próxima iteração do carrossel
- Entra `vermelha` → ativa monitor lazy + `_garantir_carrossel()`
- Entra `azul` → salva `crack_wordlists`/`crack_perfil` no AP + `_garantir_carrossel()`. Quando carrossel capturar handshake, enfileira hashcat automaticamente

### Métodos legacy preservados (não chamados pelo `mover_para_zona`)
- `_loop_deauth_zona` (linha ~4043): thread per-AP com `aireplay --deauth 0`. **Dead code** mas mantido pra modos não-live se houver
- `_iniciar_crack_async` (linha ~4134): spawna `capturar_infinito`. **Dead code**
- `PMKIDCapture.capturar_infinito` (linha ~5566): loop de captura per-AP. **Dead code**

`reset_deauth(bssid)` (linha ~4227) e `reset_crack(bssid, recapturar)` (linha ~4286) foram **adaptados** ao modelo carrossel:
- `reset_deauth`: zera contador e chama `_garantir_carrossel()`
- `reset_crack(recapturar=True)`: delega pra `recapturar_handshake` (limpa `handshake_path`, carrossel re-tenta)
- `reset_crack(recapturar=False)`: re-enfileira hashcat com handshake existente

---

## 5b. CarrosselCanal — orquestrador único de canais (v1.5.6+)

[CarrosselCanal](NetDroid.py#L5764) — single thread, orquestra TODA a operação das zonas vermelha+azul. Resolve o conflito hardware "1 placa = 1 canal por vez" via slots rotativos.

### Estado interno
- `slot_vermelha = CARROSSEL_SLOT_VERMELHA_S` (15s)
- `slot_azul = CARROSSEL_SLOT_AZUL_S` (20s — handshake precisa de mais tempo)
- `canal_atual`, `canal_inicio`, `canal_slot_s` — estado público pro frontend
- `canais_pendentes` — lista de canais aguardando próximo slot

### Loop principal ([_loop](NetDroid.py))
1. `_agrupar_por_canal()` lê estado vivo de `engine.zonas` e devolve `{canal: {vermelha:[aps], azul:[aps]}}`. APs azul com `handshake_path` já preenchido são **pulados** (não capturam de novo)
2. Para cada canal (asc): `_executar_slot(canal, grupo, slot_s)`. Slot dura 20s se há AP azul, senão 15s
3. Se zonas vazias: idle (espera 2s e re-checa)

### `_executar_slot(canal, grupo, slot_s)`
1. **Trava canal**: `iw dev <iface> set channel <canal>`
2. **Sobe airodump** (só se há AP azul): `airodump-ng --channel <C> -w <arq> --output-format cap <iface>` (sem `--bssid` filter — captura todo o tráfego do canal)
3. **Spawna `aireplay-ng --deauth 0 -a <BSSID>` para CADA AP** (vermelha+azul) do canal — múltiplos aireplays simultâneos no mesmo canal funcionam (cada um manda ~64 pkts/s pra seu BSSID)
4. **Aguarda slot** atualizando UI 1×/s: emite `carrossel_tick{canal,restante_s,slot_s,ativo,canais_pendentes}` + `ap_update` por AP do slot com `carrossel_canal` e `carrossel_slot_restante`
5. **Mata todos** os aireplays e airodump
6. **Checa cap** pra cada AP azul via `PMKIDCapture._cap_tem_handshake(cap, bssid)` (hcxpcapngtool — match perfeito)
7. **Se handshake real**: `_registrar_handshake_azul(ap, cap)` → copia cap pra `memoria/handshakes/`, registra na memória, enfileira no hashcat (se há `crack_wordlists` configurado)

### Eventos emitidos
- `carrossel_status{ativo}` — start/stop do carrossel
- `carrossel_slot{canal,vermelha,azul,slot_s}` — entrada num novo slot
- `carrossel_tick{canal,restante_s,slot_s,ativo,canais_pendentes}` — 1Hz durante slot
- `handshake_capturado{bssid,pcap}` — quando handshake real é validado e persistido

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

### Zona Vermelha (deauth via carrossel)
Drag/drop de cards verdes pra cá → carrossel inclui o AP no slot do canal dele. Card mostra `pacotes` (contador aproximado +64/s durante slot ativo). Em vez de attack contínuo per-AP, é cíclico por canal.

### Zona Azul (handshake + crack)
Drag pra cá → carrossel captura handshake no slot do canal → quando captura validada via hcxpcapngtool, enfileira hashcat com wordlists escolhidas. Card mostra estágio: `queued_carrossel` (aguardando), `capturing` (slot ativo), `queued`/`running` (hashcat), `cracked` (animação `morph-to-green` 2s + `glow-victory` 4s).

### Agrupamento por canal (v1.5.6+)
Cada zona é renderizada agrupada por canal via `_agruparPorCanal()`. Header `📡 Canal 6 — 3 APs` precede cada grupo. Dentro do grupo, APs ordenados por RSSI desc. Canais ordenados asc (`?` no fim).

No header da vermelha/azul, badge `🔄 atacando · 8s/15s` (canal sendo atendido pelo carrossel) ou `⏳ aguardando` (canal pendente). Atualiza via `carrossel_tick`.

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

### v1.6.0 (2026-05-02) — Burst-listen pattern (CORREÇÃO CRÍTICA da captura)

#### Bug crítico identificado pelo usuário
- Sintoma: "ele esta conseguindo derrubar perfeitamente, porém ele não da tempo para reconexão e a partir disso não captura de jeito nenhum o handshake"
- Causa: usar `aireplay-ng --deauth 0` contínuo na zona azul (igual vermelha) impede o cliente de reconectar — fica perpetuamente kickado
- Sem reconexão = sem handshake = sem captura

#### Fix: padrão burst-listen (industry-standard)
Diferenciamos comportamento por zona em `_executar_slot`:
- **Vermelha**: continua com `aireplay-ng --deauth 0` em Popen background (objetivo é derrubar, não capturar)
- **Azul**: NOVO padrão — `aireplay-ng -0 30` (burst finito ~1s) → espera **8s** de silêncio → próximo burst

Em um slot de 30s na azul: ~3 bursts de 30 deauths + 3 janelas de escuta de 8s. Cliente tem janelas garantidas pra completar 4-way handshake (~250ms). Espelha estratégia de wifite/airgeddon.

#### Constantes novas
- `CARROSSEL_AZUL_BURST_PKTS = 30` (deauths por burst)
- `CARROSSEL_AZUL_LISTEN_S = 8` (janela de escuta entre bursts)

#### Card azul renovado
- Agora mostra fase atual: `💥 disparando burst` ou `👂 escutando reconexão`
- Contador de bursts disparados: `💥 ${burstCount} bursts`
- Texto explicativo: "disparando burst (kick clientes)" / "escutando reconexão (cliente vai mandar EAPOL)"
- Eventos `handshake_log` mais detalhados pro debug

#### Bump VERSION="1.6.0" — mudança de comportamento substantiva merece minor bump

### v1.5.9 (2026-05-02) — Slot azul configurável + indicador de ciclos
- **Slot azul configurável**: dropdown na header da zona azul (10s padrão / 30s / 1min / 5min / ∞ infinito). Slots maiores = mais chance de pegar handshake de clientes lentos (TVs, IoT). Default 10s pra ciclo rápido.
- Novo método `CarrosselCanal.set_slot_azul(segundos, infinito, canal_lock)` simétrico ao `set_slot_vermelha`. Idem para socket handler `set_slot_azul`.
- **Métricas per-AP de tentativas**:
  - `ap["carrossel_ciclos"]`: incrementa cada vez que o AP é incluído num slot
  - `ap["carrossel_tempo_acumulado_s"]`: total de segundos que o AP foi atacado pelo carrossel (soma dos slots)
  - Reset automático quando AP entra em azul vindo de outra zona (`origem != "azul"`)
- **Card azul renovado**: mostra `🎯 ciclo #N · ⏱ Xmin Ys acumulados` em vez de só `#N`. Status `queued_carrossel` ganhou bloco visual `⏳ aguardando slot · próximo ciclo do carrossel`.
- Frontend `setSlotAzul(val)` espelha `setSlotVermelha`. Toast informa "slots maiores = mais chance pra clientes lentos".
- Bump VERSION="1.5.9"

### v1.5.8 (2026-05-02) — Azul cirúrgica + zonas mutex + --upgrade fix

#### Bug crítico: azul não capturava handshake mais
- **Causa**: v1.5.7 tinha lógica de "para deauth aos 10s, escuta passiva 14s" no `_executar_slot`. Em teoria capturaria EAPOL após cliente reconectar; em prática **falhava** porque cliente nem sempre reconecta dentro da janela e aireplay cortado no meio = deauth fraco demais.
- **Fix**: Removido todo o early-stop e listen-extra. Agora **espelha 100% a vermelha** — `aireplay-ng --deauth 0 --ignore-negative-one -a <BSSID> <iface>` + `airodump-ng --bssid <BSSID> --channel <C>` rodando contínuos pelo slot inteiro.
- **Slot azul**: `CARROSSEL_SLOT_AZUL_S` 30s → **10s** (decisão usuário). Validação roda no fim do slot via `hcxpcapngtool --apmac=<BSSID>`. Se cap não tem handshake, próximo slot tenta de novo.
- **Flush time**: nova constante `CARROSSEL_AZUL_FLUSH_S = 1.5` (era hardcoded `time.sleep(2.0)`). Pausa entre `airodump.terminate()` e validação pra cap aterrissar no disco.

#### Zonas vermelha ↔ azul mutuamente exclusivas
- Decisão do usuário: AP só pode estar em UMA das duas. **`mover_para_zona`** agora detecta conflito: se destino é vermelha e há APs em azul (ou vice-versa), todos os APs da zona conflitante são automaticamente movidos pra verde antes de aceitar o movimento. Emite evento `zona_mutex{origem,destino,movidos}`.
- **Implicação**: simplificou drasticamente `_executar_slot` — `grupo` agora tem APENAS uma das duas zonas populada. Sem mais lógica condicional separando vermelha+azul no mesmo canal. Single-zone-per-slot.

#### `--upgrade` consertado
- **Bug**: URLs apontavam pra `/main/NetDroid.py` mas o repo (`yamotoz/NetDroid`) está em `/master/`. Resultado: 404 em todas as tentativas.
- **Fix**: `GITHUB_BRANCHES = ("master", "main")` — Upgrader tenta master primeiro, fallback automático pra main. Robusto se usuário mudar branch padrão no futuro.
- Novo método `Upgrader._fetch_branch_fallback(path)` que retorna `(conteudo, branch_que_funcionou)`. Mostra no log qual branch foi usada. 404 não retenta mais (sai cedo).

#### Cleanup automático
- Boot do `CarrosselCanal.iniciar()` limpa `SLOT_TEMP_DIR` de slot caps órfãos de execuções anteriores que crasharam.

#### Bump VERSION="1.5.8"

---

### v1.5.7 (2026-04-30) — Per-AP folder + slot customizável
- **Pasta dedicada por AP em azul**: `handshakes/azul/<BSSID>/` com **apenas** `handshake.cap` + `handshake.22000`. Só é populada quando handshake REAL é detectado pra esse BSSID específico.
- **Validação cirúrgica via `hcxpcapngtool --apmac=<MAC>`**: o filtro nativo do hcxpcapngtool extrai apenas o handshake do BSSID-alvo. Se o `.22000` sai não-vazio, é handshake real e o cap é movido pra pasta dedicada. Se sai vazio, o arquivo é deletado e o slot continua. **Zero falso positivo, zero acúmulo**.
- **Cap temporário por slot** vai pra `handshakes/_slot_temp/` e é **deletado** após cada slot. Antes, 10 slots = 10 caps lotando `handshakes/`.
- **Slot vermelha customizável**: dropdown na zona vermelha (15s padrão / 1min / 5min / 1h / **∞ infinito**). Modo infinito = `modo_infinito=True` + `canal_lockado=<int>`: carrossel trava em UM canal, não rotaciona; outros canais ficam pausados. Se canal lockado fica vazio, escolhe o próximo automaticamente.
- **Novo método `CarrosselCanal.set_slot_vermelha(segundos, infinito, canal_lock)`**: setter unificado.
- **Novo socket event `set_slot_vermelha`** + handler no `LiveDashboard`.
- **Novo evento `carrossel_config`**: emitido a cada mudança de slot/modo, frontend logga.
- **Logs detalhados no slot azul**: cada AP mostra `🔍 BSSID hcx_out=NB → ✓ HANDSHAKE` ou `✗ vazio` no log do dashboard. Visibilidade total do que tá acontecendo.
- **`airodump --write-interval 1`**: força flush a cada 1s, evita cap truncado.
- Bump VERSION="1.5.7".

### v1.5.6+audit (2026-04-30) — Auditoria militar
Auditoria estática do módulo `--kamikase`. **2 bugs reais corrigidos**, 9 falsos positivos descartados.

#### Bugs corrigidos
- **🔴 CRÍTICO — Channel hopper sabotava o carrossel**: `_loop_channel_hopper` checava `capture_stops` e `deauth_procs` (modelo antigo, agora vazios) pra pausar. Como o carrossel novo guarda estado em `self.carrossel.canal_atual`, o hopper continuava trocando canal a cada 250ms durante o slot, jogando airodump/aireplay no canal errado. **Fix em [NetDroid.py:3947-3957](NetDroid.py#L3947)** — adicionado check `carrossel_ativo` que pausa o hopper enquanto o carrossel tem `canal_atual` setado.
- **🟡 BAIXO — Race em `self.subprocs`/`self.threads` no encerramento**: `_encerrar_limpo` iterava as listas enquanto threads filhas podiam appendar (RuntimeError "list changed during iteration"). **Fix em [NetDroid.py:5277-5289](NetDroid.py#L5277)** — `list(self.subprocs)` snapshot antes de iterar. Risco baixo pois `--live` não usa essas listas (carrossel tem suas próprias), mas existia no path `--kamikase` puro.

#### Falsos positivos descartados
- `CarrosselDeauth`: classe não existe (real é `CarrosselCanal`)
- `subprocess.run` sem timeout: 0/16 (todos têm)
- `bare except:`: 0 ocorrências
- `json.dump` não-atômico: já é atômico (`tmp.replace()`)
- Race em `contador_global`: tudo lockado em `with self.contador_lock:`
- `os.system` no carrossel: não usa (só `subprocess.run/Popen`)
- Divisão por zero em PPS: PPS é JS frontend com guard `dt>0?`
- `_consent_duplo` sem EOF/Ctrl+C: já trata
- `signal_handler` ausente: cleanup vem via `try/finally`, KeyboardInterrupt capturado em 8 lugares — funciona

#### Limitações documentadas (não-bugs)
- WPA3 não suportado (usa SAE, não 4-way EAPOL — limitação do método 4-way handshake genérico)

### v1.5.6 (2026-04-29) — Carrossel de canal
- **Nova classe `CarrosselCanal`** (NetDroid.py linha ~5764): orquestrador único single-thread que substitui o spawn-por-AP. Roda enquanto há APs em vermelha+azul. A cada slot:
  1. Agrupa APs ativos por canal (pula azuis com `handshake_path` já preenchido)
  2. Trava canal via `iw dev set channel`
  3. Sobe airodump-ng (se há azul) sem `--bssid` filter — captura tudo no canal
  4. Spawna `aireplay-ng --deauth 0 -a <BSSID>` pra cada AP (vermelha+azul) do canal
  5. Aguarda slot (15s vermelha-only, 20s se há azul)
  6. Mata processos, checa cap pra cada AP azul via `_cap_tem_handshake` (hcxpcapngtool)
  7. Se handshake real → registra na memória + enfileira hashcat
  8. Próximo canal
- **Compat hashcat**: continua sequencial. Captura roda paralela ao crack.
- **`mover_para_zona` refatorado**: não spawna mais thread por AP. Só registra na zona, ativa monitor mode lazy, garante carrossel rodando.
- **`recapturar_handshake` adaptado**: limpa `handshake_path` → carrossel volta a incluir AP nos slots de captura. Sem cancel-thread-and-respawn.
- **Constantes**: `CARROSSEL_SLOT_VERMELHA_S=15`, `CARROSSEL_SLOT_AZUL_S=20`, `CARROSSEL_AIRODUMP_BOOT_S=1.5`, `DEAUTH_THREAD_LIMIT=100` (era 8).
- **Frontend zonas agrupadas por canal**: `_renderZonasNow` agora chama `_agruparPorCanal` → headers `📡 Canal 6 — 3 APs` entre grupos. APs ordenados por RSSI desc dentro do canal. Canais ordenados asc; `?` no fim.
- **Badge de slot ativo nos headers**: `🔄 atacando · 8s/15s` no canal sendo atendido, `⏳ aguardando` nos pendentes. Atualiza via socket `carrossel_tick` (1Hz).
- **Eventos novos**: `carrossel_status{ativo}`, `carrossel_slot{canal,vermelha,azul,slot_s}`, `carrossel_tick{canal,restante_s,slot_s,ativo,canais_pendentes}`.
- **`_encerrar_limpo`** chama `carrossel.parar()` antes de matar subprocs (mata aireplays/airodumps em curso).
- **Métodos antigos preservados** (`_loop_deauth_zona`, `_iniciar_crack_async`, `PMKIDCapture.capturar_infinito`) — não são mais chamados pelo `mover_para_zona`, mas ficam disponíveis caso modos não-live precisem.
- Bump VERSION="1.5.6".

### v1.5.5 (2026-04-29)
- **Detecção de handshake usando `hcxpcapngtool`**: a mesma ferramenta usada pra converter `.cap` → `.22000` agora valida a presença de handshake. Match perfeito — se ela extrai, hashcat crackeia. Antes, `_cap_tem_handshake` aceitava ≥2 frames EAPOL via scapy, gerando falso positivo que quebrava no `convert_failed`.
- **Re-trava canal antes de cada burst** em `capturar_infinito` — vermelha em canal diferente roubava a iface entre tentativas.
- **Auto-restart airodump** se o processo morrer mid-loop.
- **Aborta cedo se canal=`?`**: sem canal não há captura confiável; loga erro pedindo NMCLI rescan.
- **Eventos `handshake_log`** novos: dashboard recebe trace passo-a-passo (`burst #N ch6`, `cap 4096B handshake=False`, `airodump morreu — restart`, etc).
- **Eventos `handshake_tentativa` / `handshake_capturado`** agora têm listeners no template — toast + log visível.
- Removido fallback scapy (≥2 EAPOL) — fonte do falso positivo.
- Bump VERSION="1.5.5".

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
2. **Channel hopper** (`_loop_channel_hopper`) tem 3 condições pra pausar: monitor não ativo, `capture_stops`/`deauth_procs` populados (modelo legacy), OU **`carrossel.canal_atual` setado** (modelo atual v1.5.6+). Se adicionar nova feature que precise de canal fixo, adicione check análogo
3. **Frontend dedupa por `aps[bssid]`** — sempre emite com `bssid` válido uppercase, ou JS quebra
4. **`emitir()` é thread-safe** mas argumentos não podem ter chave `nome` (kwarg conflita com SocketIO `name`)
5. **Carrossel é a fonte de verdade** das zonas vermelha+azul. Não spawna threads per-AP. NÃO chame `_loop_deauth_zona`/`_iniciar_crack_async`/`capturar_infinito` (dead code)
6. **APs azul com `handshake_path`** preenchido são pulados pelo carrossel. Pra recapturar: `recapturar_handshake(bssid)` limpa o campo
7. **Hashcat sequencial** (1 por vez, GPU dedicada). Captura roda paralela ao crack — quando primeiro handshake aparece, hashcat já começa enquanto carrossel pega os próximos

### O que perguntar ao usuário antes de mexer
- Mudanças no template HTML/JS — ele tem opinião forte sobre UX
- Estratégias de captura/ataque — ele testa em Kali real e prefere coisas simples e previsíveis
- Auto-comportamentos (auto-iniciar X, auto-fechar Y) — sempre confirma
- Adicionar dependências em `requirements.txt` — pergunta primeiro

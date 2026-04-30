# NetDroid 🤖💻

**Professional WiFi Network Analysis Toolkit — v1.5.6**
Single-file, assíncrono, Termux/Linux/Windows. **CLI minimalista de 3 modos** + booster `--root` apex militar.

![NetDroid Banner](https://img.shields.io/badge/NetDroid-v1.5.6-red?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.7+-blue?style=for-the-badge)
![Modos](https://img.shields.io/badge/Modos-3-orange?style=for-the-badge)

## 🎯 Filosofia

Apenas **3 verbos**, cada um com escopo claro:

```
--god       →  reconhecimento total (descoberta + scan + auditoria)
--godfall   →  ataque colossal (stress massivo a todos os hosts da rede)
--kamikase  →  deauth WiFi + dashboard C2 (carrossel por canal)
```

E dois **modificadores**:

```
--root      →  amplifica os 3 modos com raw sockets, scapy, binários nativos
--live      →  abre dashboard C2 web (já é IMPLÍCITO em --kamikase desde v1.5.4)
```

## 🛠️ Como Usar

```bash
# Reconhecimento completo da rede (descoberta + scan total + auditoria)
python NetDroid.py --auto --god

# Ataque massivo a todos os hosts (roteador, celular, TV, IoT, …)
python NetDroid.py --auto --godfall

# Modo apex (precisa rodar como admin/root/su)
sudo -E python NetDroid.py --root --auto --god

# Deauth WiFi + dashboard C2 — comando simplificado (--live é automático)
sudo -E python NetDroid.py --root --kamikase
```

## 📋 As 3 Flags em Detalhe

### 🛡️ `--god` — Reconhecimento Total

Pacote completo de auditoria defensiva em **3 fases automáticas**:

| Fase | O que faz |
|---|---|
| **1/3 Descoberta** | ARP cache + ping sweep + TCP probe + mDNS (5353) + NetBIOS (137) + SSDP (1900) + SMB Negotiate (445) + HTTP fingerprint + DHCP leases + nmap (opcional). Cada host recebe `hostname`, `device_type` (roteador/câmera/impressora/NAS/IoT/...) e **score de confiança 0–100**. |
| **2/3 Scan completo** | TCP scan **1–65535** em todos os hosts descobertos + banner grabbing + cruzamento com `VULN_DB` (~80 assinaturas, severidades crítica/alta/média/info) + auditoria de headers HTTP + fingerprint SSH/Apache/IIS + verificação ProFTPD/vsftpd CVEs. |
| **3/3 Auditoria defensiva** | 50+ device fingerprints, sondagem de 30+ API endpoints, probes de amplificação (SNMP `public`, NTP monlist, DNS `version.bind`), paths default (`/phpmyadmin`, `/.env`, `/.git/config`), ONVIF WS-Discovery, RTSP discovery, hunt de credenciais padrão, **Credential & Secret Hunting** (vazamentos, PSK exposta, SNMP communities), **risk scoring** consolidado por host. |

**Saída**: relatório HTML cyberpunk responsivo + TXT executivo com glossário didático.

### ⚡ `--godfall` — Ataque Colossal

> ## ⚠️ AVISO LEGAL — `--godfall`
> **Este módulo SATURA a rede com tráfego massivo a TODOS os hosts** (roteador, celular, TV, IoT). Pode derrubar o roteador.
>
> **Não há prompt de confirmação** — a flag executa direto. **Responsabilidade inteiramente do operador.**
>
> Use APENAS em sua própria rede / lab pessoal / pentest com contrato escrito / CTF / pesquisa acadêmica.
>
> **Brasil**: Lei 12.737/2012. **EUA**: CFAA. **EU**: GDPR + NIS2.

Stress profissional em **2 fases progressivas** atacando **todos os hosts da subnet** simultaneamente:

| Fase | Multiplier (insane) | Concorrência (insane) | Barrage tier (insane) |
|---|---|---|---|
| **OVERDRIVE** | 2.60x (3.60x) | 256 (384) | 2 (3) |
| **TITANFALL** | 3.50x (5.00x) | 384 (512) | 3 (4) |

**Sob `--root`**: TITANFALL chega a **6.50x** (8.00x insane) com concorrência **768** (1024 insane), mais SYN flood spoofed via scapy.

#### Safety rails (freios automáticos)

| Modo | Comportamento |
|---|---|
| `--godfall` | **Freios ATIVOS**: aborta automaticamente se latência ≥ 8x baseline, packet loss ≥ 92% ou success ≤ 4%. Recovery window de 90s. |
| `--godfall --infinite` | **Sem freios**. Anuncia `🚨 REDE CAIU` mas continua até `Ctrl+C`. |

### 📡 `--kamikase` — Deauth + Dashboard C2 (Carrossel por canal)

> ## ⚠️ AVISO LEGAL — `--kamikase`
> **Operar deauth contra rede sem autorização é CRIME** (Brasil Lei 12.737/2012 · EUA CFAA · EU GDPR/NIS2). Lab pessoal · pentest contratado · CTF · pesquisa apenas.

**Exige `--root`. `--live` é automático** (dashboard em http://127.0.0.1:5556 sobe junto). A partir de v1.5.6 a arquitetura é totalmente nova:

#### 🔄 Carrossel de canal (escala pra 60+ APs sem suar)

A limitação fundamental é hardware: **1 placa wifi = 1 rádio = 1 canal por vez**. NetDroid resolve via slots rotativos:

1. Backend agrupa APs ativos (vermelha + azul) por canal: `{ch1: [AP1,AP2], ch6: [AP9...], ...}`
2. Loop: trava ch1 via `iw set channel` → sobe airodump (se há AP azul) + `aireplay-ng --deauth 0` para CADA AP do canal → ataca por **15s** (vermelha) / **20s** (azul) → mata processos → checa cap pra handshakes → próximo canal
3. **Múltiplos APs no mesmo canal são atacados simultaneamente** dentro do slot
4. Hashcat roda em paralelo (GPU dedicada, não usa a placa wifi) — primeiro handshake pego já começa a crackear enquanto o carrossel pega os próximos

Em 1 minuto, todos os canais foram atacados ciclicamente.

#### 📋 Dashboard 3 zonas drag-and-drop

| Zona | Cor | O que faz |
|---|---|---|
| 🟢 **VERDE** | Verde | APs descobertos via NMCLI (3× no boot, dedup absoluto). Header `📡 Canal X — N APs` agrupa visualmente. Botões: `🔄 Mapear Contínuo`, `🔓 Cadeado`, `📡 NMCLI`, `🦂 Scapy` (opcional). |
| 🔴 **VERMELHA** | Vermelho pulsante | APs sob deauth flood broadcast contínuo (`aireplay --deauth 0`). Carrossel cicla por canais. Badge no header: `🔄 atacando · 8s/15s` ou `⏳ aguardando`. |
| 🔵 **AZUL** | Ciano | Captura de handshake + crack queue. Card mostra `🎯 #N` (tentativa atual) durante captura. Detecção via `hcxpcapngtool` (zero falso positivo). Botão `🔄 recapturar handshake` em cada card. |

#### 🚦 Boot, monitor mode e cadeado

- **Boot**: NMCLI roda 3× sequencial, mescla, dedupa por BSSID → zona verde populada com TODAS as redes da área (canal/freq/segurança preenchidos)
- **Monitor mode preguiçoso**: airmon-ng só ativa quando o **primeiro AP** é movido pra vermelha/azul. Antes disso, NMCLI funciona perfeitamente. Após ativação, NMCLI volta vazio (esperado — `iw dev` virou monitor) e o carrossel toma conta
- **Cadeado** 🔓/🔒 (header zona verde): trava todas as varreduras manuais. Útil quando você já tem os alvos identificados e não quer mais APs entrando

#### 🎯 Como usar com 60 APs

1. Boot → NMCLI popula zona verde, agrupada por canal
2. Move APs alvo pra vermelha (em massa OU 1 a 1, tanto faz)
3. Carrossel detecta canais únicos automaticamente, rotaciona slots
4. Pra capturar handshake: move APs pra azul. Carrossel inclui no slot do canal correspondente
5. Hashcat já vai crackeando em background os primeiros que aparecerem

#### Pré-checks de segurança

- **Consent duplo**: pré-check técnico (driver Windows na lista negra exige `FORCAR`) + consent legal (`EU AUTORIZO`)
- **Audit log obrigatório** (`kamikase_audit.log`)

#### Limitações honestas por SO

- ✅ **Linux/Kali**: caminho preferencial — funciona pleno com adapter compatível
- ⚠️ **Windows**: depende 100% do driver. Intel AC 9xxx / Realtek RTL88xx **bloqueiam injection**. Adapters Alfa AWUS036NHA / TL-WN722N v1 funcionam
- ⚠️ **Termux**: requer chip Android com suporte a monitor mode (raro)
- ⛔ **WPA3**: não suportado (usa SAE handshake, não 4-way EAPOL). Funciona em WPA/WPA2-PSK

## 💾 Persistência Local — `Pass/`, `imports/`, `memoria/`

NetDroid mantém **3 pastas locais** para persistir tudo entre sessões:

| Pasta | O que armazena | Formato |
|---|---|---|
| `memoria/db.json` | Banco completo de APs vistos: ESSID, BSSID, canal, RSSI, segurança, achados, histórico de zonas, senhas, handshakes (write atômico via tmp+replace) | JSON estruturado |
| `memoria/handshakes/` | Capturas `.cap`/`.pcapng` por AP | pcapng/cap nativo |
| **`Pass/senhas.txt`** | Todas as senhas quebradas append-only (idempotente) | `ESSID\|BSSID\|senha\|wordlist\|data` |
| **`imports/`** | Exports de zonas via botão "📤 exportar" do dashboard | TXT + PDF |
| `WordList/` | Wordlists do hashcat — coloque aqui seus `.txt` (rockyou, fasttrack, etc.) | TXT linha-a-linha |
| `WordList/_contextual_*.txt` | Wordlists geradas automaticamente pelo NetDroid (1000 variações por ESSID) | TXT |

Para limpar tudo (cuidado): `rm -rf memoria/ Pass/ imports/`. As wordlists em `WordList/` permanecem.

---

## 🌐 `--live` — Dashboard C2 em Tempo Real

Painel web local em `http://127.0.0.1:5556` com WebSocket + animações + atualização ao vivo. Tema cyberpunk preto/vermelho/branco.

```bash
sudo -E python NetDroid.py --auto --god --live        # mapeamento ao vivo
sudo -E python NetDroid.py --root --kamikase          # 3 zonas drag-drop (live implícito)
```

### Eventos WebSocket relevantes (kamikase)

| Evento | Função |
|---|---|
| `ap_descoberto` / `ap_update` | Card aparece/atualiza (dedup por BSSID) |
| `carrossel_status` | Carrossel iniciado/parado |
| `carrossel_slot` | Entrou em novo slot — `{canal,vermelha,azul,slot_s}` |
| `carrossel_tick` | 1Hz durante slot — `{canal,restante_s,slot_s,canais_pendentes}` |
| `handshake_capturado` | Handshake validado via hcxpcapngtool — toast verde |
| `handshake_log` | Trace passo-a-passo da captura visível no log do dashboard |

### Wordlist Contextual (Personalização Militar)

Quando você arrasta um AP para a zona azul, o NetDroid **gera automaticamente 1000 variações contextuais** baseadas no nome do WiFi e prepende elas **antes** da wordlist escolhida. Exemplo para `Casa01`:

```
casa01, Casa01, CASA01, c454501, C454501,           ← bases + leet speak
casa01123, casa011234, casa0112345,                 ← + sufixos numéricos
casa01@2024, Casa01@2025, casa01_2024,              ← + anos
@casa01, wificasa01, casa01wifi,                    ← + prefixos genéricos
casa01!, Casa01@123, CASA01!@#$,                    ← + símbolos
... (até 1000 variações filtradas para WPA2-PSK 8-63 chars)
```

A lógica:
- Bases: nome original + lowercase + UPPERCASE + Capitalize + leet (a→4, e→3, i→1, o→0, s→5)
- Detecta `camelCase` e separa partes (ex: `MinhaCasa` → `minha`, `casa`)
- Combina cada base com 40+ sufixos numéricos, 17 anos (2010-2026), 25 símbolos comuns, 11 prefixos genéricos
- Filtra para WPA2-PSK válido (8-63 chars)
- Ordena por probabilidade: 8-12 chars primeiro

Resultado: arquivo gerado em `./WordList/_contextual_<essid>.txt`. Hashcat testa isso primeiro — senhas óbvias caem em segundos antes da rockyou.

### Perfis hashcat (CPU/GPU)

| Perfil | Workload | Descrição |
|---|---|---|
| 🟢 **LOW** | 1 | Silencioso (~30% GPU) — bom para rodar em background |
| 🟡 **MEDIUM** | 2 | Balanceado (~60% GPU) — uso geral |
| 🟠 **HARD** | 3 | Pesado (~90% GPU) — quando você quer pressa |
| 🔴 **INSANE** | 4 | 100% GPU descontrolado — laptop pode trottlar |

### Pipeline de captura/crack na zona azul

1. Carrossel sobe `airodump-ng --channel <C> -w <arq> --output-format cap` no canal do AP
2. Spawna `aireplay-ng --deauth 0 -a <BSSID>` em paralelo (broadcast contínuo, força reconexão)
3. Após o slot, checa o `.cap` via **`hcxpcapngtool`** — se conseguir extrair `.22000`, é handshake real (zero falso positivo, mesma ferramenta usada pela conversão posterior)
4. Cap é movido pra `memoria/handshakes/` + enfileirado no hashcat com perfil/wordlists configurados
5. Senha quebrada → animação `morph-to-green` 2s + `glow-victory` 4s + persistida em `Pass/senhas.txt`

### PDF Executivo

Ao final de qualquer execução com `--god` ou `--kamikase`, um **PDF profissional** é gerado automaticamente em `{SSID}/NetDroid_*.pdf` com inventário de hosts, top vulnerabilidades, dados do kamikase e tema corporativo.

---

## 🔥 `--root` — Booster APEX

Auto-detecta SO e ativa motor militar:

| SO | Motor | Como ativar |
|---|---|---|
| Windows 10/11 | `adm` | PowerShell **como Administrador** |
| Linux/Kali | `root-kali` | `sudo -E python NetDroid.py ...` |
| Termux (Android) | `root-termux` | Magisk + `pkg install tsu` + `tsu` |

### Amplificações por modo

- **`--god` + `--root`**: ARP active sweep raw (10x mais rápido), raw ICMP echo (TTL real), SYN fingerprint OS, SNMP wordlist 40+, DNS cache snooping, ARP spoof passivo via tcpdump, LLDP/CDP listener
- **`--godfall` + `--root`**: fases ROOT com multipliers até **8.0x**, concorrência **1024**, SYN flood spoofed (IPs source aleatórios) via scapy, thermal guard em Termux
- **`--kamikase` + `--root`**: pré-requisito obrigatório (sem `--root` recusa)

## 🚀 Instalação

### Linux/Kali (caminho preferencial)
```bash
# Setup completo (1 linha — copie/cole no terminal)
sudo apt update -y && sudo apt install -y python3 python3-pip python3-venv \
  aircrack-ng mdk4 hcxdumptool hcxtools hashcat tcpdump arp-scan iw \
  wireless-tools nmap iperf3 iptables net-tools curl wget git && \
  python3 -m venv venv && source venv/bin/activate && \
  pip install --upgrade pip && pip install -r requirements.txt && \
  mkdir -p WordList && \
  (test -f /usr/share/wordlists/rockyou.txt || sudo gunzip -k /usr/share/wordlists/rockyou.txt.gz 2>/dev/null) && \
  cp /usr/share/wordlists/rockyou.txt ./WordList/ 2>/dev/null

# Rodar (sempre com sudo -E pra preservar o venv)
source venv/bin/activate
sudo -E python NetDroid.py --root --kamikase
```

Detalhes no [`requirementskali.txt`](requirementskali.txt).

### Termux (Android com root)
```bash
pkg update && pkg upgrade
pkg install python iperf3 aircrack-ng mdk4 tcpdump iw nmap tsu
pip install -r requirements.txt
tsu -c "python NetDroid.py --root --auto --god"
```

### Windows
```powershell
# PowerShell como Administrador
pip install -r requirements.txt
# Para --kamikase: instalar NPCAP de https://npcap.com/ (modo "WinPcap API-compatible")
python NetDroid.py --root --auto --god
```

---
**⚠️ AVISO LEGAL FINAL:** ferramenta para auditoria autorizada. Uso contra redes sem permissão é ilegal. O autor não se responsabiliza por danos.

# NetDroid 🤖💻

**Professional WiFi Network Analysis Toolkit — v1.5.0**
Single-file, assíncrono, Termux/Linux/Windows. **CLI minimalista de 3 modos** + booster `--root` apex militar.

![NetDroid Banner](https://img.shields.io/badge/NetDroid-v1.5.0-red?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.7+-blue?style=for-the-badge)
![Modos](https://img.shields.io/badge/Modos-3-orange?style=for-the-badge)

## 🎯 Filosofia

Apenas **3 verbos**, cada um com escopo claro:

```
--god       →  reconhecimento total (descoberta + scan + auditoria)
--godfall   →  ataque colossal (stress massivo a todos os hosts da rede)
--kamikase  →  deauth WiFi (derruba clientes 802.11)
```

E dois **modificadores**:

```
--root      →  amplifica os 3 modos com raw sockets, scapy, binários nativos
--live      →  abre dashboard C2 web localhost com WebSocket + animações
```

## 🛠️ Como Usar

```bash
# Reconhecimento completo da rede (descoberta + scan total + auditoria)
python NetDroid.py --auto --god

# Ataque massivo a todos os hosts (roteador, celular, TV, IoT, …)
python NetDroid.py --auto --godfall

# Ataque sem freios até Ctrl+C
python NetDroid.py --auto --godfall --infinite

# Modo apex (precisa rodar como admin/root/su)
sudo python NetDroid.py --root --auto --god

# Deauth WiFi (só funciona pleno em Kali Linux)
sudo python NetDroid.py --root --kamikase
```

## 📋 As 3 Flags em Detalhe

### 🛡️ `--god` — Reconhecimento Total

Pacote completo de auditoria defensiva em **3 fases automáticas**:

| Fase | O que faz |
|---|---|
| **1/3 Descoberta** | ARP cache + ping sweep + TCP probe + mDNS (5353) + NetBIOS (137) + SSDP (1900) + SMB Negotiate (445) + HTTP fingerprint + DHCP leases + nmap (opcional). Cada host recebe `hostname`, `device_type` (roteador/câmera/impressora/NAS/IoT/...) e **score de confiança 0–100**. |
| **2/3 Scan completo** | TCP scan **1–65535** em todos os hosts descobertos + banner grabbing + cruzamento com `VULN_DB` (~80 assinaturas, severidades crítica/alta/média/info) + auditoria de headers HTTP + fingerprint SSH/Apache/IIS + verificação ProFTPD/vsftpd CVEs. |
| **3/3 Auditoria defensiva** | 50+ device fingerprints, sondagem de 30+ API endpoints, probes de amplificação (SNMP `public`, NTP monlist, DNS `version.bind`), paths default (`/phpmyadmin`, `/.env`, `/.git/config`), ONVIF WS-Discovery, RTSP discovery, hunt de credenciais padrão, **Credential & Secret Hunting** (vazamentos, PSK exposta, SNMP communities), **risk scoring** consolidado por host. |

**Saída**: relatório HTML cyberpunk responsivo + TXT executivo com glossário didático explicando cada tipo de achado.

### ⚡ `--godfall` — Ataque Colossal

> ## ⚠️ AVISO LEGAL — `--godfall`
> **Este módulo SATURA a rede com tráfego massivo a TODOS os hosts** (roteador, celular, TV, IoT). Pode derrubar o roteador, dropar conexões e em modo `--infinite` causar reboot do equipamento.
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

**Vetores de ataque (em paralelo por fase)**:
- até **168 threads UDP raw** (payloads 65507/4096/512 alternados, 14 portas-chave)
- até **384 threads TCP connect-and-close**
- HTTP storm para portas web descobertas
- SYN flood spoofed (apenas com `--root` + scapy)
- baseline iperf3 (RECON inicial, se disponível)

**Comportamento sem `--god`**: o godfall ataca a **subnet inteira** (todos os 254 IPs do /24) — bom pra spray rápido sem precisar fazer descoberta antes.

**Comportamento com `--god`**: ataca **apenas os hosts vivos** descobertos na fase 1.

#### Safety rails (freios automáticos)

| Modo | Comportamento |
|---|---|
| `--godfall` | **Freios ATIVOS**: aborta automaticamente se latência ≥ 8x baseline, packet loss ≥ 92% ou success ≤ 4%. Recovery window de 90s. |
| `--godfall --infinite` | **Sem freios**. Anuncia `🚨 REDE CAIU` mas continua até `Ctrl+C`. Quando recupera: `✓ Rede recuperou — flooding continua`. |

### 📡 `--kamikase` — Deauth Flood 802.11

> ## ⚠️ AVISO LEGAL — `--kamikase`
> **Operar deauth contra rede sem autorização é CRIME** (Brasil Lei 12.737/2012 · EUA CFAA · EU GDPR/NIS2). Lab pessoal · pentest contratado · CTF · pesquisa apenas.

**Exige `--root`**. Discovery híbrido dos APs visíveis (`iw scan` / `netsh wlan show networks` / `termux-wifi-scaninfo`), monitor mode automático, ataque infinito multi-vetor:
- `aireplay-ng -0 0` por BSSID em paralelo
- `mdk4` probe + assoc flood
- Fallback scapy `Dot11Deauth` em loop

**Consent duplo**: pré-check técnico (driver Windows na lista negra exige `FORCAR`) + consent legal (`EU AUTORIZO`). **Audit log obrigatório** (`kamikase_audit.log`).

**Limitações honestas por SO**:
- ✅ **Linux/Kali**: caminho preferencial — funciona pleno com adapter compatível.
- ⚠️ **Windows**: depende 100% do driver. Intel AC 9xxx / Realtek RTL88xx **bloqueiam injection** (Camada A+B detecta e avisa antes). Adapters Alfa AWUS036NHA / TL-WN722N v1 funcionam.
- ⚠️ **Termux**: requer chip Android com suporte a monitor mode no driver (raro em consumer).

## 💾 Persistência Local — `Pass/`, `imports/`, `memoria/`

NetDroid mantém **3 pastas locais** para persistir tudo entre sessões:

| Pasta | O que armazena | Formato |
|---|---|---|
| `memoria/db.json` | Banco completo de APs vistos: ESSID, BSSID, canal, RSSI, segurança, achados, histórico de zonas, senhas, handshakes | JSON estruturado |
| `memoria/handshakes/` | Capturas `.pcapng` por AP (`<ESSID>_<BSSID>.pcapng`) | pcapng nativo |
| **`Pass/senhas.txt`** | Todas as senhas quebradas append-only (idempotente) | `ESSID\|BSSID\|senha\|wordlist\|data` |
| **`imports/`** | Exports de zonas via botão "📤 exportar" do dashboard | TXT + PDF |
| `WordList/` | Wordlists do hashcat — coloque aqui seus `.txt` (rockyou, fasttrack, etc.) | TXT linha-a-linha |
| `WordList/_contextual_*.txt` | Wordlists geradas automaticamente pelo NetDroid (1000 variações por ESSID) | TXT |

Para limpar tudo (cuidado): `rm -rf memoria/ Pass/ imports/`. As wordlists em `WordList/` permanecem.

---

## 🌐 `--live` — Dashboard C2 em Tempo Real

Abre um painel web local em `http://127.0.0.1:5556` com WebSocket + animações + atualização ao vivo. Tema cyberpunk preto/vermelho/branco, modo escuro padrão.

```bash
sudo python NetDroid.py --auto --god --live        # mapeamento ao vivo
sudo python NetDroid.py --root --kamikase --live   # 3 zonas drag-drop
```

### Combinado com `--god`

Painel "GOD · C2 LIVE" com:
- 🏷️ **Header**: logo NETDROID + tag GOD pulsante + relógio.
- 📊 **4 cards** no topo: hosts mapeados, portas abertas, vulnerabilidades, fase atual.
- ⚔️ **Inventário de hosts** ao centro: cada card clicável expande para mostrar MAC, vendor, OS, portas, fontes de descoberta e vulnerabilidades.
- 🥧 **Pie charts** lateral: distribuição por tipo de dispositivo + severidade de vulns.
- 🚨 **Lista de vulnerabilidades** detectadas com badges coloridos por severidade.
- 📡 **Log em tempo real** com timestamps e tipo (info/ok/warn/err).

### Combinado com `--kamikase`

Painel "KAMIKASE · C2 LIVE" com **3 zonas drag-and-drop**:

| Zona | Cor | O que faz |
|---|---|---|
| 🟢 **VERDE** | Verde | APs descobertos saudáveis. Arraste **para fora** desta zona para iniciar ações. |
| 🔴 **VERMELHA** | Vermelho pulsante | APs sob deauth flood: **1 pacote a cada 0.5s** infinitamente. **Animação morph-to-red 3s** ao chegar (verde→amarelo→laranja→vermelho indicando "morte progressiva"). Arraste de volta para verde para encerrar o ataque. |
| 🔵 **AZUL** | Ciano | Crack queue do hashcat: ao soltar um AP aqui, abre modal com perfil (LOW/MEDIUM/HARD/INSANE) + wordlist + checkbox "prepend variações contextuais". Captura PMKID/handshake automaticamente, dispara hashcat com **barra de progresso, ETA e contador de variações contextuais**. Senha quebrada aparece em verde com `<code>` tag. |

### Movimentação em massa

| Operação | Como fazer |
|---|---|
| **1 AP** | Arraste com mouse OU marque o checkbox e use a barra superior |
| **Vários selecionados** | Marque checkboxes em qualquer zona → barra amarela "Ação em massa" aparece no topo → escolha destino |
| **Todos de uma zona** | Cada zona tem botões: `→ todos vermelha`, `→ todos azul`, `← todos verde`, `selecionar tudo` |

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
- Ordena por probabilidade: 8-12 chars primeiro (residencial mais comum)

Resultado: arquivo gerado em `./WordList/_contextual_<essid>.txt` que **inclui as variações + a wordlist base** numa única lista. Hashcat testa isso primeiro — senhas óbvias caem em segundos antes da rockyou.

### Sidebar de Wordlists

Painel "📚 Wordlists Disponíveis" no dashboard mostra todos os `.txt` da pasta `./WordList/` em tempo real. Marca arquivos `_contextual_*` como `(contextual)` para distinguir das wordlists base.

### Perfis hashcat (CPU/GPU)

| Perfil | Workload | Descrição |
|---|---|---|
| 🟢 **LOW** | 1 | Silencioso (~30% GPU) — bom para rodar em background |
| 🟡 **MEDIUM** | 2 | Balanceado (~60% GPU) — uso geral |
| 🟠 **HARD** | 3 | Pesado (~90% GPU) — quando você quer pressa |
| 🔴 **INSANE** | 4 | 100% GPU descontrolado — laptop pode trottlar |

Cada card de AP mostra ESSID, BSSID, canal, RSSI, **score de segurança 0–100**, badges de criptografia (WPA2/WPA3/WEP/OPN), tag WPS quando habilitado, e achados específicos (sinal excessivo, beacon anômalo, etc).

Header mostra contador global de pacotes + PPS em tempo real, com pie chart vivo das 3 zonas.

### Captura PMKID/Handshake (zona azul)

Pipeline automático ao arrastar para azul:
1. **`hcxdumptool`** focado no BSSID (rápido, sem precisar cliente conectado).
2. **Fallback**: se hcxdumptool falhar, dispara `aireplay-ng -0 10` para forçar reconexão e captura via `airodump-ng`.
3. **`hcxpcapngtool`** converte pcapng → formato `22000` (PMKID + EAPOL).
4. **`hashcat -m 22000`** com perfil escolhido + wordlist da pasta `./WordList/`.

### Wordlists

Coloque arquivos `.txt` em `./WordList/`. O dashboard lista todos automaticamente no modal de configuração de crack. Wordlist padrão `comum.txt` já incluída (28 senhas frequentes em PT-BR).

```bash
# Adicionar rockyou (Kali já tem)
gunzip -k /usr/share/wordlists/rockyou.txt.gz
cp /usr/share/wordlists/rockyou.txt ./WordList/
```

### PDF Executivo

Ao final de qualquer execução com `--god` ou `--kamikase`, um **PDF profissional** é gerado automaticamente em `{SSID}/NetDroid_*.pdf` com inventário de hosts, top vulnerabilidades, dados do kamikase e tema corporativo.

---

## 🔥 `--root` — Booster APEX

Auto-detecta SO e ativa motor militar:

| SO | Motor | Como ativar |
|---|---|---|
| Windows 10/11 | `adm` | PowerShell **como Administrador** |
| Linux/Kali | `root-kali` | `sudo python NetDroid.py ...` |
| Termux (Android) | `root-termux` | Magisk + `pkg install tsu` + `tsu` |

### Amplificações por modo

- **`--god` + `--root`**: ARP active sweep raw (10x mais rápido), raw ICMP echo (TTL real), SYN fingerprint OS, SNMP wordlist 40+, DNS cache snooping, ARP spoof passivo via tcpdump, LLDP/CDP listener.
- **`--godfall` + `--root`**: fases ROOT com multipliers até **8.0x**, concorrência **1024**, SYN flood spoofed (IPs source aleatórios) via scapy paralelo à barragem UDP/TCP, thermal guard em Termux.
- **`--kamikase` + `--root`**: pré-requisito obrigatório (sem `--root` recusa).

## 📁 Saída

Pasta `{SSID}/` com:

- **`report_*.html`** — relatório cyberpunk responsivo: cards `Privilege Mode`, `Inventário de Hosts` (com Hostname, Tipo, Confiança, Fontes), `Vulnerabilidades`, `Credential & Secret Hunting`, `Risk Findings`, `Godfall Titan Sweep`, `Kamikase Death Toll`, `Latency During Stress`. Badges coloridos por tipo de dispositivo e severidade. Bloco didático expandível em cada card explicando **o que é, como validar, qual o impacto**.
- **`{SSID}_*.txt`** — resumo executivo em PT-BR com glossário didático no final explicando cada tipo de achado que apareceu na varredura.
- **`kamikase_audit.log`** (apenas se `--kamikase` rodou) — log append-only com timestamps, plataforma, BSSIDs alvo, comando completo.

## 🚀 Instalação

### Linux/Kali (caminho preferencial)
```bash
sudo apt install python3 python3-pip aircrack-ng mdk4 tcpdump arp-scan iw nmap iperf3
git clone https://github.com/yamotoz/NetDroid
cd NetDroid
pip install -r requirements.txt
sudo python NetDroid.py --root --auto --god
```

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

# NetDroid 🤖💻

**Professional WiFi Network Analysis Toolkit**  
Um script single-file robusto, assíncrono e cyberpunk desenhado para pentesters e analistas de rede. Desenvolvido para funcionar nativamente no **Termux (Android)**, **Linux** e **Windows**, sem necessidade de root.

![NetDroid Banner](https://img.shields.io/badge/NetDroid-v1.0.0-red?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.7+-blue?style=for-the-badge)
![Root](https://img.shields.io/badge/Root-Not_Required-success?style=for-the-badge)

## 🛠️ Como Usar

O script é comandado inteiramente por flags CLI que podem ser combinadas para criar fluxos de trabalho personalizados.

```bash
# Exemplo: Auditoria Total (Descoberta + Scan Completo + God Mode)
python NetDroid.py --auto --discover --Insane --god
```

## 📋 Lista Completa de Comandos

### 🛰️ Alvos e Descoberta
| Flag | O que faz? | Quando usar? |
|---|---|---|
| `--auto` | Detecta automaticamente sua rede (IP, Gateway, Subnet, SSID). | Quase sempre, para não ter que digitar IPs manualmente. |
| `--t <IP/CIDR>` | Define um alvo manual (ex: `192.168.1.5` ou `10.0.0.0/24`). | Quando quiser auditar um IP específico ou rede fora da sua. |
| `--discover` | Realiza um Ping Sweep paralelo e lê a tabela ARP do sistema. | Para descobrir quais dispositivos estão vivos na rede. |

### 🔍 Port Scanning (Análise de Portas)
| Flag | O que faz? | Estilo |
|---|---|---|
| `--normal` | Escaneia as Top 20 portas mais comuns (SSH, HTTP, etc). | Rápido e direto. |
| `--stealth` | Escaneia as Top 100 portas com delays aleatórios entre elas. | Furtivo, para evitar detecção básica. |
| `--Insane` | Escaneia TODAS as 65.535 portas de cada host encontrado. | Agressivo e lento, mas não deixa nada passar. |
| `--ports <P,P>` | Escaneia apenas as portas informadas (ex: `--ports 80,443`). | Cirúrgico. |

### ⚔️ Arsenal IoT / God Mode (Ataques Avançados)
Ao usar `--god`, todas as funções abaixo são executadas em sequência. Você também pode usá-las individualmente:

| Flag | O que faz? | Risco |
|---|---|---|
| **`--god`** | **Executa TUDO**: ONVIF, SSDP, NetBIOS, Probes, Mirai, Slowloris e RTSP-Kill. | **ALTO** (Afeta a rede) |
| `--onvif` | Procura câmeras IP via Multicast (descobre marca/modelo/firmware). | Baixo (Apenas info) |
| `--mirai` | Tenta logar em SSH/Telnet usando senhas padrão (Mirai Botnet). | Médio (Tentativa login) |
| `--slowloris` | Ataque DoS que trava painéis web de roteadores e câmeras. | **ALTO** (Derruba serviços) |
| `--rtsp-kill` | Ataque de exaustão que trava o stream de vídeo de câmeras IP. | **ALTO** (Derruba vídeo) |

### 🚀 Performance e Utilidades
| Flag | O que faz? |
|---|---|
| `--overfull` | Stress test básico usando TCP/UDP/HTTP Flooding. |
| `--overflow` | Stress test profissional usando `iperf3` (requer o binário instalado). |
| `--upgrade` | Busca e instala a versão mais recente do script via GitHub. |
| `--version` | Exibe a versão atual do NetDroid. |

## 📁 Relatórios e Resultados
Ao final de cada execução bem sucedida, uma pasta com o nome do **SSID** da rede será criada contendo:
*   **report_*.html**: Um relatório cyberpunk interativo e visualmente deslumbrante.
*   **scan_*.txt**: Um resumo executivo em texto puro para leitura rápida.

---

## 🚀 Instalação Rápida (Termux/Linux)

```bash
pkg update && pkg upgrade
pkg install python iperf3 -y
pip install -r requirements.txt
python NetDroid.py --auto --discover
```

---
**⚠️ AVISO LEGAL:** Esta ferramenta foi criada para fins de auditoria e segurança. O uso contra redes sem autorização prévia é ilegal. O autor não se responsabiliza por danos causados por ataques de stress em equipamentos sensíveis.

# 💻 Documentação da Interface de Linha de Comando (CLI `rps-sim`)

A interface de linha de comando **`rps-sim`** (`rps_br.adapters.cli`) fornece controle, inspeção de telemetria e execução autônoma do simulador diretamente a partir do terminal.

Projetada segundo a Arquitetura Hexagonal, a CLI atua como um **Adaptador Primário (*Driving Adapter*)** resiliente com comportamento de **dupla via (Dual-Mode Execution)**:
1. **Modo Conectado (API Gateway):** Quando o gateway de telemetria web (`dashboard.sh` ou `server.py`) está em execução em `http://127.0.0.1:8000`, a CLI consome os endpoints RESTful, permitindo inspecionar e comandar a simulação ativa em tempo real sem interferir no processo servidor.
2. **Modo Autônomo Local (*Core Fallback*):** Caso o servidor não esteja ativo, a CLI instancia e executa diretamente os agregados e casos de uso puros do Core (`SimulationSessionService`, `ConstellationAggregate`, `CalculateGroundStationDopUseCase`), viabilizando execuções *headless*, automações em scripts de integração contínua (CI) e avaliações em servidores remotos sem interface gráfica.

---

## 🚀 Instalação e Execução

A CLI pode ser invocada de três formas:

```bash
# 1. Executável nativo (quando instalado via pip/pipx ou setup.py):
rps-sim --help

# 2. Execução direta via módulo Python:
python3 -m rps_br.adapters.cli --help

# 3. Via script auxiliar no contêiner ou ambiente local:
./scripts/rps-sim status
```

---

## 📋 Comandos Disponíveis

```text
Uso: rps-sim [-h] {status,satellites,dop,pause,resume,speed,run} ...

🛰️ RPS-BR CLI: Controle e Monitoramento Autônomo da Constelação Regional Brasileira

Comandos:
  status       Exibe o status consolidado da simulação e métricas
  satellites   Lista efemérides e visibilidade dos 7 satélites
  dop          Exibe a matriz de DOP nas 7 estações terrestres brasileiras
  pause        Pausa a simulação
  resume       Retoma a simulação
  speed        Ajusta o fator de aceleração temporal
  run          Executa o motor de simulação autônomo no terminal
```

---

## 🔍 Detalhamento dos Comandos

### 1. `rps-sim status`
Exibe o sumário executivo da simulação, identificando a fonte de dados (Web Gateway ou Core Local), tempo virtual corrente, taxa de aceleração temporal, estado de pausa e métricas de qualidade PVT da estação ativa.

* **Exemplo de Saída:**
```text
🛰️  SPR-BR / RPS-BR - Status da Simulação (Fonte: Web/Core Ativo)
=================================================================
  Modo Operacional:      STANDALONE
  Tempo Virtual:         02:15:30 (8130.0 s)
  Aceleração Temporal:   3600.0x
  Estado de Execução:    🟢 EM ANDAMENTO
  Estação Terrestre:     São José dos Campos (ITA / SP)
  Máscara de Elevação:   5.0°
  Satélites em Visada:   6 / 7
  Qualidade PVT (PDOP):  2.41 (EXCELENTE)
  GDOP / HDOP / VDOP:    2.85 / 1.38 / 1.97
=================================================================
```

---

### 2. `rps-sim satellites`
Computa e imprime a matriz orbital completa dos 7 veículos espaciais da constelação (3 GEO + 4 IGSO), incluindo coordenadas geodésicas (Latitude, Longitude e Altitude WGS84), azimute, elevação e condição de visada direta (*Line-of-Sight*) a partir da estação terrestre de referência.

* **Exemplo de Saída:**
```text
📡 Matriz Orbital dos 7 Satélites:
--------------------------------------------------------------------------------
PRN  Nome                         Tipo   Lat (°)   Lon (°)   Alt (km)   Az (°)   El (°)   Visada
--------------------------------------------------------------------------------
1    RPS-GEO-1                    GEO    0.00      -60.00    35786.0    315.2    52.4     ✅ LOS
2    RPS-GEO-2                    GEO    0.00      -48.00    35786.0    24.2     68.1     ✅ LOS
3    RPS-GEO-3                    GEO    0.00      -36.00    35786.0    88.5     48.3     ✅ LOS
4    RPS-IGSO-1                   IGSO   -18.42    -48.15    40120.5    185.0    32.5     ✅ LOS
5    RPS-IGSO-2                   IGSO   -24.80    -42.30    42164.1    210.1    74.2     ✅ LOS
6    RPS-IGSO-3                   IGSO   12.10     -54.80    36200.4    45.0     41.0     ✅ LOS
7    RPS-IGSO-4                   IGSO   24.80     -48.00    42164.1    120.0    2.1      ❌ MASC
--------------------------------------------------------------------------------
```

---

### 3. `rps-sim dop`
Executa a avaliação geométrica multissítio simultânea em tempo real sobre as 7 principais estações terrestres de monitoramento e controle do território brasileiro (São José dos Campos, Brasília, Alcântara, Manaus, Recife, Porto Alegre e Cuiabá).

* **Exemplo de Saída:**
```text
🎯 Qualidade Geométrica PVT (DOP) nas Estações Terrestres Brasileiras:
   (Tempo Virtual: 8130.0s | Máscara: 5.0°)
---------------------------------------------------------------------------
Estação Terrestre                Vis   GDOP     PDOP     HDOP     VDOP    
---------------------------------------------------------------------------
São José dos Campos (ITA / SP)   6     2.85     2.41     1.38     1.97    
Brasília (DF)                    6     2.62     2.18     1.24     1.80    
Alcântara (CLA / MA)             6     2.98     2.50     1.45     2.04    
Manaus (AM)                      5     3.45     2.89     1.72     2.33    
Recife (PE)                      5     3.81     3.15     1.89     2.52    
Porto Alegre (RS)                5     3.60     3.02     1.80     2.43    
Cuiabá (MT)                      6     2.74     2.29     1.30     1.89    
---------------------------------------------------------------------------
```

---

### 4. `rps-sim pause` e `rps-sim resume`
Controlam o ciclo de vida temporal da simulação.
* Se a API web estiver ativa, envia a requisição HTTP `POST /api/control/pause` congelando/retomando gráficos, cálculos e transmissões WebSocket.
* Se em modo autônomo, comuta a flag `is_paused` diretamente no `SimulationSessionService`.

```bash
# Congela o avanço do tempo:
rps-sim pause
# Saída: ⏸️  Simulação pausada com sucesso via Web API.

# Retoma o avanço:
rps-sim resume
# Saída: ▶️  Simulação retomada com sucesso via Web API.
```

---

### 5. `rps-sim speed <multiplier>`
Ajusta a velocidade de propagação temporal. Permite analisar um dia sideral inteiro (24 horas) em poucos segundos reais.

* **Argumentos:**
  * `multiplier` (float, $\ge 0.1$): Fator de escala temporal ($1.0 = \text{tempo real}$, $60.0 = 1\text{ min/s}$, $3600.0 = 1\text{ h/s}$).

```bash
# Configura o motor para 1 hora por segundo:
rps-sim speed 3600
# Saída: ⚡ Aceleração ajustada para 3600.0x via Web API.
```

---

### 6. `rps-sim run [--speed MULT]`
Inicia um motor de simulação contínuo em primeiro plano no próprio terminal, imprimindo uma linha de status auto-atualizável a cada segundo. Ideal para monitoramento rápido sem necessidade de navegador ou servidor web.

* **Opções:**
  * `--speed MULT`: Multiplicador de aceleração (padrão: `60.0x`).
* **Interrupção:** `Ctrl+C` encerra o laço de forma graciosa sem deixar recursos presos.

* **Exemplo de Saída Interativa:**
```text
🚀 Iniciando Motor de Simulação Autônomo do RPS-BR (Multiplicador: 3600x)
   Pressione Ctrl+C para encerrar.

⏱️  [04:22:15] | Vel: 3600x | ITA Visíveis: 6/7 | PDOP: 2.38
```

---

## 🛠️ Automação e Integração com Scripts Shell

A CLI respeita os padrões POSIX de códigos de saída:
* `0`: Operação concluída com sucesso.
* `1`: Erro de argumento, conexão ou parâmetro fora de intervalo.

### Exemplo de Script Bash de Validação em Lote:
```bash
#!/usr/bin/env bash
set -e

echo "1. Inicializando verificação do RPS-BR..."
rps-sim status

echo "2. Validando métricas DOP de todas as estações..."
rps-sim dop

echo "3. Ajustando aceleração para 3600x..."
rps-sim speed 3600

echo "✅ Verificação da CLI concluída com êxito!"
```

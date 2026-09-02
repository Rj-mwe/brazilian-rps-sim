# 📋 Requisitos de Missão do RPS-BR

* **Documento**: REQ-RPS-BR-001
* **Versão**: 1.0 (Baseline)
* **Classificação**: Engenharia de Sistemas Aeroespaciais

---

## 1. Requisitos de Cobertura Geográfica
* **REQ-COV-01**: O sistema deve fornecer cobertura contínua e ininterrupta (24 horas por dia, 365 dias por ano) sobre todo o território continental do Brasil.
* **REQ-COV-02**: A cobertura deve abranger com visibilidade geométrica a totalidade da Zona Econômica Exclusiva (ZEE / Amazônia Azul) até o limite exterior de 200 milhas náuticas e áreas de busca e salvamento (SAR).
* **REQ-COV-03**: Em qualquer ponto do território nacional, o número mínimo de satélites RPS-BR visíveis com ângulo de elevação $\ge 10^\circ$ deve ser de pelo menos **4 satélites** (garantindo determinação autônoma de posição tridimensional sem auxílio externo).

---

## 2. Requisitos de Desempenho de Navegação (GNSS / SBAS)
* **REQ-NAV-01 (DOP)**: O Dilution of Precision de Posição ($\text{PDOP}$) médio sobre o Brasil não deve exceder $3.0$ sob constelação nominal.
* **REQ-NAV-02 (Acurácia Horizontal)**: O erro de posicionamento horizontal (95% do tempo) com correções diferenciais do RPS-BR deve ser inferior a **1.5 metros** para usuários equipados de dupla frequência.
* **REQ-NAV-03 (Acurácia Vertical)**: O erro de posicionamento vertical (95% do tempo) deve ser inferior a **2.0 metros**.

---

## 3. Requisitos de Integridade e Segurança da Vida (Safety-of-Life)
* **REQ-SAF-01 (Tempo para Alarme - TTA)**: Em caso de falha de relógio ou degradação de sinal de qualquer satélite, o sistema de integridade deve alertar o usuário dentro de **6.0 segundos** (conforme padrão ICAO Categoria I).
* **REQ-SAF-02 (Limite de Proteção Horizontal - HPL)**: Em operações de aproximação de precisão aérea (APV-I), o $\text{HPL}$ calculado não deve ultrapassar o Limite de Alerta Horizontal ($\text{HAL} = 40.0\text{ m}$).
* **REQ-SAF-03 (Limite de Proteção Vertical - VPL)**: Em operações APV-I, o $\text{VPL}$ calculado não deve ultrapassar o Limite de Alerta Vertical ($\text{VAL} = 50.0\text{ m}$).

# ADR 0003: Padrões Strategy e Observer para Monitoramento e Métricas DOP

* **Status**: Aprovado e Implementado
* **Data**: 2026-08-30

---

## 1. Contexto & Problema
A avaliação da Diluição Geométrica de Precisão (DOP) requer diferentes critérios dependendo da aplicação (ex: aviação civil exige máscara de 5° a 10°, enquanto receptores em terra podem requerer ponderação estocástica por elevação). Além disso, diversas entidades (telemetria ROS 2, geradores de log e sistemas de alarme) precisam consumir os dados de DOP sem acoplamento direto com o algoritmo de cálculo.

---

## 2. Decisão
Combinar os padrões **Strategy** e **Observer**:
1. **Strategy Pattern (`IDopCalculationStrategy`)**:
   * `StandardLeastSquaresDopStrategy`: Matriz clássica de cossenos diretores $(G^T G)^{-1}$.
   * `ElevationMaskDopStrategy`: Filtragem geométrica por ângulo de corte zenital.
   * `WeightedElevationDopStrategy`: Ponderação estocástica proporcional a $\sin(\text{el})$.
2. **Observer Pattern (`IDopObserver`, `DopSubject`)**:
   * Desacoplamento entre cálculo e consumo: o `CalculateGroundStationDopUseCase` notifica múltiplos observadores (`DopAlertThresholdObserver`, `DopTelemetryBufferObserver`, `DopLoggingObserver`).

---

## 3. Consequências
* Troca dinâmica de algoritmo em tempo de execução sem alterar o cliente.
* Facilidade para adicionar novos observadores (ex: dashboards web, telemetria MAVLink ou MQTT) com zero impacto no domínio.

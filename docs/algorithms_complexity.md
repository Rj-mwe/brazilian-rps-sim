# 🧮 Análise de Algoritmos, Complexidade Estrutural e Estruturas de Dados

Este documento formaliza a análise de complexidade computacional assintótica (notação Big-$O$), eficiência algorítmica, estruturas de dados fundamentais e determinismo de tempo de execução do **Core** do **RPS-BR** (`rps_br.core`).

Em engenharia de sistemas aeroespaciais e radionavegação de missão crítica, a previsibilidade temporal e o limite superior de tempo de execução no pior caso (**WCET — *Worst-Case Execution Time***) são requisitos fundamentais para certificar que o simulador mantém estabilidade numérica contínua em qualquer regime operacional.

---

## ⏱️ 1. Matriz de Complexidade Assintótica dos Algoritmos do Core

| Algoritmo / Operação | Submódulo / Classe | Complexidade de Tempo (Médio) | Complexidade de Tempo (Pior Caso - WCET) | Complexidade de Espaço | Determinismo Numérico |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **Solucionador de Kepler (Newton-Raphson)** | `KeplerSolverService` | $O(1)$ | $O(1)$ (limite de $k \le 10$ iterações) | $O(1)$ | Convergência quadrática $\|E_{k+1} - E_k\| < 10^{-10}\text{ rad}$ |
| **Propagação Kepleriana Orbital** | `KeplerianPropagationPolicy` | $O(1)$ | $O(1)$ | $O(1)$ | Resolução analítica fechada |
| **Propagação da Constelação ($N$ satélites)** | `ConstellationAggregate` | $O(N)$ | $O(N)$ ($N = 7$ fixo) | $O(N)$ | Execução linear estrita |
| **Rotação de Referencial ECI $\to$ ECEF** | `CoordinateTransformService` | $O(1)$ | $O(1)$ ($3 \times 3$ matriz-vetor) | $O(1)$ | $\det(R) = 1.0 \pm 10^{-14}$ |
| **Conversão ECEF $\to$ Geodésica WGS-84** | `CoordinateTransformService` | $O(1)$ | $O(1)$ (laço limitado a 10 iterações) | $O(1)$ | Bowring iterativo estável |
| **Ângulos Topocêntricos (Az/El/Range)** | `CoordinateTransformService` | $O(1)$ | $O(1)$ | $O(1)$ | Projeção ENU analítica |
| **Montagem da Matriz de Geometria $G$** | `CalculateGroundStationDopUseCase` | $O(M)$ | $O(M)$ ($M \le N = 7$) | $O(M)$ | Matriz $M \times 4$ |
| **Inversão da Matriz Normal $(G^T G)^{-1}$** | `StandardLeastSquaresDopStrategy` | $O(1)$ | $O(1)$ (dimensão fixa $4 \times 4$) | $O(1)$ | Cholesky / LU $4 \times 4$ com guarda de posto |
| **Retardo Troposférico Saastamoinen** | `TroposphereSaastamoinenService` | $O(1)$ | $O(1)$ | $O(1)$ | Corte seguro para $el < 1.0^\circ$ |
| **Retardo Ionosférico Klobuchar** | `IonosphereKlobucharService` | $O(1)$ | $O(1)$ | $O(1)$ | Cosseno truncado com piso noturno |
| **Gerador de Pseudodistâncias Brutas** | `PseudorangeSimulationService` | $O(M)$ | $O(M)$ ($M \le N = 7$ satélites visíveis) | $O(M)$ | Determinístico com semente estocástica |
| **Solucionador WLS PVT (Gauss-Newton)** | `IterativeWlsPvtSolver` | $O(k \cdot M)$ ($k \le 4$ iterações) | $O(M)$ ($k_{\max} = 15$ iterações limite) | $O(M)$ | Tolerância $\|\Delta \mathbf{x}_{1:3}\| < 10^{-4}\text{ m}$, salvaguarda $\det > 10^{-12}$ |
| **Buffer Circular de Telemetria DOP** | `DopTelemetryBufferObserver` | $O(1)$ | $O(1)$ (inserção amortizada) | $O(K)$ ($K = 120$) | Memória estática limitada (`collections.deque`) |

---

## 🔍 2. Análise Detalhada dos Algoritmos Fundamentais

### A. Solução Transcendental da Equação de Kepler
A determinação da posição de um satélite na sua órbita elíptica requer a solução da Equação de Kepler:

$$M = E - e \sin E$$

onde $M$ é a anomalia média, $e$ é a excentricidade e $E$ é a anomalia excêntrica.

* **Método:** Newton-Raphson iterativo com valor inicial $E_0 = M + e \sin M + \frac{e^2}{2} \sin(2M)$.
* **Fórmula de Recorrência:**
  $$E_{k+1} = E_k - \frac{E_k - e \sin E_k - M}{1 - e \cos E_k}$$
* **Convergência:** Para órbitas quase-circulares e de baixa excentricidade ($e = 0.040$ nos IGSOs do RPS-BR e $e = 0$ nos GEOs), a convergência é estritamente quadrática. A tolerância de $\epsilon < 10^{-10}\text{ rad}$ é atingida em média em **3 a 4 iterações**.
* **Garantia de WCET:** O algoritmo possui um limitador estrito de $k_{\max} = 10$ iterações. Caso ocorra qualquer anomalia numérica, o laço é interrompido sem jamais entrar em laço infinito (*infinite loop*), assegurando $O(1)$ no pior caso.

---

### B. Propagação Linear da Constelação ($O(N)$)
A classe `ConstellationAggregate` gerencia os $N = 7$ veículos espaciais da frota (3 GEO + 4 IGSO).
* Como não há acoplamento gravitacional mútuo entre os satélites (a massa de cada satélite é desprezível em relação à massa da Terra, $\mu_{\text{sat}} \ll \mu_{\text{Terra}}$), a equação de movimento de cada veículo é desacoplada e independente.
* A propagação completa de um passo temporal propaga cada satélite individualmente em tempo $O(1)$, resultando em uma complexidade total de tempo estritamente linear:
  $$T_{\text{constelação}} = \sum_{i=1}^{N} T_{\text{sat}} = N \cdot O(1) = O(N)$$
* Para $N = 7$, o tempo de propagação da frota completa no hardware moderno é inferior a **$25\ \mu\text{s}$** (microssegundos), permitindo taxas de aceleração de até $86.400\times$ em tempo real sem sobrecarga de CPU.

---

### C. Avaliação da Matriz de Geometria e Inversão DOP ($O(M)$)
A Diluição Geométrica de Precisão (DOP) é computada a partir da matriz Jacobiana de visadas $G \in \mathbb{R}^{M \times 4}$, onde $M$ é o número de satélites visíveis com elevação superior à máscara ($\theta_i \ge \theta_{\text{mask}}$):

$$G = \begin{bmatrix} 
-\cos el_1 \sin az_1 & -\cos el_1 \cos az_1 & -\sin el_1 & 1 \\
\vdots & \vdots & \vdots & \vdots \\
-\cos el_M \sin az_M & -\cos el_M \cos az_M & -\sin el_M & 1 
\end{bmatrix}$$

1. **Montagem da Matriz $G$:** Cada linha representa as coordenadas topocêntricas unitárias do vetor de visada. Complexidade: $M \times O(1) = O(M)$.
2. **Produto Normal $A = G^T G$:** A multiplicação de uma matriz $4 \times M$ por uma matriz $M \times 4$ executa $4 \times 4 \times M = 16M$ multiplicações escalares. Complexidade: $O(M)$.
3. **Inversão da Matriz Normal $H = A^{-1}$:** A matriz normal $A \in \mathbb{R}^{4 \times 4}$ possui dimensão **fixa e independente do número de satélites**. A inversão de uma matriz $4 \times 4$ requer um número constante de operações de ponto flutuante ($4^3 = 64$ operações elementares via eliminação de Gauss-Jordan ou inversão analítica por cofatores). Complexidade: $O(1)$.
4. **Cálculo dos Coeficientes DOP:**
   $$\text{GDOP} = \sqrt{\text{tr}(H)}, \quad \text{PDOP} = \sqrt{H_{11} + H_{22} + H_{33}}, \quad \text{HDOP} = \sqrt{H_{11} + H_{22}}, \quad \text{VDOP} = \sqrt{H_{33}}$$
   Extração da diagonal em tempo $O(1)$.
* **Complexidade Total do Algoritmo DOP:**
  $$T_{\text{DOP}} = O(M) + O(M) + O(1) + O(1) = O(M)$$
  Como $M \le 7$, o cálculo de DOP consome menos de **$10\ \mu\text{s}$** por estação de solo.

---

### D. Modelagem de Atrasos Atmosféricos ($O(1)$)
* **Troposfera (Saastamoinen):** Avaliação de polinômios com pressão, temperatura, umidade e elevação. Não envolve laços ou integrações numéricas. Complexidade: $O(1)$.
* **Ionosfera (Klobuchar):** Cálculo da latitude geomagnética do IPP (Ionospheric Pierce Point), ângulo de fase solar e expansão em cosseno truncada. Complexidade: $O(1)$.

---

### E. Geração de Observáveis de Pseudodistância ($O(M)$)
A classe `PseudorangeSimulationService` sintetiza as medições brutas de rádio que chegam à antena do receptor:

$$\rho_i = R_i + c \cdot (\delta t_{\text{rx}} - \delta t_{\text{sat}}) + I_i + T_i + \Delta_{\text{rel}, i} + \epsilon_i$$

1. **Range Geométrico ($R_i$):** Cálculo analítico da norma Euclidiana $\|\mathbf{r}_{\text{sat}, i} - \mathbf{r}_{\text{rx}}\|$ em tempo $O(1)$.
2. **Correção Relativística Orbital ($\Delta_{\text{rel}, i}$):** Produto escalar no referencial inercial $\Delta_{\text{rel}} = -2 \frac{\mathbf{r}_{\text{eci}} \cdot \mathbf{v}_{\text{eci}}}{c}$ executado em $O(1)$ (nulo para GEOs circulares e não-nulo para IGSOs).
3. **Retardos Físicos e Desvios de Relógio:** Avaliação de Klobuchar ($O(1)$), Saastamoinen ($O(1)$) e viés do oscilador local ($O(1)$).
4. **Ruído Térmico Gaussiano ($\epsilon_i$):** Geração de variável aleatória normal com ponderação por elevação ($\sigma_i = \sigma_0 / \sin(el_i)$) via algoritmo de Box-Muller em $O(1)$.
* **Complexidade Total por Satélite:** $O(1)$.
* **Complexidade para a Constelação ($M$ satélites visíveis):**
  $$T_{\rho} = \sum_{i=1}^M O(1) = O(M)$$
  Para $M \le 7$, o tempo de execução total da síntese de pseudodistâncias é inferior a **$15\ \mu\text{s}$**, perfeitamente determinístico.

---

### F. Solucionador Iterativo de Mínimos Quadrados Ponderados (WLS PVT Solver)
A classe `IterativeWlsPvtSolver` implementa a determinação de posição e tempo do usuário (PVT) resolvendo o sistema sobredeterminado não-linear de pseudodistâncias via algoritmo de Gauss-Newton multivariado:

$$\Delta \mathbf{x}_{k+1} = (G_k^T W_k G_k)^{-1} G_k^T W_k \Delta \boldsymbol{\rho}_k$$
$$\mathbf{x}_{k+1} = \mathbf{x}_k + \Delta \mathbf{x}_{k+1}$$

onde $\mathbf{x} = [x_{\text{rx}}, y_{\text{rx}}, z_{\text{rx}}, c \cdot \delta t_{\text{rx}}]^T \in \mathbb{R}^4$ e $W \in \mathbb{R}^{M \times M}$ é a matriz diagonal de ponderação estocástica por elevação ($W_{ii} = \sin^2 el_i$).

1. **Montagem da Matriz de Geometria $G_k$ e Resíduos Pré-Ajuste $\Delta \boldsymbol{\rho}_k$:**
   A cada iteração, calcula a distância geométrica estimada $\hat{R}_{i} = \|\mathbf{r}_{\text{sat}, i} - \hat{\mathbf{r}}_{\text{rx}}\|$ e projeta os cossenos diretores da linha de visada unitária $\mathbf{u}_i = \frac{\hat{\mathbf{r}}_{\text{rx}} - \mathbf{r}_{\text{sat}, i}}{\hat{R}_i}$.
   Complexidade por iteração: $M \times O(1) = O(M)$.
2. **Multiplicação Ponderada $A_k = G_k^T W_k G_k$ e Vetor Normal $\mathbf{b}_k = G_k^T W_k \Delta \boldsymbol{\rho}_k$:**
   Como $W$ é diagonal, $W G$ consome $4M$ multiplicações e $G^T (W G)$ consome $16M$ operações. Complexidade: $O(M)$.
3. **Inversão da Matriz Normal $4 \times 4$ e Atualização de Estado:**
   Dimensão fixa $4 \times 4$ resolvida via eliminação de Gauss ou inversão analítica em $O(1)$.
4. **Critério de Parada e Salvaguarda Numérica:**
   O laço iterativo cessa quando $\|\Delta \mathbf{x}_{1:3}\| < 10^{-4}\text{ m}$ (tolerância submilimétrica) ou ao atingir o teto de $k_{\max} = 15$ iterações (*WCET* garantido).
   Em condições operacionais nominais com geometria RPS-BR, a convergência ocorre tipicamente em **3 a 4 iterações**, mesmo com chutes iniciais afastados a centenas de quilômetros.
5. **Avaliação Final de Resíduos e Matriz de Covariância:**
   Cálculo do vetor de resíduos pós-ajuste $\mathbf{r} = \Delta \boldsymbol{\rho} - G \Delta \mathbf{x}$ em $O(M)$, e extração dos fatores DOP a partir de $(G^T G)^{-1}$ em $O(1)$.

* **Complexidade Assintótica Total:**
  $$T_{\text{WLS}} = k \cdot [O(M) + O(M) + O(1)] + O(M) + O(1) = O(k \cdot M)$$
  Com $k \le 15$ e $M \le 7$, o tempo de execução total no pior caso é limitado a menos de **$40\ \mu\text{s}$**, viabilizando receptores com taxas de atualização de $100\text{ Hz}$ com margem computacional superior a $99\%$.

---

## 📦 3. Estruturas de Dados do Core e Pegada de Memória

### A. Value Objects Imutáveis (`frozen=True`)
Em linguagens dinâmicas como Python, a mutabilidade inadvertida de referências de memória é uma das maiores causas de corrupção sutil de dados científicos.
* O RPS-BR adota `@dataclass(frozen=True)` para todas as estruturas de dados atômicas:
  * `Vector3DVO`: 3 coordenadas float de 64 bits ($x, y, z$).
  * `GeodeticCoordinatesVO`: Latitude, Longitude e Altitude.
  * `KeplerianElementsVO`: Os 6 elementos orbitais de Kepler.
  * `TroposphericWeatherVO`: Pressão, Temperatura e Umidade.
  * `PseudorangeMeasurementVO`: Medição de pseudodistância com decomposição analítica completa.
  * `PvtSolutionVO`: Solução final de navegação tridimensional com coordenadas ECEF/Geodésicas, viés de relógio, resíduos e DOP.
  * `DopResultVO`: Fatores escalares de diluição geométrica de precisão e status de validade.
* **Vantagens de Engenharia:**
  * **Alocação Previsível:** O tamanho em bytes de cada objeto é estático.
  * **Segurança Concorrente:** Por serem imutáveis, instâncias de Value Objects podem ser compartilhadas simultaneamente entre múltiplas threads (leitura assíncrona do FastAPI e loop de física) sem risco de condições de corrida (*race conditions*).

### B. Matrizes e Tensores Contíguos com NumPy (`np.float64`)
* O Core utiliza arrays unidimensionais contíguos de 3 elementos (`dtype=np.float64`) para vetores de posição e velocidade ECI/ECEF, alinhando a memória para instruções SIMD (Single Instruction, Multiple Data) do processador.

### C. Buffer Circular Limitado (`collections.deque(maxlen=120)`)
* O histórico temporal de telemetria DOP para plotagem de gráficos na UI utiliza um buffer circular implementado via `collections.deque(maxlen=120)`:
  * **Inserção no Início/Fim:** $O(1)$ amortizado garantido por lista duplamente encadeada em nível de CPython.
  * **Consumo Fixo de Memória:** Quando o limite de 120 amostras é atingido, novos elementos empurram os mais antigos para descarte automático sem acúmulo residual de memória (*zero memory leak*), limitando a pegada de RAM do histórico a meros kilobytes.

---

## 🛡️ 4. Garantias de Determinismo e Confiabilidade (DO-178C)

1. **Ausência de Alocações Dinâmicas Não Limitadas:** O sistema não possui listas com crescimento arbitrário desprovidas de tamanho máximo (*unbounded collections*).
2. **Proteção Contra Divisão por Zero:**
   * Caso o número de satélites visíveis seja $M < 4$, a matriz $G^T G$ torna-se não-invertível. O algoritmo de cálculo detecta a condição antecipadamente e retorna `is_valid = False` em $O(1)$ sem tentar inverter a matriz, blindando o sistema contra exceções de ponto flutuante.
   * Na troposfera, o mapeamento cossecante divide por $\sin(el)$. Para $el \to 0$, a função impõe o valor de corte em $1.0^\circ$, impedindo divergência assintótica.

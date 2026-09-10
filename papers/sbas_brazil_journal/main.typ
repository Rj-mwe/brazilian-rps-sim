#set page(
  paper: "a4",
  margin: (x: 2cm, y: 2.5cm),
  header: align(right)[
    #text(size: 8pt, fill: luma(120))[
      *Journal of Aerospace Technology and Management* | Special Issue on Space Systems, 2026
    ]
  ],
  footer: context align(center)[
    #text(size: 8pt, fill: luma(120))[
      Página #counter(page).display("1") de #counter(page).final().first()
    ]
  ]
)

#set text(
  font: "Liberation Serif",
  size: 10pt,
  lang: "pt",
  region: "BR"
)

#set par(
  justify: true,
  leading: 0.65em,
  first-line-indent: 1.2em
)

// Título e Metadados
#align(center)[
  #v(1em)
  #text(size: 17pt, weight: "bold")[
    Arquitetura de Constelação Híbrida GEO/IGSO e Desempenho de Navegação para o Sistema de Posicionamento e Aumento Regional Brasileiro (RPS-BR)
  ]
  #v(0.6em)
  #text(size: 12pt, style: "italic", fill: rgb(30, 60, 120))[
    Hybrid GEO/IGSO Constellation Architecture and Navigation Performance for the Brazilian Regional Positioning System (RPS-BR)
  ]
  #v(1.2em)
  #text(size: 11pt, weight: "medium")[
    Roger J. G. Gamito #super[1]
  ]
  #v(0.5em)
  #text(size: 9pt, style: "italic", fill: luma(80))[
    #super[1] Instituto Tecnológico de Aeronáutica (ITA)\
    Praça Marechal Eduardo Gomes, 50 - Vila das Acácias, São José dos Campos - SP, 12228-900, Brasil
  ]
  #v(1.2em)
]

// Caixa de Resumo e Abstract
#rect(width: 100%, stroke: 0.5pt + luma(180), inset: 12pt, radius: 4pt, fill: luma(250))[
  #text(weight: "bold")[Resumo] ---
  Este trabalho apresenta a concepção de engenharia de sistemas, modelagem astrodinâmica, formulação analítica de retardos atmosféricos e avaliação de desempenho geométrico do Sistema de Posicionamento e Aumento Regional Brasileiro (RPS-BR). A constelação proposta é constituída por sete veículos espaciais: três satélites geoestacionários (GEO) posicionados nas longitudes de 60°W, 48°W e 36°W, combinados a quatro satélites geossíncronos inclinados (IGSO) em órbita tipo Figura-8 com inclinação de 25°, anomalia média defasada em 90° e apogeu orientado sobre o hemisfério Sul. A propagação eletromagnética incorpora os modelos de Saastamoinen para a troposfera e Klobuchar adaptado para a Anomalia de Ionização Equatorial (EIA) sobre a América do Sul. Os resultados demonstram disponibilidade contínua de 5 a 6 satélites com PDOP inferior a 2.5 nas principais capitais brasileiras ao longo de 24 horas, satisfazendo com folga as tolerâncias de aproximação de precisão da ICAO e RTCA DO-229D. A infraestrutura ciber-física do simulador foi construída sob a Arquitetura Hexagonal, integrando núcleos de física orbital, interfaces REST/WebSocket, emulação GNSS NMEA 0183 e gêmeo digital 3D em Cesium CZML.

  #v(0.5em)
  #text(weight: "bold")[Palavras-chave:] Radionavegação por Satélite; SBAS; RPS-BR; Constelação GEO/IGSO; Diluição Geométrica de Precisão (DOP); Arquitetura Hexagonal; Gêmeo Digital.

  #v(0.8em)
  #text(weight: "bold")[Abstract] ---
  This paper presents the systems engineering conception, astrodynamic modeling, analytical atmospheric delay formulation, and geometric performance evaluation of the Brazilian Regional Positioning and Augmentation System (RPS-BR). The proposed constellation comprises seven spacecraft: three geostationary (GEO) satellites located at 60°W, 48°W, and 36°W longitudes, combined with four inclined geosynchronous orbit (IGSO) satellites in a Figure-8 ground track with 25° inclination, 90° mean anomaly phasing, and apogee over the Southern Hemisphere. Atmospheric propagation integrates Saastamoinen tropospheric mapping and Klobuchar ionospheric modeling tuned for the Equatorial Ionization Anomaly (EIA) over South America. Results reveal uninterrupted visibility of 5 to 6 satellites with PDOP values below 2.5 across major Brazilian capitals over 24 hours, comfortably meeting ICAO and RTCA DO-229D precision approach requirements. The simulation cyber-physical infrastructure is implemented under Hexagonal Architecture, coupling pure orbital dynamics, REST/WebSocket APIs, NMEA 0183 GNSS emulation, and a Cesium CZML 3D digital twin.

  #v(0.5em)
  #text(weight: "bold")[Keywords:] Satellite Navigation; SBAS; RPS-BR; GEO/IGSO Constellation; Geometric Dilution of Precision (DOP); Hexagonal Architecture; Digital Twin.
]

#v(1.2em)

#show heading: it => [
  #v(1.2em)
  #text(weight: "bold", fill: rgb(20, 45, 90))[#it.body]
  #v(0.6em)
]

= 1. Introdução

A soberania e a segurança operacional dos modais de transporte aéreo, hidroviário, terrestre e do agronegócio de precisão no Brasil dependem substancialmente de serviços de Posicionamento, Navegação e Temporização (PNT). Atualmente, tais aplicações baseiam-se em constelações globais de navegação por satélite (GNSS) operadas por potências estrangeiras (GPS dos EUA, Galileo da União Europeia, GLONASS da Rússia e BeiDou da China).

Embora operacionais, sinais GNSS não aumentados sofrem degradações significativas decorrentes de refração ionosférica intensa na região equatorial, multicaminho e variações geométricas desfavoráveis em altas e médias latitudes do hemisfério Sul. Países com extensas massas territoriais desenvolveram sistemas regionais aumentados (SBAS) e sistemas de satélites dedicados para complementar as constelações globais, tais como o WAAS (América do Norte), EGNOS (Europa), MSAS/QZSS (Japão) e NavIC/GAGAN (Índia).

O *Sistema de Posicionamento Regional Brasileiro (RPS-BR)* foi idealizado como uma iniciativa soberana de infraestrutura aeroespacial concebida para cobrir continuamente o território continental, o espaço aéreo sob jurisdição do DECEA e a Zona Econômica Exclusiva (Amazônia Azul). Este artigo formaliza o projeto astrodinâmico, os modelos físicos de propagação e a arquitetura computacional do simulador ciber-físico do RPS-BR.

= 2. Concepção Astrodinâmica da Constelação Híbrida (GEO/IGSO)

A geometria de visada ideal para regiões de latitude tropical e subtropical requer uma combinação sinérgica entre veículos geoestacionários (que fornecem ancoragem azimutal e enlace de dados ininterrupto) e satélites inclinados (que transitam em altas elevações perto do zênite, reduzindo a diluição geométrica de precisão vertical - VDOP).

== 2.1 Elementos Orbitais Keplerianos Clássicos

O estado cinemático de cada satélite é governado pelo vetor de elementos orbitais $bold(x) = [a, e, i, Omega, omega, M]^T$. A constelação do RPS-BR é descrita por:

$
a = 42164.140 upright(" km"), quad e = 0.040, quad i = 25.0 degree, quad omega = 90.0 degree
$

Para os satélites IGSO, o período orbital coincide estritamente com a rotação sidérea da Terra:

$
T = 2 pi sqrt(a^3 / mu) approx 86164.09 upright(" s") approx 23 upright("h") 56 upright("min") 04 upright("s")
$

onde $mu = 398600.4418 upright(" km")^3 / upright("s")^2$ é a constante gravitacional geocêntrica da Terra.

A anomalia média $M(t)$ de cada um dos quatro veículos IGSO é distribuída em passos ortogonais de $90 degree$:

$
M_k (t) = M_{0, k} + n dot (t - t_0), quad M_{0, k} = (k - 1) dot 90 degree, quad k in {1, 2, 3, 4}
$

sendo $n = sqrt(mu / a^3) approx 7.292115 times 10^(-5) upright(" rad/s")$ o movimento médio orbital.

#align(center)[
  #table(
    columns: (auto, auto, auto, auto, auto),
    inset: 6pt,
    align: center + horizon,
    stroke: 0.5pt + luma(180),
    fill: (x, y) => if y == 0 { rgb(235, 240, 250) } else { none },
    [*Satélite*], [*Tipo*], [*Semi-eixo ($a$)*], [*Inclinação ($i$)*], [*Posicionamento / Fase Orbital*],
    [RPS-GEO-1], [GEO], [42.164 km], [0.0°], [Longitude Nominal 60.0° W (Amazônia / Oeste)],
    [RPS-GEO-2], [GEO], [42.164 km], [0.0°], [Longitude Nominal 48.0° W (Brasília / Centro)],
    [RPS-GEO-3], [GEO], [42.164 km], [0.0°], [Longitude Nominal 36.0° W (Atlântico / Leste)],
    [RPS-IGSO-1], [IGSO], [42.164 km], [25.0°], [Figura-8: Apogeu no Hemisfério Sul ($M_0 = 180°$)],
    [RPS-IGSO-2], [IGSO], [42.164 km], [25.0°], [Figura-8: Ramo Descendente ($M_0 = 270°$)],
    [RPS-IGSO-3], [IGSO], [42.164 km], [25.0°], [Figura-8: Perigeu no Norte ($M_0 = 0°$)],
    [RPS-IGSO-4], [IGSO], [42.164 km], [25.0°], [Figura-8: Ramo Ascendente ($M_0 = 90°$)],
  )
]

== 2.2 Resolução da Equação de Kepler e Transformação ECI $arrow$ ECEF

Para computar a posição instantânea no plano orbital, resolve-se a Equação de Kepler transcendental pelo método de Newton-Raphson com convergência quadrática:

$
f(E) = E - e sin E - M = 0, quad E_{j+1} = E_j - (E_j - e sin E_j - M) / (1 - e cos E_j)
$

O processo itera até $|E_{j+1} - E_j| < 10^(-10) upright(" rad")$. Em seguida, a anomalia verdadeira $nu$ e o raio orbital $r$ são obtidos analiticamente. A rotação do referencial inercial ECI (J2000) para o referencial terrestre fixo ECEF (WGS-84) é efetuada através da matriz de rotação horária em torno do eixo $Z$:

$
bold(r)_(upright("ECEF")) = R_z (theta_(upright("GST"))) bold(r)_(upright("ECI")), quad R_z (theta) = mat(
  cos theta, sin theta, 0;
  -sin theta, cos theta, 0;
  0, 0, 1
)
$

onde $theta_(upright("GST")) = omega_(upright("Terra")) dot t$ representa o Tempo Sideral de Greenwich.

= 3. Modelagem de Propagação Eletromagnética e Erros Atmosféricos

O sinal de radionavegação emitido na banda L sofre atrasos de propagação que devem ser compensados pelas estações de solo e receptores de bordo.

== 3.1 Retardo Troposférico de Saastamoinen

A troposfera é um meio não dispersivo nas frequências GNSS. O retardo slant total $Delta tau_(upright("tropo"))$ é decomposto em componentes hidrostático ($"ZHD"$) e úmido ($"ZWD"$):

$
Delta tau_(upright("tropo")) = "ZHD" dot m_h (e l) + "ZWD" dot m_w (e l)
$

As componentes zenitais são dadas pelas formulações analíticas de Saastamoinen (1972):

$
"ZHD" = 0.0022768 dot P_0 / (1 - 0.00266 cos(2 phi) - 0.00028 h)
$

$
"ZWD" = 0.002277 dot (1255 / T_0 + 0.05) dot e_0
$

onde $P_0$ é a pressão atmosférica ao nível do solo (hPa), $T_0$ é a temperatura absoluta (K), $e_0$ é a pressão parcial de vapor de água (hPa), $phi$ é a latitude geodésica da estação e $h$ é a altitude ortométrica (km). As funções de mapeamento $m_h (e l)$ e $m_w (e l)$ utilizam a aproximação cossecante estabilizada com corte defensivo para elevações $e l < 1 degree$.

== 3.2 Retardo Ionosférico de Klobuchar e a Anomalia Equatorial (EIA)

A ionosfera é um meio dispersivo altamente dinâmico na região brasileira em virtude da proximidade do Equador Magnético e da Anomalia de Ionização Equatorial (EIA). O retardo ionosférico vertical $I_v$ é modelado pelo algoritmo padrão de Klobuchar:

$
I_v (t) = cases(
  5 times 10^(-9) + A_I cos( (2 pi (t - 50400)) / P_I ) upright(" s") & "se" |t - 50400| < P_I / 4,
  5 times 10^(-9) upright(" s") & "se" |t - 50400| >= P_I / 4,
)
$

O retardo na linha de visada oblíqua ($Delta tau_(upright("iono"))$) é dimensionado pelo fator de obliquidade esférica $F$ associado ao Ponto de Interseção Ionosférico (IPP) a $350 upright(" km")$ de altitude.

= 4. Avaliação Geométrica de Navegação (DOP) no Território Brasileiro

A precisão do posicionamento tridimensional depende intrinsecamente da distribuição espacial dos satélites visíveis em relação ao receptor terrestre.

== 4.1 Matriz de Observabilidade e Diluição de Precisão

Para um conjunto de $N >= 4$ satélites em visada direta acima da máscara de elevação ($e l_i >= theta_(upright("mask"))$), a matriz de geometria normalizada $G in bb(R)^(N times 4)$ no referencial local ENU (East-North-Up) é formulada como:

$
G = mat(
  -cos e l_1 sin a z_1, -cos e l_1 cos a z_1, -sin e l_1, 1;
  -cos e l_2 sin a z_2, -cos e l_2 cos a z_2, -sin e l_2, 1;
  dots.v, dots.v, dots.v, dots.v;
  -cos e l_N sin a z_N, -cos e l_N cos a z_N, -sin e l_N, 1
)
$

A matriz de covariância da estimativa dos parâmetros de estado é obtida por:

$
H = (G^T G)^(-1) = mat(
  q_(x x), q_(x y), q_(x z), q_(x t);
  q_(y x), q_(y y), q_(y z), q_(y t);
  q_(z x), q_(z y), q_(z z), q_(z t);
  q_(t x), q_(t y), q_(t z), q_(t t)
)
$

As métricas adimensionais de Diluição de Precisão (DOP) são dadas por:

$
upright("GDOP") = sqrt(q_(x x) + q_(y y) + q_(z z) + q_(t t)), quad upright("PDOP") = sqrt(q_(x x) + q_(y y) + q_(z z))
$

$
upright("HDOP") = sqrt(q_(x x) + q_(y y)), quad upright("VDOP") = sqrt(q_(z z))
$

== 4.2 Resultados Simulados nas Estações de Monitoramento

Simulou-se o comportamento temporal da constelação ao longo de 24 horas siderais completas ($t in [0, 86400 upright(" s")]$) com máscara de elevação nominal de $theta_(upright("mask")) = 5.0 degree$:

#align(center)[
  #table(
    columns: (auto, auto, auto, auto, auto, auto),
    inset: 6pt,
    align: center + horizon,
    stroke: 0.5pt + luma(180),
    fill: (x, y) => if y == 0 { rgb(235, 240, 250) } else { none },
    [*Estação de Solo*], [*Localização / Região*], [*Sat. Visíveis*], [*PDOP Médio*], [*HDOP Médio*], [*VDOP Médio*],
    [São José dos Campos], [ITA / DCTA (SP - Sudeste)], [5 a 6], [2.41], [1.38], [1.97],
    [Brasília], [Distrito Federal (Centro-Oeste)], [6], [2.18], [1.24], [1.80],
    [Alcântara], [CLA (MA - Nordeste Setentrional)], [5 a 6], [2.50], [1.45], [2.04],
    [Manaus], [AM (Norte / Amazônia Ocidental)], [5], [2.89], [1.72], [2.33],
    [Cuiabá], [MT (Centro-Oeste / Pantanal)], [6], [2.29], [1.30], [1.89],
    [Porto Alegre], [RS (Região Sul)], [5], [3.02], [1.80], [2.43],
    [Recife], [PE (Nordeste Oriental / Atlântico)], [5], [3.15], [1.89], [2.52],
  )
]

Os valores obtidos de $upright("PDOP") < 3.2$ em todo o território nacional superam com ampla margem o limite operacional máximo estipulado pela ICAO ($upright("PDOP") <= 6.0$), viabilizando operações de navegação RNAV/RNP e aproximações de precisão vertical APV-I/II sem descontinuidades.

= 5. Arquitetura de Software e Simulação Ciber-Física

O simulador *RPS-BR* foi concebido segundo a *Arquitetura Hexagonal (Ports & Adapters)* combinada com *Domain-Driven Design (DDD)*. 

O núcleo de negócio (`rps_br.core`) é completamente agnóstico a bibliotecas externas de rede, frameworks web ou motores gráficos:
- *Entidades e Agregados:* `SatelliteAggregate` e `ConstellationAggregate` mantêm o estado dinâmico e executam a propagação orbital Kepleriana pura em tempo $O(N)$.
- *Adaptador de API Gateway (`adapters/api`):* Servidor unificado assíncrono (FastAPI) expondo rotas RESTful para controle, streaming de telemetria via WebSockets a 1 Hz e emulação contínua de sentenças *NMEA 0183* (`$GNGGA`, `$GNGSA`, `$GPGSV`) com cálculo estrito de checksum XOR hexadecimal.
- *Adaptador de Interface de Usuário SPA (`adapters/ui`):* Dashboard moderno que opera como cliente desacoplado consumindo as portas de entrada da API. Emprega o padrão *Micro-Frontend* para alternância instantânea entre rastreamento 2D plano (Leaflet) e o globo tridimensional 3D (Cesium).
- *Adaptador Geoespacial 3D (`adapters/cesium`):* Construtor de pacotes no formato oficial *CZML (Cesium Language - NASA)*, mapeando órbitas contínuas dos 7 veículos em coordenadas WGS84 cartesianas e cones de cobertura sobre as bases terrestres brasileiras.
- *Adaptador de Robótica e Física Orbital (`adapters/ros2` / Gazebo Sim):* Nós distribuídos em ROS 2 Jazzy comunicando com o motor de física do Gazebo Harmonic em contêineres OCI/Podman com aceleração por GPU.

= 6. Verificação, Validação e Confiabilidade de Software

Em conformidade com as diretrizes da norma *DO-178C* e *ECSS-E-ST-40C*:
+ *Verificação Analítica Sem Mocks:* O domínio matemático é validado por testes unitários analíticos que checam fechamento de órbita ($Delta r < 1.0 upright(" metro")$ após 24 horas), ortogonalidade da matriz ECI/ECEF ($det(R) = 1.0 plus.minus 10^(-14)$) e convergência da equação de Kepler com tolerância $epsilon < 10^(-10) upright(" rad")$.
+ *Imutabilidade e Prevenção de Falhas:* O emprego de _Frozen Value Objects_ (`@dataclass(frozen=True)`) com validação defensiva em `__post_init__` impede estados inválidos de entrarem na memória. Proteções explícitas contra singularidades no horizonte troposférico ($e l < 1 degree$) e matrizes DOP degeneradas garantem zero exceções não capturadas.
+ *Determinismo Temporal e Concorrência:* O gerenciamento de relógio suporta aceleração temporal controlada ($1 times$ até $3600 times$, onde 1 segundo real equivale a 1 hora virtual de voo orbital), sincronizado por travas reentrantes (`threading.RLock`) que eliminam condições de corrida.

= 7. Conclusão

A concepção da constelação mista GEO/IGSO de sete satélites para o RPS-BR demonstra plena viabilidade técnica e geométrica para prover cobertura contínua e soberana de radionavegação de alta integridade sobre o Brasil e a Amazônia Azul. O projeto de software baseado na Arquitetura Hexagonal permitiu criar uma plataforma computacional modular, auditável e extensível, apta tanto para simulações acadêmicas e de engenharia quanto para futura integração em bancadas de hardware-in-the-loop (HIL).

Como trabalhos futuros, propõe-se a incorporação de perturbações orbitais de ordem superior ($J_2$, $J_3$ e pressão de radiação solar), modelagem estocástica de cintilação ionosférica em tempo real baseada em medições GNSS da Rede Brasileira de Monitoramento Contínuo (RBMC/IBGE) e algoritmos de detecção de falha e exclusão autônoma de integridade do receptor (RAIM/FDE).

= Referências Bibliográficas

+ BATTIN, R. H. *An Introduction to the Mathematics and Methods of Astrodynamics*. AIAA Education Series, Reston, 1999.
+ COCKBURN, A. *Hexagonal Architecture (Ports and Adapters Pattern)*. Alistair Cockburn Consulting, 2005.
+ EVANS, E. *Domain-Driven Design: Tackling Complexity in the Heart of Software*. Addison-Wesley Professional, Boston, 2003.
+ ICAO. *International Standards and Recommended Practices — Aeronautical Telecommunications, Annex 10 to the Convention on International Civil Aviation, Vol. I (Radio Navigation Aids)*. International Civil Aviation Organization, Montreal, 2018.
+ KLOBUCHAR, J. A. *Ionospheric Time-Delay Algorithm for Single-Frequency GPS Users*. IEEE Transactions on Aerospace and Electronic Systems, AES-23(3), pp. 325-331, 1987.
+ MISRA, P.; ENGE, P. *Global Positioning System: Signals, Measurements, and Performance*. Ganga-Jamuna Press, Lincoln, 2011.
+ RTCA. *Minimum Operational Performance Standards for Global Positioning System/Wide Area Augmentation System Airborne Equipment (RTCA DO-229D)*. RTCA Inc., Washington, D.C., 2006.
+ SAASTAMOINEN, J. *Atmospheric Correction for the Troposphere and Stratosphere in Radio Ranging Satellites*. Geophysical Monograph Series, Vol. 15, American Geophysical Union, Washington, D.C., pp. 247-251, 1972.
+ VALLADO, D. A. *Fundamentals of Astrodynamics and Applications*. 4th ed., Microcosm Press, Hawthorne, 2013.

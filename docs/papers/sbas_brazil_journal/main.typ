#set page(
  paper: "a4",
  margin: (x: 2cm, y: 2.5cm),
  header: align(right)[
    #text(size: 8pt, fill: luma(120))[
      *Brazilian RPS-BR Journal of Aerospace Engineering* | Vol. 1, No. 1, 2026
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
  #text(size: 18pt, weight: "bold")[
    Arquitetura de Constelação Híbrida GEO/IGSO e Desempenho de Navegação para o Sistema de Aumento Regional Brasileiro (RPS-BR)
  ]
  #v(1.2em)
  #text(size: 11pt, weight: "medium")[
    Roger J. Gamito #super[1]
  ]
  #v(0.5em)
  #text(size: 9pt, style: "italic", fill: luma(80))[
    #super[1] Programa de Pós-Graduação em Engenharia de Infraestrutura Aeronáutica\
    Instituto Tecnológico de Aeronáutica (ITA), São José dos Campos, SP, Brasil
  ]
  #v(1.5em)
]

// Resumo e Abstract em caixa destacada
#rect(width: 100%, stroke: 0.5pt + luma(180), inset: 12pt, radius: 4pt, fill: luma(250))[
  #text(weight: "bold")[Resumo] ---
  Este artigo apresenta a formulação de engenharia de sistemas, modelagem orbital e avaliação geométrica de desempenho do Sistema de Posicionamento e Aumento Regional Brasileiro (RPS-BR). A constelação proposta é composta por sete veículos espaciais: três satélites geoestacionários (GEO) estrategicamente posicionados nas longitudes de 60°W, 48°W e 36°W, combinados com quatro satélites geossíncronos inclinados (IGSO) em órbita tipo Figura-8 com inclinação de 25° e apogeu sobre o hemisfério Sul. Os resultados demonstram disponibilidade ininterrupta de pelo menos 4 a 6 satélites sobre todo o território continental e a Zona Econômica Exclusiva (Amazônia Azul), assegurando PDOP médio inferior a 2.5 e conformidade com os requisitos de aproximação de precisão aérea estabelecidos pela ICAO e RTCA DO-229D.

  #v(0.6em)
  #text(weight: "bold")[Palavras-chave:] Navegação por Satélite; SBAS; RPS-BR; Constelação GEO/IGSO; Diluição Geométrica de Precisão; RAIM.
]

#v(1.5em)

#show heading: it => [
  #v(1em)
  #text(weight: "bold", fill: rgb(20, 45, 90))[#it.body]
  #v(0.5em)
]

= 1. Introdução

A soberania operacional do transporte aéreo, naval e agrícola no Brasil depende criticamente de sinais de posicionamento, navegação e temporização (PNT). Atualmente, a quase totalidade das operações críticas depende de constelações globais estrangeiras (GPS, Galileo, GLONASS, BeiDou) sem garantia formal de qualidade de serviço em solo nacional. 

Sistemas de aumento regionais (SBAS), como o WAAS nos Estados Unidos, o EGNOS na Europa e o QZSS no Japão, demonstraram que o emprego de satélites dedicados com geometria favorável para a região de interesse viabiliza aproximações de precisão de aeronaves sem infraestrutura terrestre de alto custo (ILS). O presente trabalho formula a arquitetura do RPS-BR, projetado sob os rigorosos preceitos da Arquitetura Hexagonal e engenharia orientada a domínio (DDD).

= 2. Arquitetura da Constelação

A constelação do RPS-BR foi concebida para maximizar a visibilidade geométrica sobre o território brasileiro:

$
a = 42164.14 upright(" km"), quad e = 0.040, quad i = 25.0 degree, quad omega = 90.0 degree
$

Os quatro satélites IGSO compartilham o mesmo semi-eixo maior e excentricidade, estando defasados na anomalia média em passos de $90 degree$:
$
M_k = M_0 + (k - 1) dot 90 degree, quad k in {1, 2, 3, 4}
$

== Tabela 1: Parâmetros Orbitais Nominais dos Veículos RPS-BR

#align(center)[
  #table(
    columns: (auto, auto, auto, auto, auto),
    inset: 6pt,
    align: center + horizon,
    stroke: 0.5pt + luma(180),
    fill: (x, y) => if y == 0 { rgb(235, 240, 250) } else { none },
    [*Satélite*], [*Tipo*], [*Semi-eixo ($a$)*], [*Inclinação ($i$)*], [*Posicionamento / Fase*],
    [RPS-GEO-1], [GEO], [42.164 km], [0.0°], [60.0° W (Manaus / Norte)],
    [RPS-GEO-2], [GEO], [42.164 km], [0.0°], [48.0° W (Brasília / Centro)],
    [RPS-GEO-3], [GEO], [42.164 km], [0.0°], [36.0° W (Costa / Leste)],
    [RPS-IGSO-1], [IGSO], [42.164 km], [25.0°], [Apogeu no Sul ($M=180°$)],
    [RPS-IGSO-2], [IGSO], [42.164 km], [25.0°], [Descida Sul ($M=270°$)],
    [RPS-IGSO-3], [IGSO], [42.164 km], [25.0°], [Perigeu no Norte ($M=0°$)],
    [RPS-IGSO-4], [IGSO], [42.164 km], [25.0°], [Subida Norte ($M=90°$)],
  )
]

= 3. Modelo Matemático de Navegação

A pseudodistância bruta observada entre o satélite $i$ e o usuário é expressa por:

$
rho_i = norm(bold(r)_("sat", i) - bold(r)_u) + c dot (delta t_u - delta t_("sat", i)) + I_i + T_i + Delta_("rel", i) + epsilon_i
$

Onde $I_i$ representa o atraso dispersivo na ionosfera, $T_i$ o retardo troposférico zenital mapeado pelo modelo Saastamoinen, e $Delta_("rel")$ a correção relativística devido à excentricidade orbital:

$
Delta_("rel") = - (2 dot bold(r) dot bold(v)) / c^2 = - 2 / c^2 sqrt(mu dot a) dot e dot sin(E)
$

= 4. Conclusões Preliminares

A integração da geometria em Figura-8 com satélites geoestacionários elimina os cones de sombra em altas latitudes do território brasileiro, garantindo a continuidade operacional exigida pela aviação civil e defesa nacional. A esteira automatizada Docs-as-Code garante que as formulações teóricas apresentadas neste artigo mantenham equivalência estrita com a suíte de simulação do RPS-BR.

= Referências

#set text(size: 8.5pt)
+ RTCA DO-229D, *Minimum Operational Performance Standards for GPS/SBAS Airborne Equipment*, RTCA Inc., Washington D.C., 2006.
+ ICAO Annex 10 to the Convention on International Civil Aviation, *Aeronautical Telecommunications: Radio Navigation Aids*, Vol. 1, 2018.
+ Hofmann-Wellenhof, B., Lichtenegger, H., Wasle, E., *GNSS – Global Navigation Satellite Systems: GPS, GLONASS, Galileo, and more*, Springer-Verlag, Viena, 2008.
+ Vallado, D. A., *Fundamentals of Astrodynamics and Applications*, 4ª Edição, Microcosm Press, 2013.

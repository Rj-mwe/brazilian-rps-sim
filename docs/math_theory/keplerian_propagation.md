# 🪐 Astrodinâmica Kepleriana e Perturbação $J_2$

---

## 1. Equação Transcendental de Kepler
A posição orbital em um determinado instante $t$ é obtida a partir da Anomalia Média $M(t)$:
$$M(t) = M_0 + n \cdot (t - t_0)$$
onde $n = \sqrt{\frac{\mu}{a^3}}$ é o movimento médio.

A Anomalia Excêntrica $E$ é calculada iterativamente resolvendo a equação transcendental:
$$f(E) = E - e \sin(E) - M = 0$$

Utiliza-se o método de Newton-Raphson de segunda ordem com convergência quadrática:
$$E_{k+1} = E_k - \frac{E_k - e \sin(E_k) - M}{1 - e \cos(E_k)}$$
com critério de parada $|E_{k+1} - E_k| < 10^{-12}\text{ rad}$.

---

## 2. Perturbação Secular do Geopotencial ($J_2$)
Devido ao achatamento dos polos da Terra ($f \approx 1/298.257$), o campo gravitacional terrestre não é perfeitamente esférico. O harmônico zonal $J_2 = 1.08263 \times 10^{-3}$ induz efeitos seculares na linha dos nós e no argumento do perigeu:

1. **Regressão da Linha dos Nós ($\dot{\Omega}$)**:
   $$\dot{\Omega} = -\frac{3}{2} J_2 \left(\frac{R_\oplus}{p}\right)^2 n \cos(i)$$
   Para os IGSOs ($i = 25^\circ, a = 42.164\text{ km}$), $\dot{\Omega} \approx -0.013^\circ/\text{dia}$.

2. **Avanço da Linha dos Ápsides ($\dot{\omega}$)**:
   $$\dot{\omega} = \frac{3}{4} J_2 \left(\frac{R_\oplus}{p}\right)^2 n (5 \cos^2(i) - 1)$$
   Para a inclinação crítica $i = 63.435^\circ$, $\dot{\omega} = 0$. No caso dos satélites IGSO do RPS-BR com $i = 25^\circ$, a taxa é compensada por manobras periódicas de manutenção de estação (Station Keeping).

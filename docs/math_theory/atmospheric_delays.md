# 🌤️ Modelagem de Retardos Atmosféricos (Ionosfera e Troposfera)

---

## 1. Retardo Ionosférico (Modelo de Klobuchar)
A ionosfera é um meio dispersivo onde o atraso de grupo da fase portadora é proporcional ao Conteúdo Total de Elétrons ($\text{TEC}$):
$$I = \frac{40.3 \cdot \text{TEC}}{f^2}$$

Para receptores de frequência única (L1), o atraso zenital é modelado como uma função semi-cossenoidal diurna com base de 5 ns (noturna) e amplitude pico variável:
$$I_z(t) = 5 \times 10^{-9} + \sum_{n=0}^3 \alpha_n \phi_m^n \cdot \cos\left( \frac{2\pi (t - 50400)}{\sum_{n=0}^3 \beta_n \phi_m^n} \right)$$
O retardo na linha de visada oblíqua é obtido pela função de mapeamento (Obliquity Factor $F$):
$$I(\text{el}) = F(\text{el}) \cdot I_z$$
$$F(\text{el}) = 1.0 + 16.0 \cdot (0.53 - \text{el})^3$$

---

## 2. Retardo Troposférico (Modelo de Saastamoinen)
A troposfera é um meio não dispersivo até 15 GHz. O retardo total é a soma da parcela hidrostática (ar seco) e úmida (vapor d'água):
$$\Delta_{\text{tropo}} = \frac{0.002277}{\cos(\theta_z)} \left[ P_0 + \left(\frac{1255}{T_0} + 0.05\right) e_0 - B \tan^2(\theta_z) \right] + \delta_R$$
onde:
* $\theta_z = 90^\circ - \text{el}$: ângulo zenital.
* $P_0$: pressão atmosférica na antena (hPa).
* $T_0$: temperatura absoluta (K).
* $e_0$: pressão parcial de vapor d'água (hPa).
* $B, \delta_R$: correções de altura e curvatura terrestre.

# 📜 Conformidade com Normas Internacionais (ICAO & RTCA)

O projeto RPS-BR adota como referência primária as normas internacionais para aviação civil e navegação por satélite:

---

## 1. RTCA DO-229D / DO-229E
* **Título**: *Minimum Operational Performance Standards for Global Positioning System/Wide Area Augmentation System Airborne Equipment*.
* **Seções Mapeadas**:
  * **Seção 2.1.4**: Algoritmo de Mapeamento Troposférico e retardo de Saastamoinen.
  * **Apêndice A**: Estrutura das mensagens de broadcast SBAS (Correções rápidas, correções de longo prazo e mapa de atraso ionosférico em grade - GDM).
  * **Apêndice J**: Dedução analítica das equações de Níveis de Proteção ($\text{HPL}$ e $\text{VPL}$).

---

## 2. ICAO Annex 10 (Volume I - Radio Navigation Aids)
* **Capítulo 3**: Especificações técnicas para sistemas globais de navegação por satélite com aumento regional (SBAS).
* **Tabela 3.7.2.4-1**: Requisitos de nível de serviço para aproximação com orientação vertical (APV-I e APV-II):
  * Probabilidade de perda de integridade: $1 \times 10^{-7}$ por aproximação.
  * Disponibilidade de serviço: $0.99$ a $0.99999$.

---

## 3. IS-GPS-200M (Interface Specification)
* **Seção 20.3.3.5.2**: Modelo Ionosférico de Klobuchar (8 coeficientes $\alpha_n, \beta_n$).
* **Seção 20.3.3.3.3.1**: Termo relativístico orbital $\Delta t_{\text{rel}} = F \cdot e \cdot \sqrt{a} \cdot \sin(E)$.

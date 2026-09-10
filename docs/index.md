# 🛰️ Brazilian RPS Sim — Documentação da Missão

Bem-vindo ao portal de engenharia e documentação científica do **Brazilian Regional Positioning & Augmentation System Simulator (RPS-BR)**.

Este projeto modela, propaga e avalia um sistema de posicionamento e aumento regional soberano para o território brasileiro, sua Zona Econômica Exclusiva (Amazônia Azul) e espaço aéreo adjacente.

---

## 🏛️ Filosofia *Docs-as-Code* & Padrões Aeroespaciais

A documentação deste repositório é tratada com o mesmo rigor, versionamento e automação do código-fonte:
* **Arquitetura Hexagonal (Ports & Adapters)**: Desacoplamento absoluto entre formulações matemáticas de domínio puro e frameworks externos (ROS 2 / Gazebo Sim).
* **Rastreabilidade Bidirecional**: Cada modelo implementado responde a uma especificação teórica formal e a um requisito operacional rastreável no [GitHub Projects](https://github.com/users/Rj-mwe/projects/2).
* **Test-Driven Development (TDD)**: Toda equação é validada por casos de teste com tolerâncias analíticas estritas antes da integração.
* **Artigos em Typst**: Produção científica rápida, reprodutível e versionável em código-fonte puro na pasta de topo [`papers/`](../papers/).

---

## 🗺️ Mapa de Navegação da Documentação

```mermaid
graph TD
    A["Documentação da Missão"] --> B["🏛️ Decisões de Arquitetura (ADRs)"]
    A --> C["📋 Especificações & Normas"]
    A --> D["📐 Formulações Teóricas & Físicas"]
    A --> G["🔌 Interfaces & Adaptadores"]
    A --> H["🧪 Engenharia de Qualidade & Testes"]
    A --> E["📄 Artigo Científico (Typst)"]
    A --> F["📓 Folhas de Cálculo (Notebooks)"]

    B --> B1["0001: Arquitetura Hexagonal"]
    B --> B2["0002: Builder glTF 2.0"]
    B --> B3["0003: DOP Strategy & Observer"]
    B --> B4["0004: Docs-as-Code & Typst"]

    C --> C1["Requisitos de Missão"]
    C --> C2["Conformidade RTCA DO-229D / ICAO"]

    D --> D1["Astrodinâmica & Perturbação J2"]
    D --> D2["Retardos Atmosféricos (Iono/Tropo)"]
    D --> D3["Solucionador PVT de Mínimos Quadrados"]

    G --> G1["[API Gateway (REST / WS / NMEA / Cesium)](api.md)"]
    G --> G2["[Interface CLI (rps-sim)](cli.md)"]

    H --> H1["[Estratégia & Pirâmide de Testes](testing.md)"]
    H --> H2["[Qualidade, Confiabilidade & Segurança (DO-178C)](quality_safety.md)"]

    E --> E1["[Manuscrito Typst (papers/)](../papers/sbas_brazil_journal/main.typ)"]
```

---

## 📚 Guias Técnicos Rápidos

* 🌐 **[Documentação da Interface API (REST, WebSocket, NMEA 0183, Cesium 3D)](api.md)**
* 💻 **[Documentação da Interface de Linha de Comando (CLI `rps-sim`)](cli.md)**
* 🧪 **[Engenharia e Estratégia de Testes de Software](testing.md)**
* 🛡️ **[Qualidade, Confiabilidade e Segurança de Software (DO-178C, ECSS, ISO/IEC 25010)](quality_safety.md)**
* 📄 **[Artigo Científico em Typst (`papers/sbas_brazil_journal/`)](../papers/sbas_brazil_journal/)**

---

## 🚀 Constelação de Referência (7 Satélites)

| Satélite | Tipo | Órbita / Parâmetros | Função Operacional |
| :--- | :---: | :--- | :--- |
| **RPS-GEO-1** | GEO | $a = 42.164\text{ km}, i = 0^\circ, \lambda = 60^\circ\text{W}$ | Cobertura Amazônia Central e Norte |
| **RPS-GEO-2** | GEO | $a = 42.164\text{ km}, i = 0^\circ, \lambda = 48^\circ\text{W}$ | Cobertura Centro-Oeste / Brasília |
| **RPS-GEO-3** | GEO | $a = 42.164\text{ km}, i = 0^\circ, \lambda = 36^\circ\text{W}$ | Cobertura Costa Leste e Nordeste |
| **RPS-IGSO-1** | IGSO | $a = 42.164\text{ km}, e = 0.040, i = 25^\circ, \omega = 90^\circ$ | Figura-8 sobre o Brasil (Apogeu no Sul) |
| **RPS-IGSO-2** | IGSO | $a = 42.164\text{ km}, e = 0.040, i = 25^\circ, \omega = 90^\circ$ | Figura-8 sobre o Brasil (Fase $90^\circ$) |
| **RPS-IGSO-3** | IGSO | $a = 42.164\text{ km}, e = 0.040, i = 25^\circ, \omega = 90^\circ$ | Figura-8 sobre o Brasil (Fase $180^\circ$) |
| **RPS-IGSO-4** | IGSO | $a = 42.164\text{ km}, e = 0.040, i = 25^\circ, \omega = 90^\circ$ | Figura-8 sobre o Brasil (Fase $270^\circ$) |

---

## 📜 Licenciamento Híbrido & Citação

* **Código-Fonte:** Licenciado sob a **Apache License 2.0**.
* **Documentação & Artigos:** Licenciados sob a **Creative Commons CC BY 4.0**.

Para citar este projeto em artigos acadêmicos, teses ou relatórios técnicos, utilize o padrão definido no arquivo [`CITATION.cff`](https://github.com/Rj-mwe/brazilian-rps-sim/blob/main/CITATION.cff) ou o botão **Cite this repository** no GitHub.


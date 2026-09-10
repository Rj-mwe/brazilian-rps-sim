# 📄 Artigo Científico do RPS-BR (Typst)

Este diretório contém o manuscrito científico oficial do projeto **RPS-BR**, formatado em [Typst](https://typst.app/) e preparado para submissão a periódicos aeroespaciais e de engenharia de software (como o *Journal of Aerospace Technology and Management - JATM*, *IEEE AESS*, *SBC* ou *AIAA*).

* **Título:** *Arquitetura de Constelação Híbrida GEO/IGSO e Desempenho de Navegação para o Sistema de Posicionamento e Aumento Regional Brasileiro (RPS-BR)*
* **Autor:** Roger J. G. Gamito (Instituto Tecnológico de Aeronáutica - ITA)
* **Arquivo Principal:** [`main.typ`](main.typ)

---

## 🛠️ Como Compilar Localmente

O compilador nativo do Typst gera o PDF em milissegundos:

```bash
# Compilar para PDF:
typst compile papers/sbas_brazil_journal/main.typ papers/sbas_brazil_journal/paper_rps_brazil.pdf

# Modo Watch (recompilação instantânea a cada salvamento do arquivo):
typst watch papers/sbas_brazil_journal/main.typ
```

---

## 🏛️ Por que `papers/` no Topo do Repositório?

Em consonância com as melhores práticas de pesquisa reproduzível (*Reproducible Research*) e grandes projetos abertos de engenharia aeroespacial:
1. **Separação de Preocupações:** `docs/` destina-se à documentação de software, APIs e arquitetura para desenvolvedores e operadores. `papers/` destina-se a artigos científicos formais voltados para revisão por pares e divulgação acadêmica.
2. **Isolamento de Toolchain:** O Typst compila diretamente para PDF sem depender de geradores de sites estáticos web (*MkDocs* / *Sphinx*).

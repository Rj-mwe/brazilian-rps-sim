# 📄 Artigo Científico: Arquitetura e Desempenho do RPS-BR

* **Título**: *Arquitetura de Constelação Híbrida GEO/IGSO e Desempenho de Navegação para o Sistema de Aumento Regional Brasileiro (RPS-BR)*
* **Autor**: Roger J. Gamito (Instituto Tecnológico de Aeronáutica - ITA)
* **Formato**: [Typst](https://typst.app/) (`main.typ`)

---

## 🚀 Por que Typst em vez de LaTeX?
1. **Velocidade de Compilação**: Compila em menos de 50 milissegundos (instantâneo).
2. **Sintaxe Limpa**: Sem macros verbosas de `\begin{...}` e `\end{...}`.
3. **Equações Elegantes**: Tipografia matemática idêntica ou superior ao TeX com sintaxe moderna.
4. **Docs-as-Code & CI/CD**: O arquivo `main.typ` vive no Git e é compilado automaticamente pelo GitHub Actions a cada push.

---

## 🛠️ Como Compilar Localmente:
```bash
# Compilar para PDF instantaneamente:
typst compile docs/papers/sbas_brazil_journal/main.typ docs/papers/sbas_brazil_journal/paper_sbas_brazil.pdf

# Modo "Watch" (recompila em tempo real a cada salvamento do arquivo):
typst watch docs/papers/sbas_brazil_journal/main.typ
```

---

## 📥 Código-Fonte e PDF Gerado:
* [Código-Fonte em Typst (`main.typ`)](main.typ)
* O arquivo PDF compilado é gerado como artefato nas esteiras de automação e nos Releases do repositório.

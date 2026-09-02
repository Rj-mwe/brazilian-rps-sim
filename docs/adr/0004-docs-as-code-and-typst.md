# ADR 0004: Filosofia Docs-as-Code e Adoção do Typst para Artigos e Relatórios

* **Status**: Aprovado e Implementado
* **Data**: 2026-09-02

---

## 1. Contexto & Problema
Documentações acadêmicas e de engenharia armazenadas fora do repositório (ex: Word, Google Drive ou PDFs esparsos) sofrem rápida obsolescência em relação ao código (*Document Drift*). O LaTeX tradicional, embora academicamente aceito, impõe dependências gigantescas (múltiplos gigabytes), compilação lenta e mensagens de erro arcanas que dificultam esteiras de CI/CD automatizadas.

---

## 2. Decisão
1. **Filosofia Docs-as-Code**: Toda a documentação de sistemas, requisitos e formulações matemáticas reside na pasta `docs/` sob controle de versão atômico junto ao código.
2. **Typst como Padrão para Publicações**: Adotar o **Typst** para todos os artigos científicos, relatórios técnicos e memorandos do projeto.
3. **Portal Web com MkDocs**: Compilar o portal interativo em Markdown com suporte a fórmulas matemáticas MathJax/KaTeX e diagramas Mermaid.
4. **CI/CD via GitHub Actions**: Compilação automática do portal web para o GitHub Pages e compilação do paper Typst gerando PDFs automáticos como release assets.

---

## 3. Consequências
* Compilação do paper em milissegundos com tipografia de padrão periódico internacional.
* Eliminação de deriva documental: código e artigo evoluem nos mesmos commits.

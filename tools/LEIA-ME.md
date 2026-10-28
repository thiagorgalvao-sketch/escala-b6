# Como atualizar o Escala B6

- `tools/app.html` é o código-fonte do app (fonte única).
- Depois de editar, gere as páginas:
  - `python3 tools/siteindex.py tools/app.html index.html` (visão da banda)
  - `python3 tools/adminindex.py tools/app.html admin/index.html` (administração com login)
- Faça commit e push para `main`; o GitHub Pages publica em ~1 minuto.
- Dados ficam no Supabase (projeto hofrthndlstofytlapzk); scripts SQL de referência estão fora do repositório.
- `.github/workflows/sync.yml` atualiza agendas e a cópia `pub.json` a cada 6 horas.

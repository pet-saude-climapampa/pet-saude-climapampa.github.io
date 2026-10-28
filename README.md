# Site ClimaPampa — PET-Saúde: Clima (Unipampa)

Site estático, gerado em Python e publicado no GitHub Pages.

## Onde editar

| O quê | Onde |
|---|---|
| Textos do projeto, eixos, GATs, equipe, plataformas | `data/site.yml` |
| Notícias | um arquivo `.md` por notícia em `noticias/` (veja o exemplo) |
| Galeria | fotos em `galeria/<id>/` + entrada em `data/galeria.yml` (o build reduz as fotos e cria miniaturas; requer `pip install pillow`) |
| Agenda (próximas atividades) | `data/agenda.yml` (copie um bloco e preencha; o cartaz vai em `static/img/agenda/`) |
| Aparência | `static/css/style.css` |
| Estrutura das páginas | `templates/` |
| Fotos da equipe e logos | `static/img/` |

### Nova atividade na agenda
Em `data/agenda.yml`, copie o bloco do exemplo, mude `id`, `titulo`, `data` (AAAA-MM-DD), horários, links e `cartaz`.
Depois do `git push`, ela aparece em **Agenda** e na página inicial. A atividade vai sozinha para "Realizadas" no dia seguinte
(o site é refeito todo dia às 00h30, horário de Brasília).

### Nova notícia
Crie `noticias/2026-11-05-titulo-da-noticia.md`:

```
---
titulo: "Título da notícia"
data: 2026-11-05
categoria: "Ações no território"
autor: "Nome"
resumo: "Uma ou duas frases que aparecem na lista."
---

Texto em Markdown...
```
Use `rascunho: true` no cabeçalho para não publicar ainda.

### Ligar uma plataforma
Em `data/site.yml`, na seção `plataformas`, preencha `url:` (ex.: o geoportal ou o painel).
O botão "Em desenvolvimento" vira "Acessar" automaticamente.

## Ver no seu computador
```
pip install -r requirements.txt
python build.py --serve      # abre em http://localhost:8000
```

## Publicar no GitHub Pages
1. Crie o repositório e envie esta pasta (`git push` na branch `main`).
2. No GitHub: **Settings → Pages → Build and deployment → Source: GitHub Actions**.
3. A cada push, o workflow `.github/workflows/pages.yml` gera o site e publica.
4. Se o endereço for `usuario.github.io/nome-do-repo/`, ajuste `base_url` em `data/site.yml` (só afeta a página 404).

Os links internos são relativos, então o site funciona em qualquer endereço (inclusive domínio próprio).


## Autoria, licença e como citar
- **Autoria:** Alexandro Gularte Schäfer (Unipampa), com a equipe do PET-Saúde: Clima.
- **Uso de IA:** o site foi desenvolvido com apoio de uma ferramenta de inteligência artificial (Claude Code, Anthropic), com curadoria e revisão da equipe.
- **Licença:** código sob MIT e textos sob CC BY 4.0; fotos de pessoas, logotipos e cartazes de terceiros ficam de fora (veja `LICENSE.md`).
- **Como citar:** SCHÄFER, A. G. *Site do ClimaPampa — PET-Saúde: Clima (Unipampa)*. 2026. Disponível em: https://pet-saude-climapampa.github.io/. Acesso em: ___.
  O GitHub também oferece o botão "Cite this repository", a partir do arquivo `CITATION.cff`.

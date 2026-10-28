# Site ClimaPampa (PET-Saúde: Clima · Unipampa)

Site estático em Python (Jinja2), publicado no GitHub Pages em
https://pet-saude-climapampa.github.io. Idioma do site e dos textos: português do Brasil.

## Comandos
- `pip install -r requirements.txt`
- `python build.py` gera `dist/`
- `python build.py --serve` gera e serve em http://localhost:8000
- Publicação: push na `main` → workflow `.github/workflows/pages.yml`.

## Onde fica cada coisa
- `data/site.yml`: textos do projeto, eixos, GATs, equipe (papel, função, foto, lattes), plataformas, contato.
- `noticias/*.md`: uma notícia por arquivo (cabeçalho YAML: titulo, data, categoria, autor, resumo; `rascunho: true` não publica).
- `galeria/<id>/` + `data/galeria.yml`: álbuns de fotos por atividade; `build.py` reduz as fotos e gera miniaturas em `dist/static/galeria/` (Pillow). Só publicar fotos com autorização de imagem.
- `templates/`: HTML (Jinja2). `static/css/style.css`: visual. `static/img/`: logos e fotos da equipe.

## Regras
- Links internos são **relativos** (`{{ root }}`), para funcionar em qualquer endereço. Não usar caminhos absolutos.
- Identidade visual do manual PET-Saúde Clima: verde #2FA250, lima #96D335, amarelo #F9BA38, vermelho #EB2C35, azul #59B8D7, petróleo #3DA8AF. Texto escuro sobre cores claras (contraste AA); botões com #157A38.
- Acessibilidade: manter uma `h1` por página, `alt` nas imagens, foco visível, respeitar `prefers-reduced-motion`.
- **Repositório público: nunca commitar dados pessoais** (termos assinados, CPF, telefones, comprovantes, nomes de estudantes sem autorização). Esses arquivos ficam fora do repositório.
- Trocar o conteúdo pelos dados, não pelo HTML: edite `data/site.yml` sempre que possível.

## Pendências de conteúdo
- Links do Lattes (campo `lattes:` de cada pessoa em `data/site.yml`).
- Orientadores de serviço (3): nomes e fotos.
- Tutores por GAT dentro dos eixos 1 e 2 (3 e 4): hoje aparecem por eixo.
- Fonte oficial Alte Haas Grotesk: hoje usa Plus Jakarta Sans via Google Fonts (autohospedar se possível).
- E-mail de contato no rodapé (`contato.email`), se puder ser público.
- Links das plataformas (`url:` em `plataformas`) quando o geoportal e os painéis estiverem no ar.

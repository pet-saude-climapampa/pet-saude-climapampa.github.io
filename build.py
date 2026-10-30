#!/usr/bin/env python3
"""Gerador do site ClimaPampa (PET-Saúde: Clima · Unipampa).

Uso:
    python build.py            # gera a pasta dist/
    python build.py --serve    # gera e abre em http://localhost:8000

Conteúdo:
    data/site.yml       dados do projeto, eixos, GATs, equipe e plataformas
    noticias/*.md       uma notícia por arquivo (Markdown com cabeçalho YAML)
    templates/          modelos HTML (Jinja2)
    static/             CSS, JS, imagens
"""
import argparse
import datetime as dt
import functools
import http.server
import re
import shutil
import socketserver
from pathlib import Path

import markdown
import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro"]


def data_br(d):
    return f"{d.day} de {MESES[d.month - 1]} de {d.year}"


DIAS_SEMANA = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MESES_ABREV = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def hora_br(h):
    """'19:00' -> '19h', '19:30' -> '19h30'."""
    hh, mm = str(h).split(":")
    return f"{int(hh)}h" + ("" if mm == "00" else mm)


def carregar_agenda(hoje):
    """Lê data/agenda.yml e separa em próximas e realizadas (pela data, no horário de Brasília)."""
    arq = ROOT / "data" / "agenda.yml"
    itens = (yaml.safe_load(arq.read_text(encoding="utf-8")) or []) if arq.exists() else []
    for a in itens:
        d = a["data"]
        if isinstance(d, str):
            d = dt.date.fromisoformat(d)
        a["data"] = d
        a["dia"], a["mes"] = d.day, MESES_ABREV[d.month - 1]
        a["data_br"] = data_br(d)
        a["dia_semana"] = DIAS_SEMANA[d.weekday()]
        a["horario"] = hora_br(a["inicio"]) + (f" às {hora_br(a['fim'])}" if a.get("fim") else "") if a.get("inicio") else ""
        a["html"] = markdown.markdown(a.get("descricao", ""), extensions=["extra", "sane_lists"])
        a["descricao_longa"] = bool(a.get("descricao"))
        a["futura"] = d >= hoje
    proximas = sorted([a for a in itens if a["futura"]], key=lambda a: (a["data"], a.get("inicio", "")))
    realizadas = sorted([a for a in itens if not a["futura"]], key=lambda a: a["data"], reverse=True)
    return proximas, realizadas


def ics_atividade(a, site):
    """Arquivo .ics (calendário) de uma atividade. Horário de Brasília convertido para UTC."""
    from zoneinfo import ZoneInfo
    def utc(d, h):
        hh, mm = map(int, str(h).split(":"))
        return dt.datetime(d.year, d.month, d.day, hh, mm, tzinfo=ZoneInfo("America/Sao_Paulo")).astimezone(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    def esc(t):
        return str(t).replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
    desc = [a.get("resumo", "")]
    if a.get("link"):
        desc.append("Link da reunião: " + a["link"])
    if a.get("inscricao"):
        desc.append("Inscrição: " + a["inscricao"])
    ini = a.get("inicio", "09:00")
    fim = a.get("fim")
    if not fim:  # sem horário de término: 1 hora
        hh, mm = map(int, str(ini).split(":"))
        fim = f"{min(hh + 1, 23):02d}:{mm:02d}"
    linhas = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//ClimaPampa//Agenda//PT-BR", "CALSCALE:GREGORIAN", "BEGIN:VEVENT",
              f"UID:{a['id']}@pet-saude-climapampa.github.io",
              "DTSTAMP:" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ"),
              *(["DTSTART;VALUE=DATE:" + a["data"].strftime("%Y%m%d"), "DTEND;VALUE=DATE:" + (a["data"] + dt.timedelta(days=1)).strftime("%Y%m%d")]
                if not a.get("inicio") else ["DTSTART:" + utc(a["data"], ini), "DTEND:" + utc(a["data"], fim)]),
              "SUMMARY:" + esc(a["titulo"]), "DESCRIPTION:" + esc("\n".join(x for x in desc if x)),
              "LOCATION:" + esc(a.get("modalidade", "")), "END:VEVENT", "END:VCALENDAR"]
    return "\r\n".join(linhas) + "\r\n"


def carregar_site():
    with open(ROOT / "data" / "site.yml", encoding="utf-8") as f:
        site = yaml.safe_load(f)
    est = ROOT / "data" / "estudantes.yml"
    site["estudantes"] = (yaml.safe_load(est.read_text(encoding="utf-8")) or []) if est.exists() else []
    return site


def carregar_noticias():
    posts = []
    for arq in sorted((ROOT / "noticias").glob("*.md")):
        texto = arq.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", texto, re.S)
        meta, corpo = (yaml.safe_load(m.group(1)) or {}, m.group(2)) if m else ({}, texto)
        if meta.get("rascunho"):
            continue
        data = meta.get("data")
        if isinstance(data, str):
            data = dt.date.fromisoformat(data)
        if not data:
            data = dt.date.today()
        slug = re.sub(r"^\d{4}-\d{2}-\d{2}-", "", arq.stem)
        posts.append({
            "slug": slug,
            "titulo": meta.get("titulo", slug),
            "data": data,
            "data_br": data_br(data),
            "resumo": meta.get("resumo", ""),
            "autor": meta.get("autor", ""),
            "categoria": meta.get("categoria", "Notícia"),
            "html": markdown.markdown(corpo, extensions=["extra", "sane_lists"]),
        })
    posts.sort(key=lambda p: p["data"], reverse=True)
    return posts


IMG_EXT = {".jpg", ".jpeg", ".png", ".webp"}


def carregar_galeria():
    """Lê data/galeria.yml, reduz as fotos de galeria/<id>/ e cria miniaturas em dist/static/galeria/."""
    arq = ROOT / "data" / "galeria.yml"
    albuns = (yaml.safe_load(arq.read_text(encoding="utf-8")) or {}).get("albuns", []) if arq.exists() else []
    try:
        from PIL import Image, ImageOps
    except ImportError:
        Image = None
        print("Aviso: Pillow não instalado (pip install pillow); as fotos serão copiadas sem redução.")
    for a in albuns:
        pasta = ROOT / "galeria" / a["id"]
        saida = DIST / "static" / "galeria" / a["id"]
        saida.mkdir(parents=True, exist_ok=True)
        legendas = a.get("legendas") or {}
        fotos = []
        arquivos = sorted(pasta.iterdir()) if pasta.exists() else []
        for f in arquivos:
            if f.suffix.lower() not in IMG_EXT:
                continue
            base = re.sub(r"[^a-z0-9]+", "-", f.stem.lower()).strip("-")
            if Image:
                im = ImageOps.exif_transpose(Image.open(f))
                if im.mode in ("RGBA", "LA", "P"):
                    im = im.convert("RGBA")
                    fundo = Image.new("RGB", im.size, (255, 255, 255))
                    fundo.paste(im, mask=im.split()[3])
                    im = fundo
                else:
                    im = im.convert("RGB")
                grande = im.copy()
                grande.thumbnail((1600, 1600))
                grande.save(saida / f"{base}.jpg", quality=84, optimize=True)
                mini = im.copy()
                mini.thumbnail((560, 560))
                mini.save(saida / f"{base}-t.jpg", quality=80, optimize=True)
                full, thumb, (w, h) = f"static/galeria/{a['id']}/{base}.jpg", f"static/galeria/{a['id']}/{base}-t.jpg", grande.size
            else:
                shutil.copy(f, saida / (base + f.suffix.lower()))
                full = thumb = f"static/galeria/{a['id']}/{base}{f.suffix.lower()}"
                w = h = None
            fotos.append({"arquivo": f.name, "full": full, "thumb": thumb, "w": w, "h": h,
                          "legenda": legendas.get(f.name, "")})
        capa = next((x for x in fotos if x["arquivo"] == a.get("capa")), fotos[0] if fotos else None)
        a["fotos"], a["capa_foto"] = fotos, capa
        d = a.get("data")
        a["data_br"] = data_br(d) if isinstance(d, dt.date) else ""
    albuns.sort(key=lambda x: x["data"] if isinstance(x.get("data"), dt.date) else dt.date.min, reverse=True)
    return albuns


PAPEIS_NUM = [("coordenacao", "Coordenação geral"), ("tutoria", "Tutores"), ("preceptoria", "Preceptores"), ("orientacao", "Orientadores de serviço"),
              ("bolsista", "Estudantes bolsistas"), ("voluntario", "Estudantes voluntários")]


def estatisticas(site):
    """Contagens da equipe para a página 'Em números' (só números, nenhum dado pessoal)."""
    from collections import Counter
    pes, est = site["equipe"]["pessoas"], site["estudantes"]
    cor_gat = {g: e["cor"] for e in site["eixos"] for g in e["gats"]}
    eixo_gat = {g: e["curto"] for e in site["eixos"] for g in e["gats"]}

    def papel(x):
        return x["papel"] if "papel" in x else ("voluntario" if x.get("voluntario") else "bolsista")

    def curso(x):
        return x.get("curso") or "Não informado"

    mapa_campus = site.get("campus_por_curso") or {}

    def campus(x):
        return x.get("campus") or mapa_campus.get(x.get("curso") or "") or "Não informado"

    def ordenar(c):
        return sorted(c.items(), key=lambda t: (t[0] == "Não informado", -t[1], t[0]))

    def contar(lista):
        c = Counter(papel(x) for x in lista)
        seg = [{"id": k, "rotulo": r, "n": c.get(k, 0)} for k, r in PAPEIS_NUM]
        return seg

    gats = []
    for g in sorted(cor_gat):
        membros = [x for x in pes if x.get("gat") == g and x["papel"] != "coordenacao"] + [x for x in est if x["gat"] == g]
        alunos = [x for x in est if x["gat"] == g]
        cursos = sorted(Counter(curso(x) for x in alunos).items(), key=lambda t: (t[0] == "Não informado", -t[1], t[0]))
        gats.append({"n": g, "cor": cor_gat[g], "eixo": eixo_gat[g], "total": len(membros), "estudantes": len(alunos),
                     "seg": contar(membros), "cursos": cursos,
                     "campi": ordenar(Counter(campus(x) for x in alunos))})
    todos = [x for x in pes] + list(est)
    cursos = sorted(Counter(curso(x) for x in est).items(), key=lambda t: (t[0] == "Não informado", -t[1], t[0]))
    return {
        "total": len(todos), "estudantes": len(est),
        "bolsistas": sum(1 for x in est if not x.get("voluntario")), "voluntarios": sum(1 for x in est if x.get("voluntario")),
        "ndcursos": len([c for c, _ in cursos if c != "Não informado"]),
        "seg": contar(todos), "cursos": cursos,
        "campi": ordenar(Counter(campus(x) for x in est)),
        "campi_doc": ordenar(Counter(campus(x) for x in pes if x["papel"] in ("coordenacao", "tutoria"))),
        "ndoc": sum(1 for x in pes if x["papel"] in ("coordenacao", "tutoria")),
        "cursos_serv": ordenar(Counter(x["formacao"] for x in pes if x["papel"] in ("preceptoria", "orientacao") and x.get("formacao"))),
        "nserv": sum(1 for x in pes if x["papel"] in ("preceptoria", "orientacao")),
        "ncampi": len({campus(x) for x in est} - {"Não informado"}), "maxcurso": max(n for _, n in cursos), "gats": gats,
        "tutores": sum(1 for x in pes if x["papel"] == "tutoria"), "preceptores": sum(1 for x in pes if x["papel"] == "preceptoria"),
        "orientadores": sum(1 for x in pes if x["papel"] == "orientacao"),
    }


def estrutura_equipe(site):
    """Eixos e GATs para a página inicial da equipe (cartões que abrem a equipe de cada GAT)."""
    pes, est = site["equipe"]["pessoas"], site["estudantes"]
    saida = []
    for e in site["eixos"]:
        cards = []
        for g in e["gats"]:
            membros = [x for x in pes if x.get("gat") == g and x["papel"] != "coordenacao"]
            alunos = [x for x in est if x["gat"] == g]
            tutores = [x["nome"] for x in membros if x["papel"] == "tutoria"]
            cards.append({"n": g, "total": len(membros) + len(alunos), "estudantes": len(alunos), "tutores": tutores})
        saida.append({"eixo": e, "gats": cards})
    return saida


def gerar():
    site = carregar_site()
    noticias = carregar_noticias()
    gats = {g["n"]: g for g in site["gats"]}
    eixos = {e["n"]: e for e in site["eixos"]}
    pessoas = {p["id"]: p for p in site["equipe"]["pessoas"]}

    if DIST.exists():
        shutil.rmtree(DIST, ignore_errors=True)  # limpeza "melhor esforço"
    DIST.mkdir(exist_ok=True)
    shutil.copytree(ROOT / "static", DIST / "static", dirs_exist_ok=True)
    (DIST / ".nojekyll").write_text("")
    albuns = carregar_galeria()

    env = Environment(loader=FileSystemLoader(ROOT / "templates"),
                      autoescape=select_autoescape(["html"]),
                      trim_blocks=True, lstrip_blocks=True)
    ano = dt.date.today().year
    from zoneinfo import ZoneInfo
    hoje = dt.datetime.now(ZoneInfo("America/Sao_Paulo")).date()
    ag_prox, ag_real = carregar_agenda(hoje)

    def render(template, destino, base_abs=None, **ctx):
        # destino: caminho relativo dentro de dist/, ex.: "grupos/gat-1/index.html"
        profundidade = len(Path(destino).parts) - 1
        root = base_abs if base_abs is not None else "../" * profundidade
        html = env.get_template(template).render(
            site=site, noticias=noticias, agenda_prox=ag_prox, agenda_home=[a for a in ag_prox if a.get("destaque", True)][:1], agenda_real=ag_real, gats=gats, eixos=eixos, pessoas=pessoas,
            root=root, ano=ano, **ctx)
        saida = DIST / destino
        saida.parent.mkdir(parents=True, exist_ok=True)
        saida.write_text(html, encoding="utf-8")

    render("home.html", "index.html", active="home")
    render("documentos.html", "documentos/index.html", active="documentos", title="Documentos")
    render("enviar.html", "enviar/index.html", active="enviar", title="Envie conteúdo")
    render("sobre.html", "sobre/index.html", active="sobre", title="Sobre o site")
    render("projeto.html", "o-projeto/index.html", active="projeto", title="O projeto")
    ordem=sorted(eixos)
    for i,n in enumerate(ordem):
        render("eixo.html",f"eixos/eixo-{n}/index.html",active="eixos",title=f"Eixo {n}: {eixos[n]['curto']}",eixo=eixos[n],anterior=eixos[ordem[i-1]] if i>0 else None,proximo=eixos[ordem[i+1]] if i<len(ordem)-1 else None)
    render("equipe.html", "equipe/index.html", active="equipe", title="Equipe", estrutura=estrutura_equipe(site))
    render("equipe_coordenacao.html", "equipe/coordenacao/index.html", active="equipe", title="Coordenação geral")
    for e in site["eixos"]:
        for g in e["gats"]:
            render("equipe_gat.html", f"equipe/gat-{g}/index.html", active="equipe", title=f"Equipe do GAT {g}", eixo=e, gat=g)
    render("equipe_orientadores.html", "equipe/orientadores/index.html", active="equipe", title="Orientação de serviço")
    render("equipe_numeros.html", "equipe/em-numeros/index.html", active="equipe_numeros", title="A equipe em números", n=estatisticas(site))
    for cat in site["produtos_categorias"]:
        itens = [p for p in site["produtos"] if p["categoria"] == cat["id"]]
        itens.sort(key=lambda p: int(p.get("ano") or 0), reverse=True)
        cat["total"] = len(itens)
        render("produto_categoria.html", f"produtos/{cat['id']}/index.html", active="produtos",
               title=cat["titulo"], cat=cat, itens=itens)
    render("produtos.html", "produtos/index.html", active="produtos", title="Produtos")
    render("galeria.html", "galeria/index.html", active="galeria", title="Galeria", albuns=albuns)
    for a in albuns:
        render("galeria_album.html", f"galeria/{a['id']}/index.html", active="galeria",
               title=a["titulo"], album=a)
    render("agenda.html", "agenda/index.html", active="agenda", title="Agenda")
    for a in ag_prox + ag_real:
        (DIST / "agenda").mkdir(parents=True, exist_ok=True)
        (DIST / "agenda" / f"{a['id']}.ics").write_text(ics_atividade(a, site), encoding="utf-8", newline="")
    render("noticias.html", "noticias/index.html", active="noticias", title="Notícias")
    for p in noticias:
        render("post.html", f"noticias/{p['slug']}/index.html", active="noticias",
               title=p["titulo"], post=p, description=p["resumo"])
    # 404: usa a raiz do site (BASE) em vez de caminho relativo
    base = site.get("base_url", "/")
    render("404.html", "404.html", base_abs=base, title="Página não encontrada")
    print(f"Site gerado em {DIST} ({len(noticias)} notícia(s)).")


def servir(porta=8000):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", porta), handler) as httpd:
        print(f"Abra http://localhost:{porta}  (Ctrl+C para parar)")
        httpd.serve_forever()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--serve", action="store_true", help="serve dist/ em localhost:8000")
    args = ap.parse_args()
    gerar()
    if args.serve:
        servir()

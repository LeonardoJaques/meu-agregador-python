from flask import Flask, render_template, redirect, url_for, jsonify, request
import feedparser
from datetime import datetime, timedelta, timezone
import time
import re
import json
import os
import copy

# --- Configurações (FEEDS_POR_CATEGORIA, etc. permanecem iguais) ---
FEEDS_POR_CATEGORIA = {
    "tecnologia": [
        "http://feeds.feedburner.com/TechCrunch/",
        "https://www.theverge.com/rss/index.xml",
        "https://tecnoblog.net/feed/",
        "https://canaltech.com.br/rss/",
        "https://gizmodo.uol.com.br/feed/",
        "https://www.engadget.com/rss.xml",
        "https://www.cnet.com/rss/news/",
        "https://www.bbc.co.uk/news/technology/rss.xml",
        "https://www.reuters.com/news/technology",
        "https://www.bbc.co.uk/news/technology/rss.xml",
        "https://www.wired.com/feed/category/tech/latest/rss",
        "https://www.techcrunch.com/feed/",
        "https://www.zdnet.com/news/rss.xml",
        "https://ycombinator.com/rss",
        "https://www.theguardian.com/technology/rss",
        "https://www.nytimes.com/svc/collections/v1/publish/www.nytimes.com/section/technology/rss.xml",
    ],
    "quadrinhos": [
        "http://feeds.feedburner.com/comicsbeat", # The Beat
        "https://bleedingcool.com/comics/feed/", # Bleeding Cool Comics
    ],
    "economia": [
        "http://feeds.reuters.com/reuters/businessNews", # Reuters Business
        "https://www.valor.com.br/rss",
        "https://www.infomoney.com.br/rss",
        "https://www.cnnbrasil.com.br/feed/",
        "https://www.bbc.co.uk/news/business/rss.xml",
        "https://www.nytimes.com/svc/collections/v1/publish/www.nytimes.com/section/business/rss.xml",
        "https://www.wsj.com/xml/rss/3_7085.xml", # Wall Street Journal
        
    ]
}
CATEGORIAS_DISPONIVEIS = list(FEEDS_POR_CATEGORIA.keys())
CATEGORIA_PADRAO = "tecnologia"

HORAS_RECENTES_FEED = 48
MAX_NOTICIAS_SALVAS_PARA_EXIBIR = 10
MAX_FEEDS_RECENTES_PARA_EXIBIR = 30
DATA_DIR = 'data'
SALVAS_JSON_PATH = os.path.join(DATA_DIR, 'noticias_salvas.json')
FEEDS_RECENTES_JSON_PATH = os.path.join(DATA_DIR, 'feeds_recentes.json')

# --- Funções de utilidade para JSON, Conversão, buscar_novidades_dos_feeds, ordenar_noticias_salvas (sem alterações) ---
def garantir_pasta_data():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR); print(f"Pasta '{DATA_DIR}' criada.")
def carregar_json(caminho_arquivo):
    garantir_pasta_data()
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f: return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError): return []
def salvar_json(caminho_arquivo, dados):
    garantir_pasta_data()
    with open(caminho_arquivo, 'w', encoding='utf-8') as f: json.dump(dados, f, indent=4, ensure_ascii=False)
def converter_para_datetime_utc(struct_time):
    try: return datetime.fromtimestamp(time.mktime(struct_time), timezone.utc)
    except Exception: return datetime(struct_time[0], struct_time[1], struct_time[2], struct_time[3], struct_time[4], struct_time[5], tzinfo=timezone.utc)
def buscar_novidades_dos_feeds():
    print("Buscando novidades dos feeds RSS por categoria...")
    noticias_salvas = carregar_json(SALVAS_JSON_PATH)
    links_salvos = {noticia['link'] for noticia in noticias_salvas}
    novidades_coletadas_geral = []
    agora_utc = datetime.now(timezone.utc)
    limite_tempo_feed = agora_utc - timedelta(hours=HORAS_RECENTES_FEED)
    for categoria, urls_feeds in FEEDS_POR_CATEGORIA.items():
        print(f"Processando categoria: {categoria}")
        for url_feed in urls_feeds:
            print(f"  Processando feed: {url_feed}")
            try: feed_data = feedparser.parse(url_feed)
            except Exception as e: print(f"    Erro ao acessar o feed {url_feed}: {e}"); continue
            for entry in feed_data.entries:
                link_noticia = entry.link if hasattr(entry, 'link') else None
                if not link_noticia or link_noticia in links_salvos: continue
                data_publicacao_struct = entry.published_parsed or entry.updated_parsed
                if not data_publicacao_struct: continue
                data_publicacao_dt = converter_para_datetime_utc(data_publicacao_struct)
                if data_publicacao_dt >= limite_tempo_feed:
                    titulo = entry.title if hasattr(entry, 'title') else "Sem título"
                    resumo_html = entry.summary or entry.description or ""
                    resumo_limpo = re.sub(r'<[^>]+>', '', resumo_html)
                    resumo_curto = (resumo_limpo[:300] + '...') if len(resumo_limpo) > 300 else resumo_limpo
                    noticia_coletada = {"titulo": titulo, "link": link_noticia, "resumo": resumo_curto.strip(), "publicado_em_ts": data_publicacao_dt.timestamp(), "publicado_em_str": data_publicacao_dt.strftime("%d/%m/%Y %H:%M"), "fonte": feed_data.feed.title if hasattr(feed_data, 'feed') and hasattr(feed_data.feed, 'title') else url_feed, "categoria": categoria}
                    if not any(n['link'] == link_noticia for n in novidades_coletadas_geral): novidades_coletadas_geral.append(noticia_coletada)
    novidades_coletadas_geral.sort(key=lambda x: x['publicado_em_ts'], reverse=True)
    salvar_json(FEEDS_RECENTES_JSON_PATH, novidades_coletadas_geral)
    print(f"{len(novidades_coletadas_geral)} notícias coletadas de todas categorias e salvas em feeds_recentes.json")
def ordenar_noticias_salvas(noticias):
    return sorted(noticias, key=lambda x: (x.get('relevancia', 0), x.get('publicado_em_ts', 0)), reverse=True)


# --- Configuração do Flask e Rotas ---
app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_importante_e_diferente' # Mude isso!

@app.route('/')
def pagina_inicial():
    categoria_ativa = request.args.get('categoria', CATEGORIA_PADRAO)
    if categoria_ativa not in CATEGORIAS_DISPONIVEIS:
        categoria_ativa = CATEGORIA_PADRAO

    # Notícias Salvas: Carrega TODAS, ordena TODAS, e depois fatia para exibição.
    # Não são mais filtradas pela categoria_ativa para exibição.
    noticias_salvas_todas = carregar_json(SALVAS_JSON_PATH)
    noticias_salvas_ordenadas = ordenar_noticias_salvas(noticias_salvas_todas)
    noticias_salvas_para_exibir = noticias_salvas_ordenadas[:MAX_NOTICIAS_SALVAS_PARA_EXIBIR]
    
    # Notícias Coletadas dos Feeds (CONTINUAM filtradas pela categoria_ativa)
    noticias_feeds_recentes_todas = carregar_json(FEEDS_RECENTES_JSON_PATH)
    noticias_feeds_da_categoria = [n for n in noticias_feeds_recentes_todas if n.get('categoria') == categoria_ativa]
    noticias_feeds_da_categoria.sort(key=lambda x: x.get('publicado_em_ts', 0), reverse=True) 
    noticias_feeds_para_exibir = noticias_feeds_da_categoria[:MAX_FEEDS_RECENTES_PARA_EXIBIR]

    hora_atualizacao_pagina = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return render_template('index.html', 
                           categorias_disponiveis=CATEGORIAS_DISPONIVEIS,
                           categoria_ativa=categoria_ativa,
                           noticias_salvas=noticias_salvas_para_exibir, 
                           total_salvas_armazenadas=len(noticias_salvas_ordenadas), # Total geral de salvas
                           noticias_feeds_recentes=noticias_feeds_para_exibir,
                           total_feeds_na_categoria=len(noticias_feeds_da_categoria), # Total de feeds para a categoria ativa
                           max_feeds_recentes_para_exibir=MAX_FEEDS_RECENTES_PARA_EXIBIR,
                           atualizado_em=hora_atualizacao_pagina)

# --- Rotas /refresh_feeds, /salvar_noticia, /delete_salva, _alterar_relevancia_noticia_salva, 
# --- /rank_up_salva, /rank_down_salva, /reset_relevance_salva (sem alterações diretas na sua lógica interna)
# --- Apenas o redirecionamento em /salvar_noticia e /delete_salva continua usando a categoria para 
# --- manter o usuário na aba de onde a ação pode ter sido originada (para feeds) ou para consistência.
@app.route('/refresh_feeds')
def rota_refresh_feeds():
    buscar_novidades_dos_feeds()
    categoria_ativa = request.args.get('categoria', CATEGORIA_PADRAO)
    return redirect(url_for('pagina_inicial', categoria=categoria_ativa))

@app.route('/salvar_noticia/<path:noticia_link>')
def rota_salvar_noticia(noticia_link):
    feeds_recentes = carregar_json(FEEDS_RECENTES_JSON_PATH)
    noticia_para_salvar_original = None
    categoria_da_noticia_salva = CATEGORIA_PADRAO
    for noticia_feed in feeds_recentes:
        if noticia_feed['link'] == noticia_link:
            noticia_para_salvar_original = noticia_feed
            categoria_da_noticia_salva = noticia_feed.get('categoria', CATEGORIA_PADRAO)
            break
    if noticia_para_salvar_original:
        noticia_para_salvar = copy.deepcopy(noticia_para_salvar_original)
        noticias_salvas = carregar_json(SALVAS_JSON_PATH)
        if not any(n['link'] == noticia_para_salvar['link'] for n in noticias_salvas):
            noticia_para_salvar['relevancia'] = 0
            noticias_salvas.append(noticia_para_salvar)
            salvar_json(SALVAS_JSON_PATH, noticias_salvas)
            feeds_recentes_atualizado = [n for n in feeds_recentes if n['link'] != noticia_link]
            salvar_json(FEEDS_RECENTES_JSON_PATH, feeds_recentes_atualizado)
    return redirect(url_for('pagina_inicial', categoria=categoria_da_noticia_salva)) # Mantém na aba ativa

def _alterar_relevancia_noticia_salva(noticia_link, nova_relevancia_abs=None, delta_relevancia=None):
    noticias_salvas = carregar_json(SALVAS_JSON_PATH)
    modificada = False; relevancia_final = 0; categoria_noticia = CATEGORIA_PADRAO
    for noticia in noticias_salvas:
        if noticia['link'] == noticia_link:
            categoria_noticia = noticia.get('categoria', CATEGORIA_PADRAO)
            if nova_relevancia_abs is not None: noticia['relevancia'] = nova_relevancia_abs
            elif delta_relevancia is not None: noticia['relevancia'] = noticia.get('relevancia', 0) + delta_relevancia
            noticia['relevancia'] = max(0, noticia['relevancia']); relevancia_final = noticia['relevancia']; modificada = True; break
    if modificada: salvar_json(SALVAS_JSON_PATH, noticias_salvas)
    return modificada, relevancia_final, categoria_noticia

@app.route('/rank_up_salva/<path:noticia_link>', methods=['POST'])
def rota_aumentar_relevancia_salva(noticia_link):
    modificada, nova_relevancia, _ = _alterar_relevancia_noticia_salva(noticia_link, delta_relevancia=1)
    if modificada: return jsonify(success=True, link=noticia_link, nova_relevancia=nova_relevancia)
    return jsonify(success=False, link=noticia_link, message="Notícia não encontrada ou erro.")

@app.route('/rank_down_salva/<path:noticia_link>', methods=['POST'])
def rota_diminuir_relevancia_salva(noticia_link):
    modificada, nova_relevancia, _ = _alterar_relevancia_noticia_salva(noticia_link, delta_relevancia=-1)
    if modificada: return jsonify(success=True, link=noticia_link, nova_relevancia=nova_relevancia)
    return jsonify(success=False, link=noticia_link, message="Notícia não encontrada ou erro.")

@app.route('/reset_relevance_salva/<path:noticia_link>', methods=['POST'])
def rota_resetar_relevancia_salva(noticia_link):
    modificada, nova_relevancia, _ = _alterar_relevancia_noticia_salva(noticia_link, nova_relevancia_abs=0)
    if modificada: return jsonify(success=True, link=noticia_link, nova_relevancia=nova_relevancia)
    return jsonify(success=False, link=noticia_link, message="Notícia não encontrada ou erro.")

@app.route('/delete_salva/<path:noticia_link>')
def rota_excluir_noticia_salva(noticia_link):
    noticias_salvas = carregar_json(SALVAS_JSON_PATH)
    categoria_noticia_excluida = CATEGORIA_PADRAO
    for n in noticias_salvas:
        if n['link'] == noticia_link: categoria_noticia_excluida = n.get('categoria', CATEGORIA_PADRAO); break
    noticias_filtradas = [n for n in noticias_salvas if n['link'] != noticia_link]
    if len(noticias_filtradas) < len(noticias_salvas): salvar_json(SALVAS_JSON_PATH, noticias_filtradas)
    return redirect(url_for('pagina_inicial', categoria=categoria_noticia_excluida)) # Mantém na aba ativa


if __name__ == '__main__':
    garantir_pasta_data()
    print("Limpando feeds_recentes.json na inicialização...")
    salvar_json(FEEDS_RECENTES_JSON_PATH, []) 
    app.run(host='0.0.0.0', port=5000, debug=True)
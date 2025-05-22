from flask import Flask, render_template, redirect, url_for, jsonify, request
import feedparser
from datetime import datetime, timedelta, timezone
import time
import re
import json
import os
import copy

# --- Configurações ---
FEEDS_POR_CATEGORIA = {
    "tecnologia": [ # Mantendo a existente
        "http://feeds.feedburner.com/TechCrunch/",
        "https://www.theverge.com/rss/index.xml",
        "https://tecnoblog.net/feed/",
    ],
    "ia": [ # Nova categoria IA
        "https://news.mit.edu/topic/artificial-intelligence2/feed", # MIT News - AI
        "https://blog.research.google/feeds/posts/default/-/artificial%20intelligence", # Google Research - AI
        "https://aws.amazon.com/blogs/machine-learning/feed/", # AWS ML Blog
        "https://www.technologyreview.com/c/artificial-intelligence/feed/" # MIT Tech Review - AI
    ],
    "java": [ # Nova categoria Java
        "https://www.baeldung.com/category/java/feed", # Baeldung Java
        "https://blogs.oracle.com/java/rss", # Oracle Java Blog
        "https://feed.infoq.com/java/news/", # InfoQ Java
        "https://foojay.io/today/feed/" # Friends of OpenJDK
    ],
    "quadrinhos": [
        "http://feeds.feedburner.com/comicsbeat", 
        "https://bleedingcool.com/comics/feed/",
    ],
    "economia": [
        "http://feeds.reuters.com/reuters/businessNews",
        "https://www.valor.com.br/rss",
    ]
}
CATEGORIAS_DISPONIVEIS = list(FEEDS_POR_CATEGORIA.keys()) # Atualizará automaticamente
CATEGORIA_PADRAO = "tecnologia" # Você pode mudar se quiser

# Palavras-chave para simular "tendências" por categoria
PALAVRAS_CHAVE_TENDENCIA_POR_CATEGORIA = {
    "tecnologia": ["lançamento", "nova versão", "inovação", "vazamento", "review"],
    "ia": ["llm", "gpt", "generativa", "deep learning", "machine learning", "openai", "modelo", "pesquisa"],
    "java": ["jdk", "spring boot", "jvm", "framework", "microservices", "release", "jakarta ee", "vulnerabilidade"],
    "quadrinhos": ["adaptação", "trailer", "crítica", "anúncio", "evento", "hq", "mangá"],
    "economia": ["inflação", "juros", "selic", "mercado", "bolsa", "investimento", "crescimento"]
}

HORAS_RECENTES_FEED = 48
MAX_NOTICIAS_SALVAS_PARA_EXIBIR = 10
MAX_FEEDS_RECENTES_PARA_EXIBIR = 10 
DATA_DIR = 'data'
SALVAS_JSON_PATH = os.path.join(DATA_DIR, 'noticias_salvas.json')
FEEDS_RECENTES_JSON_PATH = os.path.join(DATA_DIR, 'feeds_recentes.json')

# O RESTANTE DO CÓDIGO PYTHON (funções de utilidade, buscar_novidades_dos_feeds,
# ordenar_noticias_salvas, rotas Flask, etc.) PERMANECE EXATAMENTE O MESMO
# da versão anterior, pois ele já foi projetado para iterar sobre
# FEEDS_POR_CATEGORIA e CATEGORIAS_DISPONIVEIS dinamicamente.

# --- Funções de utilidade para JSON, Conversão (sem alteração) ---
def garantir_pasta_data():
    if not os.path.exists(DATA_DIR): os.makedirs(DATA_DIR); print(f"Pasta '{DATA_DIR}' criada.")
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

# --- Lógica Principal com Categorias ---
def buscar_novidades_dos_feeds():
    print("Buscando novidades dos feeds RSS por categoria...")
    noticias_salvas = carregar_json(SALVAS_JSON_PATH)
    links_salvos = {noticia['link'] for noticia in noticias_salvas}
    
    novidades_coletadas_geral = []
    agora_utc = datetime.now(timezone.utc)
    limite_tempo_feed = agora_utc - timedelta(hours=HORAS_RECENTES_FEED)

    palavras_chave_tendencia_globais = PALAVRAS_CHAVE_TENDENCIA_POR_CATEGORIA

    for categoria, urls_feeds in FEEDS_POR_CATEGORIA.items():
        print(f"Processando categoria: {categoria}")
        palavras_chave_categoria = [palavra.lower() for palavra in palavras_chave_tendencia_globais.get(categoria, [])]

        for url_feed in urls_feeds:
            try:
                feed_data = feedparser.parse(url_feed)
            except Exception as e:
                print(f"    Erro ao acessar o feed {url_feed}: {e}")
                continue

            for entry in feed_data.entries:
                link_noticia = entry.link if hasattr(entry, 'link') else None
                if not link_noticia or link_noticia in links_salvos:
                    continue

                data_publicacao_struct = entry.published_parsed or entry.updated_parsed
                if not data_publicacao_struct: continue

                data_publicacao_dt = converter_para_datetime_utc(data_publicacao_struct)
                if data_publicacao_dt >= limite_tempo_feed:
                    titulo = entry.title if hasattr(entry, 'title') else "Sem título"
                    resumo_html = entry.summary or entry.description or ""
                    resumo_limpo = re.sub(r'<[^>]+>', '', resumo_html)
                    resumo_curto = (resumo_limpo[:300] + '...') if len(resumo_limpo) > 300 else resumo_limpo

                    fator_tendencia = 0
                    texto_para_busca_tendencia = (titulo + " " + resumo_curto).lower()
                    if any(palavra_chave in texto_para_busca_tendencia for palavra_chave in palavras_chave_categoria):
                        fator_tendencia = 1
                        
                    noticia_coletada = {
                        "titulo": titulo,
                        "link": link_noticia,
                        "resumo": resumo_curto.strip(),
                        "publicado_em_ts": data_publicacao_dt.timestamp(),
                        "publicado_em_str": data_publicacao_dt.strftime("%d/%m/%Y %H:%M"),
                        "fonte": feed_data.feed.title if hasattr(feed_data, 'feed') and hasattr(feed_data.feed, 'title') else url_feed,
                        "categoria": categoria,
                        "fator_tendencia": fator_tendencia
                    }
                    if not any(n['link'] == link_noticia for n in novidades_coletadas_geral):
                        novidades_coletadas_geral.append(noticia_coletada)
    
    salvar_json(FEEDS_RECENTES_JSON_PATH, novidades_coletadas_geral) # Salva todas, a ordenação por tendência será na rota
    print(f"{len(novidades_coletadas_geral)} notícias coletadas de todas categorias e salvas em feeds_recentes.json")

def ordenar_noticias_salvas(noticias):
    return sorted(noticias, key=lambda x: (x.get('relevancia', 0), x.get('publicado_em_ts', 0)), reverse=True)

# --- Configuração do Flask e Rotas ---
app = Flask(__name__)
app.secret_key = 'mudar_esta_chave_para_algo_seguro_em_producao_final_final'

@app.route('/')
def pagina_inicial():
    categoria_ativa = request.args.get('categoria', CATEGORIA_PADRAO)
    if categoria_ativa not in CATEGORIAS_DISPONIVEIS:
        categoria_ativa = CATEGORIA_PADRAO

    noticias_salvas_todas = carregar_json(SALVAS_JSON_PATH)
    noticias_salvas_ordenadas = ordenar_noticias_salvas(noticias_salvas_todas)
    noticias_salvas_para_exibir = noticias_salvas_ordenadas[:MAX_NOTICIAS_SALVAS_PARA_EXIBIR]
    
    noticias_feeds_recentes_todas = carregar_json(FEEDS_RECENTES_JSON_PATH)
    noticias_feeds_da_categoria = [n for n in noticias_feeds_recentes_todas if n.get('categoria') == categoria_ativa]
    noticias_feeds_da_categoria.sort(key=lambda x: (x.get('fator_tendencia', 0), x.get('publicado_em_ts', 0)), reverse=True) 
    noticias_feeds_para_exibir = noticias_feeds_da_categoria[:MAX_FEEDS_RECENTES_PARA_EXIBIR]

    hora_atualizacao_pagina = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    return render_template('index.html', 
                           categorias_disponiveis=CATEGORIAS_DISPONIVEIS,
                           categoria_ativa=categoria_ativa,
                           noticias_salvas=noticias_salvas_para_exibir, 
                           total_salvas_armazenadas=len(noticias_salvas_ordenadas),
                           noticias_feeds_recentes=noticias_feeds_para_exibir,
                           total_feeds_na_categoria=len(noticias_feeds_da_categoria),
                           max_feeds_recentes_para_exibir=MAX_FEEDS_RECENTES_PARA_EXIBIR,
                           atualizado_em=hora_atualizacao_pagina)

@app.route('/refresh_feeds')
def rota_refresh_feeds():
    buscar_novidades_dos_feeds()
    categoria_ativa = request.args.get('categoria', CATEGORIA_PADRAO)
    return redirect(url_for('pagina_inicial', categoria=categoria_ativa))

@app.route('/salvar_noticia/<path:noticia_link>')
def rota_salvar_noticia(noticia_link):
    feeds_recentes = carregar_json(FEEDS_RECENTES_JSON_PATH)
    noticia_para_salvar_original = None; categoria_da_noticia_salva = CATEGORIA_PADRAO
    for noticia_feed in feeds_recentes:
        if noticia_feed['link'] == noticia_link:
            noticia_para_salvar_original = noticia_feed
            categoria_da_noticia_salva = noticia_feed.get('categoria', CATEGORIA_PADRAO); break
    if noticia_para_salvar_original:
        noticia_para_salvar = copy.deepcopy(noticia_para_salvar_original)
        noticias_salvas = carregar_json(SALVAS_JSON_PATH)
        if not any(n['link'] == noticia_para_salvar['link'] for n in noticias_salvas):
            noticia_para_salvar['relevancia'] = 0
            if 'fator_tendencia' in noticia_para_salvar: del noticia_para_salvar['fator_tendencia'] 
            noticias_salvas.append(noticia_para_salvar)
            salvar_json(SALVAS_JSON_PATH, noticias_salvas)
            feeds_recentes_atualizado = [n for n in feeds_recentes if n['link'] != noticia_link]
            salvar_json(FEEDS_RECENTES_JSON_PATH, feeds_recentes_atualizado)
    return redirect(url_for('pagina_inicial', categoria=categoria_da_noticia_salva))

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
    return redirect(url_for('pagina_inicial', categoria=categoria_noticia_excluida))


if __name__ == '__main__':
    garantir_pasta_data()
    print("Limpando feeds_recentes.json na inicialização...")
    salvar_json(FEEDS_RECENTES_JSON_PATH, []) 
    app.run(host='0.0.0.0', port=5000, debug=True)
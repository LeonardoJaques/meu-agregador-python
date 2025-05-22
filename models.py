# models.py
import json
import os
import re
import time
from datetime import datetime, timedelta, timezone
import feedparser
import copy

# --- Configurações de Dados ---
FEEDS_POR_CATEGORIA = {
    "tecnologia": [
        "http://feeds.feedburner.com/TechCrunch/", "https://www.theverge.com/rss/index.xml",
        "https://tecnoblog.net/feed/",
    ],
    "ia": [
        "https://news.mit.edu/topic/artificial-intelligence2/feed",
        "https://blog.research.google/feeds/posts/default/-/artificial%20intelligence",
        "https://aws.amazon.com/blogs/machine-learning/feed/",
    ],
    "java": [
        "https://www.baeldung.com/category/java/feed", "https://blogs.oracle.com/java/rss",
        "https://feed.infoq.com/java/news/",
        "https://www.infoq.com/java/articles/feed/",
        "https://www.oracle.com/technetwork/java/index.html",
        "https://www.oracle.com/technetwork/java/javaee/overview/index.html",
        "https://www.oracle.com/technetwork/java/javase/overview/index.html"
    ],
    "quadrinhos": [
        "http://feeds.feedburner.com/comicsbeat", "https://bleedingcool.com/comics/feed/",
    ],
    "economia": [
        "http://feeds.reuters.com/reuters/businessNews", "https://www.valor.com.br/rss",
    ]
}
CATEGORIAS_DISPONIVEIS = list(FEEDS_POR_CATEGORIA.keys())
CATEGORIA_PADRAO = "tecnologia"

PALAVRAS_CHAVE_TENDENCIA_POR_CATEGORIA = {
    "tecnologia": ["lançamento", "nova versão", "inovação", "vazamento", "review"],
    "ia": ["llm", "gpt", "generativa", "deep learning", "machine learning", "openai"],
    "java": ["jdk", "spring boot", "jvm", "framework", "microservices", "release"],
    "quadrinhos": ["adaptação", "trailer", "crítica", "anúncio", "evento"],
    "economia": ["inflação", "juros", "selic", "mercado", "bolsa", "investimento"]
}

HORAS_RECENTES_FEED = 48
DATA_DIR = 'data'
SALVAS_JSON_PATH = os.path.join(DATA_DIR, 'noticias_salvas.json')
FEEDS_RECENTES_JSON_PATH = os.path.join(DATA_DIR, 'feeds_recentes.json')

# --- Funções de Persistência (JSON) ---
def _garantir_pasta_data():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def carregar_json_data(caminho_arquivo):
    _garantir_pasta_data()
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def salvar_json_data(caminho_arquivo, dados):
    _garantir_pasta_data()
    with open(caminho_arquivo, 'w', encoding='utf-8') as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

def limpar_feeds_recentes_iniciais():
    salvar_json_data(FEEDS_RECENTES_JSON_PATH, [])
    print("feeds_recentes.json limpo na inicialização.")

# --- Funções de Conversão e Utilidade ---
def _converter_para_datetime_utc(struct_time):
    try:
        return datetime.fromtimestamp(time.mktime(struct_time), timezone.utc)
    except Exception:
        return datetime(struct_time[0], struct_time[1], struct_time[2],
                        struct_time[3], struct_time[4], struct_time[5],
                        tzinfo=timezone.utc)

# --- Lógica de Negócios das Notícias ---
def buscar_e_processar_novidades_dos_feeds():
    print("MODEL: Buscando novidades dos feeds...")
    noticias_salvas = carregar_json_data(SALVAS_JSON_PATH)
    links_salvos = {noticia['link'] for noticia in noticias_salvas}
    novidades_coletadas_geral = []
    agora_utc = datetime.now(timezone.utc)
    limite_tempo_feed = agora_utc - timedelta(hours=HORAS_RECENTES_FEED)

    for categoria, urls_feeds in FEEDS_POR_CATEGORIA.items():
        palavras_chave_categoria = [palavra.lower() for palavra in PALAVRAS_CHAVE_TENDENCIA_POR_CATEGORIA.get(categoria, [])]
        for url_feed in urls_feeds:
            try:
                feed_data = feedparser.parse(url_feed)
            except Exception as e:
                print(f"MODEL: Erro ao acessar o feed {url_feed}: {e}")
                continue
            for entry in feed_data.entries:
                link_noticia = entry.link if hasattr(entry, 'link') else None
                if not link_noticia or link_noticia in links_salvos: continue
                data_publicacao_struct = entry.published_parsed or entry.updated_parsed
                if not data_publicacao_struct: continue
                data_publicacao_dt = _converter_para_datetime_utc(data_publicacao_struct)

                if data_publicacao_dt >= limite_tempo_feed:
                    titulo = entry.title if hasattr(entry, 'title') else "Sem título"
                    resumo_html = entry.summary or entry.description or ""
                    resumo_limpo = re.sub(r'<[^>]+>', '', resumo_html)
                    resumo_curto = (resumo_limpo[:300] + '...') if len(resumo_limpo) > 300 else resumo_limpo
                    fator_tendencia = 1 if any(palavra in (titulo + " " + resumo_curto).lower() for palavra in palavras_chave_categoria) else 0
                    
                    noticia_coletada = {
                        "titulo": titulo, "link": link_noticia, "resumo": resumo_curto.strip(),
                        "publicado_em_ts": data_publicacao_dt.timestamp(),
                        "publicado_em_str": data_publicacao_dt.strftime("%d/%m/%Y %H:%M"),
                        "fonte": feed_data.feed.title if hasattr(feed_data, 'feed') and hasattr(feed_data.feed, 'title') else url_feed,
                        "categoria": categoria, "fator_tendencia": fator_tendencia
                    }
                    if not any(n['link'] == link_noticia for n in novidades_coletadas_geral):
                        novidades_coletadas_geral.append(noticia_coletada)
    
    salvar_json_data(FEEDS_RECENTES_JSON_PATH, novidades_coletadas_geral)
    print(f"MODEL: {len(novidades_coletadas_geral)} notícias coletadas e salvas em feeds_recentes.json")
    return novidades_coletadas_geral

def obter_noticias_salvas_todas():
    return carregar_json_data(SALVAS_JSON_PATH)

def obter_feeds_recentes_todos():
    return carregar_json_data(FEEDS_RECENTES_JSON_PATH)

def ordenar_noticias_por_relevancia(noticias):
    return sorted(noticias, key=lambda x: (x.get('relevancia', 0), x.get('publicado_em_ts', 0)), reverse=True)

def ordenar_noticias_feeds(noticias):
     return sorted(noticias, key=lambda x: (x.get('fator_tendencia', 0), x.get('publicado_em_ts', 0)), reverse=True)

def salvar_nova_noticia(link_noticia_a_salvar):
    feeds_recentes = carregar_json_data(FEEDS_RECENTES_JSON_PATH)
    noticia_encontrada = None
    for noticia_feed in feeds_recentes:
        if noticia_feed['link'] == link_noticia_a_salvar:
            noticia_encontrada = copy.deepcopy(noticia_feed)
            break
    
    if not noticia_encontrada:
        return None, False # Retorna None para categoria se não encontrar

    noticias_salvas = carregar_json_data(SALVAS_JSON_PATH)
    if not any(n['link'] == noticia_encontrada['link'] for n in noticias_salvas):
        noticia_encontrada['relevancia'] = 0
        if 'fator_tendencia' in noticia_encontrada:
            del noticia_encontrada['fator_tendencia']
        noticias_salvas.append(noticia_encontrada)
        salvar_json_data(SALVAS_JSON_PATH, noticias_salvas)

        feeds_recentes_atualizado = [n for n in feeds_recentes if n['link'] != link_noticia_a_salvar]
        salvar_json_data(FEEDS_RECENTES_JSON_PATH, feeds_recentes_atualizado)
        return noticia_encontrada.get('categoria', CATEGORIA_PADRAO), True
    return noticia_encontrada.get('categoria', CATEGORIA_PADRAO), False # Já existia ou erro

def excluir_noticia_salva(link_noticia_a_excluir):
    noticias_salvas = carregar_json_data(SALVAS_JSON_PATH)
    categoria_original = CATEGORIA_PADRAO
    encontrou = False
    for n in noticias_salvas:
        if n['link'] == link_noticia_a_excluir:
            categoria_original = n.get('categoria', CATEGORIA_PADRAO)
            encontrou = True
            break
            
    if encontrou:
        noticias_filtradas = [n for n in noticias_salvas if n['link'] != link_noticia_a_excluir]
        if len(noticias_filtradas) < len(noticias_salvas):
            salvar_json_data(SALVAS_JSON_PATH, noticias_filtradas)
            return categoria_original, True
    return categoria_original, False


def alterar_relevancia_salva(link_noticia, nova_relevancia_abs=None, delta_relevancia=None):
    noticias_salvas = carregar_json_data(SALVAS_JSON_PATH)
    modificada = False
    relevancia_final = 0
    for noticia in noticias_salvas:
        if noticia['link'] == link_noticia:
            if nova_relevancia_abs is not None:
                noticia['relevancia'] = nova_relevancia_abs
            elif delta_relevancia is not None:
                noticia['relevancia'] = noticia.get('relevancia', 0) + delta_relevancia
            noticia['relevancia'] = max(0, noticia['relevancia'])
            relevancia_final = noticia['relevancia']
            modificada = True
            break
    if modificada:
        salvar_json_data(SALVAS_JSON_PATH, noticias_salvas)
    return modificada, relevancia_final
# routes.py
from flask import Flask, render_template, redirect, url_for, jsonify, request
from datetime import datetime
import models # Importa o nosso módulo models

app = Flask(__name__) # A instância do Flask é criada aqui
app.secret_key = 'sua_chave_secreta_aqui_mvc' # Mantenha uma chave secreta

# Constantes de exibição que o controller usa
MAX_NOTICIAS_SALVAS_PARA_EXIBIR = 10
MAX_FEEDS_RECENTES_PARA_EXIBIR = 10

@app.route('/')
def pagina_inicial():
    categoria_ativa_req = request.args.get('categoria', models.CATEGORIA_PADRAO)
    if categoria_ativa_req not in models.CATEGORIAS_DISPONIVEIS:
        categoria_ativa_req = models.CATEGORIA_PADRAO

    # Notícias Salvas (todas, ordenadas e fatiadas pelo Model/Controller)
    noticias_salvas_todas = models.obter_noticias_salvas_todas()
    noticias_salvas_ordenadas = models.ordenar_noticias_por_relevancia(noticias_salvas_todas)
    noticias_salvas_para_exibir = noticias_salvas_ordenadas[:MAX_NOTICIAS_SALVAS_PARA_EXIBIR]
    
    # Notícias Coletadas dos Feeds (filtradas por categoria, ordenadas e fatiadas)
    feeds_recentes_todos = models.obter_feeds_recentes_todos()
    feeds_da_categoria_ativa = [n for n in feeds_recentes_todos if n.get('categoria') == categoria_ativa_req]
    feeds_da_categoria_ordenados = models.ordenar_noticias_feeds(feeds_da_categoria_ativa)
    feeds_para_exibir = feeds_da_categoria_ordenados[:MAX_FEEDS_RECENTES_PARA_EXIBIR]

    hora_atual_pagina = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    
    return render_template('index.html', 
                           categorias_disponiveis=models.CATEGORIAS_DISPONIVEIS,
                           categoria_ativa=categoria_ativa_req,
                           noticias_salvas=noticias_salvas_para_exibir, 
                           total_salvas_armazenadas=len(noticias_salvas_ordenadas),
                           noticias_feeds_recentes=feeds_para_exibir,
                           total_feeds_na_categoria=len(feeds_da_categoria_ordenados),
                           max_feeds_recentes_para_exibir=MAX_FEEDS_RECENTES_PARA_EXIBIR, # Passando para o template
                           atualizado_em=hora_atual_pagina)

@app.route('/refresh_feeds')
def rota_refresh_feeds_controller():
    models.buscar_e_processar_novidades_dos_feeds()
    categoria_para_retorno = request.args.get('categoria', models.CATEGORIA_PADRAO)
    return redirect(url_for('pagina_inicial', categoria=categoria_para_retorno))

@app.route('/salvar_noticia/<path:noticia_link>')
def rota_salvar_noticia_controller(noticia_link):
    categoria_origem, _ = models.salvar_nova_noticia(noticia_link)
    return redirect(url_for('pagina_inicial', categoria=categoria_origem or models.CATEGORIA_PADRAO))

@app.route('/delete_salva/<path:noticia_link>')
def rota_excluir_noticia_salva_controller(noticia_link):
    categoria_origem, _ = models.excluir_noticia_salva(noticia_link)
    return redirect(url_for('pagina_inicial', categoria=categoria_origem or models.CATEGORIA_PADRAO))

# Rotas AJAX para relevância
@app.route('/rank_up_salva/<path:noticia_link>', methods=['POST'])
def rota_aumentar_relevancia_controller(noticia_link):
    modificada, nova_relevancia = models.alterar_relevancia_salva(noticia_link, delta_relevancia=1)
    if modificada:
        return jsonify(success=True, link=noticia_link, nova_relevancia=nova_relevancia)
    return jsonify(success=False, link=noticia_link, message="Notícia não encontrada ou erro ao aumentar relevância.")

@app.route('/rank_down_salva/<path:noticia_link>', methods=['POST'])
def rota_diminuir_relevancia_controller(noticia_link):
    modificada, nova_relevancia = models.alterar_relevancia_salva(noticia_link, delta_relevancia=-1)
    if modificada:
        return jsonify(success=True, link=noticia_link, nova_relevancia=nova_relevancia)
    return jsonify(success=False, link=noticia_link, message="Notícia não encontrada ou erro ao diminuir relevância.")

@app.route('/reset_relevance_salva/<path:noticia_link>', methods=['POST'])
def rota_resetar_relevancia_controller(noticia_link):
    modificada, nova_relevancia = models.alterar_relevancia_salva(noticia_link, nova_relevancia_abs=0)
    if modificada:
        return jsonify(success=True, link=noticia_link, nova_relevancia=nova_relevancia)
    return jsonify(success=False, link=noticia_link, message="Notícia não encontrada ou erro ao resetar relevância.")
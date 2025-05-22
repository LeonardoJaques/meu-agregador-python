# Meu Agregador de Notícias Pessoal - Jornada de Aprendizado em Python e Web

## 🎯 Propósito Educacional do Projeto

Este projeto foi desenvolvido como um exercício prático e educacional com o objetivo principal de aprender e aplicar conceitos fundamentais de programação em Python, desenvolvimento web básico com Flask, e interatividade no front-end com JavaScript. A ideia central é construir, passo a passo, um agregador de notícias funcional, partindo de um script simples até uma aplicação web interativa.

Através da construção deste agregador, exploramos:

* A leitura e processamento de dados externos (feeds RSS).
* Manipulação de datas e horários.
* Armazenamento e recuperação de dados utilizando arquivos JSON.
* Criação de uma interface web local utilizando o microframework Flask.
* Renderização de HTML dinâmico com Jinja2 templates.
* Estilização básica com CSS.
* Adição de interatividade no lado do cliente com JavaScript puro, incluindo chamadas AJAX (Fetch API) para atualizações dinâmicas sem recarregamento total da página.
* Organização de funcionalidades em uma aplicação web, como rotas, views e manipulação de estado.
* Resolução de problemas e refatoração de código à medida que novas funcionalidades foram solicitadas.

Este repositório serve como um registro dessa jornada de aprendizado, demonstrando a evolução de um conceito simples para uma aplicação com múltiplas funcionalidades.

## ✨ Funcionalidades Desenvolvidas

Ao longo do projeto, implementamos as seguintes funcionalidades:

1.  **Coleta de Notícias:** Leitura de feeds RSS de diversas fontes.
2.  **Categorização:** Organização das notícias em abas por categorias (ex: Tecnologia, Quadrinhos, Economia).
3.  **Curadoria Pessoal:**
    * Exibição de notícias coletadas (não salvas) filtradas por categoria.
    * Botão para "Salvar" notícias de interesse.
    * Seção unificada para "Minhas Notícias Salvas", exibindo todas as notícias que o usuário escolheu guardar, com a indicação da sua categoria original através de uma tag.
4.  **Ranking de Relevância:**
    * Notícias salvas possuem um score de relevância.
    * Botões para aumentar, diminuir e zerar a relevância de notícias salvas.
    * As notícias salvas são exibidas ordenadas por relevância (e data como critério de desempate).
5.  **Atualização Dinâmica:** A alteração da relevância de uma notícia salva atualiza seu score na tela e reordena a lista visualmente *sem a necessidade de recarregar a página inteira*, utilizando JavaScript e AJAX.
6.  **Persistência de Dados:** As notícias salvas e as notícias coletadas temporariamente são armazenadas em arquivos JSON locais.
7.  **Interface Web Local:** A aplicação roda localmente e é acessível via navegador.
8.  **Limites de Exibição:** Tanto as notícias coletadas quanto as salvas têm um limite de exibição na tela (ex: as 10 mais recentes/relevantes).
9.  **Controle de Feeds:** Botão para "Atualizar Feeds" por categoria e limpeza automática das notícias coletadas (não salvas) ao iniciar o servidor.

## 🛠️ Tecnologias e Conceitos Abordados

* **Back-end:**
    * **Python 3:** Linguagem principal do projeto.
    * **Flask:** Microframework web para criar a aplicação e as APIs.
    * **Feedparser:** Biblioteca para ler e analisar feeds RSS.
    * **JSON:** Formato para armazenamento de dados.
    * **Manipulação de Datas/Horas:** Módulo `datetime` do Python.
* **Front-end:**
    * **HTML5:** Estrutura das páginas web.
    * **CSS3:** Estilização básica para a interface.
    * **JavaScript (ES6+):** Para interatividade no cliente, manipulação da DOM e chamadas AJAX (Fetch API).
* **Conceitos Gerais:**
    * Desenvolvimento Web Full-Stack (básico).
    * Criação de APIs RESTful simples.
    * Programação Orientada a Objetos (implícito na estrutura do Flask e manipulação de dados).
    * Manipulação da DOM.
    * Requisições assíncronas.
    * Controle de versão com Git (assumindo que está usando).
    * Estrutura de projeto para aplicações web pequenas.

## 🚀 Evolução do Projeto (Etapas de Aprendizado)

1.  **Script Inicial:** Um simples script Python para ler feeds e exibir no console.
2.  **Interface Web com Flask:** Transição para uma aplicação web local, servindo HTML.
3.  **Persistência:** Salvamento das notícias em arquivos JSON.
4.  **Interatividade Básica:** Adição de funcionalidades de ranking e exclusão com recarregamento da página.
5.  **Categorização e Abas:** Organização das notícias por temas com navegação por abas.
6.  **Atualizações Dinâmicas (AJAX):** Implementação de atualizações de relevância sem refresh total da página, utilizando JavaScript e a API Fetch.
7.  **Refinamentos de UX:** Melhorias na apresentação e no fluxo de interação do usuário.

## ⚙️ Como Executar o Projeto

1.  **Clone o repositório:**
    ```bash
    git clone [https://github.com/seu-usuario/nome-do-repositorio.git](https://github.com/seu-usuario/nome-do-repositorio.git)
    cd nome-do-repositorio
    ```
2.  **Crie um ambiente virtual (recomendado):**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # No Linux/macOS
    # venv\Scripts\activate   # No Windows
    ```
3.  **Instale as dependências:**
    ```bash
    pip install Flask feedparser
    ```
4.  **Execute a aplicação Flask:**
    ```bash
    python agregador_flask.py
    ```
5.  **Acesse no navegador:** Abra seu navegador e vá para `http://127.0.0.1:5000/`.

    *A pasta `data` será criada automaticamente para armazenar os arquivos JSON, assim como o arquivo `feeds_recentes.json` será limpo a cada inicialização.*

## 🌱 Próximos Passos (Sugestões para Continuar Aprendendo)

* Implementar um sistema de usuários para que diferentes pessoas possam ter suas próprias listas de notícias salvas.
* Utilizar um banco de dados (SQLite, PostgreSQL) em vez de arquivos JSON para persistência.
* Melhorar a interface do usuário com um framework CSS (Bootstrap, Tailwind CSS) ou mais CSS customizado.
* Adicionar funcionalidades de busca e filtragem avançada nas notícias salvas.
* Permitir que o usuário adicione/remova URLs de feeds RSS pela interface.
* Explorar frameworks JavaScript (Vue.js, React) para uma reatividade mais avançada no front-end.
* Fazer o deploy da aplicação em uma plataforma como Heroku, PythonAnywhere ou Vercel.

---

Este README foi elaborado com base na nossa conversa e na evolução do projeto. Sinta-se à vontade para adaptá-lo e adicionar mais detalhes conforme achar necessário!

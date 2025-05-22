# run.py
from routes import app  # Importa a instância 'app' do Flask de routes.py
import models          # Importa models para acessar a função de inicialização

if __name__ == '__main__':
    models.limpar_feeds_recentes_iniciais() # Limpa o JSON de feeds recentes ao iniciar
    app.run(host='0.0.0.0', port=5000, debug=True)
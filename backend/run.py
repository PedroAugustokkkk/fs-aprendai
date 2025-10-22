# /run.py

# Importa a função create_app que está dentro do pacote 'app'
from app import create_app

# Cria a instância do app chamando a fábrica
app = create_app()

# Este bloco só é executado se você rodar 'python run.py'
if __name__ == '__main__':
    # Roda o servidor de desenvolvimento do Flask
    # 'debug=True' faz o servidor reiniciar automaticamente
    # quando você salvar uma alteração no código.
    app.run(debug=True)
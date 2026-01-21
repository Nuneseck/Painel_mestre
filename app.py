from flask import Flask, render_template

def create_app():
    app = Flask(__name__)

    app.config['SECRET_KEY'] = 'uma-string-secreta-bem-aleatoria-98765'
    
    from geracao_tesouros.routes import tesouros_bp
    app.register_blueprint(tesouros_bp, url_prefix='/tesouros')
    
    from destino_npc.routes import destino_bp
    app.register_blueprint(destino_bp, url_prefix='/destino')
    
    from geracao_encontros.routes import encontros_bp
    app.register_blueprint(encontros_bp, url_prefix='/encontros')
    
    from geracao_hex.routes import hex_bp
    app.register_blueprint(hex_bp, url_prefix='/hex')
    
    from geracao_npcs.routes import npcs_bp
    app.register_blueprint(npcs_bp, url_prefix='/npcs')
    
    from geracao_eventos.routes import eventos_bp
    app.register_blueprint(eventos_bp, url_prefix='/eventos')

    from geracao_rumores.routes import rumores_bp
    app.register_blueprint(rumores_bp, url_prefix='/rumores')

    # Rota da página inicial
    @app.route('/')
    def index():
        """Renderiza o painel principal com links para as ferramentas."""
        tools = [
            {"url": "/destino", "name": "Destino NPC Mensal", "desc": "Gerencia o destino dos reinos e NPCs, integrando com Obsidian."},
            {"url": "/tesouros", "name": "Gerador de Tesouros", "desc": "Rola tesouros, riquezas, itens e poções por ND."},
            {"url": "/encontros", "name": "Geração de Encontros", "desc": "Cria eventos de encontros baseado em ND e tipo."},
            {"url": "/eventos", "name": "Geração de Eventos", "desc": "Gerador de eventos e acontecimentos durante viagens."},
            {"url": "/hex", "name": "Geração de Hex", "desc": "Ferramenta para criação e gerenciamento de hexcrawl."},
            {"url": "/npcs", "name": "Geração de NPCs", "desc": "Criação rápida de NPCs com nomes, traços e estatísticas."},
            {"url": "/rumores", "name": "Gerador de Rumores", "desc": "Cria rumores de taverna baseados no destino mensal dos reinos."},
            {"url": "https://www.omgm.rocks/shop", "name": "Gerador de Lojas", "desc": "Ferramenta web para gerar inventários de lojas."},
            {"url": "https://donjon.bin.sh/fantasy/demographics/", "name": "Gerador de Demografia", "desc": "Calcula a população e a composição de vilas e cidades."},
            {"url": "https://watabou.itch.io/medieval-fantasy-city-generator", "name": "Gerador de Cidades", "desc": "Gera mapas de cidades medievais fantásticas."}
        ]
        return render_template('index.html', tools=tools)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run()
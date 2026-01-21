from flask import Blueprint, render_template, request
import json
import random
import os

# 1. Cria o Blueprint e define o caminho base (bp_dir)
hex_bp = Blueprint('hex', __name__,
                   template_folder='templates',
                   static_folder='static')

# bp_dir é o caminho absoluto para a pasta 'geracao_hex'
bp_dir = os.path.abspath(os.path.dirname(__file__))

# 2. NOVA Função: Helper para criar caminhos absolutos a partir do blueprint
def get_bp_path(relative_path: str):
    """Cria um caminho absoluto a partir do diretório do blueprint."""
    return os.path.join(bp_dir, relative_path)

# ========== FUNÇÕES UTILITÁRIAS (Lógica original, mas usa 'file_path' absoluto) ==========

def select_by_weight(options: dict):
    """Seleciona uma chave de um dicionário com base em seus valores (pesos)."""
    if not isinstance(options, dict):
        print(f"Erro: 'select_by_weight' esperava um dicionário, mas recebeu {type(options)}")
        return "Opção Inválida"
    items = list(options.items()); total_weight = sum(item[1] for item in items)
    if total_weight == 0:
        if items: return random.choice([item[0] for item in items])
        else: return "Dicionário Vazio"
    r = random.uniform(0, total_weight); upto = 0
    for key, weight in items:
        if upto + weight >= r: return key
        upto += weight
    return items[-1][0] if items else "Dicionário Vazio" # Fallback

def roll_for_detail(file_path: str):
    """Carrega um arquivo JSON (caminho absoluto) e seleciona um item."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            details = json.load(f)
        return select_by_weight(details)
    except FileNotFoundError:
        print(f"AVISO: Arquivo não encontrado em '{file_path}'")
        return "Detalhe não encontrado (arquivo ausente)"
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Erro ao processar o arquivo JSON '{file_path}': {e}")
        return "Detalhe não encontrado (erro no JSON)"

def select_multiple(file_path: str, min_select: int = 1, max_select: int = 3):
    """Seleciona múltiplos itens de um arquivo JSON (caminho absoluto)."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            options = json.load(f)
        if isinstance(options, dict): options = list(options.keys())
        if not options: return ""
        num_to_select = random.randint(min_select, min(max_select, len(options)))
        selected = random.sample(options, num_to_select)
        return ", ".join(selected)
    except FileNotFoundError:
        print(f"AVISO: Arquivo não encontrado em '{file_path}'")
        return "Palavra-chave não encontrada"
    except Exception as e:
        print(f"Erro em 'select_multiple' com '{file_path}': {e}")
        return "Erro ao selecionar palavras-chave"


# ========== FUNÇÕES DE GERAÇÃO (Caminhos de arquivo corrigidos com get_bp_path) ==========

def load_hex_tables(terrain: str):
    """Carrega as tabelas sensoriais para um terreno."""
    tables = {}
    terrain_path = get_bp_path(os.path.join('encounters', 'hex', terrain))
    
    for table_name in ['paisagens', 'sons', 'odores', 'eventos']:
        file_path = os.path.join(terrain_path, f'{table_name}.json')
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tables[table_name] = json.load(f)
        except Exception as e:
            print(f"Erro ao carregar '{file_path}': {e}")
            tables[table_name] = {"Erro": f"Arquivo {table_name}.json não encontrado ou inválido"}
    return tables

def generate_assentamento(terrain: str):
    """Gera detalhes completos de um assentamento."""
    base_path = get_bp_path(os.path.join('encounters', 'hex', terrain, 'assentamentos'))
    ocupacao = roll_for_detail(os.path.join(base_path, 'ocupacao.json'))
    condicoes = roll_for_detail(os.path.join(base_path, 'condicoes.json'))
    tipo = roll_for_detail(os.path.join(base_path, 'tipos.json'))

    detalhes = f"Tipo: {tipo}<br>Ocupação: {ocupacao}<br>Condições: {condicoes}"
    
    if 'Ocupado' in ocupacao:
        ocupantes = roll_for_detail(os.path.join(base_path, 'ocupantes.json'))
        detalhes += f"<br>Ocupantes: {ocupantes}"
    else: 
        motivo_abandono = roll_for_detail(os.path.join(base_path, 'abandono.json'))
        detalhes += f"<br>Motivo do Abandono: {motivo_abandono}"
    return {'conteudo': f"Assentamento: {tipo}", 'detalhes': detalhes}

def generate_ruina(terrain: str):
    """Gera detalhes completos de uma ruína."""
    base_path = get_bp_path(os.path.join('encounters', 'hex', terrain, 'ruinas'))
    tipo_ruina = roll_for_detail(os.path.join(base_path, 'tipos.json'))
    ocupacao = roll_for_detail(os.path.join(base_path, 'ocupacao.json'))
    detalhes_dict = {
        "Tipo": tipo_ruina,
        "Propósito Original": roll_for_detail(os.path.join(base_path, 'proposito_original.json')),
        "Propósito Atual": roll_for_detail(os.path.join(base_path, 'proposito_atual.json')),
        "Localização": roll_for_detail(os.path.join(base_path, 'localizacao.json')),
        "Peculiaridade": roll_for_detail(os.path.join(base_path, 'peculiaridade.json')),
        "Idade": roll_for_detail(os.path.join(base_path, 'idade.json')),
        "Ocupação": ocupacao
    }
    if 'Ocupado' in ocupacao:
        detalhes_dict["Ocupantes"] = roll_for_detail(os.path.join(base_path, 'ocupantes.json'))
    detalhes_dict["Palavras-chave"] = select_multiple(os.path.join(base_path, 'palavras_chave.json'), 1, 3)
    detalhes = "<br>".join(f"<b>{key}:</b> {value}" for key, value in detalhes_dict.items() if value)
    return {'conteudo': f"Ruína: {tipo_ruina}", 'detalhes': detalhes}

def generate_obstaculo(terrain: str):
    """Gera detalhes completos de um obstáculo."""
    base_path = get_bp_path(os.path.join('encounters', 'hex', terrain, 'obstaculo'))
    categoria = roll_for_detail(os.path.join(base_path, 'categorias.json'))
    file_name = categoria.lower().replace("ç", "c").replace("ã", "a").replace(" ", "_") + ".json"
    obstaculo_especifico = roll_for_detail(os.path.join(base_path, file_name))
    detalhes = f"Categoria: {categoria}<br>Obstáculo: {obstaculo_especifico}"
    return {'conteudo': f"Obstáculo:", 'detalhes': detalhes, 'categoria': categoria}

def generate_marco_paisagem(terrain: str):
    """Gera detalhes completos de um marco na paisagem."""
    base_path = get_bp_path(os.path.join('encounters', 'hex', terrain, 'marcos_paisagem'))
    tipo_marco = roll_for_detail(os.path.join(base_path, 'tipos.json'))
    
    if "não encontrado" in tipo_marco:
        return {'conteudo': "Erro: Tipo de Marco inválido.", 'detalhes': f"Verifique 'tipos.json' em {base_path}"}
        
    marco_path = os.path.join(base_path, tipo_marco)
    detalhes_dict = {
        "Tipo": tipo_marco,
        "Entrada": roll_for_detail(os.path.join(marco_path, 'entrada.json')),
        "Peculiaridade Geral": roll_for_detail(os.path.join(base_path, 'peculiaridade.json'))
    }
    optional_files = {
        "Interior": "interior.json", "Peculiaridade Específica": "peculiaridade.json", "Habitantes": "habitantes.json"
    }
    for display_name, file_name in optional_files.items():
        file_path_to_check = os.path.join(marco_path, file_name)
        if os.path.exists(file_path_to_check):
            detalhes_dict[display_name] = roll_for_detail(file_path_to_check)
    
    detalhes_dict["Palavras-chave"] = select_multiple(os.path.join(base_path, 'palavras_chave.json'), 0, 3)
    detalhes = "<br>".join(f"<b>{key}:</b> {value}" for key, value in detalhes_dict.items() if value)
    return {'conteudo': f"Marco na Paisagem: {tipo_marco}", 'detalhes': detalhes}

def generate_hex_description(terrain: str):
    """Gera a descrição completa de um hexágono."""
    dist_path = get_bp_path(os.path.join('encounters', 'hex', 'distribuicao.json'))
    try:
        with open(dist_path, 'r', encoding='utf-8') as f:
            distribuicao = json.load(f).get(terrain, {})
    except Exception as e:
        print(f"Erro ao carregar 'distribuicao.json': {e}")
        return {'error': "Arquivo 'distribuicao.json' não encontrado ou inválido."}

    if not distribuicao:
        return {'error': f"Dados de distribuição não encontrados para '{terrain}'."}

    tipo_conteudo = select_by_weight(distribuicao)
    tabelas = load_hex_tables(terrain)

    resultado = {
        'terreno': terrain,
        'paisagem': select_by_weight(tabelas.get('paisagens', {})),
        'sons': select_by_weight(tabelas.get('sons', {})),
        'odores': select_by_weight(tabelas.get('odores', {})),
        'conteudo': "Não definido", 'detalhes': ""
    }

    if tipo_conteudo == 'paisagem_mundana':
        resultado['conteudo'] = "Paisagem Mundana"
        resultado['detalhes'] = "Nada de especial além da paisagem, sons e odores típicos do terreno."
    elif tipo_conteudo == 'assentamento':
        resultado.update(generate_assentamento(terrain))
    elif tipo_conteudo == 'ruina':
        resultado.update(generate_ruina(terrain))
    elif tipo_conteudo == 'obstaculo':
        resultado.update(generate_obstaculo(terrain))
    elif tipo_conteudo == 'marco_paisagem':
        resultado.update(generate_marco_paisagem(terrain))
    elif tipo_conteudo == 'evento':
        resultado['conteudo'] = "Evento Especial"
        resultado['detalhes'] = select_by_weight(tabelas.get('eventos', {}))
    elif tipo_conteudo == 'obstaculo_ruina':
        obstaculo_data = generate_obstaculo(terrain)
        ruina_data = generate_ruina(terrain)
        resultado['conteudo'] = f"Obstáculo e Ruína"
        resultado['detalhes'] = f"<b>Obstáculo:</b><br>{obstaculo_data['detalhes']}<br><br><b>Ruína:</b><br>{ruina_data['detalhes']}"
    
    return resultado

# ========== ROTAS FLASK (Convertidas para Blueprint) ==========

def get_terrains():
    """Carrega os tipos de terreno do JSON."""
    terrains_path = get_bp_path('tipos_terreno.json')
    try:
        with open(terrains_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Erro ao carregar 'tipos_terreno.json': {e}")
        return {'floresta': 'Floresta (Padrão)'} # Fallback

@hex_bp.route('/', methods=['GET'])
def hex_form():
    """Exibe o formulário para gerar um hexágono."""
    terrains = get_terrains()
    return render_template('hex.html', terrains=terrains)

# (em geracao_hex/routes.py)

@hex_bp.route('/generate', methods=['POST'])
def generate_hex():
    """Processa o formulário e exibe o resultado do hexágono gerado."""
    terreno_selecionado = request.form.get('terreno')
    hex_data = generate_hex_description(terreno_selecionado)
    terrains = get_terrains()
    
    # --- CORREÇÃO AQUI ---
    # Renderiza o novo nome do template
    return render_template('hex_results.html', hex=hex_data, terrains=terrains)
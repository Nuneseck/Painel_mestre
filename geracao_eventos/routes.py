from flask import Blueprint, render_template, request, jsonify, send_from_directory, session
import json
import random
import os
import datetime
from functools import lru_cache
from pathlib import Path
import sys
import re
from io import StringIO

# --- 1. CONFIGURAÇÃO DO BLUEPRINT ---
eventos_bp = Blueprint('eventos', __name__,
                       template_folder='templates',
                       static_folder='static')

# bp_dir é o caminho absoluto para a pasta 'geracao_eventos'
bp_dir = os.path.abspath(os.path.dirname(__file__))

# Tenta importar o gerador de equipamentos local
try:
    from .gerador_equipamentos import GeradorEquipamentos
except ImportError:
    print("AVISO: 'gerador_equipamentos.py' não encontrado em 'geracao_eventos/'. Rota /gerar-equipamentos irá falhar.")
    class GeradorEquipamentos: # Classe 'dummy' para evitar que o app quebre
        def __init__(self, base_path=None): # Adicionado base_path para compatibilidade
            print("ERRO: Classe GeradorEquipamentos não carregada.")
        def gerar_equipamentos(self, **kwargs): return {}
        def formatar_equipamento(self, item, escudo=None, arma_secundaria=None): return "Erro ao formatar"

# --- 2. FUNÇÃO HELPER DE CAMINHO ---
def get_bp_path(relative_path: str):
    """Cria um caminho absoluto a partir do diretório do blueprint."""
    return os.path.join(bp_dir, relative_path)

# ========== CONFIGURAÇÃO INICIAL (Caminhos corrigidos) ==========
def create_folder_structure():
    """Cria a estrutura de pastas necessária DENTRO de geracao_eventos"""
    base_terrains = ['floresta', 'deserto', 'cidade', 'planicie', 'costa']
    default_categories = {
        "Humanoide|humanoide/tipos.json": 12, "Animal|animal/tipos.json": 8,
        "Monstro|monstro/tipos.json": 6, "Construto|construto/tipos.json": 4,
        "Morto-vivo|morto-vivo/tipos.json": 3, "Espirito|espirito/tipos.json": 2,
        "Lefeu|lefeu/tipos.json": 1
    }

    for terrain in base_terrains:
        Path(get_bp_path(f'encounters/{terrain}/creatures')).mkdir(parents=True, exist_ok=True)
        Path(get_bp_path('encounters/caracteristicas')).mkdir(parents=True, exist_ok=True)
        
        categories_file = get_bp_path(f'encounters/{terrain}/creatures/categories.json')
        if not os.path.exists(categories_file):
            with open(categories_file, 'w', encoding='utf-8') as f:
                json.dump(default_categories, f, indent=2)
        
        creature_types = {
            'humanoide': ['tipos.json', 'condicoes.json', 'racas.json'],
            'animal': ['tipos.json', 'condicoes.json'],
            'monstro': ['tipos.json', 'condicoes.json'],
            'morto-vivo': ['tipos.json', 'condicoes.json'],
            'espirito': ['tipos.json', 'condicoes.json'],
            'construto': ['tipos.json', 'condicoes.json'],
            'lefeu': ['tipos.json', 'condicoes.json']
        }
        
        for folder, files in creature_types.items():
            Path(get_bp_path(f'encounters/{terrain}/creatures/{folder}')).mkdir(parents=True, exist_ok=True)
            for file in files:
                file_path = get_bp_path(f'encounters/{terrain}/creatures/{folder}/{file}')
                if not os.path.exists(file_path):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        if 'tipos' in file:
                            json.dump({f"Exemplo de tipo de {folder} 1": 1}, f, indent=2)
                        elif 'condicoes' in file:
                            json.dump({f"Exemplo de condição de {folder} 1": 1}, f, indent=2)
                        elif 'racas' in file and folder == 'humanoide':
                            json.dump({"Humano": 5, "Elfo": 3}, f, indent=2)

        for file in ['false_alarms.json', 'anomalies.json', 'temporary_obstacles.json', 'events.json']:
            file_path = get_bp_path(f'encounters/{terrain}/{file}')
            if not os.path.exists(file_path):
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump({"Exemplo": "Descrição do evento"}, f, indent=2)

create_folder_structure()

# ========== FUNÇÕES UTILITÁRIAS (Caminhos corrigidos) ==========

def select_by_weight(options):
    """Seleciona uma opção baseada em pesos, compatível com múltiplos formatos"""
    if isinstance(options, dict) and all(isinstance(v, (int, float)) for v in options.values()):
        # Formato "chave": peso
        items = list(options.items())
        descriptions = [item[0] for item in items]
        weights = [item[1] for item in items]
    elif isinstance(options, dict) and 'options' in options:
        # Formato { "options": [{"description": ..., "weight": ...}] }
        descriptions = [opt['description'] for opt in options['options']]
        weights = [opt['weight'] for opt in options['options']]
    elif isinstance(options, dict) and any('-' in k for k in options.keys()):
        # Formato "1-5": "descrição" (assume peso 1)
        descriptions = list(options.values())
        weights = [1] * len(descriptions)
    else:
        # Fallback para listas simples ou formatos não reconhecidos
        if isinstance(options, list):
            return random.choice(options) if options else "Indefinido"
        if isinstance(options, dict):
             return random.choice(list(options.keys())) if options else "Indefinido"
        print(f"Erro: Formato de 'options' não reconhecido: {options}")
        return "Indefinido"
    
    total = sum(weights)
    if total == 0:
        return random.choice(descriptions) if descriptions else "Indefinido"
    r = random.uniform(0, total)
    upto = 0
    for i, weight in enumerate(weights):
        if upto + weight >= r:
            return descriptions[i]
        upto += weight
    return descriptions[-1] # Fallback

def roll_for_detail(file_path):
    """Rola detalhes específicos, compatível com vários formatos"""
    try:
        # file_path JÁ DEVE ser absoluto
        with open(file_path, 'r', encoding='utf-8') as f:
            details = json.load(f)
        return select_by_weight(details)
    except Exception as e:
        print(f"Erro ao rolar detalhe em {file_path}: {str(e)}")
        return "Indefinido"

def roll_for_type_by_rarity(file_path, terrain):
    """Rola um tipo de criatura baseado em um sistema de raridade aninhado."""
    try:
        rarity_weights_path = get_bp_path(f'encounters/{terrain}/creatures/rarity_weights.json')
        with open(rarity_weights_path, 'r', encoding='utf-8') as f:
            rarity_weights = json.load(f)
        chosen_rarity = select_by_weight(rarity_weights)

        with open(file_path, 'r', encoding='utf-8') as f:
            types_by_rarity = json.load(f)

        creature_options = types_by_rarity.get(chosen_rarity)
        if not creature_options:
             creature_options = types_by_rarity.get("comum", {})
             if not creature_options:
                 # Fallback se 'comum' não existir, usa a primeira raridade disponível
                 creature_options = list(types_by_rarity.values())[0] if types_by_rarity else {}
                 if not creature_options:
                     return "Tipo Padrão (sem raridade definida)"
        return select_by_weight(creature_options)
    except Exception as e:
        print(f"Erro ao rolar tipo por raridade: {str(e)}")
        return "Indefinido (Erro de sistema)"

# ========== FUNÇÕES DE ROLAGEM DE DADOS (COPIADAS DO DESTINO_NPC) ==========
def _roll_match(match):
    """Função auxiliar interna para o dice parser."""
    full_text = match.group(0) # ex: "1d4-1"
    num_dice = int(match.group(1)) # ex: 1
    die_face = int(match.group(2)) # ex: 4
    operator = match.group(4) # ex: "-"
    modifier = int(match.group(5) or 0) # ex: 1
    
    roll_total = sum(random.randint(1, die_face) for _ in range(num_dice))
    
    final_total = roll_total
    if operator == '+':
        final_total = roll_total + modifier
    elif operator == '-':
        final_total = max(1, roll_total - modifier) # Garante que não seja menor que 1

    return f"{full_text} (rolado {final_total})"

def resolve_dice_in_string(text):
    """Encontra e rola todas as notações de dado (ex: "1d6", "1d4-1") em uma string."""
    pattern = r'(\d+)d(\d+)(([+-])(\d+))?'
    return re.sub(pattern, _roll_match, text)

# ========== FUNÇÕES DE DEBUG (Caminhos corrigidos) ==========
def calculate_theoretical_chance(categories, target_category):
    """Calcula a probabilidade teórica de uma categoria"""
    total = 0
    for range_str, data in categories.items():
        if data['category'] == target_category:
            if '-' in range_str:
                min_val, max_val = map(int, range_str.split('-'))
                total += (max_val - min_val + 1)
            else:
                total += 1
    return total / 20

def debug_category_probabilities(terrain='floresta', samples=100000):
    """Analisa as probabilidades reais de encontro por categoria"""
    try:
        with open(get_bp_path(f'encounters/{terrain}/creatures/categories.json'), 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
        
        # ... (Sua lógica de debug original) ...
        print(f"<br>=== DEBUG DE PROBABILIDADES ({terrain.upper()}) ===")
        return {}
    except Exception as e:
        print(f"Erro no debug: {str(e)}"); return {}

def debug_encounter_types(terrain='floresta', samples=10000):
    """Analisa a distribuição dos tipos de encontro"""
    try:
        with open(get_bp_path('tipos_encontro.json'), 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # ... (Sua lógica de debug original) ...
        print(f"<br>=== DEBUG DE TIPOS DE ENCONTRO ({terrain.upper()}) ===")
        return {}
    except Exception as e:
        print(f"Erro no debug: {str(e)}"); return {}

# ========== FUNÇÕES PRINCIPAIS (Caminhos corrigidos) ==========
def load_terrain_encounters(terrain):
    """Carrega eventos específicos do terreno"""
    return {
        'false_alarms': json.load(open(get_bp_path(f'encounters/{terrain}/false_alarms.json'), encoding='utf-8')),
        'anomalies': json.load(open(get_bp_path(f'encounters/{terrain}/anomalies.json'), encoding='utf-8')),
        'temporary_obstacles': json.load(open(get_bp_path(f'encounters/{terrain}/temporary_obstacles.json'), encoding='utf-8')),
        'events': json.load(open(get_bp_path(f'encounters/{terrain}/events.json'), encoding='utf-8'))
    }

def generate_creature(terrain):
    """Gera uma criatura com tipo e características"""
    try:
        with open(get_bp_path(f'encounters/{terrain}/creatures/categories.json'), 'r', encoding='utf-8') as f:
            categories_data = json.load(f)
        
        if isinstance(categories_data, dict) and all('|' in key for key in categories_data.keys()):
            selected = select_by_weight(categories_data)
            category, file_path = selected.split('|')
            category_data = {'category': category.strip(), 'file': file_path.strip()}
        elif isinstance(categories_data, dict):
            roll = random.randint(1, 20); category_data = None
            for range_str, data in categories_data.items():
                if '-' in range_str:
                    min_val, max_val = map(int, range_str.split('-'))
                    if min_val <= roll <= max_val: category_data = data; break
                elif int(range_str) == roll: category_data = data; break
        else:
            return {'descricao': "Criatura desconhecida (formato categories.json inválido)", 'tipo': None}

        if not category_data:
            return {'descricao': "Criatura desconhecida (rolagem fora da faixa)", 'tipo': None}

        folder_name = category_data['category'].lower().replace('í', 'i').replace(' ', '-')
        base_path = get_bp_path(f'encounters/{terrain}/creatures/{folder_name}/')
        
        tipos_file_path = os.path.join(base_path, 'tipos.json')
        tipo = roll_for_type_by_rarity(tipos_file_path, terrain)
        
        condicao = roll_for_detail(os.path.join(base_path, 'condicoes.json'))
        
        if category_data['category'].lower() == 'humanoide':
            raca = roll_for_detail(os.path.join(base_path, 'racas.json'))
            return {'descricao': f"Humanoide - {tipo} ({condicao}, {raca})", 'tipo': 'humanoide'}
        
        return {'descricao': f"{category_data['category']} - {tipo} ({condicao})", 'tipo': folder_name}

    except Exception as e:
        print(f"Erro ao gerar criatura: {str(e)}")
        return {'descricao': "Criatura indefinida (erro)", 'tipo': None}

def generate_single_encounter(is_night, terrain, encounter_type=None):
    """Gera um encontro completo com probabilidades por terreno"""
    try:
        encounters = load_terrain_encounters(terrain)
        type_names = {
            'false_alarm': 'Alarme falso', 'creatures': 'Criaturas', 'anomaly': 'Anomalia',
            'creatures_anomaly': 'Criaturas + Anomalia', 'temporary_obstacle': 'Obstáculo temporário',
            'obstacle_creatures': 'Obstáculo + Criaturas', 'event': 'Evento especial',
            'double_roll': 'Evento duplo'
        }

        if not encounter_type:
            with open(get_bp_path('tipos_encontro.json'), 'r', encoding='utf-8') as f:
                config = json.load(f)
            terrain_config = config.get(terrain, {})
            
            if isinstance(terrain_config, dict) and all(isinstance(v, (int, float)) for v in terrain_config.values()):
                encounter_type = select_by_weight(terrain_config)
            else: # Fallback para o seu formato antigo de 1-20
                roll = random.randint(1, 20)
                for encounter, range_values in terrain_config.items():
                    if isinstance(range_values, list) and len(range_values) == 2:
                        if range_values[0] <= roll <= range_values[1]:
                            encounter_type = encounter; break
                    elif isinstance(range_values, int) and roll == range_values:
                        encounter_type = encounter; break

        if not encounter_type:
            return {'description': "Encontro indefinido", 'time_roll': random.randint(1, 20), 'encounter_data': None}

        # --- Bloco de Geração de Descrição ---
        description = "Tipo de encontro desconhecido"
        encounter_data_out = None

        if encounter_type == 'false_alarm':
            options = encounters['false_alarms']; chosen = select_by_weight(options)
            description = f"{type_names['false_alarm']}: {chosen}"
        elif encounter_type == 'creatures':
            creature_data = generate_creature(terrain)
            description = f"{type_names['creatures']}: {creature_data['descricao']}"
            encounter_data_out = {'tipo': creature_data['tipo']}
        elif encounter_type == 'anomaly':
            options = encounters['anomalies']; chosen = select_by_weight(options)
            description = f"{type_names['anomaly']}: {chosen}"
        elif encounter_type == 'creatures_anomaly':
            creature_data = generate_creature(terrain); anomaly = select_by_weight(encounters['anomalies'])
            description = f"{type_names['creatures_anomaly']}: {creature_data['descricao']} e {anomaly}"
            encounter_data_out = {'tipo': creature_data['tipo']}
        elif encounter_type == 'temporary_obstacle':
            options = encounters['temporary_obstacles']; chosen = select_by_weight(options)
            description = f"{type_names['temporary_obstacle']}: {chosen}"
        elif encounter_type == 'obstacle_creatures':
            obstacle = select_by_weight(encounters['temporary_obstacles']); creature_data = generate_creature(terrain)
            description = f"{type_names['obstacle_creatures']}: {obstacle} e {creature_data['descricao']}"
            encounter_data_out = {'tipo': creature_data['tipo']}
        elif encounter_type == 'event':
            options = encounters['events']; chosen = select_by_weight(options)
            description = f"{type_names['event']}: {chosen}"
        elif encounter_type == 'double_roll':
            first = generate_single_encounter(is_night, terrain); second = generate_single_encounter(is_night, terrain)
            if not first or not second:
                description = "Evento duplo falhou"
            else:
                first_desc = first['description'].split(": ", 1)[-1]; second_desc = second['description'].split(": ", 1)[-1]
                description = f"Evento duplo: {first_desc} e também {second_desc}"
        
        # --- ATUALIZAÇÃO AQUI ---
        # Rola quaisquer dados (ex: "2d4 bandidos") na string de descrição final
        resolved_description = resolve_dice_in_string(description)
        
        return {
            'description': resolved_description, # Retorna a descrição com os dados rolados
            'time_roll': random.randint(1, 20),
            'encounter_data': encounter_data_out
        }

    except Exception as e:
        print(f"Erro ao gerar encontro: {str(e)}")
        return {'description': "Erro no sistema", 'time_roll': random.randint(1, 20), 'encounter_data': None}

def save_to_txt(results, terrain, days, is_night):
    """Salva os resultados em arquivo TXT na pasta 'logs' do blueprint"""
    try:
        log_dir = get_bp_path('logs')
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"viagem_{terrain}_{timestamp}.txt"
        full_path = os.path.join(log_dir, filename)
        
        content = f"=== Relatório de Viagem ===\n"
        content += f"Terreno: {terrain}\nDias: {days}\nPeríodo: {'noite' if is_night else 'dia'}\n\n"
        for r in results:
            content += f"Dia {r['day']}: "
            content += f"{r['encounter']} ({r['time_of_day']})\n" if r['encounter'] else "Sem eventos\n"
        
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"logs/{filename}" # Retorna o caminho *relativo*
    except Exception as e:
        print(f"Erro ao salvar TXT: {str(e)}"); return None

@lru_cache(maxsize=8)
def load_characteristics_file(tipo: str) -> dict:
    """Carrega arquivos de características com cache"""
    arquivos = {
        'humanoide': 'humanoide.json', 'animal': 'animal.json', 'monstro': 'monstro.json',
        'espirito': 'espirito.json', 'morto-vivo': 'mortos_vivo.json',
        'lefeu': 'lefeu.json', 'construto': 'construto.json'
    }
    arquivo = arquivos.get(tipo)
    if not arquivo: raise ValueError(f"Tipo {tipo} não suportado")
    
    caminho = get_bp_path(os.path.join('encounters', 'caracteristicas', arquivo))
    if not os.path.exists(caminho):
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
    
    with open(caminho, 'r', encoding='utf-8') as f:
        return json.load(f)

# ========== ROTAS PRINCIPAIS (Convertidas para Blueprint) ==========
@eventos_bp.route('/')
def index():
    terrains = json.load(open(get_bp_path('tipos_terreno.json'), encoding='utf-8'))
    return render_template('eventos.html', terrains=terrains)

@eventos_bp.route('/generate', methods=['POST', 'GET'])
def generate():
    terrains = json.load(open(get_bp_path('tipos_terreno.json'), encoding='utf-8'))
    
    if request.method == 'POST':
        terrain = request.form['terrain']; days = int(request.form['days'])
        is_night = request.form.get('time') == 'night'
        session['viagem_params'] = {'terrain': terrain, 'days': days, 'is_night': is_night}
    else:
        params = session.get('viagem_params', {})
        terrain = params.get('terrain', 'floresta'); days = params.get('days', 1)
        is_night = params.get('is_night', False)
    
    with open(get_bp_path('chance_encontro.json'), 'r', encoding='utf-8') as f:
        chances_data = json.load(f)

    periodo = "noite" if is_night else "dia"
    default_chance = 8 
    encounter_chance = chances_data.get(terrain, {}).get(periodo, default_chance)

    results = []
    for day in range(1, days + 1):
        peso_encontro = encounter_chance
        peso_sem_encontro = max(0, 100 - peso_encontro)
        opcoes_de_evento = {"encontro": peso_encontro, "sem_encontro": peso_sem_encontro}
        resultado_do_dia = select_by_weight(opcoes_de_evento)

        if resultado_do_dia == "encontro":
            encounter_data = generate_single_encounter(is_night, terrain)
            horarios = json.load(open(get_bp_path('horario.json'), encoding='utf-8'))
            time_of_day = None
            for time, time_range in horarios.items():
                if isinstance(time_range, list):
                    if time_range[0] <= encounter_data['time_roll'] <= time_range[1]:
                        time_of_day = time; break
                elif time_range == encounter_data['time_roll']:
                    time_of_day = time; break
            
            results.append({
                'day': day, 'encounter': encounter_data['description'],
                'time_of_day': time_of_day, 'encounter_data': encounter_data['encounter_data']
            })
        else: # sem_encontro
            results.append({
                'day': day, 'encounter': None, 'time_of_day': None, 'encounter_data': None
            })
    
    txt_file = save_to_txt(results, terrains.get(terrain, terrain), days, is_night)
    caracteristicas_qtd = request.args.get('qtd_carac', default=1, type=int)
    
    return render_template('eventos_results.html',
                           results=results,
                           terrain=terrains.get(terrain, terrain),
                           days=days,
                           txt_file=txt_file,
                           qtd_caracteristicas=caracteristicas_qtd)

@eventos_bp.route('/gerar-caracteristicas/<tipo>')
def gerar_caracteristicas(tipo):
    """Gera múltiplas características para o tipo especificado"""
    try:
        qtd = request.args.get('qtd', default=1, type=int)
        caracteristicas = load_characteristics_file(tipo)
        qtd = min(qtd, len(caracteristicas)); resultados = []
        chaves = list(caracteristicas.keys())
        
        for _ in range(qtd):
            if not chaves: break
            chave = random.choice(chaves)
            resultados.append({'caracteristica': chave, 'efeito': caracteristicas[chave]})
            chaves.remove(chave)
        return jsonify(resultados)
    except Exception as e:
        print(f"Erro ao gerar características: {str(e)}")
        return jsonify({'error': str(e)}), 400
    
@eventos_bp.route('/gerar-equipamentos')
def gerar_equipamentos_route():
    """Gera armas e armaduras usando o GeradorEquipamentos."""
    try:
        qtd_armas = request.args.get('qtd_armas', default=0, type=int)
        qtd_armaduras = request.args.get('qtd_armaduras', default=0, type=int)
        
        # A importação de GeradorEquipamentos está no topo do arquivo
        # Passa o caminho base do blueprint para o gerador
        gerador = GeradorEquipamentos(base_path=bp_dir) 

        equipamentos = gerador.gerar_equipamentos(qtd_armas=qtd_armas, qtd_armaduras=qtd_armaduras)

        armaduras_formatadas = []
        for armadura in equipamentos.get("armaduras", []):
            armaduras_formatadas.append(gerador.formatar_equipamento(armadura))

        armas_formatadas = []
        for arma_primaria in equipamentos.get("armas_primarias", []):
            nome_arma = arma_primaria.get('nome', '')
            escudo = equipamentos["armas_com_escudos"].get(nome_arma)
            arma_secundaria = equipamentos["armas_duplas"].get(nome_arma)
            armas_formatadas.append(gerador.formatar_equipamento(arma_primaria, escudo, arma_secundaria))
            
        return jsonify({'armaduras': armaduras_formatadas, 'armas': armas_formatadas})
    except NameError:
         return jsonify({'error': "'gerador_equipamentos.py' não foi encontrado ou falhou ao carregar."}), 500
    except FileNotFoundError as e:
        # Pega o nome do arquivo que faltou, se disponível
        fnf_error = str(e)
        if 'equipamentos.json' in fnf_error:
             return jsonify({'error': "Arquivo 'equipamentos.json' não encontrado. Verifique a pasta 'geracao_eventos'."}), 500
        return jsonify({'error': fnf_error}), 500
    except Exception as e:
        print(f"Erro ao gerar equipamentos: {str(e)}")
        return jsonify({'error': str(e)}), 400

@eventos_bp.route('/limpar-cache')
def limpar_cache():
    load_characteristics_file.cache_clear()
    return jsonify({'status': 'Cache de características limpo'})

@eventos_bp.route('/logs/<filename>')
def serve_log(filename):
    # Serve arquivos do diretório de logs do blueprint
    return send_from_directory(get_bp_path('logs'), filename)

# ========== ROTAS DE DEBUG (Convertidas para Blueprint) ==========
@eventos_bp.route('/debug/probabilidades/<terrain>')
def debug_probabilidades_route(terrain):
    old_stdout = sys.stdout; sys.stdout = buffer = StringIO()
    debug_category_probabilities(terrain)
    sys.stdout = old_stdout
    return f"<pre>{buffer.getvalue()}</pre>"

@eventos_bp.route('/debug/eventos/<terrain>')
def debug_eventos_route(terrain):
    old_stdout = sys.stdout; sys.stdout = buffer = StringIO()
    debug_encounter_types(terrain)
    sys.stdout = old_stdout
    return f"<pre>{buffer.getvalue()}</pre>"

@eventos_bp.route('/debug/all')
def debug_all():
    results = []; terrains = ['floresta', 'deserto', 'cidade', 'planicie', 'costa']
    for terrain in terrains:
        old_stdout = sys.stdout; sys.stdout = buffer = StringIO()
        debug_category_probabilities(terrain, samples=5000)
        sys.stdout = old_stdout
        results.append(f"<h2>{terrain.upper()}</h2><pre>{buffer.getvalue()}</pre>")
        
        old_stdout = sys.stdout; sys.stdout = buffer = StringIO()
        debug_encounter_types(terrain, samples=5000)
        sys.stdout = old_stdout
        results.append(f"<pre>{buffer.getvalue()}</pre><hr>")
    return ''.join(results)
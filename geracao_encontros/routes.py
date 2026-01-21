import os
import json
import random
import math
from flask import Blueprint, render_template, request, jsonify

# 1. Cria o Blueprint
encontros_bp = Blueprint('encontros', __name__,
                        template_folder='templates',
                        static_folder='static')

# 2. Define o caminho base
bp_dir = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(bp_dir, 'data') # Caminho para a pasta 'data'

# 3. Funções de Carregamento de Dados
def load_monsters(allowed_types, allowed_origins, min_creature_nd, max_creature_nd):
    """Carrega todos os encontros dos arquivos JSON permiatidos."""
    all_monsters = []
    
    if not allowed_types or not allowed_origins:
        return []

    for type_name in allowed_types:
        filepath = os.path.join(DATA_DIR, f"{type_name}.json") # Usa o DATA_DIR
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for source_book, monsters in data.items():
                    if source_book in allowed_origins:
                        for monster in monsters:
                            monster['origem'] = source_book
                            monster['categoria'] = type_name
                            if min_creature_nd <= monster['nd'] <= max_creature_nd:
                                all_monsters.append(monster)
        except FileNotFoundError:
            print(f"Aviso: Arquivo {filepath} não encontrado.")
        except json.JSONDecodeError:
            print(f"Aviso: Erro ao decodificar {filepath}.")
            
    return all_monsters

# 4. Rotas (mudam de @app.route para @encontros_bp.route)
@encontros_bp.route('/')
def index():
    """Renderiza a página inicial do gerador de encontros."""
    available_types = []
    available_origins = set() 
    # ... (lógica para carregar tipos e origens) ...
    try:
        all_files = [f for f in os.listdir(DATA_DIR) if f.endswith('.json')]
        available_types = [f.replace('.json', '') for f in all_files]
        for filename in all_files:
            filepath = os.path.join(DATA_DIR, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    available_origins.update(data.keys())
            except json.JSONDecodeError:
                print(f"Erro ao ler origens de {filename}")
    except FileNotFoundError:
        pass 
        
    # CORREÇÃO: Renderiza o template com nome único
    return render_template(
        'encontros.html', 
        available_types=sorted(available_types),
        available_origins=sorted(list(available_origins))
    )

@encontros_bp.route('/gerar_encontro', methods=['POST'])
def gerar_encontro_route():
    """Rota da API para gerar o encontro."""
    try:
        data = request.json
        
        target_nd = float(data.get('target_nd', 1))
        min_creature_nd = float(data.get('min_creature_nd', 0.25))
        max_creature_nd = float(data.get('max_creature_nd', 20))
        min_creatures = int(data.get('min_creatures', 1))
        max_creatures = int(data.get('max_creatures', 10))
        allowed_types = data.get('allowed_types', [])
        allowed_origins = data.get('allowed_origins', [])
        composition = data.get('composition', 'varias solo + lacaios')
        
        if not allowed_types:
            return jsonify({'error': 'Selecione ao menos um tipo de criatura.'}), 400
        if not allowed_origins:
            return jsonify({'error': 'Selecione ao menos uma origem.'}), 400
        if min_creatures > max_creatures:
            return jsonify({'error': 'Quantidade mínima deve ser menor ou igual à máxima.'}), 400
        if min_creature_nd > max_creature_nd:
            return jsonify({'error': 'ND Mínimo deve ser menor ou igual ao ND Máximo.'}), 400

        encounter, error = generate_encounter_logic(
            target_nd, min_creature_nd, max_creature_nd, min_creatures, max_creatures, 
            allowed_types, allowed_origins, composition
        )
        
        if error:
            return jsonify({'error': error}), 400
        
        final_nd = calculate_nd_different(encounter)
        
        return jsonify({
            'encontro': encounter,
            'nd_calculado': final_nd,
            'target_nd': target_nd,
            'contagem_criaturas': len(encounter)
        })

    except Exception as e:
        return jsonify({'error': f'Erro interno no servidor: {str(e)}'}), 500

# 5. Toda a lógica de geração (sem mudanças, apenas colada abaixo)
# (calculate_nd_same, calculate_nd_different, generate_encounter_logic)

def calculate_nd_same(creature_nd, quantity):
    if quantity == 0: return 0
    if quantity == 1: return creature_nd
    if creature_nd < 1: return creature_nd * quantity
    else: return creature_nd + 2 * math.log2(quantity)

def calculate_nd_different(monster_list):
    if not monster_list: return 0
    first_nd = monster_list[0]['nd']
    all_same_nd_value = all(monster['nd'] == first_nd for monster in monster_list)
        
    if all_same_nd_value:
        return calculate_nd_same(first_nd, len(monster_list))
    else:
        groups = {}
        for monster in monster_list:
            nd = monster['nd']
            if nd not in groups: groups[nd] = []
            groups[nd].append(monster)
        
        group_nd_list = [calculate_nd_same(nd_value, len(monsters_in_group)) for nd_value, monsters_in_group in groups.items()]
        
        if len(group_nd_list) == 1:
            return math.floor(group_nd_list[0])
            
        sorted_group_nds = sorted(group_nd_list, reverse=True)
        nd_base = sorted_group_nds[0]; encounter_nd = nd_base
        
        for other_group_nd in sorted_group_nds[1:]:
            nd_diff = nd_base - other_group_nd
            if nd_diff <= 1: encounter_nd += 1
            elif 1 < nd_diff <= 2: encounter_nd += 0.5
            elif 2 < nd_diff <= 3: encounter_nd += 0.25
        return math.floor(encounter_nd)

def generate_encounter_logic(target_nd, min_creature_nd, max_creature_nd, min_creatures, max_creatures, allowed_types, allowed_origins, composition):
    all_monsters = load_monsters(allowed_types, allowed_origins, min_creature_nd, max_creature_nd)
    if not all_monsters: return None, "Nenhuma criatura encontrada com os filtros."
    
    solos = [m for m in all_monsters if m['tipo'] == 'solo']
    lacaios = [m for m in all_monsters if m['tipo'] == 'lacaio']
    base_pool = []; filler_pool = []

    if composition == "1 solo + lacaios":
        if not solos: return None, "Nenhuma criatura 'solo' encontrada."
        base_pool = solos; filler_pool = lacaios
        if not filler_pool: filler_pool = solos
    elif composition == "somente lacaios":
        if not lacaios: return None, "Nenhuma criatura 'lacaio' encontrada."
        base_pool = lacaios; filler_pool = lacaios
    else: base_pool = solos + lacaios; filler_pool = solos + lacaios
    
    if not base_pool: return None, "Nenhuma criatura 'base' disponível."
    if not filler_pool: filler_pool = base_pool

    MAX_ATTEMPTS = 500
    best_encounter = None; best_encounter_score = float('inf')

    for _ in range(MAX_ATTEMPTS):
        encounter = []
        valid_base_monsters = [m for m in base_pool if m['nd'] <= target_nd]
        if not valid_base_monsters: valid_base_monsters = [min(base_pool, key=lambda m: m['nd'])]
        if not valid_base_monsters: continue
        
        base_monster = random.choice(valid_base_monsters)
        encounter = [base_monster]
        
        while len(encounter) < max_creatures:
            current_nd = calculate_nd_different(encounter)
            if current_nd > target_nd + 1.0: break
            if current_nd == target_nd and len(encounter) >= min_creatures: break

            best_candidate = None; best_score = float('inf')
            add_bodies_mode = (abs(current_nd - target_nd) <= 0.5) and (len(encounter) < min_creatures)

            for m_to_add in filler_pool:
                temp_encounter = encounter + [m_to_add]
                new_nd = calculate_nd_different(temp_encounter)
                
                if new_nd > target_nd + 1.0: continue
                
                if add_bodies_mode:
                    score = m_to_add['nd']
                    if new_nd > current_nd + 0.5: continue
                    if score < best_score: best_score = score; best_candidate = m_to_add
                else:
                    score = abs(new_nd - target_nd)
                    if new_nd < current_nd: score += 10
                    if score < best_score:
                        best_score = score; best_candidate = m_to_add
                    elif score == best_score:
                        if best_candidate is None or m_to_add['nd'] > best_candidate['nd']:
                            best_candidate = m_to_add
            
            if best_candidate: encounter.append(best_candidate)
            else: break
        
        final_nd = calculate_nd_different(encounter); final_count = len(encounter)
        
        if (abs(final_nd - target_nd) <= 1.0) and (min_creatures <= final_count <= max_creatures):
            current_score = abs(final_nd - target_nd)
            if current_score < best_encounter_score:
                best_encounter_score = current_score
                best_encounter = encounter
            if best_encounter_score == 0: break

    if best_encounter: return best_encounter, None
    return None, f"Não foi possível gerar um encontro com ND {target_nd} (Min {min_creatures}/Max {max_creatures} criaturas) após {MAX_ATTEMPTS} tentativas."
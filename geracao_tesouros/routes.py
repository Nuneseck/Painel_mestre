import os
import json
import random
import re
import math
from flask import Blueprint, render_template, request, jsonify

# 1. Cria o Blueprint
tesouros_bp = Blueprint('tesouros', __name__,
                        template_folder='templates',
                        static_folder='static') # Adicione esta linha

# 2. Define o caminho base para este blueprint
bp_dir = os.path.abspath(os.path.dirname(__file__))

# 3. Funções de Carregamento de Dados (agora usam o caminho do blueprint)
def load_data(filename):
    """Carrega um arquivo JSON relativo a este blueprint."""
    filepath = os.path.join(bp_dir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ERRO: Não foi possível carregar {filepath}: {e}")
        return {}

ALL_NDS = load_data("nds.json")
ALL_RIQUEZAS = load_data("riquezas.json")
ALL_DIVERSOS = load_data("diversos.json")
ALL_EQUIPAMENTOS = load_data("equipamentos.json")
ALL_SUPERIORES = load_data("superiores.json")
ALL_POCOES = load_data("pocoes.json")


# 4. Rotas (mudam de @app.route para @tesouros_bp.route)
@tesouros_bp.route('/')
def index():
    """Renderiza a página inicial do rolador de tesouros."""
    if not ALL_NDS:
        return "ERRO: nds.json não carregado.", 500
    nd_levels = sorted(
        ALL_NDS.keys(), 
        key=lambda x: float(x.replace("nd ", ""))
    )
    # CORREÇÃO: Renderiza o template com nome único
    return render_template('tesouros.html', nd_levels=nd_levels)

@tesouros_bp.route('/rolar_tesouro', methods=['POST'])
def rolar_tesouro():
    """Executa a rolagem ponderada para Dinheiro E Itens."""
    try:
        data = request.json
        nd_key = data.get('nd')
        treasure_type = data.get('treasure_type', 'padrao')
        
        if nd_key not in ALL_NDS:
            return jsonify({'error': f'ND "{nd_key}" não encontrado no JSON.'}), 404
            
        nd_tables = ALL_NDS[nd_key]

        num_rolls = 2 if treasure_type == 'dobro' else 1
        
        all_dinheiro_results = []
        all_item_results = []
        all_dinheiro_tabela_rolls = []
        all_item_tabela_rolls = []
        all_d100_dinheiro_rolls = []
        all_d100_item_rolls = []

        for _ in range(num_rolls):
            dinheiro_table = nd_tables.get("Dinheiro", {})
            if not dinheiro_table:
                return jsonify({'error': f'Tabela "Dinheiro" não encontrada para {nd_key}.'}), 404
            
            rolled_dinheiro_str, d100_dinheiro = get_weighted_roll_d100(dinheiro_table, 0)
            all_dinheiro_tabela_rolls.append(rolled_dinheiro_str)
            all_d100_dinheiro_rolls.append(d100_dinheiro)
            
            dinheiro_results_list = resolve_treasure_roll(rolled_dinheiro_str, treasure_type)
            all_dinheiro_results.extend(dinheiro_results_list)

            itens_table = nd_tables.get("Itens", {})
            if not itens_table:
                return jsonify({'error': f'Tabela "Itens" não encontrada para {nd_key}.'}), 404

            rolled_item_str, d100_item = get_weighted_roll_d100(itens_table, 0)
            all_item_tabela_rolls.append(rolled_item_str)
            all_d100_item_rolls.append(d100_item)
            
            item_results_list = resolve_treasure_roll(rolled_item_str, "padrao")
            all_item_results.extend(item_results_list)
        
        return jsonify({
            'nd': nd_key,
            'dinheiro_tabela_roll': ", ".join(all_dinheiro_tabela_rolls),
            'item_tabela_roll': ", ".join(all_item_tabela_rolls),
            'dinheiro_results': all_dinheiro_results,
            'item_results': all_item_results,
            'd100_dinheiro_rolls': all_d100_dinheiro_rolls,
            'd100_item_rolls': all_d100_item_rolls
        })
        
    except Exception as e:
        print(f"Erro na rota /rolar_tesouro: {e}")
        return jsonify({'error': f'Erro interno do servidor: {str(e)}'}), 500

# 5. Toda a lógica de rolagem (sem mudanças, apenas colada abaixo)
# (get_weighted_roll_d100, roll_dice_string, roll_material_especial, etc.)

def get_weighted_roll_d100(table, bonus_pct=0):
    if not table: return None, "(Tabela vazia)"
    roll = random.randint(1, 100); roll_with_bonus = roll + bonus_pct
    if roll_with_bonus > 100: roll_with_bonus = 100
    d100_details_str = f"(d100: {roll}"
    if bonus_pct > 0: d100_details_str += f" + {bonus_pct} = {roll_with_bonus}"
    d100_details_str += ")"
    current_pct = 0
    for item_key, weight in table.items():
        current_pct += weight
        if roll_with_bonus <= current_pct:
            return item_key, d100_details_str
    return list(table.keys())[-1], d100_details_str

def roll_dice_string(dice_str):
    dice_str = str(dice_str).strip()
    match = re.match(r'(\d+)d(\d+)(?:([+x])(\d+))?', dice_str, re.IGNORECASE)
    if not match:
        try: return int(dice_str), f"({dice_str})"
        except ValueError: return 0, "(String de dado inválida)"
    num_dice = int(match.group(1)); die_face = int(match.group(2))
    operator = match.group(3); modifier = int(match.group(4) or 0)
    roll_total = sum(random.randint(1, die_face) for _ in range(num_dice))
    final_total = roll_total; details = f"(Rolagem: {roll_total} no {num_dice}d{die_face})"
    if operator == '+': final_total = roll_total + modifier; details = f"(Rolagem: {roll_total} + {modifier})"
    elif operator == 'x': final_total = roll_total * modifier; details = f"(Rolagem: {roll_total} x {modifier})"
    return final_total, details

def roll_material_especial():
    roll = random.randint(1, 6)
    materiais = {1: "Aço-rubi", 2: "Adamante", 3: "Gelo eterno", 4: "Madeira Tollon", 5: "Matéria vermelha", 6: "Mitral"}
    return f"de {materiais[roll]}"

def map_d6_to_category(roll):
    if roll <= 3: return "arma"
    elif roll <= 5: return "armadura"
    else: return "esoterico"

def resolve_treasure_roll(roll_string, treasure_type="padrao"):
    results = []; bonus_pct = 20 if "+%" in roll_string else 0
    match_riqueza = re.match(r'([\w\d+x]+) riquezas? (menor(?:es)?|media|média|maior(?:es)?)', roll_string, re.IGNORECASE)
    if match_riqueza:
        dice_str = match_riqueza.group(1).strip()
        tipo_raw = match_riqueza.group(2).lower()
        if tipo_raw.startswith("menor"): tipo = "menor"
        elif tipo_raw.startswith("media") or tipo_raw.startswith("média"): tipo = "media"
        elif tipo_raw.startswith("maior"): tipo = "maior"
        else: results.append(f"Erro: Tipo de riqueza desconhecido '{tipo_raw}'"); return results
        quantity, _ = roll_dice_string(dice_str); total_value_tibar = 0
        for i in range(quantity):
            table = ALL_RIQUEZAS.get(tipo, {}); rolled_item_str, d100_details = get_weighted_roll_d100(table, bonus_pct=bonus_pct) 
            if not rolled_item_str: results.append(f"Erro: Tabela de riqueza '{tipo}' não encontrada."); continue
            match_item = re.match(r'(.*) \[([\w\d+x]+ T\$)\]', rolled_item_str)
            if not match_item: results.append(f"Item mal formatado em riquezas.json: {rolled_item_str}"); continue
            desc = match_item.group(1).strip(); value_dice = match_item.group(2).replace(" T$", "").strip()
            item_value, details = roll_dice_string(value_dice)
            if treasure_type == "metade": item_value = math.floor(item_value / 2); details += " (metade)"
            total_value_tibar += item_value
            results.append(f"{desc} {d100_details} (Valor: {item_value} T$ {details})")
        results.append(f"**Valor Total das Riquezas: {total_value_tibar} T$**"); return results
    match_superior = re.match(r'Superior \((\d+) melhorias?\)', roll_string, re.IGNORECASE)
    if match_superior:
        num_melhorias_total = int(match_superior.group(1)); is_2d = "2D" in roll_string
        d6_rolls = [random.randint(1, 6)]; d6_rolls.append(random.randint(1, 6)) if is_2d else None
        final_options = []; rolled_item_strings = [] 
        for roll in d6_rolls:
            categoria = map_d6_to_category(roll); generated_item_str = None
            for _ in range(10):
                item_base_table = ALL_EQUIPAMENTOS.get(categoria, {}); item_base, item_base_d100 = get_weighted_roll_d100(item_base_table, 0) 
                if not item_base: generated_item_str = f"Erro: Tabela '{categoria}' não encontrada."; break
                melhoria_table = ALL_SUPERIORES.get(categoria, {});
                if not melhoria_table: generated_item_str = f"Erro: Tabela '{categoria}' não encontrada."; break
                melhorias_duplas = ["Pungente", "Sob medida"]; melhorias_roladas = []; melhorias_gastas = 0; tentativas = 0
                while melhorias_gastas < num_melhorias_total and tentativas < 10:
                    tentativas += 1; melhoria, melhoria_d100 = get_weighted_roll_d100(melhoria_table, 0)
                    if melhoria in melhorias_roladas: continue 
                    custo_melhoria = 2 if melhoria in melhorias_duplas else 1
                    if (melhorias_gastas + custo_melhoria) <= num_melhorias_total:
                        melhorias_gastas += custo_melhoria
                        if melhoria == "Material especial":
                            if any("de " in m for m in melhorias_roladas): tentativas += 1; continue
                            melhorias_roladas.append(roll_material_especial() + " (1d6)")
                        else: melhorias_roladas.append(f"{melhoria} {melhoria_d100}")
                if not melhorias_roladas: melhorias_roladas = ["(Falha ao rolar melhoria)"]
                resultado_parcial = f"{item_base} {item_base_d100} {', '.join(melhorias_roladas)}"
                if resultado_parcial not in rolled_item_strings:
                    generated_item_str = f"{categoria.capitalize()}: {resultado_parcial}"; rolled_item_strings.append(resultado_parcial); break
            if generated_item_str is None: generated_item_str = f"{categoria.capitalize()}: {resultado_parcial} (duplicado)"
            final_options.append(generated_item_str)
        if is_2d: roll_str = f"(Rolagens 2D: {d6_rolls[0]} e {d6_rolls[1]})"; results.append(f"Item Superior {roll_str}, **escolha 1**: " + " **OU** ".join(final_options))
        else: results.append("Item Superior: " + final_options[0])
        return results
    match_pocao = re.match(r'([\w\d+]+) poç(?:ão|ões)', roll_string, re.IGNORECASE)
    if match_pocao:
        dice_str = match_pocao.group(1).strip(); quantity, _ = roll_dice_string(dice_str)
        for i in range(quantity):
            if not ALL_POCOES: results.append("Erro: 'pocoes.json' não carregado."); break
            pocao, d100_details = get_weighted_roll_d100(ALL_POCOES, bonus_pct=bonus_pct)
            results.append(f"Poção: {pocao} {d100_details}")
        return results
    if roll_string.startswith("Equipamento"):
        is_2d = "2D" in roll_string; d6_rolls = [random.randint(1, 6)]; d6_rolls.append(random.randint(1, 6)) if is_2d else None
        final_options = []; rolled_items = [] 
        for roll in d6_rolls:
            categoria = map_d6_to_category(roll); table = ALL_EQUIPAMENTOS.get(categoria, {}); item_str = None
            for _ in range(10):
                item, item_d100 = get_weighted_roll_d100(table, 0) 
                if item not in rolled_items: item_str = f"{categoria.capitalize()}: {item} {item_d100}"; rolled_items.append(item); break
            if item_str is None: item_str = f"{categoria.capitalize()}: {item} {item_d100} (duplicado)"
            final_options.append(item_str)
        if is_2d: roll_str = f"(Rolagens 2D: {d6_rolls[0]} e {d6_rolls[1]})"; results.append(f"Equipamento {roll_str}, **escolha 1**: " + " **OU** ".join(final_options))
        else: results.append("Equipamento: " + final_options[0])
        return results
    if roll_string == "Diverso":
        item, item_d100 = get_weighted_roll_d100(ALL_DIVERSOS, 0)
        if item: results.append(f"Item Diverso: {item} {item_d100}")
        else: results.append("Erro: Tabela 'diversos.json' não encontrada.")
        return results
    match_dinheiro = re.match(r'([\w\d+x]+) (TC|T\$|TO)', roll_string, re.IGNORECASE)
    if match_dinheiro:
        dice_str = match_dinheiro.group(1).strip(); unit = match_dinheiro.group(2)
        total, details = roll_dice_string(dice_str)
        if treasure_type == "metade": total = math.floor(total / 2); details += " (metade)"
        results.append(f"{total} {unit.upper()} {details}"); return results
    results.append(roll_string); return results
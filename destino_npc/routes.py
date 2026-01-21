import os
import json
import random
import re 
import shutil 
import unicodedata
from flask import Blueprint, render_template, request, jsonify

destino_bp = Blueprint('destino', __name__, template_folder='templates', static_folder='static')
bp_dir = os.path.abspath(os.path.dirname(__file__))

# --- CONSTANTES ---
SAVE_DIR = os.path.join(bp_dir, "datas")
STATE_FILE = os.path.join(SAVE_DIR, "estado_reinos.json")
NPC_FOLDER_NAME = "NPCs importantes"
REINADO_FOLDER_NAME = "Reinado" 

REINOS_LIST = [
    "Bielefeld", "Yuden", "Deheon", "Callistia", "Ermos Purpura",
    "Doherimm", "Khubar", "Wynlla", "Fortuna e Petrynia", "Pondsmânia",
    "Sckharshantallas", "Ahlen e Collen", "Tyrondir e Lamnor", "Zakharov",
    "Namalkah", "Aslothia", "Sallistick", "Lomatubar e Tollon", "Trebuck",
    "Sambúrdia e Ghondriann", "Tapista", "Uivantes"
]

EVENTOS_REINO = {
        1: "Catástrofe", 
        2: "Turbulência política",
        3: "Praga", 4: "Praga",
        5: "Terror mágico", 6: "Terror mágico",
        7: "Intriga", 8: "Intriga",
        9: "Criaturas míticas",
        10: "Nada muito fora do habitual", 11: "Nada muito fora do habitual",
        12: "Tesouro Natural", 
        13: "Descoberta", 
        14: "Renascimento religioso",
        15: "Boom comercial",
        16: "Heróis", 17: "Heróis",
        18: "Avanço no conhecimento", 19: "Avanço no conhecimento", 
        20: "Muita fortuna"
}

# --- CARREGAMENTO ---
def load_data_from_bp(filename):
    filepath = os.path.join(bp_dir, filename)
    try:
        with open(filepath, 'r', encoding='utf-8') as f: return json.load(f)
    except: return {}

def load_reino_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f: return json.load(f)
        except: return {}
    return {}

def save_reino_state(state):
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        with open(STATE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=4, ensure_ascii=False)
    except Exception as e: print(f"Erro save state: {e}")

OPTIONS_NPC_IMPORTANTE = load_data_from_bp("eventos_npcs.json")
EVENTOS_NPC_IRRELEVANTE = load_data_from_bp("eventos_npcs_comuns.json")
ALL_VIZINHOS = load_data_from_bp("vizinhos.json")
REGRAS_PILARES = load_data_from_bp("regras_pilares.json")
EVENTOS_MAIORES_DB = load_data_from_bp("eventos_maiores.json")
EVENTOS_DUPLOS_DB = load_data_from_bp("eventos_duplos.json")
# NOVA IMPLEMENTAÇÃO: Carregando os efeitos
EFEITOS_DESTINO_DB = load_data_from_bp("efeitos_destino.json")

# --- LÓGICA DE CÁLCULO ---
def normalize_string(s):
    """Remove acentos e coloca em minúsculas para comparação."""
    return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn').lower()

def get_efeitos_por_nome(evento_nome):
    """
    Busca os efeitos no JSON lidando com discrepâncias de acentos e nomes.
    Ex: 'Turbulência política' (Python) vs 'Turbulencia politica' (JSON)
    """
    nome_norm = normalize_string(evento_nome)
    
    # Tentativa 1: Busca normalizada
    for key, val in EFEITOS_DESTINO_DB.items():
        if normalize_string(key) == nome_norm:
            return val
            
    # Tentativa 2: Caso específico do "Nada muito fora do habitual" vs "Nada fora do habitual"
    if "nada" in nome_norm and "habitual" in nome_norm:
        # Tenta achar a chave que tem 'nada' e 'habitual' no JSON
        for key, val in EFEITOS_DESTINO_DB.items():
            k_norm = normalize_string(key)
            if "nada" in k_norm and "habitual" in k_norm:
                return val
                
    return None

def calcular_novos_status(status_atual, evento_nome):
    regras = REGRAS_PILARES.get(evento_nome, {})
    novo = status_atual.copy() if status_atual else {"militar":0, "economica":0, "social":0, "magica":0}
    
    for p in ["militar", "economica", "social", "magica"]:
        if p not in novo: novo[p] = 0
    for pilar, mod in regras.items():
        if pilar in novo:
            novo[pilar] += mod
            novo[pilar] = max(-5, min(5, novo[pilar]))
            
    return novo

def verificar_gatilhos(status):
    extremos_neg = [p for p, v in status.items() if v <= -6]
    extremos_pos = [p for p, v in status.items() if v >= 6]
    
    evento_maior = []
    reset_list = [] 
    if len(extremos_pos) >= 2:
        pilares_str = " e ".join([p.upper() for p in extremos_pos])
        opcoes = EVENTOS_DUPLOS_DB.get("positivo", [])
        template = random.choice(opcoes) if opcoes else "CRISE DE HEGEMONIA: Disputa sangrenta entre facções de {pilares}."
        evento_maior.append(template.replace("{pilares}", pilares_str))
        reset_list.extend(extremos_pos)
        
    elif len(extremos_neg) >= 2:
        pilares_str = " e ".join([p.upper() for p in extremos_neg])
        opcoes = EVENTOS_DUPLOS_DB.get("negativo", [])
        template = random.choice(opcoes) if opcoes else "RENASCIMENTO: Ajuda externa salva o reino do colapso em {pilares}."
        evento_maior.append(template.replace("{pilares}", pilares_str))
        reset_list.extend(extremos_neg)
    else:
        for p in extremos_pos:
            opcoes = EVENTOS_MAIORES_DB.get(p, {}).get("positivo", [])
            texto = random.choice(opcoes) if opcoes else f"{p.upper()} NO ÁPICE."
            evento_maior.append(texto)
            reset_list.append(p)
        for p in extremos_neg:
            opcoes = EVENTOS_MAIORES_DB.get(p, {}).get("negativo", [])
            texto = random.choice(opcoes) if opcoes else f"{p.upper()} EM COLAPSO."
            evento_maior.append(texto)
            reset_list.append(p)
    
    return evento_maior, reset_list

# --- ROTAS ---
@destino_bp.route('/')
def index():
    # Caminho default para facilitar testes, mude conforme necessário
    default_vault_path = r"C:\Users\Nuneseck\Desktop\Minecraft\Mestrando\Desaventureiros - T20".replace("\\", "/")
    return render_template('destino.html', default_vault_path=default_vault_path)

@destino_bp.route('/gerar_destinos_reinos', methods=['POST'])
def gerar_destinos_reinos():
    """Passo 1: Calcula Previsão e inclui Efeitos do JSON."""
    data = request.json
    vault_path = data.get('vault_path')
    
    if not vault_path: return jsonify({"error": "Caminho inválido"}), 400
    base_npc_path = os.path.normpath(os.path.join(vault_path, NPC_FOLDER_NAME))
    
    estado_geral = load_reino_state()
    reinos_com_destinos = []
    
    for reino in REINOS_LIST:
        roll, evento_nome = roll_reino_destino()
        
        # 1.1 Recupera efeitos descritivos e mecânicos
        efeitos_data = get_efeitos_por_nome(evento_nome)
        
        status_atual = estado_geral.get(reino, {"militar":0, "economica":0, "social":0, "magica":0})
        novo_status = calcular_novos_status(status_atual, evento_nome)
        eventos_maiores, resets = verificar_gatilhos(novo_status)
        
        for p in resets: novo_status[p] = 0 
        status_str = (f"Militar: {novo_status['militar']} | Economica: {novo_status['economica']} | "
                      f"Social: {novo_status['social']} | Mágica: {novo_status['magica']}")
        
        # Monta objeto do reino
        reino_obj = {
            "reino": reino, 
            "evento_num": roll, 
            "evento_nome": evento_nome,
            "status_pilares": novo_status,
            "status_formatted": status_str,
            "eventos_maiores": eventos_maiores,
            "npcs_found": []
        }
        
        # Adiciona dados do efeitos_destino.json se existirem
        if efeitos_data:
            reino_obj["efeitos_desc"] = efeitos_data.get("descricao", "")
            reino_obj["efeitos_jogadores"] = efeitos_data.get("efeito_jogadores", [])
            reino_obj["efeitos_reino"] = efeitos_data.get("efeito_reino", [])
        else:
            reino_obj["efeitos_desc"] = ""
            reino_obj["efeitos_jogadores"] = []
            reino_obj["efeitos_reino"] = []

        reinos_com_destinos.append(reino_obj)

    # Scan de NPCs
    try:
        if os.path.exists(base_npc_path):
            reinos_pastas = [d for d in os.listdir(base_npc_path) if os.path.isdir(os.path.join(base_npc_path, d))]
            for r_nome in reinos_pastas:
                r_data = next((x for x in reinos_com_destinos if x["reino"] == r_nome), None)
                if r_data:
                    path = os.path.join(base_npc_path, r_nome)
                    idx = f"{r_nome}.md"
                    r_data["npcs_found"] = sorted([f for f in os.listdir(path) if f.endswith(".md") and f.lower() != idx.lower()])
    except: pass

    agrupado = {}
    for item in reinos_com_destinos:
        evt = item["evento_nome"]
        num = min(k for k, v in EVENTOS_REINO.items() if v == evt)
        if evt not in agrupado: agrupado[evt] = {"num": num, "reinos": []}
        agrupado[evt]["reinos"].append(item) 
        
    return jsonify(sorted(agrupado.items(), key=lambda x: x[1]["num"]))

@destino_bp.route('/gerar_relatorio_final', methods=['POST'])
def gerar_relatorio_final():
    data = request.json
    reinos_data_flat = data.get("reinos_data", [])
    date = data.get("date", "sem_data")
    vault_path = data.get("vault_path")
    
    # 1. Atualiza JSON (Persistência)
    estado_atual_disco = load_reino_state()
    for item in reinos_data_flat:
        if item.get("processar_pilares", False):
            estado_atual_disco[item["reino"]] = item.get("status_pilares")
    save_reino_state(estado_atual_disco)
    
    # 2. Gera Relatório TXT e Atualiza Markdown
    report_lines = []
    report_lines.append(f"=== RELATÓRIO DE DESTINO MENSAL - {date} ===")
    
    all_reinos_map = {item["reino"]: {"evento_nome": item["evento_nome"], "evento_num": int(item.get("evento_num", 9))} for item in reinos_data_flat}
    
    for item in sorted(reinos_data_flat, key=lambda x: x['reino']):
        reino = item["reino"]
        processar_pilares = item.get("processar_pilares", False)
        
        # Garante que temos os efeitos carregados para salvar no MD,
        # mesmo que o front não tenha devolvido tudo.
        if "efeitos_desc" not in item:
            ef_data = get_efeitos_por_nome(item["evento_nome"])
            if ef_data:
                item["efeitos_desc"] = ef_data.get("descricao", "")
                item["efeitos_jogadores"] = ef_data.get("efeito_jogadores", [])
                item["efeitos_reino"] = ef_data.get("efeito_reino", [])

        # --- BLOCO 1: ATUALIZAÇÃO DO REINO ---
        if processar_pilares:
            # Escreve no MD do Reino (agora com efeitos)
            update_reino_md(vault_path, reino, date, item)
            
            evento = item["evento_nome"]
            status_str = item.get("status_formatted", "")
            maiores = item.get("eventos_maiores", [])
            
            report_lines.append(f"\n> **{reino.upper()}**")
            report_lines.append(f"Destino: {evento} | Status: {status_str}")
            
            # Adiciona resumo dos efeitos no relatório TXT se desejar, ou mantém só no MD.
            # Aqui mantive simples para o TXT não ficar gigante, focando no MD.
            
            if maiores:
                for m in maiores: report_lines.append(f"⚠️ {m}")
        else:
            report_lines.append(f"\n> **{reino.upper()}** (Apenas NPCs atualizados)")
            
        # --- BLOCO 2: ATUALIZAÇÃO DE NPCS ---
        npcs_sel = item.get("importantes", [])
        if npcs_sel:
            report_lines.append("   - NPCs Importantes:")
            for npc_file in npcs_sel:
                safe = os.path.basename(npc_file).replace('.md', '')
                res, new_r = roll_npc_importante(reino, item["evento_nome"], date, all_reinos_map)
                report_lines.append(f"     * {safe}: {res.split(':',1)[1].strip()}")
                update_npc_md(vault_path, reino, npc_file, date, res, new_r)
        
        num_irr = int(item.get("irrelevantes", 0))
        if num_irr > 0:
            res_irr = roll_npc_irrelevante(num_irr, date, reino, all_reinos_map)
            report_lines.append("   - NPCs Irrelevantes:")
            for l in res_irr: report_lines.append(f"     * {l.replace(chr(10), ' ')}")
            
    try:
        os.makedirs(SAVE_DIR, exist_ok=True)
        safe_date = re.sub(r'[\\/*?:"<>|]', "-", date)
        filepath = os.path.join(SAVE_DIR, f"destino_{safe_date}.txt")
        with open(filepath, 'w', encoding='utf-8') as f: f.write("\n".join(report_lines))
        return jsonify({"report": "\n".join(report_lines), "filepath": filepath})
    except Exception as e: return jsonify({"report": "", "error": str(e)})

# --- HELPERS ---

def update_reino_md(vault_path, reino_name, date, reino_data):
    """
    Escreve em Reinado/NomeDoReino/NomeDoReino.md incluindo os Efeitos de Destino.
    """
    folder_path = os.path.join(vault_path, REINADO_FOLDER_NAME, reino_name)
    reino_path = os.path.join(folder_path, f"{reino_name}.md")
    
    if not os.path.exists(folder_path):
        try: os.makedirs(folder_path, exist_ok=True)
        except: pass
    
    if not os.path.exists(reino_path):
        try:
            with open(reino_path, 'w', encoding='utf-8') as f:
                f.write(f"# {reino_name}\n\nArquivo gerado automaticamente.\n")
        except: return
        
    evento = reino_data.get("evento_nome", "?")
    roll = reino_data.get("evento_num", 0)
    status_str = reino_data.get("status_formatted", "")
    eventos_maiores = reino_data.get("eventos_maiores", [])
    
    # Extração dos novos dados
    desc = reino_data.get("efeitos_desc", "")
    efeitos_jog = reino_data.get("efeitos_jogadores", [])
    efeitos_reino = reino_data.get("efeitos_reino", [])
    
    md_content = f"\n\n---\n"
    md_content += f"### 📅 Registro: {date}\n"
    md_content += f"- **Destino:** {evento} (🎲 {roll})\n"
    md_content += f"- **Estado Atual:** `{status_str}`\n"
    
    if eventos_maiores:
        md_content += f"> [!WARNING] EVENTOS MAIORES\n"
        for evt in eventos_maiores:
            md_content += f"> - {evt}\n"
    
    # NOVA SEÇÃO: Efeitos do Mês no Obsidian
    if desc or efeitos_jog or efeitos_reino:
        md_content += f"\n#### 📜 Efeitos do Mês\n"
        if desc:
            md_content += f"_{desc}_\n\n"
        
        if efeitos_jog:
            md_content += f"**Para os Jogadores:**\n"
            for ef in efeitos_jog:
                md_content += f"- {ef}\n"
            md_content += "\n"
            
        if efeitos_reino:
            md_content += f"**Para o Reino:**\n"
            for ef in efeitos_reino:
                md_content += f"- {ef}\n"

    try:
        with open(reino_path, 'a', encoding='utf-8') as f: f.write(md_content)
    except Exception as e: print(f"Erro MD Reino: {e}")

# (Helpers de rolagem de dados e NPC mantêm-se iguais)
def update_npc_md(vault_path, reino, filename, date, text, new_reino):
    try:
        current_path = os.path.normpath(os.path.join(vault_path, NPC_FOLDER_NAME, reino, filename))
        if not os.path.exists(current_path): return
        history = f"\n\n---\n### Histórico de Destino\n- **({date}):** {text.split(':', 1)[1].strip()}\n"
        with open(current_path, 'a', encoding='utf-8') as f: f.write(history)
        if new_reino and new_reino != reino:
            new_folder = os.path.join(vault_path, NPC_FOLDER_NAME, new_reino)
            os.makedirs(new_folder, exist_ok=True)
            shutil.move(current_path, os.path.join(new_folder, filename))
    except: pass

def roll_reino_destino():
    r = random.randint(1, 20)
    return r, EVENTOS_REINO[r]

def _roll_match(match):
    full_text = match.group(0); num_dice = int(match.group(1)); die_face = int(match.group(2))
    operator = match.group(4); modifier = int(match.group(5) or 0)
    roll_total = sum(random.randint(1, die_face) for _ in range(num_dice))
    final_total = roll_total
    if operator == '+': final_total = roll_total + modifier
    elif operator == '-': final_total = max(1, roll_total - modifier) 
    return f"{full_text} (rolado {final_total})"

def resolve_dice_in_string(text):
    pattern = r'(\d+)d(\d+)(([+-])(\d+))?'
    return re.sub(pattern, _roll_match, text)

def resolve_movement_in_string(text, current_reino, all_reinos_map):
    neighbors = ALL_VIZINHOS.get(current_reino, [])
    destination = None; resolved_text = text
    if not neighbors and ("vizinho" in text or "próximo" in text): return f"{text} (S/ Vizinhos)", None
    if "pior condição" in text:
        worst = min(neighbors, key=lambda n: all_reinos_map.get(n, {}).get("evento_num", 99))
        resolved_text = text.replace("reino vizinho em pior condição", f"vizinho em pior condição ({worst})")
        destination = worst
    elif "reino vizinho aleatório" in text or "reino mais próximo" in text:
        destination = random.choice(neighbors)
        resolved_text = text.replace("reino vizinho aleatório", f"vizinho aleatório ({destination})").replace("reino mais próximo", f"vizinho mais próximo ({destination})")
    elif "melhor rolagem" in text or "reino mais próspero" in text:
        best = max(neighbors, key=lambda n: all_reinos_map.get(n, {}).get("evento_num", 0))
        resolved_text = text.replace("reino com melhor rolagem", f"reino próspero ({best})").replace("reino mais próspero em volta", f"reino próspero ({best})")
        destination = best
    elif "Terror Mágico" in text or "Criaturas míticas" in text:
        targets = ["Terror mágico", "Criaturas míticas"]
        cands = [r for r, d in all_reinos_map.items() if d["evento_nome"] in targets]
        destination = random.choice(cands) if cands else None
        resolved_text = text.replace("reino afetado por 'Terror Mágico' ou 'Criaturas míticas'", f"reino afetado ({destination if destination else 'Nenhum'})")
    elif "reino qualquer" in text:
        others = [r for r in REINOS_LIST if r != current_reino]
        destination = random.choice(others) if others else current_reino
        resolved_text = text.replace("reino qualquer", f"reino qualquer ({destination})")
    return resolved_text, destination

def roll_npc_importante(current_reino_name, evento_nome, date, all_reinos_map):
    tabela = next((opt for opt in OPTIONS_NPC_IMPORTANTE 
                   if normalize_string(opt.get("name", "")) == normalize_string(evento_nome)), None)
    
    if not tabela: 
        return f"| {date}: Sem alteração", None

    opcoes = tabela.get("options", [])

    if not opcoes:
        return f"| {date}: Sem alteração (Opções vazias)", None
    opcao = random.choice(opcoes)
    texto_dados = resolve_dice_in_string(opcao)
    texto_final, novo_reino = resolve_movement_in_string(texto_dados, current_reino_name, all_reinos_map)
    
    return f"| {date}: {texto_final}", novo_reino

def roll_npc_irrelevante(num, date, current_reino, all_reinos_map):
    res = []
    if not EVENTOS_NPC_IRRELEVANTE: return ["Erro: sem eventos irrelevantes"]
    for i in range(1, num + 1):
        evt = random.choice(EVENTOS_NPC_IRRELEVANTE)
        t_evt = resolve_movement_in_string(resolve_dice_in_string(evt.get('evento','')), current_reino, all_reinos_map)[0]
        t_eff = resolve_movement_in_string(resolve_dice_in_string(evt.get('efeito','')), current_reino, all_reinos_map)[0]
        res.append(f"Irrelevante {i} | {date}: {t_evt} (Efeito: {t_eff})")
    return res
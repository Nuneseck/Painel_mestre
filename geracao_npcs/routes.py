from flask import Blueprint, render_template, jsonify, request
import random
import json
import os
import re
from .bonus_raca import aplicar_bonus_raca 

# Definição do Blueprint
npcs_bp = Blueprint('npcs', __name__,
                    template_folder='templates',
                    static_folder='static')

bp_dir = os.path.abspath(os.path.dirname(__file__))

# =========================================
# FUNÇÕES DE CARREGAMENTO
# =========================================

def carregar_dados(nome_arquivo):
    pasta_data = os.path.join(bp_dir, 'data')
    for pasta_raiz, _, arquivos in os.walk(pasta_data):
        if nome_arquivo in arquivos:
            caminho = os.path.join(pasta_raiz, nome_arquivo)
            with open(caminho, 'r', encoding='utf-8') as f:
                return json.load(f)
    print(f"Arquivo não encontrado: {nome_arquivo}")
    return {} # Retorna dict vazio para evitar quebras

def escolher_por_peso(opcoes_dict):
    """Seleciona uma chave de um dicionário onde os valores são pesos."""
    if not opcoes_dict: return "Indefinido"
    opcoes = list(opcoes_dict.keys())
    pesos = list(opcoes_dict.values())
    return random.choices(opcoes, weights=pesos, k=1)[0]

# =========================================
# GERADORES ESPECÍFICOS
# =========================================

def gerar_atributos():
    return {
        "Força": random.randint(-2, 5), "Destreza": random.randint(-2, 5),
        "Constituição": random.randint(-2, 5), "Inteligência": random.randint(-2, 5),
        "Sabedoria": random.randint(-2, 5), "Carisma": random.randint(-2, 5)
    }

def gerar_idade():
    faixas_idade = [(16, 40), (40, 55), (55, 100)]
    pesos = [7, 2, 1] 
    faixa = random.choices(faixas_idade, weights=pesos, k=1)[0]
    return random.randint(faixa[0], faixa[1])

def escolher_raca():
    racas_com_pesos = carregar_dados('racas.json')
    return escolher_por_peso(racas_com_pesos)

def escolher_classe():
    classes_com_pesos = carregar_dados('classes.json')
    return escolher_por_peso(classes_com_pesos)

def escolher_nivel():
    niveis_com_pesos = carregar_dados('niveis_classe.json')
    return escolher_por_peso(niveis_com_pesos)

# --- NOVA LÓGICA DE PERSONALIDADE ---

def gerar_traco_unico():
    """Carrega positivos e negativos, une e escolhe APENAS UM."""
    positivos = carregar_dados('tracos_mentais_positivos.json') or {}
    negativos = carregar_dados('tracos_mentais_negativos.json') or {}
    
    # Une os dois dicionários
    todos = {**positivos, **negativos}
    
    if not todos: return ("Neutro", "Sem traços marcantes.")
    
    # Retorna uma tupla (Chave, Valor) ex: ("Sádico", "Gosta de causar dor")
    return random.choice(list(todos.items()))

def gerar_proposito():
    """Carrega propósitos e escolhe um."""
    dados = carregar_dados('propositos.json')
    if isinstance(dados, dict):
        return escolher_por_peso(dados)
    elif isinstance(dados, list):
        return random.choice(dados)
    return "Sobreviver"

def gerar_modo_agir():
    """Carrega modos de agir e escolhe um."""
    dados = carregar_dados('modos_agir.json')
    # Verifica se está dentro de uma chave "Modos" ou se é o dict direto
    if "Modos" in dados:
        lista = list(dados["Modos"].items())
    else:
        lista = list(dados.items())
        
    if lista:
        return random.choice(lista)
    return ("Imprevisível", "Age de forma errática.")

# ------------------------------------

def carregar_tracos_aparencia():
    return carregar_dados('tracos_aparencia_positivos.json'), carregar_dados('tracos_aparencia_negativos.json')

def carregar_alturas_raciais(): return carregar_dados('alturas_raciais.json')

def gerar_altura(raca):
    alturas = carregar_alturas_raciais()
    if raca not in alturas: return random.randint(100, 200)
    faixas = alturas[raca]["faixas_altura"]
    intervalos = [f["intervalo"] for f in faixas]
    pesos = [f["peso"] for f in faixas]
    faixa = random.choices(intervalos, weights=pesos, k=1)[0]
    return random.randint(faixa[0], faixa[1])

def carregar_tipo_corporal(): return carregar_dados('tipo_corporal.json')
def escolher_tipo_corporal(): return random.choice(carregar_tipo_corporal()['tipos_corporais'])

def carregar_cor_pele(): return carregar_dados('cor_pele.json')
def gerar_cor_pele(raca, cor_pele):
    return random.choice(cor_pele[raca]) if raca in cor_pele else "Cor de pele desconhecida"

def carregar_cabelos(): return carregar_dados('cabelos.json')
def gerar_cabelo(raca):
    cabelos = carregar_cabelos()
    cor = random.choice(cabelos["Cores Naturais"] + cabelos["Cores Fantasiosas"])
    tipo = random.choice(cabelos["Tipos"]); estilo = random.choice(cabelos["Estilos"])
    cabelo = {"Cor": cor, "Tipo": tipo, "Estilo": estilo}
    if raca in cabelos["Raças Específicas"]:
        cabelo["Raça Específica"] = random.choice(cabelos["Raças Específicas"][raca])
    return cabelo

def escolher_devocao():
    deuses = carregar_dados('deuses.json')
    return escolher_por_peso(deuses)

def escolher_deus_menor(): 
    dados = carregar_dados('deuses_menores.json')
    if isinstance(dados, list): return random.choice(dados)
    return "Nenhum"

def escolher_nivel_devocao():
    niveis = carregar_dados('niveis_devocao.json')
    return escolher_por_peso(niveis)

def gerar_devocao_npc():
    devocao = escolher_devocao()
    if devocao == "Não Devoto": return {"Devocao": "Não Devoto", "Nível": None}
    elif devocao == "Deus menor": return {"Devocao": escolher_deus_menor(), "Nível": None}
    else: return {"Devocao": devocao, "Nível": escolher_nivel_devocao()}
    
def gerar_tendencia():
    bom = random.randint(0, 10); mau = random.randint(0, 10 - bom); neutro_m = 10 - (bom + mau)
    ord = random.randint(0, 10); cao = random.randint(0, 10 - ord); neutro_a = 10 - (ord + cao)
    return {
        "Moral": {"Bom": bom, "Neutro": neutro_m, "Mau": mau},
        "Alinhamento": {"Ordeiro": ord, "Neutro": neutro_a, "Caótico": cao}
    }

# =========================================
# FUNÇÃO PRINCIPAL DE GERAÇÃO
# =========================================

def gerar_npc():
    generos = carregar_dados('genero.json')
    orientacao_sexual = carregar_dados('orientacao_sexual.json')
    relacionamentos = carregar_dados('relacionamento.json')
    comunidade = carregar_dados('comunidade.json')
    familiares = carregar_dados('familiares.json')
    tracos_a_pos, tracos_a_neg = carregar_tracos_aparencia()
    cor_pele = carregar_cor_pele() 
    nomes_masculinos = carregar_dados('nomes_masculinos.json')
    nomes_femininos = carregar_dados('nomes_femininos.json')
    sobrenomes = carregar_dados('sobrenomes.json')

    raca = escolher_raca(); classe = escolher_classe()
    nivel = escolher_nivel(); atributos = gerar_atributos()
    genero = random.choice(generos); idade = gerar_idade()
    tendencia = gerar_tendencia()

    # --- ELEMENTOS DO NÚCLEO NARRATIVO ---
    traco_unico = gerar_traco_unico() # Tupla (Nome, Desc)
    proposito = gerar_proposito()     # String
    modo_agir = gerar_modo_agir()     # Tupla (Nome, Desc)

    nome = "NomePadrao"
    if genero == "Masculino" and nomes_masculinos: nome = random.choice(nomes_masculinos)
    elif genero == "Feminino" and nomes_femininos: nome = random.choice(nomes_femininos)
    elif nomes_masculinos or nomes_femininos: nome = random.choice(nomes_masculinos + nomes_femininos)
    
    sobrenome = random.choice(sobrenomes) if sobrenomes else ""
    nome_completo = f"{nome} {sobrenome}".strip()

    atributos = aplicar_bonus_raca(atributos, raca)

    aparencia = {
        "Traço Aleatório": random.choice(list(tracos_a_pos.items()) + list(tracos_a_neg.items())),
        "Altura": f"{gerar_altura(raca)} cm",
        "Tipo Corporal": escolher_tipo_corporal(),
        "Cor da Pele": gerar_cor_pele(raca, cor_pele),
        "Cabelo": gerar_cabelo(raca)
    }

    return {
        "Name": nome_completo, "Race": raca, "Class": classe, "Level": nivel,
        "Gender": genero, "Orientação_Sexual": random.choice(orientacao_sexual),
        "Relacionamentos": random.choice(relacionamentos), "Comunidade": random.choice(comunidade),
        "Devocao": gerar_devocao_npc(), "Familiares": random.choice(familiares),
        "Age": idade, "Tendencia": tendencia, 
        "Appearance": aparencia, "AbilityScores": atributos,
        
        # NOVOS CAMPOS JSON
        "PersonalityTrait": traco_unico, 
        "Proposito": proposito,          
        "ModoAgir": modo_agir            
    }

# =========================================
# FORMATAR MARKDOWN
# =========================================

def formatar_texto_seguro(dado):
    """
    Função auxiliar para limpar o texto no Python (igual ao JS formatarDado).
    Resolve listas ["Nome", "Desc"] e adiciona espaço após vírgulas coladas.
    """
    if isinstance(dado, list):
        return f"{dado[0]}: {dado[1]}"
    
    if isinstance(dado, str):
        # Regex para adicionar espaço após vírgula se não houver (Ex: "Afiado,Tem" -> "Afiado, Tem")
        return re.sub(r',([^\s])', r', \1', dado)
        
    return str(dado)

import re # Certifique-se de que esta linha está no topo do arquivo com os outros imports

# ... (código anterior) ...

def formatar_texto_seguro(dado):
    """
    Função auxiliar para limpar o texto no Python (igual ao JS formatarDado).
    Resolve listas ["Nome", "Desc"] e adiciona espaço após vírgulas coladas.
    """
    if isinstance(dado, list):
        return f"{dado[0]}: {dado[1]}"
    
    if isinstance(dado, str):
        # Regex para adicionar espaço após vírgula se não houver (Ex: "Afiado,Tem" -> "Afiado, Tem")
        return re.sub(r',([^\s])', r', \1', dado)
        
    return str(dado)

def formatar_npc_markdown(npc, observacoes):
    """Converte o JSON do NPC para o formato Markdown do Obsidian."""
    lines = []
    lines.append(f"# {npc['Name']}")
    
    lines.append("\n## Informações Básicas")
    lines.append(f"- **Raça**:: {npc['Race']}")
    lines.append(f"- **Classe**:: {npc['Class']} {npc['Level']}")
    lines.append(f"- **Gênero**:: {npc['Gender']}")
    lines.append(f"- **Idade**:: {npc['Age']}")

    lines.append("\n## Atributos")
    lines.append("| For | Des | Con | Int | Sab | Car |")
    lines.append("|:---:|:---:|:---:|:---:|:---:|:---:|")
    lines.append(f"| {npc['AbilityScores']['Força']} | {npc['AbilityScores']['Destreza']} | {npc['AbilityScores']['Constituição']} | {npc['AbilityScores']['Inteligência']} | {npc['AbilityScores']['Sabedoria']} | {npc['AbilityScores']['Carisma']} |")

    lines.append("\n## Aparência")
    # Aplica formatação segura no traço de aparência também
    traco_ap = npc['Appearance']['Traço Aleatório']
    # Se for tupla/lista (Key, Val), pega o Val [1]. Se for string, usa direto.
    val_traco_ap = traco_ap[1] if isinstance(traco_ap, (list, tuple)) else traco_ap
    lines.append(f"- **Traço**:: {formatar_texto_seguro(val_traco_ap)}")
    
    lines.append(f"- **Corpo**:: {npc['Appearance']['Altura']}, {npc['Appearance']['Tipo Corporal']}, {npc['Appearance']['Cor da Pele']}")
    
    cabelo = npc['Appearance']['Cabelo']
    cabelo_str = f"{cabelo['Cor']}, {cabelo['Tipo']}, {cabelo['Estilo']}"
    if "Raça Específica" in cabelo: cabelo_str += f", {cabelo['Raça Específica']}"
    lines.append(f"- **Cabelo**:: {cabelo_str}")

    # === SEÇÃO ATUALIZADA ===
    lines.append("\n## Personalidade & Propósito")
    # PersonalityTrait é uma tupla ('Key', Value). Pegamos o Value [1].
    lines.append(f"- **Traço**:: {formatar_texto_seguro(npc['PersonalityTrait'][1])}")
    lines.append(f"- **Propósito**:: {npc['Proposito']}")
    # ModoAgir é uma tupla ('Nome', 'Descrição').
    lines.append(f"- **Conduta**:: {npc['ModoAgir'][0]}: {formatar_texto_seguro(npc['ModoAgir'][1])}")
    # ========================

    lines.append("\n## Tendência")
    moral = npc['Tendencia']['Moral']; alin = npc['Tendencia']['Alinhamento']
    lines.append(f"- **Moral**:: (Bom {moral['Bom']} / Neutro {moral['Neutro']} / Mau {moral['Mau']})")
    lines.append(f"- **Alinhamento**:: (Ordeiro {alin['Ordeiro']} / Neutro {alin['Neutro']} / Caótico {alin['Caótico']})")

    lines.append("\n## Relações")
    lines.append(f"- **Orientação**:: {npc['Orientação_Sexual']}")
    lines.append(f"- **Relacionamento**:: {npc['Relacionamentos']}")
    lines.append(f"- **Comunidade**:: {npc['Comunidade']}")
    lines.append(f"- **Familiares**:: {npc['Familiares']}")
    
    devocao = npc['Devocao']; devocao_str = devocao['Devocao']
    if devocao['Nível']: devocao_str += f" ({devocao['Nível']})"
    lines.append(f"- **Devoção**:: {devocao_str}")
    
    if observacoes:
        lines.append("\n## Observações")
        lines.append(observacoes)
        
    return "\n".join(lines)

# =========================================
# ROTAS FLASK
# =========================================

# Pasta para salvar os NPCs
SAVE_DIR = os.path.join(bp_dir, "npcs")

@npcs_bp.route('/salvar_npc', methods=['POST'])
def salvar_npc_route():
    try:
        data = request.json; npc_data = data.get('npc_data'); observacoes = data.get('observacoes', '')
        if not npc_data: return jsonify({'error': 'Nenhum dado de NPC recebido.'}), 400
        npc_markdown = formatar_npc_markdown(npc_data, observacoes)
        npc_name = npc_data.get("Name", "NPC_Sem_Nome"); filename = f"{npc_name}.txt"
        os.makedirs(SAVE_DIR, exist_ok=True); filepath = os.path.join(SAVE_DIR, filename)
        with open(filepath, 'w', encoding='utf-8') as f: f.write(npc_markdown)
        return jsonify({'status': 'success', 'filepath': filepath})
    except Exception as e:
        print(f"Erro ao salvar NPC: {e}"); return jsonify({'error': str(e)}), 500

@npcs_bp.route('/')
def index():
    return render_template('npcs.html')

@npcs_bp.route('/gerar_npc')
def gerar_npc_route():
    return jsonify(gerar_npc())
import json
import random
import os
import re
from flask import Blueprint, render_template, request, jsonify

# =====================================================
# CONFIGURAÇÃO DO BLUEPRINT
# =====================================================
rumores_bp = Blueprint(
    "rumores",
    __name__,
    template_folder="templates",
    static_folder="static"
)

# Diretório base deste módulo
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Caminhos absolutos para dados
DATA_DIR = os.path.join(BASE_DIR, "data")
ESTADOS_DIR = os.path.join(BASE_DIR, "estados")


# =====================================================
# FUNÇÕES AUXILIARES
# =====================================================
def carregar_json(path):
    """Carrega JSON a partir de um caminho relativo ao módulo."""
    caminho = os.path.join(BASE_DIR, path)
    if not os.path.exists(caminho):
        # Silencioso ou log leve, pois estados.json é opcional se tivermos fallback
        return None
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao ler {caminho}: {e}")
        return None


def carregar_json_data(filename):
    """Carrega JSON do diretório /data."""
    caminho = os.path.join(DATA_DIR, filename)
    if not os.path.exists(caminho):
        return []
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao ler {caminho}: {e}")
        return []


def carregar_json_estado(filename):
    """Carrega JSON do diretório /estados."""
    caminho = os.path.join(ESTADOS_DIR, filename)
    if not os.path.exists(caminho):
        # Retorna estrutura vazia segura
        return {"templates": [], "boost": {}, "veracidade_mod": {}}
    try:
        with open(caminho, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[ERRO] Falha ao ler {caminho}: {e}")
        return {"templates": [], "boost": {}, "veracidade_mod": {}}


# =====================================================
# LÓGICA PRINCIPAL
# =====================================================
def gerar_rumor_por_estado(estado):
    # ---------------------------------------------
    # 1) Carregar arquivo do estado
    # ---------------------------------------------
    # Se o nome do estado tiver espaços, garanta que o arquivo tenha o mesmo nome
    dados_estado = carregar_json_estado(f"{estado}.json")

    # ---------------------------------------------
    # 2) Carregar tabelas neutras
    # ---------------------------------------------
    categorias = [
        "quem", "quem_2", "acao", "onde",
        "como", "motivacao", "arma",
        "grupo", "item"
    ]

    data = {}
    for cat in categorias:
        val = carregar_json_data(f"{cat}.json")
        data[cat] = val if isinstance(val, list) else []

    # ---------------------------------------------
    # 3) Carregar Templates
    # ---------------------------------------------
    templates_estado = dados_estado.get("templates", [])
    templates_neutros = carregar_json_data("templates.json")

    # templates.json pode vir como {"templates": [...]} ou como lista direta
    if isinstance(templates_neutros, dict):
        templates_neutros = templates_neutros.get("templates", [])
    elif not isinstance(templates_neutros, list):
        templates_neutros = []

    templates = templates_estado + templates_neutros

    if not templates:
        templates = ["{Quem} realizou {Acao} em {Onde}."]

    template = random.choice(templates)

    # ---------------------------------------------
    # 4) Escolha dos campos + Boosts
    # ---------------------------------------------
    boosts = dados_estado.get("boost", {})

    def escolher(tag):
        key = tag.lower()
        
        lista_neutra = data.get(key, [])
        lista_boost = boosts.get(key, [])
        
        # Garante que sejam listas antes de somar
        if not isinstance(lista_neutra, list): lista_neutra = []
        if not isinstance(lista_boost, list): lista_boost = []

        if not lista_neutra and not lista_boost:
            return f"[{tag}]"

        lista_final = lista_neutra + lista_boost
        return random.choice(lista_final)

    # Preencher template
    rumor = template
    tags = re.findall(r"\{(.*?)\}", template)

    for tag in tags:
        rumor = rumor.replace(f"{{{tag}}}", escolher(tag), 1)

    # ---------------------------------------------
    # 5) Veracidade (ATUALIZADO)
    # ---------------------------------------------
    veracidade_cfg = carregar_json_data("veracidade.json")

    if isinstance(veracidade_cfg, dict) and veracidade_cfg:
        ver_base = veracidade_cfg
    else:
        # FALLBACK ATUALIZADO com todas as suas opções
        ver_base = {
            "verdadeiro": 25,
            "exagero": 35,
            "ameaca_maior": 5,
            "mentira": 35,
            "mal_interpretado": 10,
            "parcial": 30,
            "desatualizado": 15,
            "pressagio": 5
        }

    mod = dados_estado.get("veracidade_mod", {})

    categorias_v = list(ver_base.keys())
    pesos_finais = []
    
    for k in categorias_v:
        peso_original = ver_base[k]
        multiplicador = mod.get(k, 1) # Se não houver mod, multiplica por 1
        peso_calc = max(0.01, peso_original * multiplicador)
        pesos_finais.append(peso_calc)

    veracidade_chave = random.choices(categorias_v, weights=pesos_finais, k=1)[0]

    # Opcional: Formatar a chave para exibição (ex: "ameaca_maior" -> "Ameaca Maior")
    # Se preferir exibir exatamente como no JSON, remova a linha abaixo.
    veracidade_display = veracidade_chave.replace("_", " ").title()

    # Resultado final
    return {
        "estado": estado,
        "rumor": rumor,
        "veracidade": veracidade_display  # Retorna formatado para ficar bonito no card
    }


# =====================================================
# ROTAS
# =====================================================
@rumores_bp.route("/")
def index():
    # Carrega estados.json, que agora esperamos ser uma lista simples
    estados = carregar_json("estados.json")

    # Fallback se falhar ou estiver vazio
    if not estados:
        estados = ["Nada muito fora do habitual"]
    
    # Se por acaso ainda for um dicionário (legado), extrai valores únicos
    if isinstance(estados, dict):
        estados = sorted(list(set(estados.values())))

    return render_template("rumores.html", estados=estados)


@rumores_bp.route("/gerar_rumor", methods=["POST"])
def gerar_rumor_api():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"erro": "Payload inválido"}), 400

        estado = payload.get("estado")
        if not estado:
            return jsonify({"erro": "Estado não fornecido"}), 400

        resultado = gerar_rumor_por_estado(estado)
        return jsonify(resultado)

    except Exception as e:
        print(f"[ERRO FATAL] {e}")
        return jsonify({"erro": str(e)}), 500
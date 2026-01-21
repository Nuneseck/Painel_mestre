import random

atributos_por_raca = {
    "Anão": {"Constituição": 2, "Sabedoria": 1, "Destreza": -1},
    "Dahllan": {"Sabedoria": 2, "Destreza": 1, "Inteligência": -1},
    "Elfo": {"Inteligência": 2, "Destreza": 1, "Constituição": -1},
    "Goblin": {"Destreza": 2, "Inteligência": 1, "Carisma": -1},
    "Humano": "Escolhe +1 em três atributos diferentes",
    "Hynne": {"Destreza": 2, "Carisma": 1, "Força": -1},
    "Kliren": {"Inteligência": 2, "Carisma": 1, "Força": -1},
    "Lefou": "Escolhe +1 em três atributos diferentes (exceto Carisma), Carisma -1",
    "Medusa": {"Destreza": 2, "Carisma": 1},
    "Minotauro": {"Força": 2, "Constituição": 1, "Sabedoria": -1},
    "Osteon": "Escolhe +1 em três atributos diferentes (exceto Constituição), Constituição -1",
    "Osteon (Soterrado)": "Escolhe +1 em três atributos diferentes (exceto Constituição), Constituição -1",
    "Qareen": {"Carisma": 2, "Inteligência": 1, "Sabedoria": -1},
    "Sereia/Tritão": "Escolhe +1 em três atributos diferentes",
    "Sílfide": {"Carisma": 2, "Destreza": 1, "Força": -2},
    "Suraggel (Aggelus)": {"Sabedoria": 2, "Carisma": 1},
    "Suraggel (Sulfure)": {"Destreza": 2, "Inteligência": 1},
    "Trog": {"Constituição": 2, "Força": 1, "Inteligência": -1},
    "Trog (Anão)": {"Constituição": 2, "Força": 1, "Inteligência": -1, "Destreza": -1},
    "Bugbear": {"Força": 2, "Destreza": 1, "Carisma": -1},
    "Centauro": {"Sabedoria": 2, "Força": 1, "Destreza": -1, "Inteligência": -1},
    "Ceratops": {"Constituição": 2, "Força": 1, "Destreza": -1, "Inteligência": -1},
    "Elfo-do-Mar": {"Destreza": 2, "Constituição": 1, "Inteligência": -1},
    "Finntroll": {"Inteligência": 2, "Constituição": 1, "Força": -1},
    "Gnoll": {"Constituição": 2, "Sabedoria": 1, "Inteligência": -1},
    "Golem": {"Força": 1, "Carisma": -1},
    "Harpia": {"Destreza": 2, "Carisma": 1, "Inteligência": -1},
    "Hobgoblin": {"Constituição": 2, "Destreza": 1, "Carisma": -1},
    "Kaijin": {"Força": 2, "Constituição": 1, "Carisma": -2},
    "Kallyanach": "Escolhe +2 em um atributo ou +1 em dois atributos",
    "Kappa": {"Destreza": 2, "Constituição": 1, "Carisma": -1},
    "Kobolds": {"Destreza": 2, "Força": -1},
    "Meio-Orc": {"Força": 2, "Outro atributo (exceto Carisma)": 1},
    "Minauro": "Força +1 e +1 em dois atributos à escolha",
    "Moreau (Herança do Coruja)": "+1 dois atributos a escolha e +1 específico",
    "Moreau (Herança do Hiena)": "+1 dois atributos a escolha e +1 específico",
    "Moreau (Herança do Raposa)": "+1 dois atributos a escolha e +1 específico",
    "Moreau (Herança do Serpente)": "+1 dois atributos a escolha e +1 específico",
    "Moreau (Herança do Búfalo)": "+1 dois atributos a escolha e +1 específico",
    "Moreau (Herança do Coelho)": "+1 dois atributos a escolha e +1 específico",
    "Moreau (Herança do Crocodilo)": "+1 dois atributos a escolha e +1 específico",
    "Moreau (Herança do Gato)": "+1 dois atributos a escolha e +1 específico",
    "Moreau (Herança do Leão)": "+1 dois atributos a escolha e +1 específico",
    "Moreau (Herança do Lobo)": "+1 dois atributos a escolha e +1 específico",
    "Moreau (Herança do Morcego)": "+1 dois atributos a escolha e +1 específico",
    "Moreau (Herança do Urso)": "+1 dois atributos a escolha e +1 específico",
    "Nagah (Macho)": {"Força": 1, "Destreza": 1, "Constituição": 1},
    "Nagah (Fêmea)": {"Inteligência": 1, "Sabedoria": 1, "Carisma": 1},
    "Nezumi": {"Constituição": 2, "Destreza": 1, "Inteligência": -1},
    "Ogro": {"Força": 3, "Constituição": 2, "Inteligência": -1, "Carisma": -1},
    "Orc": {"Força": 2, "Constituição": 1, "Inteligência": -1},
    "Pteros": {"Sabedoria": 2, "Destreza": 1, "Inteligência": -1},
    "Tabrachi": {"Constituição": 2, "Força": 1, "Carisma": -1},
    "Tengu": {"Destreza": 2, "Inteligência": 1},
    "Velocis": {"Destreza": 2, "Sabedoria": 1, "Inteligência": -1},
    "Voracis": {"Destreza": 2, "Constituição": 1, "Inteligência": -1},
    "Yidishan": "Escolhe +1 em três atributos diferentes (exceto Carisma), Carisma -2",
    "Elfos-do-céu": {"Destreza": 2, "Carisma": 1, "Constituição": -1}
}

def aplicar_bonus_raca(atributos, raca):
    """
    Aplica os bônus de atributos específicos de acordo com a raça do NPC.
    """
    if raca not in atributos_por_raca:
        return atributos  # Se a raça não estiver no dicionário, retorna os atributos sem alterações

    bonus = atributos_por_raca[raca]

    if isinstance(bonus, dict):  
        # Aplica os bônus fixos diretamente
        for atributo, valor in bonus.items():
            atributos[atributo] += valor
    else:
        # Regras especiais para raças que escolhem bônus
        if raca in ["Humano", "Sereia/Tritão"]:
            atributos_aleatorios = random.sample(list(atributos.keys()), 3)
            for atributo in atributos_aleatorios:
                atributos[atributo] += 1

        elif raca == "Lefou":
            atributos_aleatorios = random.sample([attr for attr in atributos.keys() if attr != "Carisma"], 3)
            for atributo in atributos_aleatorios:
                atributos[atributo] += 1
            atributos["Carisma"] -= 1

        elif raca in ["Osteon", "Osteon (Soterrado)"]:
            atributos_aleatorios = random.sample([attr for attr in atributos.keys() if attr != "Constituição"], 3)
            for atributo in atributos_aleatorios:
                atributos[atributo] += 1
            atributos["Constituição"] -= 1

        elif raca == "Minauro":
            atributos["Força"] += 1
            atributos_aleatorios = random.sample(list(atributos.keys()), 2)
            for atributo in atributos_aleatorios:
                atributos[atributo] += 1

        elif raca == "Yidishan":
            atributos_aleatorios = random.sample([attr for attr in atributos.keys() if attr != "Carisma"], 3)
            for atributo in atributos_aleatorios:
                atributos[atributo] += 1
            atributos["Carisma"] -= 2

        # Raças com escolha de atributos
        elif raca == "Kallyanach":
            escolha = random.choice([1, 2])  # 1 para +2 em um atributo, 2 para +1 em dois atributos
            if escolha == 1:
                atributo = random.choice(list(atributos.keys()))
                atributos[atributo] += 2
            else:
                atributos_aleatorios = random.sample(list(atributos.keys()), 2)
                for atributo in atributos_aleatorios:
                    atributos[atributo] += 1

        elif "Moreau" in raca:
            bonus_moreau = {
                "Herança da Coruja": "Sabedoria",
                "Herança da Hiena": "Sabedoria",
                "Herança da Raposa": "Inteligência",
                "Herança da Serpente": "Inteligência",
                "Herança do Búfalo": "Força",
                "Herança do Coelho": "Destreza",
                "Herança do Crocodilo": "Constituição",
                "Herança do Gato": "Carisma",
                "Herança do Leão": "Força",
                "Herança do Lobo": "Carisma",
                "Herança do Morcego": "Destreza",
                "Herança do Urso": "Constituição"
            }
            for heranca, atributo in bonus_moreau.items():
                if heranca in raca:  # Verifica se o nome da herança está presente na raça
                    atributos[atributo] += 1
            atributos_aleatorios = random.sample(list(atributos.keys()), 2)
            for atributo in atributos_aleatorios:
                atributos[atributo] += 1

    return atributos

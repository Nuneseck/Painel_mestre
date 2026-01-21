niveis_pesos = {
    "1": 6000,
    "2": 5500,
    "3": 5000,
    "4": 4500,
    "5": 4000,
    "6": 3500,
    "7": 3000,
    "8": 2500,
    "9": 2000,
    "10": 1400,
    "11": 1000,
    "12": 700,
    "13": 500,
    "14": 300,
    "15": 150,
    "16": 100,
    "17": 50,
    "18": 30,
    "19": 20,
    "20": 10,
    "21": 1
}

# Calculando o total de pesos
total_pesos = sum(niveis_pesos.values())

# Calculando as porcentagens
niveis_porcentagem = {nivel: (peso / total_pesos) * 100 for nivel, peso in niveis_pesos.items()}

# Ordenando por maior chance primeiro
niveis_porcentagem = dict(sorted(niveis_porcentagem.items(), key=lambda x: x[1], reverse=True))

print (niveis_porcentagem)
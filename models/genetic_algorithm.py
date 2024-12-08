import random
import numpy as np
from deap import base, creator, tools, algorithms
import csv
from collections import defaultdict
import json
from geopy.distance import geodesic
import geopandas as gpd
import pandas as pd

alpha = 1.0
beta = 1.0
gamma = 1.0
file_path = 'estacoes_associadas_bacias.csv'
np.random.seed(42)

bacias = gpd.read_file("../data/watersheds/all_basians/bacias_nivel_6.shp").to_crs(epsg=4326)

def calcular_numero_dias(data_inicio, data_fim):
    try:
        if data_fim is None:
            data_fim = pd.to_datetime('today')
        
        return (pd.to_datetime(data_fim) - pd.to_datetime(data_inicio)).days
    except Exception as e:
        return 0
    
def objective_function(individual):
    fitness = 0
    for bacia_idx, estacao_local_idx in enumerate(individual):
        if estacao_local_idx < len(bacia_estacoes[bacia_idx]):
            estacao_idx = bacia_estacoes[bacia_idx][estacao_local_idx]
            if estacao_idx < len(estacoes_base):
                area_drenagem = estacoes_base[estacao_idx][0]
                dias_funcionando = estacoes_base[estacao_idx][1]
                fitness += alpha * area_drenagem + beta * dias_funcionando
    return fitness,

def create_individual():
    return [random.randint(0, len(bacia_estacoes[bacia_idx]) - 1) for bacia_idx in range(len(bacia_estacoes))]

def mutate(individual):
    for i in range(len(individual)):
        if random.random() < 0.01:  # Taxa de mutação
            max_index = len(bacia_estacoes[i]) - 1
            if max_index > 0:
                individual[i] = random.randint(0, max_index)
    return individual,

grouped = defaultdict(list)

with open(file_path, mode="r", encoding="utf-8") as file:
    reader = csv.reader(file)
    next(reader) 
    for row in reader:
        bacia_id, estacao_nome = int(row[0]), row[1]
        grouped[bacia_id].append(estacao_nome)

base = [grouped[key] for key in sorted(grouped.keys())]

estacoes_por_bacia = [np.array(sublista) for sublista in base]

print(estacoes_por_bacia)

with open('../data/gauging_station/gt_data.json', 'r') as file:
    estacoes_data = json.load(file)

def buscar_atributos(estacao_nome, estacoes_data):
    for estacao in estacoes_data:
        if estacao["Estacao_Nome"] == estacao_nome:
            return {
                "Area_Drenagem": estacao["Area_Drenagem"],
                "Latitude": estacao["Latitude"],
                "Longitude": estacao["Longitude"],
                "Periodo_Fim": estacao["Data_Periodo_Escala_Fim"],
                "Periodo_Inicio": estacao["Data_Periodo_Escala_Inicio"] 
            }
    return None

atributos_por_estacao = []

for bacia in estacoes_por_bacia:
    atributos_bacia = []
    for estacao_nome in bacia:
        atributos = buscar_atributos(estacao_nome, estacoes_data)
        if atributos:
            atributos_bacia.append(atributos)
    atributos_por_estacao.append(atributos_bacia)

for bacia in atributos_por_estacao:
    for estacao in bacia:
        
        inicio = estacao['Periodo_Inicio']
        fim = estacao['Periodo_Fim']
        

        resultado = calcular_numero_dias(inicio, fim)
        

        estacao['periodo_operando'] = resultado

estacoes_base = []

for sublista in atributos_por_estacao:
    for item in sublista:
        area_drenagem = float(item['Area_Drenagem']) if item['Area_Drenagem'] not in [None, 'None', 'null', ''] else 0.0
        periodo_operando = float(item['periodo_operando'])
        estacoes_base.append([area_drenagem, periodo_operando])

grouped2 = defaultdict(list)
with open(file_path, mode="r", encoding="utf-8") as file:
    reader = csv.reader(file)
    next(reader) 
    for row in reader:
        bacia_id, estacao_nome = int(row[0]), row[1]
        grouped2[bacia_id].append(bacia_id)

base2 = [grouped2[key] for key in sorted(grouped2.keys())]
bacia_estacoes = [np.array(sublista) for sublista in base2]

creator.create("FitnessMax", base.Fitness, weights=(1.0,))
creator.create("Individual", list, fitness=creator.FitnessMax)

toolbox = base.Toolbox()
toolbox.register("individual", tools.initIterate, creator.Individual, create_individual)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)
toolbox.register("evaluate", objective_function)
toolbox.register("mate", tools.cxUniform, indpb=0.5)
toolbox.register("mutate", mutate)
toolbox.register("select", tools.selTournament, tournsize=3)

population = toolbox.population(n=150)
num_generations = 120
crossover_prob = 0.7
mutation_prob = 0.2

result = algorithms.eaSimple(population, toolbox, cxpb=crossover_prob, mutpb=mutation_prob, ngen=num_generations, stats=None, halloffame=None)

best_individual = tools.selBest(population, 1)[0]

lista_bacias = []
for i, indice in enumerate(best_individual):
    if indice < len(bacia_estacoes[i]):
        lista_bacias.append(bacia_estacoes[i][indice])
    else:
        lista_bacias.append(None)

with open('ga_results.csv', 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)
    
    # Cabeçalho
    writer.writerow(["Bacia", "Estações", "Melhor Resultado"])
    
    # Escrever os dados
    for bacia, estacoes, resultado in zip(lista_bacias, base, best_individual):
        writer.writerow([bacia, ", ".join(estacoes), resultado])
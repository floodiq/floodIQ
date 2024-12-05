import numpy as np
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.core.problem import Problem
from pymoo.optimize import minimize
from shapely.geometry import Point, Polygon
import geopandas as gpd
import pandas as pd

gpf = gpd.read_file(r"C:\Users\Wendson\Desktop\AIFORGOOD\floodIQ\gausian\gausian_base\gausian_br.gpkg")

guasian_data = pd.DataFrame(gpf)
guasian_data.columns = guasian_data.columns.str.strip()

atributos_relevantes = guasian_data[(guasian_data['Operando'] == 'Sim') & 
                                    (guasian_data['TipoEstacao'] == 'Fluviométrica')]

print("Estações válidas após o filtro:")
print(atributos_relevantes[['TipoEstacao', 'Operando', 'AreaDrenagem']].head())

dados_bacias = [
    {'id': 1, 'centro': (10, 20), 'poligono': Polygon([(9, 19), (9, 21), (11, 21), (11, 19)])},  # Bacia 1
    {'id': 2, 'centro': (30, 40), 'poligono': Polygon([(29, 39), (29, 41), (31, 41), (31, 39)])}   # Bacia 2
]

dados_estacoes = [
    {'id': 101, 'coordenadas': (12, 22), 'area_drenagem': 1000, 'periodo': 15, 'responsavel': 'ANA'},
    {'id': 102, 'coordenadas': (14, 24), 'area_drenagem': 800, 'periodo': 10, 'responsavel': 'ANA'},
    {'id': 201, 'coordenadas': (31, 41), 'area_drenagem': 500, 'periodo': 8, 'responsavel': 'Outro'},
    {'id': 202, 'coordenadas': (35, 45), 'area_drenagem': 300, 'periodo': 5, 'responsavel': 'ANA'}
]

def associar_estacoes_a_bacias(dados_bacias, dados_estacoes):
    """Associa estações às bacias com base na localização geográfica."""
    estacoes_por_bacia = {bacia['id']: [] for bacia in dados_bacias}
    for estacao in dados_estacoes:
        for bacia in dados_bacias:
            if bacia['poligono'].contains(Point(estacao['coordenadas'])):
                estacoes_por_bacia[bacia['id']].append(estacao)
    return estacoes_por_bacia

estacoes_por_bacia = associar_estacoes_a_bacias(dados_bacias, dados_estacoes)

def calcular_distancia(bacia_centro, estacao_coordenada):
    return np.linalg.norm(np.array(bacia_centro) - np.array(estacao_coordenada))

def funcao_distancia(solucao, dados_bacias, dados_estacoes):
    f1 = []
    for i, estacao_id in enumerate(solucao):
        bacia = dados_bacias[i]
        estacao = dados_estacoes[int(estacao_id)]
        f1.append(calcular_distancia(bacia['centro'], estacao['coordenadas']))
    return sum(f1)

def funcao_area_drenagem(solucao, dados_estacoes):
    return -sum(dados_estacoes[int(estacao_id)]['area_drenagem'] for estacao_id in solucao)

def funcao_periodo(solucao, dados_estacoes):
    return -sum(dados_estacoes[int(estacao_id)]['periodo'] for estacao_id in solucao)

def funcao_responsavel(solucao, dados_estacoes):
    return -sum(1 if dados_estacoes[int(estacao_id)]['responsavel'] == 'ANA' else 0 for estacao_id in solucao)

class MyProblem(Problem):
    def __init__(self, n_bacias):
        super().__init__(n_var=n_bacias, 
                         n_obj=4, 
                         n_constr=0, 
                         xl=0, 
                         xu=len(dados_estacoes) - 1)

    def _evaluate(self, X, out, *args, **kwargs):
        X = np.round(X).astype(int)
        f1, f2, f3, f4 = [], [], [], []
        for sol in X:
            f1.append(funcao_distancia(sol, dados_bacias, dados_estacoes))
            f2.append(funcao_area_drenagem(sol, dados_estacoes))
            f3.append(funcao_periodo(sol, dados_estacoes))
            f4.append(funcao_responsavel(sol, dados_estacoes))
        out["F"] = np.column_stack([f1, f2, f3, f4])

n_bacias = len(dados_bacias)
algorithm = NSGA2(pop_size=100)

res = minimize(MyProblem(n_bacias),
               algorithm,
               ('n_gen', 200), 
               verbose=True)

print("Soluções Ótimas (estações selecionadas por bacia):")
print(np.round(res.X).astype(int)) 
print("Funções Objetivo:")
print(res.F) 

import matplotlib.pyplot as plt

plt.scatter(res.F[:, 0], res.F[:, 1], label="Distância x Área Drenagem", alpha=0.7)
plt.xlabel("Distância (minimizar)")
plt.ylabel("Área de Drenagem (maximizar)")
plt.title("Soluções Pareto")
plt.legend()
plt.show()

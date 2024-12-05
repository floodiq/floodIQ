import geopandas as gpd
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from sklearn.cluster import KMeans
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn_extra.cluster import KMedoids
from sklearn.metrics import pairwise_distances
from sklearn.cluster import DBSCAN
from sklearn.impute import SimpleImputer
import hdbscan
from k_means_constrained import KMeansConstrained
from sklearn.metrics import silhouette_score, silhouette_samples
from yellowbrick.cluster import InterclusterDistance
import sweetviz as sv

def graficos_clusters(df, colunas_interesse, cluster_col="clusters"):
    sns.set(style="whitegrid")
    
    for coluna in colunas_interesse:
        plt.figure(figsize=(8, 6))
        sns.boxplot(
            data=df, 
            x=cluster_col, 
            y=coluna, 
            palette="Set3"
        )
        plt.title(f"Distribuição de {coluna} por Cluster", fontsize=14)
        plt.xlabel("Cluster", fontsize=12)
        plt.ylabel(coluna, fontsize=12)
        plt.show()
        
        categorias = ['Altas', 'Baixas', 'Médias']
        frequencias_por_cluster = []
        
        for cluster in sorted(df[cluster_col].unique()):
            cluster_data = df[df[cluster_col] == cluster]
            limiar_alto = cluster_data[coluna].quantile(0.75) 
            limiar_baixo = cluster_data[coluna].quantile(0.25) 
            frequencias = [
                (cluster_data[coluna] > limiar_alto).sum(),
                (cluster_data[coluna] < limiar_baixo).sum(),
                cluster_data.shape[0] - (cluster_data[coluna] > limiar_alto).sum() - (cluster_data[coluna] < limiar_baixo).sum(),
            ]
            frequencias_por_cluster.append(frequencias)

        freq_df = pd.DataFrame(frequencias_por_cluster, columns=categorias, index=[f"Cluster {c}" for c in sorted(df[cluster_col].unique())])

        plt.figure(figsize=(8, 6))
        freq_df.plot(kind="bar", stacked=True, colormap="viridis")
        plt.title(f"Distribuição Categórica de {coluna} por Cluster", fontsize=14)
        plt.xlabel("Cluster", fontsize=12)
        plt.ylabel("Frequência", fontsize=12)
        plt.legend(title="Categoria")
        plt.show()


def analisar_clusters(df, colunas_interesse, cluster_col="clusters"):
    resultados = {}
    
    for cluster in sorted(df[cluster_col].unique()):
        cluster_data = df[df[cluster_col] == cluster]
        
        estatisticas = cluster_data[colunas_interesse].describe()
        
        frequencias = {}
        for coluna in colunas_interesse:
            limiar_alto = cluster_data[coluna].quantile(0.75)  
            limiar_baixo = cluster_data[coluna].quantile(0.25) 
            
            frequencias[coluna] = {
                "Altas": (cluster_data[coluna] > limiar_alto).sum(),
                "Baixas": (cluster_data[coluna] < limiar_baixo).sum(),
                "Médias": cluster_data.shape[0] - (cluster_data[coluna] > limiar_alto).sum() - (cluster_data[coluna] < limiar_baixo).sum(),
            }
        
        resultados[cluster] = {
            "Estatísticas Descritivas": estatisticas,
            "Frequências por Categoria": frequencias
        }
    
    return resultados


gdf = gpd.read_file(r"C:\Users\Wendson\Desktop\AIFORGOOD\floodIQ\basians\all_basians\bacias_nivel_6.shp")

atributos_relevantes = ["cod_otto", "area_total", "popul_2010", "dem_humurb", 
                        "dispohidri", "dem_humrur", "dens_hidro", "dens_drena"]

base_data = gdf[atributos_relevantes]

df = pd.DataFrame(base_data)


df_at = df[["area_total", "popul_2010", "dem_humurb", "dispohidri", "dem_humrur", "dens_hidro", "dens_drena"]]

imputer = SimpleImputer(strategy='mean')
df_filled = pd.DataFrame(imputer.fit_transform(df_at), columns=df_at.columns)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(df_filled)

# db = DBSCAN(eps=0.2, min_samples=6, metric='euclidean')
# clusters = db.fit_predict(X_scaled)

# df['Cluster'] = clusters

# print(df['Cluster'].value_counts())

# clusterer = hdbscan.HDBSCAN(min_cluster_size=75, min_samples=1, metric="correlation")
# clusters = clusterer.fit_predict(X_scaled)

# df["Cluster"] = clusters

# num_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
# print(f"Número de clusters formados: {num_clusters}")

# print(df["Cluster"].value_counts())

# plt.scatter(X_scaled[:, 0], X_scaled[:, 1], c=clusters, cmap='rainbow', s=5)
# plt.colorbar(label="Cluster")
# plt.title("Clusters gerados pelo HDBSCAN")
# plt.show()

num_clusters = 5
clusterer = KMeansConstrained(n_clusters=num_clusters, size_min=700, size_max=1000, random_state=42)
clusters = clusterer.fit_predict(X_scaled)

df["clusters"] = clusters

print(df)


# resultados_clusters = analisar_clusters(df, atributos_relevantes)

# for cluster, resultados in resultados_clusters.items():
#     print(f"\nCluster {cluster}:")
#     print("Estatísticas Descritivas:")
#     print(resultados["Estatísticas Descritivas"])
#     print("\nFrequências por Categoria:")
#     for coluna, frequencia in resultados["Frequências por Categoria"].items():
#         print(f" - {coluna}: {frequencia}")

graficos_clusters(df, atributos_relevantes)

report = sv.analyze(df)

report.show_html('relatorio.html')

df_cod_otto_clusters = df[["cod_otto", "clusters"]].sort_values(by=["clusters"])

df_cod_otto_clusters.to_csv("cod_otto_por_cluster.csv", index=False, sep=';')

print(df_cod_otto_clusters)
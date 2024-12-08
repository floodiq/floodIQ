import geopandas as gpd
import pandas as pd

gdf_estacoes = gpd.read_file('../data/gauging_station/gt.gpkg')
gdf_bacias = gpd.read_file('../data/watersheds/all_basians/bacias_nivel_6.shp')

gdf_estacoes = gdf_estacoes.to_crs(epsg=32718)
gdf_bacias = gdf_bacias.to_crs(epsg=32718)

gdf_estacoes_fluviometricas = gdf_estacoes[gdf_estacoes['TipoEstacao'] == 'Fluviométrica']

gdf_estacoes_fluviometricas['geometry'] = gdf_estacoes_fluviometricas['geometry'].buffer(150)

estacoes_bacias = gpd.sjoin(gdf_estacoes_fluviometricas, gdf_bacias, how='inner', predicate='intersects')

res = estacoes_bacias[['cod_otto', 'Nome']]

res.to_csv('estacoes_associadas_bacias.csv', index=False)
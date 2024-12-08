import pandas as pd
import geopandas as gpd

csv_file = "../models/ga_results.csv"
selected_bacias = pd.read_csv(csv_file)

bacia_codes = selected_bacias['Bacia'].astype(str)

shapefile_path = "../data/watersheds/all_basians/bacias_nivel_6.shp"
bacias_gdf = gpd.read_file(shapefile_path)

filtered_bacias_gdf = bacias_gdf[bacias_gdf['cod_otto'].astype(str).isin(bacia_codes)]

if 'id' in filtered_bacias_gdf.columns:
    filtered_bacias_gdf = filtered_bacias_gdf.rename(columns={"id": "gauge_id"})

output_shapefile_path = "bacias_filtradas.shp"
filtered_bacias_gdf.to_file(output_shapefile_path)
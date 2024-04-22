import geopandas as gpd
import pandas as pd
from pandas import unique

# Load the GML file
gdf = gpd.read_file(r'C:\Python\GML_duplicate_finder\gml.gml')

# Ensure the CRS is appropriate for distance measurements
gdf = gdf.to_crs('EPSG:25832')

# Identify unique object types
obj_types = unique(gdf['OBJTYPE'])

# Initialize an empty GeoDataFrame to store potential duplicates
potential_duplicates = gpd.GeoDataFrame(columns=gdf.columns)

NV_buffer = 5  # Larger buffer for different NGIS_FLAGG
duplicate_buffer = 20   # Smaller buffer for the same NGIS_FLAGG

for obj_type in obj_types:
    # Filter by object type
    subset = gdf[gdf['OBJTYPE'] == obj_type]
    
    # Create spatial index
    spatial_index = subset.sindex
    
    for index, row in subset.iterrows():
        # Find nearby objects within the larger buffer
        possible_matches_index = list(spatial_index.intersection(row.geometry.buffer(NV_buffer).bounds))
        possible_matches = subset.iloc[possible_matches_index]
        
        # Filter matches with different 'NGIS_FLAGG'
        final_matches_diff = possible_matches[possible_matches['NGIS_FLAGG'] != row['NGIS_FLAGG']]
        if not final_matches_diff.empty:
            potential_duplicates = pd.concat([potential_duplicates, final_matches_diff], ignore_index=True)
        
        # Now, filter matches with the same 'NGIS_FLAGG' but use the smaller buffer
        final_matches_same = possible_matches[possible_matches['NGIS_FLAGG'] == row['NGIS_FLAGG']]
        for _, match_row in final_matches_same.iterrows():
            if match_row.geometry.distance(row.geometry) < duplicate_buffer and match_row.name != index:
                potential_duplicates = pd.concat([potential_duplicates, pd.DataFrame([match_row])], ignore_index=True)

# Deduplicate potential_duplicates if necessary
potential_duplicates.drop_duplicates(subset=['geometry'], inplace=True)

output_file_path = r'C:\Python\GML_duplicate_finder\potential_duplicates.gml'

try:
    # Save the potential duplicates GeoDataFrame to a GML file
    potential_duplicates.to_file(output_file_path, driver='GML')
    print(f"The file {output_file_path} has been created.")
except Exception as e:
    print(f"An error occurred while creating the file: {e}")

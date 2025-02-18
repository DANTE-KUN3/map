import streamlit as st
import folium
import geopandas as gpd
import rasterio
import numpy as np
import os
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
from folium.plugins import FloatImage

# Define data folder paths
DATA_FOLDERS = {
    "Base": "data/base/",
    "2030": "data/2030/",
    "2050": "data/2050/",
    "2080": "data/2080/"
}

# Define legends for different risk types
LEGEND_FILES = {
    "Flood": "assets/legend_flood.png",
    "Heat": "assets/legend_heat.png",
    "Drought": "assets/legend_drought.png"
}

# Default map center coordinates
DEFAULT_MAP_CENTER = [20.5937, 78.9629]  # Center of India

# City locations
CITY_LOCATIONS = {
    "Mumbai": [19.0760, 72.8777],
    "Delhi": [28.7041, 77.1025],
    "Bangalore": [12.9716, 77.5946]
}

def save_raster_as_png(raster_path, output_png="processed_raster.png"):
    """Loads raster, normalizes it, and saves as PNG."""
    if not os.path.exists(raster_path):
        st.error(f"❌ Raster file not found: {raster_path}")
        return None, None

    with rasterio.open(raster_path) as src:
        bounds = src.bounds
        image = src.read(1).astype(float)

        # Handle NoData values
        if src.nodata is not None:
            image[image == src.nodata] = np.nan

        # Normalize raster values between 0-255
        min_val, max_val = np.nanmin(image), np.nanmax(image)
        norm_image = ((image - min_val) / (max_val - min_val) * 255).astype(np.uint8)

        # Save as grayscale PNG
        plt.imsave(output_png, norm_image, cmap="gray", format='png')

        return output_png, bounds

def overlay_raster_on_map(map_obj, raster_png, bounds, layer_name):
    """Overlays the processed raster PNG onto the Folium map."""
    if not raster_png or not bounds:
        st.error("❌ Unable to overlay raster. PNG or bounds are missing.")
        return

    min_lat, min_lon, max_lat, max_lon = bounds.bottom, bounds.left, bounds.top, bounds.right

    folium.raster_layers.ImageOverlay(
        image=raster_png,
        bounds=[[min_lat, min_lon], [max_lat, max_lon]],
        opacity=0.7,
        name=layer_name
    ).add_to(map_obj)

def load_vector(shapefile_path, map_obj, layer_name):
    """Loads and visualizes a vector shapefile on a Folium map."""
    try:
        if not os.path.exists(shapefile_path):
            st.warning(f"⚠️ Vector file not found: {shapefile_path}")
            return
        
        gdf = gpd.read_file(shapefile_path)
        folium.GeoJson(gdf, name=layer_name).add_to(map_obj)
        st.success(f"✅ Vector layer loaded: {shapefile_path}")
    
    except Exception as e:
        st.error(f"❌ Error loading vector file: {shapefile_path} - {e}")

def show_map(region, city, time_projection):
    """Creates a Folium map centered on the selected region or city."""
    
    if region == "India":
        map_center = DEFAULT_MAP_CENTER
        zoom_level = 5  # Zoomed out for India view
        layer_name = "India Boundary"
        vector_file = f"data/india_boundary.shp"  # Assuming a national boundary layer
    else:
        map_center = CITY_LOCATIONS.get(city, DEFAULT_MAP_CENTER)
        zoom_level = 10  # Zoomed in for city view
        layer_name = f"{city} Boundary ({time_projection})"
        vector_file = f"{DATA_FOLDERS.get(time_projection, 'data/base/')}{city}.shp"

    city_map = folium.Map(location=map_center, zoom_start=zoom_level, tiles="CartoDB Positron")

    # Load boundary layer
    st.write(f"🗺️ Checking boundary layer: {vector_file}")
    load_vector(vector_file, city_map, layer_name)

    return city_map

def add_layers(map_obj, region, city, time_projection, risk_types):
    """Adds vector and raster layers for the selected risk types."""
    data_folder = DATA_FOLDERS.get(time_projection, "data/base/")
    
    for risk in risk_types:
        raster_file = f"{data_folder}{city}_{risk}.tif"
        st.write(f"🔄 Processing raster file: {raster_file}")

        png_file, bounds = save_raster_as_png(raster_file)

        if png_file:
            overlay_raster_on_map(map_obj, png_file, bounds, f"{risk} Risk ({time_projection})")

        # Add legend for the risk type
        legend_path = LEGEND_FILES.get(risk)
        if legend_path and os.path.exists(legend_path):
            FloatImage(legend_path, bottom=10, left=10).add_to(map_obj)
            st.success(f"✅ Legend added for {risk}")

    folium.LayerControl().add_to(map_obj)

def sidebar():
    """Creates a sidebar with user filters for region, city, time projection, and risk type selection."""
    st.sidebar.title("🌍 Climate Risk Assessment Filters")
    
    region = st.sidebar.selectbox("Select Region", ["India", "City-Specific"], key="sidebar_region")
    city = None
    if region == "City-Specific":
        city = st.sidebar.selectbox("Select City", ["Mumbai", "Delhi", "Bangalore"], key="sidebar_city")
    
    time_projection = st.sidebar.radio("Select Time Projection", ["Base", "2030", "2050", "2080"], key="sidebar_time")
    risk_type = st.sidebar.multiselect("Select Risk Type", ["Flood", "Heat", "Drought"], key="sidebar_risk")
    
    return region, city, time_projection, risk_type

def main():
    """Main function to display the dashboard and handle user interactions."""
    st.title("🌍 Climate Risk Assessment Dashboard")
    
    region, city, time_projection, risk_types = sidebar()
    
    city_map = show_map(region, city, time_projection)
    
    if risk_types:
        st.write("🛰️ Adding selected risk layers...")
        add_layers(city_map, region, city, time_projection, risk_types)
        st.subheader(f"**Selected Risk Types:** {', '.join(risk_types)}")
    
    st_folium(city_map, width=700, height=500)

if __name__ == "__main__":
    main()

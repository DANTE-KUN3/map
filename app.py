import streamlit as st
import folium
import geopandas as gpd
import rasterio
import numpy as np
import os
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
import streamlit as st


st.set_page_config(layout="wide")

st.markdown("""
    <style>
        .streamlit-folium iframe {
            height: calc(100vh - 250px);  /* Adjust this value based on your layout */
            width: 100%;                  /* Ensure the map takes up the full width */
        }
    </style>
""", unsafe_allow_html=True)

# Set page configuration to wide mode by default


# Default map center coordinates (Mumbai Coordinates)
DEFAULT_MAP_CENTER = [19.0760, 72.8777]

# City locations (Mumbai)
CITY_LOCATIONS = {
    "Mumbai": [19.0760, 72.8777]
}

def save_raster_as_png(raster_path):
    """Reads a raster file and saves it as a PNG image."""
    try:
        with rasterio.open(raster_path) as src:
            data = src.read(1)  # Read the first band
            bounds = src.bounds  # Get the bounds of the raster
        
            data_normalized = np.uint8(data / np.max(data) * 255)
        
            plt.imshow(data_normalized, cmap='viridis')
            plt.axis('off')
            plt.savefig("temp_raster.png", format="png", bbox_inches="tight", pad_inches=0)
            plt.close()
        
            return "temp_raster.png", bounds
    except Exception as e:
        st.error(f"❌ Error saving raster as PNG: {e}")
        return None, None

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

def show_map(selected_layers):
    """Creates a Folium map centered on Mumbai and adds selected layers."""
    map_center = CITY_LOCATIONS["Mumbai"]
    zoom_level = 10  # Zoomed in for city view

    city_map = folium.Map(location=map_center, zoom_start=zoom_level, tiles="CartoDB Positron")

    # Add selected base layers
    for layer in selected_layers:
        if layer == "MMR":
            # Example for MMR layer, replace with actual layer data
            folium.GeoJson("data/mmr.shp").add_to(city_map)
        elif layer == "Tehsil":
            folium.GeoJson("data/tehsil.shp").add_to(city_map)
        elif layer == "SPA":
            folium.GeoJson("data/spa.shp").add_to(city_map)
        elif layer == "ULB":
            folium.GeoJson("data/urban_local_body.shp").add_to(city_map)
        elif layer == "Village":
            folium.GeoJson("data/village.shp").add_to(city_map)
        elif layer == "Roads":
            # Example: Add roads layer
            folium.GeoJson("data/roads.shp").add_to(city_map)
        elif layer == "Rail":
            # Example: Add rail layer
            folium.GeoJson("data/rail.shp").add_to(city_map)
        elif layer == "Stations":
            # Example: Add stations layer
            folium.GeoJson("data/stations.shp").add_to(city_map)

    return city_map

def sidebar():
    """Creates a sidebar with the necessary filter options."""
    
    # Select Area (Town or Village)
    Town = st.sidebar.selectbox("Select Area", ["Urban Local Body", "Village"], key="sidebar_Town")

    # Select Base Layers (Administrative Boundaries, Transport Layers, etc.)
    base_layers = st.sidebar.multiselect(
        "Select Base Layers", 
        ["MMR", "Tehsil", "SPA", "ULB", "Village", "Roads", "Rail", "Stations"],
        key="sidebar_base_layers"
    )

    # Select Risk Layers
    risk_type = st.sidebar.multiselect(
        "Select Risk Type", 
        ["Individual Risk", "Compound Risk"],
        key="sidebar_risk"
    )

    return Town, base_layers, risk_type

def display_region_stats(Town):
    """Displays statistics corresponding to the selected region and Town."""
    if Town == "Urban Local Body":
        st.write("📊 **Urban Local Body Stats**: High flood risk, population of 1 million.")
    elif Town == "Village":
        st.write("📊 **Village Stats**: Moderate heat risk, low flood risk.")
    else:
        st.write("📊 **Region Stats**: General stats for the entire Mumbai Metropolitan Region.")

def main():
    """Main function to display the dashboard and handle user interactions."""

    # Centered Title with padding using custom HTML (CSS injected)
    st.markdown("""
    <h1 style='text-align: center; padding-top: 50px;'>Climate Risk Assessment Dashboard</h1>
    """, unsafe_allow_html=True)

    # Call sidebar function to get user selections
    Town, base_layers, risk_type = sidebar()

    # Generate the map with the selected layers
    city_map = show_map(base_layers)

    # Layout: 2 columns, one for map and one for stats
    col1, col2 = st.columns([3, 1])  # 3:1 ratio
    
    with col1:
        # Display map in wide mode (100% width)
        st_folium(city_map, width="100%", height=0)  # height is controlled by CSS
    
    with col2:
        st.write("📊 **Statistical Information**:")
        # Display statistical information based on the selected area (Town or Village)
        if Town == "Urban Local Body":
            st.write("📊 **Urban Local Body Stats**: High flood risk, population of 1 million.")
        elif Town == "Village":
            st.write("📊 **Village Stats**: Moderate heat risk, low flood risk.")

if __name__ == "__main__":
    main()

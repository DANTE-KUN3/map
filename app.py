import streamlit as st
import folium
import geopandas as gpd
import rasterio
import numpy as np
import os
import matplotlib.pyplot as plt
from streamlit_folium import st_folium
import pathlib

# Function to load CSS from the 'assets' folder
def load_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
        st.markdown("""
            <style>
            div.stButton > button:first-child {
            display: none; /* Hide unnecessary buttons */
            }
            .stSidebar {
            background-color: #f8f9fa; /* Light background for sidebar */
            font-family: 'Century Gothic', sans-serif;
            }
            .stMarkdown h1 {
            color: #4CAF50; /* Green title color */
            text-align: center; /* Center align the title */
            font-family: 'Century Gothic', sans-serif;
            }
            .stMarkdown h2, .stMarkdown h3 {
            color: #333; /* Darker headings */
            font-family: 'Century Gothic', sans-serif;
            }
            .stDataFrame {
            border: 1px solid #ddd; /* Add border to tables */
            border-radius: 5px;
            padding: 10px;
            font-family: 'Century Gothic', sans-serif;
            }
            .stSidebar .css-18e3th9 {
                display: flex;
                justify-content: flex-start;
            }
            .css-1cpxqw2 {
                display: flex;
                flex-direction: column;
            }
            .css-17b6wyv {
                display: flex;
                flex-direction: column;
                width: 100%;
            }
            .css-162dklb {
                margin-right: 20px;
            }
            </style>
        """, unsafe_allow_html=True)

# Load the external CSS
css_path = pathlib.Path("assets/style.css")
load_css(css_path)

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
DEFAULT_MAP_CENTER = [19.0760, 72.8777]  # Mumbai Coordinates

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

def show_map(region, city, time_projection, extent):
    """Creates a Folium map centered on the selected region or city."""
    if region == "Mumbai":
        map_center = CITY_LOCATIONS.get(city, DEFAULT_MAP_CENTER)
        zoom_level = 10  # Zoomed in for city view
    else:
        map_center = DEFAULT_MAP_CENTER
        zoom_level = 5  # Zoomed out for India view

    city_map = folium.Map(location=map_center, zoom_start=zoom_level, tiles="CartoDB Positron")

    # Load selected extent layer (e.g., ULB or Village)
    if extent == "ULB":
        vector_file = f"data/{region}/ulb.shp"
    elif extent == "Village":
        vector_file = f"data/{region}/village.shp"
    else:
        vector_file = f"data/{region}/mmr.shp"
    
    load_vector(vector_file, city_map, extent)

    return city_map

def sidebar():
    """Creates a sidebar with user filters for region, city, extent, time projection, and risk type selection."""
    st.sidebar.title("🌍 Climate Risk Assessment Dashboard ")
    
    region = st.sidebar.selectbox("Select Region", ["Mumbai"], key="sidebar_region")
    city = st.sidebar.selectbox("Select City", ["Mumbai", "Delhi", "Bangalore"], key="sidebar_city")
    extent = st.sidebar.selectbox("Choose Extent", ["Urban Local Body", "Village"], key="sidebar_extent")
    
    if extent == "Village":
        tehsil = st.sidebar.selectbox("Select Tehsil", ["Tehsil 1", "Tehsil 2"], key="sidebar_tehsil")

    time_projection = st.sidebar.radio("Select Time Projection", ["Base", "2030", "2050", "2080"], key="sidebar_time")
    risk_type = st.sidebar.multiselect("Select Risk Type", ["Flood", "Heat", "Drought"], key="sidebar_risk")
    
    return region, city, time_projection, risk_type, extent

def display_region_stats(region, extent):
    """Displays statistics corresponding to the selected region and extent."""
    # Dummy stats based on region and extent
    if extent == "Urban Local Body":
        st.write("📊 **Urban Local Body Stats**: High flood risk, population of 1 million.")
    elif extent == "Village":
        st.write("📊 **Village Stats**: Moderate heat risk, low flood risk.")
    else:
        st.write("📊 **Region Stats**: General stats for the entire Mumbai Metropolitan Region.")

def main():
    """Main function to display the dashboard and handle user interactions."""
    st.title("🌍Climate Risk Assessment Dashboard")
    
    region, city, time_projection, risk_types, extent = sidebar()

    # Display region-specific statistics
    display_region_stats(region, extent)
    
    # Generate the map with selected region, time projection, and extent
    city_map = show_map(region, city, time_projection, extent)
    
    if risk_types:
        st.write("🛰️ Adding selected risk layers...")
        for risk_type in risk_types:
            raster_path = f"data/{region}/{time_projection}/{risk_type.lower()}.tif"
            raster_png, bounds = save_raster_as_png(raster_path)
            overlay_raster_on_map(city_map, raster_png, bounds, risk_type)
    
    # Layout: 2 columns, one for map and one for stats
    col1, col2 = st.columns([3, 1])  # 3:1 ratio
    
    with col1:
        st_folium(city_map, width="100%", height=600)  # Adjust map size for a smaller display
    
    with col2:
        st.write("📊 **Statistical Information**:")
        display_region_stats(region, extent)

if __name__ == "__main__":
    main()

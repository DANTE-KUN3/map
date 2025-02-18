import rasterio
import numpy as np
import matplotlib.pyplot as plt
import os

def convert_single_band_tiff_to_grayscale_png(input_tiff, output_png="grayscale_raster.png"):
    """Converts a single-band TIFF raster to a grayscale PNG."""
    if not os.path.exists(input_tiff):
        print(f"❌ Error: Raster file not found: {input_tiff}")
        return None

    with rasterio.open(input_tiff) as src:
        num_bands = src.count

        if num_bands > 1:
            print(f"⚠️ Warning: Multi-band TIFF detected ({num_bands} bands). Only single-band rasters are supported.")
            return None
        
        image = src.read(1).astype(float)  # Read first band
        image[image == src.nodata] = np.nan  # Handle NoData values

        # Normalize image between 0 and 255 (for grayscale)
        min_val = np.nanmin(image)
        max_val = np.nanmax(image)
        norm_image = ((image - min_val) / (max_val - min_val) * 255).astype(np.uint8)

        # Save as grayscale PNG
        plt.imsave(output_png, norm_image, cmap="gray", format='png')

        print(f"✅ Successfully converted '{input_tiff}' to grayscale PNG: '{output_png}'")

    return output_png

# Example usage
if __name__ == "__main__":
    input_tiff = "Mumbai_heat.tif"  # Update with your TIFF file path
    output_png = "output/grayscale_raster.png"  # Output PNG path

    # Ensure output folder exists
    os.makedirs(os.path.dirname(output_png), exist_ok=True)

    convert_single_band_tiff_to_grayscale_png(input_tiff, output_png)

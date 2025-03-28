import arcpy
import os
import zipfile

# Set environment
arcpy.env.workspace = r"C:\path\to\your\gdb"  # Change this to your geodatabase or folder
output_folder = r"C:\path\to\output"  # Output folder for intermediate KMLs
final_kmz = os.path.join(output_folder, "merged.kmz")  # Final KMZ file

# List of layers to export
layers = ["Layer1", "Layer2", "Layer3"]  # Change to your layer names
kml_files = []

# Export each layer to KML
for layer in layers:
    layer_kml = os.path.join(output_folder, f"{layer}.kmz")
    arcpy.LayerToKML_conversion(layer, layer_kml, scale=1, is_compressed=True)
    kml_files.append(layer_kml)

# Merge all KMZs into a single KMZ
with zipfile.ZipFile(final_kmz, 'w', zipfile.ZIP_DEFLATED) as kmz:
    for kml in kml_files:
        with zipfile.ZipFile(kml, 'r') as zip_ref:
            for file in zip_ref.namelist():
                kmz.writestr(file, zip_ref.read(file))

print("KMZ file created successfully:", final_kmz)

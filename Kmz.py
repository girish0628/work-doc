import arcpy
import os

# Set workspace and project
workspace = r"C:\GIS\Project"  # Change this to your workspace
aprx_path = os.path.join(workspace, "MapProject.aprx")  # ArcGIS Pro project file
output_folder = os.path.join(workspace, "KMZ_Output")
service_folder = "GIS_Services"  # Change this to your ArcGIS Server folder name
server_connection = r"C:\GIS\MyServer.ags"  # Change to your ArcGIS Server connection file

# Ensure output folder exists
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# Open ArcGIS Pro Project
aprx = arcpy.mp.ArcGISProject(aprx_path)
map_obj = aprx.listMaps()[0]  # Select the first map

# Iterate through layers in the map
for layer in map_obj.listLayers():
    if layer.isFeatureLayer:
        output_kmz = os.path.join(output_folder, f"{layer.name}.kmz")

        try:
            # Export to KMZ
            arcpy.LayerToKML_conversion(layer, output_kmz, "1", "NO_COMPOSITE", "DEFAULT", "1024", "CLAMPED_TO_GROUND")
            print(f"Exported KMZ: {layer.name} -> {output_kmz}")
            
            # Publish as Service
            service_name = layer.name.replace(" ", "_")  # Avoid spaces in service name
            sddraft = os.path.join(output_folder, f"{service_name}.sddraft")
            sd = os.path.join(output_folder, f"{service_name}.sd")

            # Create Service Definition Draft
            arcpy.mp.CreateWebLayerSDDraft(layer, sddraft, service_name, "MY_HOSTED_SERVICES",
                                           "FEATURE_ACCESS", server_connection, service_folder, True)

            # Stage Service Definition
            arcpy.StageService_server(sddraft, sd)

            # Upload and Publish to ArcGIS Server
            arcpy.UploadServiceDefinition_server(sd, server_connection)
            print(f"Published Service: {service_name}")

        except Exception as e:
            print(f"Error processing {layer.name}: {e}")

# Cleanup
del aprx
print("KMZ export and service publishing completed.")

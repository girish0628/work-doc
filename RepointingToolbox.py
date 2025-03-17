import arcpy
import os

class Toolbox(object):
    def __init__(self):
        """Define the toolbox properties."""
        self.label = "Repoint Data Source Toolbox"
        self.alias = "RepointDataSource"
        self.tools = [RepointDataSource]

class RepointDataSource(object):
    def __init__(self):
        """Define tool properties."""
        self.label = "Repoint Data Source"
        self.description = "Find all APRX files in a folder and update data sources."
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define the parameters."""
        param0 = arcpy.Parameter(
            displayName="Input Folder",
            name="input_folder",
            datatype="DEFolder",
            parameterType="Required",
            direction="Input"
        )

        param1 = arcpy.Parameter(
            displayName="Old Data Source",
            name="old_data_source",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
        )

        param2 = arcpy.Parameter(
            displayName="New Data Source",
            name="new_data_source",
            datatype="DEWorkspace",
            parameterType="Required",
            direction="Input"
        )

        return [param0, param1, param2]

    def execute(self, parameters, messages):
        """Execute the tool."""
        input_folder = parameters[0].valueAsText
        old_source = parameters[1].valueAsText
        new_source = parameters[2].valueAsText

        if not os.path.exists(input_folder):
            arcpy.AddError("Input folder does not exist.")
            return

        aprx_files = [os.path.join(root, file) for root, _, files in os.walk(input_folder) for file in files if file.endswith(".aprx")]

        if not aprx_files:
            arcpy.AddMessage("No APRX files found in the selected folder.")
            return

        arcpy.AddMessage(f"Found {len(aprx_files)} APRX files. Processing...")

        for aprx_path in aprx_files:
            try:
                arcpy.AddMessage(f"Processing: {aprx_path}")
                aprx = arcpy.mp.ArcGISProject(aprx_path)

                for map_obj in aprx.listMaps():
                    for layer in map_obj.listLayers():
                        if layer.supports("DATASOURCE") and old_source in layer.dataSource:
                            layer.replaceDataSource(new_source, "FILEGDB_WORKSPACE" if new_source.endswith(".gdb") else "SDE_WORKSPACE")
                            arcpy.AddMessage(f"Updated layer: {layer.name}")

                aprx.save()
                arcpy.AddMessage(f"Updated and saved: {aprx_path}")

            except Exception as e:
                arcpy.AddError(f"Error processing {aprx_path}: {str(e)}")
        
        arcpy.AddMessage("Repointing completed successfully.")

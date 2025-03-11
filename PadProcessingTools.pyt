import os
import arcpy

class Toolbox(object):
    def __init__(self):
        """Define the toolbox (the name of the toolbox is the name of the .pyt file)."""
        self.label = "Pad Processing Tools"
        self.alias = "padtools"
        self.tools = [PadProcessingTool]

class PadProcessingTool(object):
    def __init__(self):
        """Define the tool (tool name is the class name)."""
        self.label = "Process Pad and Classification Data"
        self.description = "Process pad and classification data to generate points, polylines, and CSV output"
        self.canRunInBackground = False

    def getParameterInfo(self):
        """Define parameter definitions"""
        # Input Pad Feature Class - Allow selection from Content pane
        param0 = arcpy.Parameter(
            displayName="Input Pad Feature Class",
            name="pad_fc_path",
            datatype=["GPFeatureLayer", "DEFeatureClass", "DEShapefile"],  # Support layers from Content pane
            parameterType="Required",
            direction="Input")
        # Remove filter.list as it doesn't work with GPFeatureLayer
        # We'll validate the geometry type in updateMessages instead

        # Input Classification Feature Class - Allow selection from Content pane
        param1 = arcpy.Parameter(
            displayName="Input Classification Feature Class",
            name="classify_fc_path",
            datatype=["GPFeatureLayer", "DEFeatureClass", "DEShapefile"],  # Support layers from Content pane
            parameterType="Required",
            direction="Input")

        # Output CSV Location
        param2 = arcpy.Parameter(
            displayName="Output CSV Location",
            name="output_csv",
            datatype="DEFile",
            parameterType="Required",
            direction="Output")
        param2.filter.list = ["csv"]

        # Processing Location Option
        param3 = arcpy.Parameter(
            displayName="Processing Location",
            name="processing_location",
            datatype="GPString",
            parameterType="Required",
            direction="Input")
        param3.filter.type = "ValueList"
        param3.filter.list = ["In Memory", "File Geodatabase"]
        param3.value = "File Geodatabase"  # Default value

        # Output Workspace for intermediate files (only used if File Geodatabase is selected)
        param4 = arcpy.Parameter(
            displayName="Output Workspace (for File Geodatabase option)",
            name="output_workspace",
            datatype=["DEWorkspace", "DEFeatureDataset"],  # Support both file GDB and feature datasets
            parameterType="Optional",
            direction="Input")
        param4.enabled = True  # Initially enabled since File Geodatabase is the default

        # Fields to drop from spatial join result
        param5 = arcpy.Parameter(
            displayName="Fields to Drop (Optional)",
            name="fields_to_drop",
            datatype="GPString",
            parameterType="Optional",
            direction="Input",
            multiValue=True)

        return [param0, param1, param2, param3, param4, param5]

    def isLicensed(self):
        """Set whether tool is licensed to execute."""
        return True

    def updateParameters(self, parameters):
        """Modify the values and properties of parameters before internal
        validation is performed.  This method is called whenever a parameter
        has been changed."""
        # Enable/disable output workspace parameter based on processing location choice
        if parameters[3].value == "In Memory":
            parameters[4].enabled = False
        else:
            parameters[4].enabled = True
        return

    def updateMessages(self, parameters):
        """Modify the messages created by internal validation for each tool
        parameter.  This method is called after internal validation."""
        # Validate input pad feature class
        if parameters[0].value:
            try:
                # Get the describe object for the input
                desc = arcpy.Describe(parameters[0].value)
                
                # Check if it has a valid shape type property
                if hasattr(desc, "shapeType"):
                    # Validate that it's a polygon
                    if desc.shapeType != "Polygon":
                        parameters[0].setErrorMessage("Input must be a polygon feature layer or feature class")
                else:
                    # If it doesn't have a shapeType property, try to get it from the layer
                    if hasattr(desc, "featureClass"):
                        fc_desc = arcpy.Describe(desc.featureClass)
                        if fc_desc.shapeType != "Polygon":
                            parameters[0].setErrorMessage("Input must be a polygon feature layer or feature class")
                    else:
                        parameters[0].setErrorMessage("Unable to determine geometry type. Please select a polygon feature layer or feature class")
            except Exception as e:
                parameters[0].setErrorMessage(f"Error validating input: {str(e)}")
                
        # Validate input classification feature class
        if parameters[1].value:
            try:
                # We don't need to check geometry type for classification, but ensure it's a valid feature layer
                desc = arcpy.Describe(parameters[1].value)
                if not hasattr(desc, "shapeType") and not hasattr(desc, "featureClass"):
                    parameters[1].setErrorMessage("Input must be a feature layer or feature class")
            except Exception as e:
                parameters[1].setErrorMessage(f"Error validating input: {str(e)}")
        
        # Validate output workspace if File Geodatabase is selected
        if parameters[3].value == "File Geodatabase" and parameters[4].value:
            try:
                desc = arcpy.Describe(parameters[4].valueAsText)
                if desc.dataType not in ["Workspace", "FeatureDataset"]:
                    parameters[4].setErrorMessage("Output workspace must be a file geodatabase or feature dataset")
            except Exception as e:
                parameters[4].setErrorMessage(f"Error validating workspace: {str(e)}")
        
        # Require output workspace if File Geodatabase is selected
        if parameters[3].value == "File Geodatabase" and not parameters[4].value:
            parameters[4].setErrorMessage("Output workspace is required when File Geodatabase option is selected")
        
        return

    def execute(self, parameters, messages):
        """The source code of the tool."""
        # Get parameters
        pad_fc_path = parameters[0].valueAsText
        classify_fc_path = parameters[1].valueAsText
        output_csv = parameters[2].valueAsText
        processing_location = parameters[3].valueAsText
        output_workspace = parameters[4].valueAsText if processing_location == "File Geodatabase" else "in_memory"
        fields_to_drop = parameters[5].valueAsText.split(';') if parameters[5].value else []

        # Log input types and processing location
        try:
            pad_desc = arcpy.Describe(pad_fc_path)
            classify_desc = arcpy.Describe(classify_fc_path)
            
            # Get more detailed information about the inputs
            pad_type = pad_desc.dataType
            if hasattr(pad_desc, "featureClass"):
                pad_type += f" (Feature Layer from {arcpy.Describe(pad_desc.featureClass).dataType})"
                
            classify_type = classify_desc.dataType
            if hasattr(classify_desc, "featureClass"):
                classify_type += f" (Feature Layer from {arcpy.Describe(classify_desc.featureClass).dataType})"
            
            arcpy.AddMessage(f"Input Pad Feature Class: {pad_fc_path} (Type: {pad_type})")
            arcpy.AddMessage(f"Input Classification Feature Class: {classify_fc_path} (Type: {classify_type})")
            arcpy.AddMessage(f"Processing Location: {processing_location}")
            
            if processing_location == "File Geodatabase":
                workspace_desc = arcpy.Describe(output_workspace)
                arcpy.AddMessage(f"Output Workspace: {output_workspace} (Type: {workspace_desc.dataType})")
            
            arcpy.AddMessage(f"Output CSV: {output_csv}")
        except Exception as e:
            arcpy.AddWarning(f"Warning during input description: {str(e)}")

        # Set up intermediate outputs
        if processing_location == "In Memory":
            arcpy.AddMessage("Using in-memory workspace for processing (faster but temporary)")
            # For in-memory workspace, use simple names
            pad_fc_type_pad = "in_memory/pad_fc_type_pad"
            pad_fc_type_pad_copy = "in_memory/pad_fc_type_pad_copy"
            pad_fc_type_pad_copy_classify = "in_memory/pad_fc_type_pad_copy_classify"
            pad_fc_type_pad_copy_classify_points = "in_memory/pad_fc_type_pad_copy_classify_points"
            pad_fc_points_et_01 = "in_memory/pad_fc_points_et_01"
            pad_fc_points_et_01_lines = "in_memory/pad_fc_points_et_01_lines"
            pad_fc_points_et_12 = "in_memory/pad_fc_points_et_12"
            pad_fc_points_et_12_copy = "in_memory/pad_fc_points_et_12_copy"
            pad_fc_points_et_12_lines = "in_memory/pad_fc_points_et_12_lines"
        else:
            # For file geodatabase, use full paths
            pad_fc_type_pad = os.path.join(output_workspace, "pad_fc_type_pad")
            pad_fc_type_pad_copy = os.path.join(output_workspace, "pad_fc_type_pad_copy")
            pad_fc_type_pad_copy_classify = os.path.join(output_workspace, "pad_fc_type_pad_copy_classify")
            pad_fc_type_pad_copy_classify_points = os.path.join(output_workspace, "pad_fc_type_pad_copy_classify_points")
            pad_fc_points_et_01 = os.path.join(output_workspace, "pad_fc_points_et_01")
            pad_fc_points_et_01_lines = os.path.join(output_workspace, "pad_fc_points_et_01_lines")
            pad_fc_points_et_12 = os.path.join(output_workspace, "pad_fc_points_et_12")
            pad_fc_points_et_12_copy = os.path.join(output_workspace, "pad_fc_points_et_12_copy")
            pad_fc_points_et_12_lines = os.path.join(output_workspace, "pad_fc_points_et_12_lines")

        try:
            arcpy.AddMessage("Starting pad processing workflow...")

            # Select pads
            arcpy.AddMessage("Selecting pad features...")
            arcpy.Select_analysis(in_features=pad_fc_path, out_feature_class=pad_fc_type_pad, 
                                where_clause="PolyType = 'Pad'")

            # Copy features
            arcpy.AddMessage("Copying pad features...")
            arcpy.CopyFeatures_management(in_features=pad_fc_type_pad, 
                                        out_feature_class=pad_fc_type_pad_copy)

            # Spatial join
            arcpy.AddMessage("Performing spatial join with classification data...")
            arcpy.SpatialJoin_analysis(target_features=pad_fc_type_pad_copy, 
                                    join_features=classify_fc_path, 
                                    out_feature_class=pad_fc_type_pad_copy_classify, 
                                    join_operation="JOIN_ONE_TO_ONE", 
                                    join_type="KEEP_ALL", 
                                    match_option="INTERSECT")

            # Delete fields if specified
            if fields_to_drop:
                arcpy.AddMessage(f"Deleting specified fields: {fields_to_drop}")
                arcpy.DeleteField_management(in_table=pad_fc_type_pad_copy_classify, 
                                            drop_field=fields_to_drop)

            # Add centroid attributes
            arcpy.AddMessage("Adding geometry attributes...")
            arcpy.AddGeometryAttributes_management(Input_Features=pad_fc_type_pad_copy_classify, 
                                                Geometry_Properties="CENTROID")

            # Add fields
            arcpy.AddMessage("Adding Height and COMMENTS fields...")
            arcpy.AddField_management(in_table=pad_fc_type_pad_copy_classify, 
                                    field_name="Height", field_type="DOUBLE")
            arcpy.AddField_management(in_table=pad_fc_type_pad_copy_classify, 
                                    field_name="COMMENTS", field_type="TEXT")

            # Calculate fields
            arcpy.AddMessage("Calculating field values...")
            arcpy.CalculateField_management(in_table=pad_fc_type_pad_copy_classify, 
                                        field="Height", 
                                        expression="!PlannedAHD!", 
                                        expression_type="PYTHON3")
            arcpy.CalculateField_management(in_table=pad_fc_type_pad_copy_classify, 
                                        field="COMMENTS", 
                                        expression="'Sump ' + str(!Sump!) + ' Dip ' + str(!PlannedInc!) + ' Azi ' + str(!PlannedAzi!) + ' Depth ' + str(!PlannedDep!)", 
                                        expression_type="PYTHON3")

            # Delete unnecessary fields
            arcpy.AddMessage("Deleting unnecessary fields...")
            arcpy.DeleteField_management(in_table=pad_fc_type_pad_copy_classify, 
                                        drop_field=["PlannedAHD", "PlannedAzi", "PlannedDep"])

            # Convert polygons to points
            arcpy.AddMessage("Converting polygons to points...")
            self.PolygonToPoints(in_features=pad_fc_type_pad_copy_classify, 
                                out_feature_class=pad_fc_type_pad_copy_classify_points, 
                                convert_option="Vertex", 
                                remove_duplicates=True, 
                                calc_point_pos=False, 
                                keep_ZM=False)

            # Select points with ET_ORDER 0 or 1
            arcpy.AddMessage("Selecting points with ET_ORDER 0 or 1...")
            arcpy.Select_analysis(in_features=pad_fc_type_pad_copy_classify_points, 
                                out_feature_class=pad_fc_points_et_01, 
                                where_clause="ET_ORDER = 0 OR ET_ORDER = 1")

            # Convert points to polylines
            arcpy.AddMessage("Converting points to polylines (ET_ORDER 0 or 1)...")
            self.PointsToPolylines(in_dataset=pad_fc_points_et_01, 
                                out_dataset=pad_fc_points_et_01_lines, 
                                polyline_id_field="PadName_1")

            # Add length attribute
            arcpy.AddMessage("Adding length attribute to polylines...")
            arcpy.AddGeometryAttributes_management(Input_Features=pad_fc_points_et_01_lines, 
                                                Geometry_Properties=["LENGTH"])

            # Join fields
            arcpy.AddMessage("Joining length field to pad features...")
            arcpy.JoinField_management(in_data=pad_fc_type_pad_copy_classify, 
                                    in_field="PadName_1", 
                                    join_table=pad_fc_points_et_01_lines, 
                                    join_field="ET_ID", 
                                    fields=["LENGTH"])

            # Select points with ET_ORDER 1 or 2
            arcpy.AddMessage("Selecting points with ET_ORDER 1 or 2...")
            arcpy.Select_analysis(in_features=pad_fc_type_pad_copy_classify_points, 
                                out_feature_class=pad_fc_points_et_12, 
                                where_clause="ET_ORDER = 1 OR ET_ORDER = 2")

            # Copy features
            arcpy.AddMessage("Copying selected points...")
            arcpy.CopyFeatures_management(in_features=pad_fc_points_et_12, 
                                        out_feature_class=pad_fc_points_et_12_copy)

            # Convert points to polylines
            arcpy.AddMessage("Converting points to polylines (ET_ORDER 1 or 2)...")
            self.PointsToPolylines(in_dataset=pad_fc_points_et_12_copy, 
                                out_dataset=pad_fc_points_et_12_lines, 
                                polyline_id_field="PadName_2", 
                                order_field="ET_ORDER")

            # Add geometry attributes
            arcpy.AddMessage("Adding geometry attributes to polylines...")
            arcpy.AddGeometryAttributes_management(Input_Features=pad_fc_points_et_12_lines, 
                                                Geometry_Properties=["LENGTH", "LINE_START_MID_END"])

            # Add azimuth field
            arcpy.AddMessage("Adding and calculating azimuth field...")
            arcpy.AddField_management(in_table=pad_fc_points_et_12_lines, 
                                    field_name="Azimuth", field_type="DOUBLE")

            # Calculate azimuth
            arcpy.CalculateField_management(in_table=pad_fc_points_et_12_lines, 
                                        field="Azimuth", 
                                        expression="180-math.degrees(math.atan2((!END_Y! - !START_Y!),(!END_X! - !START_X!)))", 
                                        expression_type="PYTHON3")

            # Rename LENGTH field to WIDTH
            arcpy.AddMessage("Renaming LENGTH field to WIDTH...")
            arcpy.AlterField_management(in_table=pad_fc_points_et_12_lines, 
                                    field="LENGTH", 
                                    new_field_name="WIDTH")

            # Delete unnecessary fields
            arcpy.AddMessage("Deleting unnecessary fields...")
            arcpy.DeleteField_management(in_table=pad_fc_points_et_12_lines, 
                                        drop_field=["START_X", "START_Y", "MID_X", "MID_Y", "END_X", "END_Y"])

            # Join fields
            arcpy.AddMessage("Joining width and azimuth fields to pad features...")
            arcpy.JoinField_management(in_data=pad_fc_type_pad_copy_classify, 
                                    in_field="PadName_1", 
                                    join_table=pad_fc_points_et_12_lines, 
                                    join_field="ET_ID", 
                                    fields=["WIDTH", "Azimuth"])

            # Add additional fields
            arcpy.AddMessage("Adding additional fields...")
            arcpy.AddField_management(in_table=pad_fc_type_pad_copy_classify, field_name="Status_ID", field_type="TEXT", field_length=15)
            arcpy.AddField_management(in_table=pad_fc_type_pad_copy_classify, field_name="Sump_1_ID", field_type="TEXT", field_length=15)
            arcpy.AddField_management(in_table=pad_fc_type_pad_copy_classify, field_name="Sump_2_ID", field_type="TEXT", field_length=15)
            arcpy.AddField_management(in_table=pad_fc_type_pad_copy_classify, field_name="Sump_3_ID", field_type="TEXT", field_length=15)
            arcpy.AddField_management(in_table=pad_fc_type_pad_copy_classify, field_name="Sump_4_ID", field_type="TEXT", field_length=15)
            arcpy.AddField_management(in_table=pad_fc_type_pad_copy_classify, field_name="Type", field_type="DOUBLE")
            arcpy.AddField_management(in_table=pad_fc_type_pad_copy_classify, field_name="Azimuth_ID", field_type="TEXT", field_length=15)

            # Calculate field values
            arcpy.AddMessage("Calculating field values...")
            arcpy.CalculateField_management(in_table=pad_fc_type_pad_copy_classify, field="Status_ID", expression="!PadStatus!", expression_type="PYTHON3")
            arcpy.CalculateField_management(in_table=pad_fc_type_pad_copy_classify, field="Sump_1_ID", expression="!Sump!", expression_type="PYTHON3")
            arcpy.CalculateField_management(in_table=pad_fc_type_pad_copy_classify, field="Type", expression="1", expression_type="PYTHON3")
            arcpy.CalculateField_management(in_table=pad_fc_type_pad_copy_classify, field="Azimuth_ID", expression="!PlannedInc!", expression_type="PYTHON3")
            arcpy.CalculateField_management(in_table=pad_fc_type_pad_copy_classify, field="Azimuth_ID", expression="'Vertical' if !Azimuth_ID! == '-90' else 'Inclined'", expression_type="PYTHON3")

            # Export to CSV
            arcpy.AddMessage(f"Exporting results to CSV: {output_csv}")
            arcpy.ExportTable_conversion(
                in_rows=pad_fc_type_pad_copy_classify, 
                out_table=output_csv, 
                field_names="PadName_1;CENTROID_X;CENTROID_Y;Height;COMMENTS;LENGTH;WIDTH;Azimuth;Status_ID;Sump_1_ID;Sump_2_ID;Sump_3_ID;Sump_4_ID;Type;Azimuth_ID;PlannedAHD"
            )

            arcpy.AddMessage("Processing complete!")
            
        except Exception as e:
            arcpy.AddError(f"Error during processing: {str(e)}")
            raise
            
        finally:
            # Clean up in-memory workspace if used
            if processing_location == "In Memory":
                arcpy.AddMessage("Cleaning up in-memory workspace...")
                try:
                    arcpy.Delete_management("in_memory")
                    arcpy.AddMessage("In-memory workspace cleaned up successfully")
                except:
                    arcpy.AddWarning("Could not clean up in-memory workspace completely")
        
        return

    def PolygonToPoints(self, in_features, out_feature_class, convert_option, remove_duplicates=False, calc_point_pos=False, keep_ZM=False):
        """
        Converts a polygon dataset to a point feature class based on the specified conversion option.

        Parameters:
            in_features (str): Path to the input polygon feature class.
            out_feature_class (str): Path to the output point feature class.
            convert_option (str): "Vertex", "Label", "Center", "CenterIn", "DeepestPoint".
            remove_duplicates (bool): If True, removes duplicate points (only for "Vertex").
            calc_point_pos (bool): If True, calculates point position along the polygon boundary (only for "Vertex").
            keep_ZM (bool): If True, retains Z(M) values if the input dataset supports them.
        """
        arcpy.AddMessage(f"Running PolygonToPoints with option: {convert_option}")
        
        valid_options = ["Vertex", "Label", "Center", "CenterIn", "DeepestPoint"]
        if convert_option not in valid_options:
            raise ValueError(f"Invalid conversion option: {convert_option}. Choose from {valid_options}")

        # Delete output if it exists
        if arcpy.Exists(out_feature_class):
            arcpy.Delete_management(out_feature_class)
            arcpy.AddMessage(f"Deleted existing output: {out_feature_class}")

        spatial_ref = arcpy.Describe(in_features).spatialReference
        arcpy.CreateFeatureclass_management(
            out_path=os.path.dirname(out_feature_class),
            out_name=os.path.basename(out_feature_class),
            geometry_type="POINT",
            spatial_reference=spatial_ref,
            has_z="ENABLED" if keep_ZM else "DISABLED",
            has_m="ENABLED" if keep_ZM else "DISABLED"
        )

        # Add fields
        arcpy.AddField_management(out_feature_class, "ET_ORDER", "DOUBLE" if calc_point_pos else "LONG")
        arcpy.AddField_management(out_feature_class, "ET_IDP", "LONG")
        if convert_option == "Vertex":
            arcpy.AddField_management(out_feature_class, "ET_IDR", "TEXT", field_length=50)  # "FID_RingIndex"
        arcpy.AddField_management(out_feature_class, "ET_X", "DOUBLE")
        arcpy.AddField_management(out_feature_class, "ET_Y", "DOUBLE")
        if keep_ZM:
            arcpy.AddField_management(out_feature_class, "ET_Z", "DOUBLE")
            arcpy.AddField_management(out_feature_class, "ET_M", "DOUBLE")

        fields = ["SHAPE@", "ET_ORDER", "ET_IDP", "ET_X", "ET_Y"]
        if convert_option == "Vertex":
            fields.append("ET_IDR")  # Add ring identifier field
        if keep_ZM:
            fields.extend(["ET_Z", "ET_M"])

        with arcpy.da.InsertCursor(out_feature_class, fields) as insert_cursor:
            with arcpy.da.SearchCursor(in_features, ["OID@", "SHAPE@"]) as search_cursor:
                for row in search_cursor:
                    polygon_id, polygon_geom = row
                    new_points = []
                    seen_coords = set()

                    if convert_option == "Vertex":
                        ring_index = 0  # Track ring index

                        for part in polygon_geom:
                            boundary_length = polygon_geom.length if calc_point_pos else None
                            cumulative_length = 0
                            vertex_count = len(part) if part else 0  # Total vertices

                            for i, vertex in enumerate(part):
                                if vertex:  # Skip None vertices (which represent interior rings)
                                    point_tuple = (vertex.X, vertex.Y)
                                    if keep_ZM:
                                        point_tuple += (vertex.Z, vertex.M)

                                    if remove_duplicates and point_tuple in seen_coords:
                                        continue

                                    seen_coords.add(point_tuple)

                                    # Calculate ET_Order: either normalized (0-1) or raw index
                                    et_order = (cumulative_length / boundary_length) if calc_point_pos and boundary_length else i

                                    # Create ET_IDR as "FID_RingIndex"
                                    et_idr = f"{polygon_id}_{ring_index}"

                                    new_points.append((vertex, et_order, et_idr))

                                    # Compute distance for next step
                                    if i < len(part) - 1 and part[i + 1]:
                                        next_point = part[i + 1]
                                        cumulative_length += arcpy.PointGeometry(vertex).distanceTo(arcpy.PointGeometry(next_point))

                            ring_index += 1  # Increment for next ring

                    elif convert_option == "Label":
                        new_points.append((polygon_geom.labelPoint, None, None))

                    elif convert_option == "Center":
                        new_points.append((polygon_geom.centroid, None, None))

                    elif convert_option == "CenterIn":
                        centroid = polygon_geom.centroid
                        new_points.append((centroid if polygon_geom.contains(centroid) else polygon_geom.labelPoint, None, None))

                    elif convert_option == "DeepestPoint":
                        deepest_point, max_distance = None, 0
                        for part in polygon_geom:
                            for vertex in part:
                                if vertex:
                                    distance = min([vertex.distanceTo(boundary) for boundary in polygon_geom.boundary])
                                    if distance > max_distance:
                                        max_distance = distance
                                        deepest_point = vertex
                        if deepest_point:
                            new_points.append((deepest_point, None, None))

                    # Insert new points
                    for point, et_order, et_idr in new_points:
                        row_data = [point, et_order, polygon_id, point.X, point.Y]
                        if convert_option == "Vertex":
                            row_data.append(et_idr)
                        if keep_ZM:
                            row_data.extend([point.Z, point.M])
                        insert_cursor.insertRow(row_data)

        arcpy.AddMessage(f"PolygonToPoints conversion completed: {out_feature_class}")

    def PointsToPolylines(self, in_dataset, out_dataset, polyline_id_field, 
                          Z_value_field=None, M_value_field=None, 
                          order_field=None, link_field=None):
        """
        Converts points to polylines based on a common ID field.

        Parameters:
            in_dataset (str): Path to the input point feature class.
            out_dataset (str): Path to the output polyline feature class.
            polyline_id_field (str): Field that identifies which points belong to the same polyline.
            Z_value_field (str, optional): Field containing Z values.
            M_value_field (str, optional): Field containing M values.
            order_field (str, optional): Field to sort points within each polyline.
            link_field (str, optional): Field to store link information.
        """
        arcpy.AddMessage(f"Running PointsToPolylines with ID field: {polyline_id_field}")

        # Describe the input dataset
        desc = arcpy.Describe(in_dataset)
        spatial_ref = desc.spatialReference
        has_z = Z_value_field is not None or desc.hasZ
        has_m = M_value_field is not None or desc.hasM

        if arcpy.Exists(out_dataset):
            arcpy.Delete_management(out_dataset)
            arcpy.AddMessage(f"Deleted existing output: {out_dataset}")
            
        # Create an empty polyline feature class
        arcpy.CreateFeatureclass_management(
            out_path=os.path.dirname(out_dataset),
            out_name=os.path.basename(out_dataset),
            geometry_type="POLYLINE",
            spatial_reference=spatial_ref,
            has_z="ENABLED" if has_z else "DISABLED",
            has_m="ENABLED" if has_m else "DISABLED"
        )

        # Add required fields
        arcpy.AddField_management(out_dataset, "ET_ID", "TEXT")
        if link_field:
            arcpy.AddField_management(out_dataset, "ET_FromAtt", "TEXT")
            arcpy.AddField_management(out_dataset, "ET_ToAtt", "TEXT")

        # Prepare fields for cursor
        fields = ["SHAPE@", polyline_id_field]
        if order_field:
            fields.append(order_field)
        if link_field:
            fields.append(link_field)
        if Z_value_field:
            fields.append(Z_value_field)
        if M_value_field:
            fields.append(M_value_field)

        # Read points into dictionary grouped by Polyline ID
        points_dict = {}
        with arcpy.da.SearchCursor(in_dataset, fields) as cursor:
            for row in cursor:
                polyline_id = row[1]
                shape = row[0]
                
                # Set default values
                order_val = 0
                link_val = None
                
                # Get values if fields are provided
                field_index = 2
                if order_field:
                    order_val = row[field_index]
                    field_index += 1
                if link_field:
                    link_val = row[field_index]
                    field_index += 1

                if polyline_id not in points_dict:
                    points_dict[polyline_id] = []

                points_dict[polyline_id].append((shape, order_val, link_val))

        # Create polylines from points
        insert_fields = ["SHAPE@", "ET_ID"]
        if link_field:
            insert_fields.extend(["ET_FromAtt", "ET_ToAtt"])

        with arcpy.da.InsertCursor(out_dataset, insert_fields) as insert_cursor:
            for polyline_id, points in points_dict.items():
                if order_field:
                    points.sort(key=lambda x: x[1])  # Sort by order field if provided

                polyline = arcpy.Array([p[0].firstPoint for p in points])
                first_link = points[0][2] if link_field else None
                last_link = points[-1][2] if link_field else None

                insert_values = [arcpy.Polyline(polyline), polyline_id]
                if link_field:
                    insert_values.extend([first_link, last_link])

                insert_cursor.insertRow(insert_values)

        arcpy.AddMessage(f"PointsToPolylines conversion completed: {out_dataset}")
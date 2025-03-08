import arcpy
import os

def PolygonToPoints(input_dataset, out_feature_class, conversion_option, remove_duplicates=False, calc_point_pos=False, keep_ZM=False):
    """
    Converts a polygon dataset to a point feature class based on the specified conversion option.

    Parameters:
        input_dataset (str): Path to the input polygon feature class.
        out_feature_class (str): Path to the output point feature class.
        conversion_option (str): "Vertex", "Label", "Center", "CenterIn", "DeepestPoint".
        remove_duplicates (bool): If True, removes duplicate points (only for "Vertex").
        calc_point_pos (bool): If True, calculates point position along the polygon boundary (only for "Vertex").
        keep_ZM (bool): If True, retains Z(M) values if the input dataset supports them.

    Returns:
        None
    """
    valid_options = ["Vertex", "Label", "Center", "CenterIn", "DeepestPoint"]
    if conversion_option not in valid_options:
        raise ValueError(f"Invalid conversion option: {conversion_option}. Choose from {valid_options}")

    # Delete output if it exists
    if arcpy.Exists(out_feature_class):
        arcpy.Delete_management(out_feature_class)
        print(f"Deleted existing output: {out_feature_class}")

    spatial_ref = arcpy.Describe(input_dataset).spatialReference
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
    if conversion_option == "Vertex":
        arcpy.AddField_management(out_feature_class, "ET_IDR", "TEXT", field_length=50)  # "FID_RingIndex"
    arcpy.AddField_management(out_feature_class, "ET_X", "DOUBLE")
    arcpy.AddField_management(out_feature_class, "ET_Y", "DOUBLE")
    if keep_ZM:
        arcpy.AddField_management(out_feature_class, "ET_Z", "DOUBLE")
        arcpy.AddField_management(out_feature_class, "ET_M", "DOUBLE")

    fields = ["SHAPE@", "ET_ORDER", "ET_IDP", "ET_X", "ET_Y"]
    if conversion_option == "Vertex":
        fields.append("ET_IDR")  # Add ring identifier field
    if keep_ZM:
        fields.extend(["ET_Z", "ET_M"])

    with arcpy.da.InsertCursor(out_feature_class, fields) as insert_cursor:
        with arcpy.da.SearchCursor(input_dataset, ["OID@", "SHAPE@"]) as search_cursor:
            for row in search_cursor:
                polygon_id, polygon_geom = row
                new_points = []
                seen_coords = set()

                if conversion_option == "Vertex":
                    ring_index = 0  # Track ring index

                    for part in polygon_geom:
                        boundary_length = polygon_geom.length if calc_point_pos else None
                        cumulative_length = 0
                        vertex_count = len(part) if part else 0  # Total vertices

                        for i, vertex in enumerate(part):
                            point_tuple = (vertex.X, vertex.Y, vertex.Z if keep_ZM else None, vertex.M if keep_ZM else None)

                            if remove_duplicates and point_tuple in seen_coords:
                                continue

                            seen_coords.add(point_tuple)

                            # Calculate ET_Order: either normalized (0-1) or raw index
                            et_order = (cumulative_length / boundary_length) if calc_point_pos and boundary_length else i

                            # Create ET_IDR as "FID_RingIndex"
                            et_idr = f"{polygon_id}_{ring_index}"

                            new_points.append((vertex, et_order, et_idr))

                            # Compute distance for next step
                            if i < len(part) - 1:
                                next_point = part[i + 1]
                                cumulative_length += arcpy.PointGeometry(vertex).distanceTo(arcpy.PointGeometry(next_point))

                        ring_index += 1  # Increment for next ring

                elif conversion_option == "Label":
                    new_points.append((polygon_geom.labelPoint, None, None))

                elif conversion_option == "Center":
                    new_points.append((polygon_geom.centroid, None, None))

                elif conversion_option == "CenterIn":
                    centroid = polygon_geom.centroid
                    new_points.append((centroid if polygon_geom.contains(centroid) else polygon_geom.labelPoint, None, None))

                elif conversion_option == "DeepestPoint":
                    deepest_point, max_distance = None, 0
                    for part in polygon_geom:
                        for vertex in part:
                            distance = min([vertex.distanceTo(boundary) for boundary in polygon_geom.boundary])
                            if distance > max_distance:
                                max_distance = distance
                                deepest_point = vertex
                    if deepest_point:
                        new_points.append((deepest_point, None, None))

                # Insert new points
                for point, et_order, et_idr in new_points:
                    row_data = [point, et_order, polygon_id, point.X, point.Y]
                    if conversion_option == "Vertex":
                        row_data.append(et_idr)
                    if keep_ZM:
                        row_data.extend([point.Z, point.M])
                    insert_cursor.insertRow(row_data)

    print(f"Conversion completed: {out_feature_class}")

# Example Usage:
# PolygonToPoints("input_polygon.shp", "output_points.shp", "Vertex", remove_duplicates=True, calc_point_pos=True, keep_ZM=True)

# Example Usage:
# PolygonToPoints(r"C:\Users\giris\Documents\ArcGIS\Projects\MyProject\lam.shp", r"C:\Users\giris\Documents\ArcGIS\Projects\MyProject\output_points.shp", "Vertex", remove_duplicates=True, calc_point_pos=True, keep_ZM=True)
input_dataset = r"C:\Users\giris\Documents\ArcGIS\Projects\MyProject\lam.shp"
out_feature_class = r"C:\Users\giris\Documents\ArcGIS\Projects\MyProject\output_v_points.shp"
conversion_option = "Vertex"

PolygonToPoints(input_dataset=input_dataset,
                out_feature_class=out_feature_class,
                conversion_option=conversion_option,
                remove_duplicates=True,
                calc_point_pos=False,
                keep_ZM=False)



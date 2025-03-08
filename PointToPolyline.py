import os
import arcpy

def PointToPolyline(input_dataset, out_feature_class, polylineID_field, 
                    Z_value_field=None, M_value_field=None, 
                    order_field=None, link_field=None):

    # Describe the input dataset
    desc = arcpy.Describe(input_dataset)
    spatial_ref = desc.spatialReference
    has_z = Z_value_field is not None or desc.hasZ
    has_m = M_value_field is not None or desc.hasM

    if arcpy.Exists(out_feature_class):
        arcpy.Delete_management(out_feature_class)
    # Create an empty polyline feature class
    arcpy.CreateFeatureclass_management(
        out_path=os.path.dirname(out_feature_class),
        out_name=os.path.basename(out_feature_class),
        geometry_type="POLYLINE",
        spatial_reference=spatial_ref,
        has_z="ENABLED" if has_z else "DISABLED",
        has_m="ENABLED" if has_m else "DISABLED"
    )

    # Add required fields
    arcpy.AddField_management(out_feature_class, "ET_ID", "TEXT")
    if link_field:
        arcpy.AddField_management(out_feature_class, "ET_FromAtt", "TEXT")
        arcpy.AddField_management(out_feature_class, "ET_ToAtt", "TEXT")

    # Prepare fields for cursor
    fields = ["SHAPE@", polylineID_field]
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
    with arcpy.da.SearchCursor(input_dataset, fields) as cursor:
        for row in cursor:
            polyline_id = row[1]
            order_val = row[2] if order_field else 0
            shape = row[0]
            link_val = row[3] if link_field else None

            if polyline_id not in points_dict:
                points_dict[polyline_id] = []

            points_dict[polyline_id].append((shape, order_val, link_val))

    # Create polylines from points
    insert_fields = ["SHAPE@", "ET_ID"]
    if link_field:
        insert_fields.extend(["ET_FromAtt", "ET_ToAtt"])

    with arcpy.da.InsertCursor(out_feature_class, insert_fields) as insert_cursor:
        for polyline_id, points in points_dict.items():
            points.sort(key=lambda x: x[1])  # Sort by order field if provided

            polyline = arcpy.Array([p[0].firstPoint for p in points])
            first_link = points[0][2] if link_field else None
            last_link = points[-1][2] if link_field else None

            insert_values = [arcpy.Polyline(polyline), polyline_id]
            if link_field:
                insert_values.extend([first_link, last_link])

            insert_cursor.insertRow(insert_values)

    print(f"Polyline feature class created: {out_feature_class}")

# Example usage:
# PointToPolyline("input_points.shp", "output_polylines.shp", "PolylineID",
#                 Z_value_field=None, M_value_field=None,
#                 order_field="PointOrder", link_field="LinkField")

# Example usage:

input_dataset = r"C:\Users\giris\Documents\ArcGIS\Projects\MyProject\output_v_points.shp"
out_feature_class = r"C:\Users\giris\Documents\ArcGIS\Projects\MyProject\output_va_points.shp"
conversion_option = "Vertex"

# PointToPolyline(input_dataset=input_dataset, out_feature_class=out_feature_class, polylineID_field="ET_IDR",
#                 order_field="ET_ORDER")

PointToPolyline(input_dataset=input_dataset, out_feature_class=out_feature_class,polylineID_field="ET_IDR",
                Z_value_field=None, M_value_field=None,
                order_field="ET_ORDER", link_field="")

# PointToPolyline(input_dataset=input_dataset, out_feature_class=out_feature_class, polylineID_field="ET_IDR",
#                 order_field="ET_ORDER", link_field=None, Z_value_field=None, M_value_field=None)
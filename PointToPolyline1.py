import arcpy

def point_to_polyline(input_dataset, out_feature_class, polylineID_field, 
                       z_value_field=None, m_value_field=None, 
                       order_field=None, link_field=None):
    try:
        arcpy.env.overwriteOutput = True
        
        # Determine spatial reference from input
        spatial_ref = arcpy.Describe(input_dataset).spatialReference
        
        # Set geometry type based on Z and M fields
        has_z = bool(z_value_field)
        has_m = bool(m_value_field)
        
        # Create empty polyline feature class
        arcpy.CreateFeatureclass_management(
            out_path=arcpy.Describe(out_feature_class).path,
            out_name=arcpy.Describe(out_feature_class).name,
            geometry_type="POLYLINE",
            template=input_dataset,
            spatial_reference=spatial_ref,
            has_z=has_z,
            has_m=has_m
        )
        
        # Add required fields
        arcpy.AddField_management(out_feature_class, "ET_ID", "TEXT")
        if link_field:
            arcpy.AddField_management(out_feature_class, "ET_FromAtt", "TEXT")
            arcpy.AddField_management(out_feature_class, "ET_ToAtt", "TEXT")
        
        # Read input points and group by polyline ID
        points_dict = {}
        with arcpy.da.SearchCursor(input_dataset, ["SHAPE@", polylineID_field, order_field, link_field, z_value_field, m_value_field]) as cursor:
            for row in cursor:
                shape, poly_id, order, link, z, m = row
                if poly_id not in points_dict:
                    points_dict[poly_id] = []
                points_dict[poly_id].append((shape, order, link, z, m))
        
        # Create polylines and write to output feature class
        with arcpy.da.InsertCursor(out_feature_class, ["SHAPE@", "ET_ID", "ET_FromAtt", "ET_ToAtt"]) as insert_cursor:
            for poly_id, points in points_dict.items():
                if len(points) < 2:
                    continue
                
                # Sort points by order field if available
                if order_field:
                    points.sort(key=lambda x: x[1] if x[1] is not None else 0)
                
                # Create polyline
                polyline = arcpy.Polyline(arcpy.Array([p[0] for p in points]), spatial_ref, has_z=has_z, has_m=has_m)
                
                # Extract first and last link values
                from_att = points[0][2] if link_field else None
                to_att = points[-1][2] if link_field else None
                
                # Insert new polyline feature
                insert_cursor.insertRow((polyline, poly_id, from_att, to_att))
        
        arcpy.AddMessage("Polyline feature class created successfully!")
    except Exception as e:
        arcpy.AddError(f"Error: {str(e)}")

if __name__ == "__main__":
    # Get parameters from script tool
    input_dataset = arcpy.GetParameterAsText(0)
    out_feature_class = arcpy.GetParameterAsText(1)
    polylineID_field = arcpy.GetParameterAsText(2)
    z_value_field = arcpy.GetParameterAsText(3)
    m_value_field = arcpy.GetParameterAsText(4)
    order_field = arcpy.GetParameterAsText(5)
    link_field = arcpy.GetParameterAsText(6)
    
    point_to_polyline(input_dataset, out_feature_class, polylineID_field, z_value_field, m_value_field, order_field, link_field)

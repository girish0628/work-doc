import arcpy, os

import "./PolygonToPoints.py"
import "./PointsToPolylines.py"

pad_fc_path = ""
classify_fc_path = ""
pad_fc_type_pad_classify_drop = []

arcpy.Select_analysis(in_features=pad_fc_path, out_feature_class="pad_fc_type_pad", where_clause="PolyType = 'Pad'")

arcpy.CopyFeatures_management(in_features="pad_fc_type_pad", out_feature_class="pad_fc_type_pad_copy")

arcpy.SpatialJoin_analysis(target_features="pad_fc_type_pad_copy", join_features=classify_fc_path, out_feature_class="pad_fc_type_pad_copy_classify", join_operation="JOIN_ONE_TO_ONE", join_type="KEEP_ALL", match_option="INTERSECT", search_radius="", distance_field_name="")

arcpy.DeleteField_management(in_table="pad_fc_type_pad_copy_classify", drop_field=pad_fc_type_pad_classify_drop)

arcpy.AddGeometryAttributes_management(Input_Features="pad_fc_type_pad_copy_classify", Geometry_Properties="CENTROID")



arcpy.AddField_management(in_table="pad_fc_type_pad_copy_classify", field_name="Height", field_type="DOUBLE")
arcpy.AddField_management(in_table="pad_fc_type_pad_copy_classify", field_name="COMMENTS", field_type="TEXT")

arcpy.CalculateField_management(in_table="pad_fc_type_pad_copy_classify", field="Height", expression="!PlannedAHD!", expression_type="PYTHON_9.3")
arcpy.CalculateField_management(in_table="pad_fc_type_pad_copy_classify", field="COMMENTS", expression="'Sump ' + !Sump! + ' Dip ' + !PlannedInc! + ' Azi ' + !PlannedAzi!+ ' Depth ' + !PlannedDep!", expression_type="PYTHON_9.3")

arcpy.DeleteField_management(in_table="pad_fc_type_pad_copy_classify", drop_field=["PlannedAHD", "PlannedAzi", "PlannedDep"])

PolygonToPoints(in_features="pad_fc_type_pad_copy_classify", out_feature_class="pad_fc_type_pad_copy_classify_points", convert_option="Vertex", remove_duplicates=True, calc_point_pos=False, keep_z=False, keep_m=False)

arcpy.Select_analysis(in_features="pad_fc_type_pad_copy_classify_points", out_feature_class="pad_fc_points_et_01", where_clause="ET_ORDER = 0 OR ET_ORDER = 1")

PointsToPolylines(in_dataset="pad_fc_points_et_01", out_dataset="pad_fc_points_et_01_lines", polyline_id_field="PadName_1")

arcpy.AddGeometryAttributes_management(Input_Features="pad_fc_points_et_01_lines", Geometry_Properties=["LENGTH"])

arcpy.JoinField_management(in_data="pad_fc_type_pad_copy_classify", in_field="PadName_1", join_table="pad_fc_points_et_01_lines", join_field="ET_ID", fields=["LENGTH"])

arcpy.Select_analysis(in_features="pad_fc_type_pad_copy_classify_points", out_feature_class="pad_fc_points_et_12", where_clause="ET_ORDER = 1 OR ET_ORDER = 2")

arcpy.CopyFeatures_management(in_features="pad_fc_points_et_12", out_feature_class="pad_fc_points_et_12_copy")

PointsToPolylines(in_dataset="pad_fc_points_et_12_copy", out_dataset="pad_fc_points_et_12_lines", polyline_id_field="PadName_2", order_field="ET_ORDER")

arcpy.AddGeometryAttributes_management(Input_Features="pad_fc_points_et_12_lines", Geometry_Properties=["LENGTH", "LINE_START_MID_END"])

arcpy.AddField_management(in_table="pad_fc_points_et_12_lines", field_name="Azimuth", field_type="DOUBLE")

arcpy.CalculateField_management(in_table="pad_fc_points_et_12_lines", field="Azimuth", expression="180-math.degrees(math.atan2((!END_Y! - !START_Y!),(!END_X! - !START_X!)))", expression_type="PYTHON_9.3")

arcpy.AlterField_management(in_table="pad_fc_points_et_12_lines", field="LENGTH", new_field_name="WIDTH")

arcpy.DeleteField_management(in_table="pad_fc_points_et_12_lines", drop_field=["START_X", "START_Y", "MID_X", "MID_Y", "END_X", "END_Y"])

arcpy.JoinField_management(in_data="pad_fc_type_pad_copy_classify", in_field="PadName_1", join_table="pad_fc_points_et_12_lines", join_field="ET_ID", fields=["WIDTH", "Azimuth"])

arcpy.AddField_management(in_table="pad_fc_type_pad_copy_classify", field_name="Status_ID", field_type="TEXT", field_length=15)
arcpy.AddField_management(in_table="pad_fc_type_pad_copy_classify", field_name="Sump_1_ID", field_type="TEXT", field_length=15)
arcpy.AddField_management(in_table="pad_fc_type_pad_copy_classify", field_name="Sump_2_ID", field_type="TEXT", field_length=15)
arcpy.AddField_management(in_table="pad_fc_type_pad_copy_classify", field_name="Sump_3_ID", field_type="TEXT", field_length=15)
arcpy.AddField_management(in_table="pad_fc_type_pad_copy_classify", field_name="Sump_4_ID", field_type="TEXT", field_length=15)
arcpy.AddField_management(in_table="pad_fc_type_pad_copy_classify", field_name="Type", field_type="DOUBLE")
arcpy.AddField_management(in_table="pad_fc_type_pad_copy_classify", field_name="Azimuth_ID", field_type="TEXT", field_length=15)



arcpy.CalculateField_management(in_table="pad_fc_type_pad_copy_classify", field="Status_ID", expression="!PadStatus!", expression_type="PYTHON_9.3")
arcpy.CalculateField_management(in_table="pad_fc_type_pad_copy_classify", field="Sump_1_ID", expression="!Sump!", expression_type="PYTHON_9.3")
arcpy.CalculateField_management(in_table="pad_fc_type_pad_copy_classify", field="Type", expression="1", expression_type="PYTHON_9.3")
arcpy.CalculateField_management(in_table="pad_fc_type_pad_copy_classify", field="Azimuth_ID", expression="!PlannedInc!", expression_type="PYTHON_9.3")
arcpy.CalculateField_management(in_table="pad_fc_type_pad_copy_classify", field="Azimuth_ID", expression="'Vertical' if !Azimuth_ID! == '-90' else 'Inclined'", expression_type="PYTHON_9.3")

arcpy.ExportTable_conversion(in_rows="pad_fc_type_pad_copy_classify", out_table="C:\\Stuff\\BHP\\Geoscience\\out.csv", field_names="PadName_1;CENTROID_X;CENTROID_Y;Height;COMMENTS;LENGTH;WIDTH;Azimuth;Status_ID;Sump_1_ID;Sump_2_ID;Sump_3_ID;Sump_4_ID;Type;Azimuth_ID;PlannedAHD")
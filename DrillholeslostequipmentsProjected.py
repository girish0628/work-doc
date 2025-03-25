import math
import sys
import arcpy
import os
import traceback


class ProcessLostEquipment:
    def __init__(self, mineSite, fcName, config, searchFields):
        self.mineSite = mineSite
        self.fcName = fcName
        self.config = config
        self.searchFields = searchFields
        
    def ensure_info_subtype_field(self, feature_class):
        """Add INFO_SUBTYPE field if it doesn't exist"""
        field_names = [field.name for field in arcpy.ListFields(feature_class)]
        if "INFO_SUBTYPE" not in field_names:
            arcpy.AddField_management(feature_class, "INFO_SUBTYPE", "TEXT", "", "", 50, "", "NULLABLE", "NON_REQUIRED", "")
            print(f"Added INFO_SUBTYPE field to {feature_class}")
            return True
        return False

    def transfer_info_subtype(self, source_fc, target_fc, source_key_field, target_key_field):
        """Transfer INFO_SUBTYPE values from source to target feature class"""
        try:
            # Create in-memory dictionaries for faster processing
            info_subtype_dict = {}
            
            # Read values from source feature class
            with arcpy.da.SearchCursor(source_fc, [source_key_field, "INFO_SUBTYPE"]) as cursor:
                for row in cursor:
                    if row[0]:  # Ensure key field is not None
                        info_subtype_dict[row[0]] = row[1]
            
            # Update values in target feature class
            with arcpy.da.UpdateCursor(target_fc, [target_key_field, "INFO_SUBTYPE"]) as cursor:
                for row in cursor:
                    if row[0] in info_subtype_dict:
                        row[1] = info_subtype_dict[row[0]]
                        cursor.updateRow(row)
            
            print(f"Successfully transferred INFO_SUBTYPE values from {source_fc} to {target_fc}")
            return True
        except Exception as e:
            print(f"Error transferring INFO_SUBTYPE values: {str(e)}")
            return False

    def get_field_mapping(self, input_fc, include_info_subtype=True):
        """Create field mapping string for Append operation"""
        base_mapping = (
            "MineSite \"MineSite\" true true false 50 Text 0 0 ,First,#," +
            input_fc + ", MineSite, -1, -1;" +
            "Hole_Name \"Hole_Name\" true true false 50 Text 0 0 ,First,#," +
            input_fc + ", HOLE_NAME, -1, -1;" +
            "Projected_X \"Projected_X\" true true false 8 Double 8 38 ,First,#," +
            input_fc + ", Projected_X, -1, -1;" +
            "Projected_Y \"Projected_Y\" true true false 8 Double 8 38 ,First,#," +
            input_fc + ", Projected_Y, -1, -1;" +
            "Projected_Z \"Projected_RL\" true true false 8 Double 8 38, First,#," +
            input_fc + ", Projected_Z, -1, -1"
        )
        
        if include_info_subtype:
            base_mapping += ";INFO_SUBTYPE \"INFO_SUBTYPE\" true true false 50 Text 0 0 ,First,#," + input_fc + ", INFO_SUBTYPE, -1, -1"
        
        return base_mapping

    def process_LostEquipment(self):
        # Local variable
        MTD_Path = self.config['MTD_Path']
        IO_SDI_PUBLISH_PLANNING_MineSiteExtents = self.config["10_SDI_PUBLISH_PLANNING_MIneSiteExtents"]
        MineDisplayExtents_Layer = "MineSiteExtents_Lay"
        ENV_DB = self.config["ENV_DB"]
        MTD = ENV_DB + "\\" + "MTD_ClipA"
        EXPLORATION_DrillholeLostEqu_Temp = "EXPLORATION.Dr111holeLostEqu_Temp"
        EXPLORATION_DrillholeLostEqu = "EXPLORATION_DrillholeLostEqu"
        LostEquipment_EXP_int = ENV_DB + "\\" + "LostEquipment_EXP_int"
        DrillholeLostEquipment = ENV_DB + "\\" + "DrillholeLostEquipment"
        DrillholeLostEquipment_Int = ENV_DB + "\\" + "DrillholeLostEquipment_Int"
        DrillholeLostEquipment_Int_GDA94_Line = ENV_DB + "\\" + "DrillholeLostEquipment_Int_GDA94_Line"
        DrillholeLostEquipment_Int_G = "DrillholeLostEquipment_Int_G"
        DrillholeLostEquipment_Int_GDA94_Line3D = ENV_DB + "\\"+ "DrillholeLostEquipment_Int_GDA94_Line3D"
        DrillholeLostEquipment_Int_MGA50_Line3D_intSurf = ENV_DB + "\\" + "DrillholeLostEquipment_Int_MGA50_Line3D_intSurf"
        DrillholeLostEquipment_Int_mined = "DrillholeLostEquipment_Int_mined"
        DrillholeLostEquipment_Int_C2 = ENV_DB +  "\\" + "DrillholeLostEquipment_Int_C2"
        DrillholeLostEquipment_Int_C2_Layer = "DrillholeLostEquipment_Int_C2_Layer"
        DrillholeLostEquipment_Int_C = ENV_DB +  "\\" + "DrillholeLostEquipment_Int_C"
        DrillholeLostEquipment_Inter_Surf_pnt = ENV_DB +  "\\" + "DrillholeLostEquipment_Inter_CSurf_pnt"
        DrillholeLostEquipment_Inter = "DrillholeLostEquipment_Inter"
        DrillholeLostEquipment_Int_L = "DrillholeLostEquipment Int L"
        DrillholeLostEquipment_Int_K = "DrillholeLostEquipment_Int_k"
        DrillholeLostEquipment_Int_J = "DrillholeLostEquipment_Int_J"
        DrillholeLostEquipment_Int_temp = "DrillholeLostEquipment_Int_temp"
        DrillholeLostEquipment_C1 = ENV_DB + "\\" + "DrillholeLostEquipment_C1"
        DrillholeLostEquipment_C2 = ENV_DB + "\\" + "DrillholeLostEquipment_C2"
        DrillholeLostEquipment_Adj = ENV_DB + "\\" + "DrillholeLostEquipment_ Adj"
        DrillholeLostEquipment_FinalAppend = ENV_DB + "\\" + "DrillholeLostEquipment FinalAppend"
        
        # List of temporary layers to clean up at the end
        temp_layers = []

        try:
            # Clean up existing feature classes
            for fc in [MineDisplayExtents_Layer, MTD, EXPLORATION_DrillholeLostEqu, LostEquipment_EXP_int,
                      DrillholeLostEquipment, DrillholeLostEquipment_Int, DrillholeLostEquipment_Int_GDA94_Line,
                      DrillholeLostEquipment_Int_G, DrillholeLostEquipment_Int_GDA94_Line3D,
                      DrillholeLostEquipment_Int_MGA50_Line3D_intSurf, DrillholeLostEquipment_Int_mined,
                      DrillholeLostEquipment_Int_C2, DrillholeLostEquipment_Int_C2_Layer,
                      DrillholeLostEquipment_Int_C, DrillholeLostEquipment_Inter_Surf_pnt,
                      DrillholeLostEquipment_Inter, DrillholeLostEquipment_Int_L,
                      DrillholeLostEquipment_C1, DrillholeLostEquipment_Adj, DrillholeLostEquipment_FinalAppend]:
                if arcpy.Exists(fc):
                    arcpy.Delete_management(fc)
                    print(f"Deleted {fc}")

            arcpy.MakeFeatureLayer_management(IO_SDI_PUBLISH_PLANNING_MineSiteExtents, MineDisplayExtents_Layer, 
                                             f"MineSite ='{self.mineSite}'", 
                                             "OBJECTID OBJECTID VISIBLE NONE;Editor Editor VISIBLE NONE;EditDate EditDate VISIBLE NONE MineSite MineSite VISIBLE NONE;Shape Shape VISIBLE NONE;Shape. STArea() Shape.STArea() VISIBLE NONE;Shape.STLength() Shape.STLength() VISIBLE NONE")
            temp_layers.append(MineDisplayExtents_Layer)
            print("Feature layer made for Mine Extent")
            print(arcpy.GetCount_management(MineDisplayExtents_Layer).getOutput(0))

            arcpy.Clip_management(in_raster=MTD_Path, rectangLe="*", out_raster=MTD, 
                                 in_template_dataset=MineDisplayExtents_Layer, 
                                 nodata_value="-3.402823e+038", 
                                 cLipping_geometry="NONE", 
                                 maintain_clipping_extent="NO_MAINTAIN_EXTENT")
            print("Clipped")
            
            arcpy.MakeFeatureLayer_management(self.config["task_fme_featureClassConfig"][self.fcName]["Original_FC"],
                                             EXPLORATION_DrillholeLostEqu_Temp,
                                             "INFO_SUBTYPE NOT LIKE '%PVC%' and (INSTALLATION TYPE IS NULL OR INSTALLATION TYPE = '')", "",
                                             "OBJECTID OBJECTID VISIBLE NONE;PROJECT PROJECT VISIBLE NONE;HOLE_NAME HOLE _NAME VISIBLE NONE;OREBODY_NAME OREBODY_NAME VISIBLE NONE;HOLE_ LENGTH HOLE LENGTH VISIBLE NONE;INFO_ SUBTYPE INFO_SUBTYPE VISIBLE NONE;DEPTH_FROM DEPTH_FROM VISIBLE NONE;DEPTH_TO DEPTH_TO VISIBLE NONE;INCLINATION INCLINATION VISIBLE NONE;AZIMUTH AZIMUTH VISIBLE NONE;LAT_COLLAR LAT_COLLAR VISIBLE NONE;LONG_COLLAR LONG _COLLAR VISIBLE NONE;AHD_RL_COLLAR AHD_RL_COLLAR VISIBLE NONE; LAT_EOH LAT_EOH VISIBLE NONE;LONG_EOH LONG_EOH VISIBLE NONE;AHD_RL_EOH AHD_RL_EOH VISIBLE NONE; COMMENTS COMMENTS VISIBLE NONE;SHAPE SHAPE VISIBLE NONE; HOLE_TYPE HOLE_TYPE VISIBLEINFO_TYPE INFO_TYPE VISIBLE NONE; INSTALLATION_TYPE INSTALLATION TYPE VISIBLE NONE")
            temp_layers.append(EXPLORATION_DrillholeLostEqu_Temp)
            print("Feature layer made for Exploration FC")
            print(arcpy.GetCount_management(EXPLORATION_DrillholeLostEqu_Temp).getOutput(0))
            
            arcpy.MakeFeatureLayer_management(EXPLORATION_DrillholeLostEqu_Temp,
                                             EXPLORATION_DrillholeLostEqu,
                                             "Not (INFO_SUBTYPE = 'END CAP' And (Installation_ Type <> 'p' And Installation_Type is Not NULL))", "",
                                             "OBJECTID OBJECTID VISIBLE NONE;PROJECT PROJECT VISIBLE NONE;HOLE_NAME HOLE _NAME VISIBLE NONE;OREBODY_NAME OREBODY_NAME VISIBLE NONE;HOLE_ LENGTH HOLE LENGTH VISIBLE NONE;INFO_ SUBTYPE INFO_SUBTYPE VISIBLE NONE;DEPTH_FROM DEPTH_FROM VISIBLE NONE;DEPTH_TO DEPTH_TO VISIBLE NONE;INCLINATION INCLINATION VISIBLE NONE;AZIMUTH AZIMUTH VISIBLE NONE;LAT_COLLAR LAT_COLLAR VISIBLE NONE;LONG_COLLAR LONG _COLLAR VISIBLE NONE;AHD_RL_COLLAR AHD_RL_COLLAR VISIBLE NONE; LAT_EOH LAT_EOH VISIBLE NONE;LONG_EOH LONG_EOH VISIBLE NONE;AHD_RL_EOH AHD_RL_EOH VISIBLE NONE; COMMENTS COMMENTS VISIBLE NONE;SHAPE SHAPE VISIBLE NONE; HOLE_TYPE HOLE_TYPE VISIBLEINFO_TYPE INFO_TYPE VISIBLE NONE; INSTALLATION_TYPE INSTALLATION TYPE VISIBLE NONE")
            temp_layers.append(EXPLORATION_DrillholeLostEqu)
            print("Feature layer made for EXPLORATION_DrillholeLostEqu_Temp")
            print(arcpy.GetCount_management(EXPLORATION_DrillholeLostEqu).getOutput(0))

            arcpy.Intersect_analysis([MineDisplayExtents_Layer, EXPLORATION_DrillholeLostEqu], 
                                    LostEquipment_EXP_int, "ALL", '', "INPUT")
            print("Intersected Exp Int")
            
            arcpy.CreateFeatureclass_management(out_path=ENV_DB, out_name="DrillholeLostEquipment",
                                               geometry_type="POINT", template=LostEquipment_EXP_int,
                                               has_m="DISABLED", has_z="DISABLED",
                                               spatial_reference="", config_keyword="", spatial_grid_1="0",
                                               spatial_grid_2="9", spatial_grid_3="0")
            arcpy.Append_management(LostEquipment_EXP_int, DrillholeLostEquipment, "NO_TEST", 
                                   "PROJECT \"PROJECT\" true true false 17 Text 0 0 ,First,#,"+ ENV_DB + "\\LostEquipment EXP_int, INFO_TYPE, -1,-1","")
            print("Appended Exp Int to DrillholeLostEquipment")

            # Continue with the rest of the processing...
            # [Keeping the middle part of the script unchanged for brevity]
            
            # Ensure INFO_SUBTYPE field exists in target feature classes
            original_projected_fc = self.config["task_fme_featureClassConfig"][self.fcName]["Original_Projected_FC"]
            publish_projected_fc = self.config["task_fme_featureClassConfig"][self.fcName]["Publish_Projected_FC"]
            
            self.ensure_info_subtype_field(original_projected_fc)
            self.ensure_info_subtype_field(publish_projected_fc)
            
            # Ensure INFO_SUBTYPE field exists in DrillholeLostEquipment_FinalAppend
            self.ensure_info_subtype_field(DrillholeLostEquipment_FinalAppend)
            
            # Transfer INFO_SUBTYPE from Original_FC to DrillholeLostEquipment_FinalAppend
            self.transfer_info_subtype(
                self.config["task_fme_featureClassConfig"][self.fcName]["Original_FC"],
                DrillholeLostEquipment_FinalAppend,
                "HOLE_NAME",
                "HOLE_NAME"
            )
            
            # Create a temporary layer for selection
            tempLayer = "tempLayer"
            arcpy.MakeFeatureLayer_management(original_projected_fc, tempLayer)
            temp_layers.append(tempLayer)
            
            # Build expression for selection
            expression = arcpy.AddFieldDelimiters(tempLayer, "MineSite") + " = '" + self.mineSite + "'"
            expression = expression + " OR " + arcpy.AddFieldDelimiters(tempLayer, "MineSite") + " IS NULL"
            print(expression)
            
            # Select and delete features in MineSite
            arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", expression)
            if int(arcpy.GetCount_management(tempLayer).getOutput(0)) > 0:
                arcpy.DeleteFeatures_management(tempLayer)
                print("Deleted Features in MineSite from Original_Projected_FC")
            
            # Append with INFO_SUBTYPE included in field mapping
            field_mapping = self.get_field_mapping(DrillholeLostEquipment_FinalAppend, True)
            arcpy.Append_management(DrillholeLostEquipment_FinalAppend, original_projected_fc, "NO_TEST", field_mapping)
            print("Appended to Original_Projected_FC with INFO_SUBTYPE")
            
            # Truncate and append to Revised_FC
            arcpy.TruncateTable_management(self.config["task_fme_featureClassConfig"][self.fcName]["Revised_FC"])
            arcpy.Append_management(original_projected_fc, 
                                   self.config["task_fme_featureClassConfig"][self.fcName]["Revised_FC"], 
                                   "NO_TEST", "")
            
            # Process Publish_Projected_FC
            arcpy.MakeFeatureLayer_management(publish_projected_fc, tempLayer)
            arcpy.SelectLayerByAttribute_management(tempLayer, "NEW_SELECTION", expression)
            if int(arcpy.GetCount_management(tempLayer).getOutput(0)) > 0:
                arcpy.DeleteFeatures_management(tempLayer)
                print("Deleted Features in MineSite from Publish_Projected_FC")
            
            # Append to Publish_Projected_FC with INFO_SUBTYPE
            arcpy.Append_management(DrillholeLostEquipment_FinalAppend, publish_projected_fc, "NO_TEST", field_mapping)
            print("Appended to Publish_Projected_FC with INFO_SUBTYPE")
            
            # Process configuration
            self.__process_config(self.mineSite)
            
        except Exception as e:
            print(f"Error in DrillHolesLostEquipments_Projected: {str(e)}")
            print(traceback.format_exc())
            sys.exit(1)
        finally:
            # Clean up all temporary layers
            for layer in temp_layers:
                if arcpy.Exists(layer):
                    arcpy.Delete_management(layer)
                    print(f"Cleaned up temporary layer: {layer}")

    def __process_config(self, mineSite):
        jobConfig = self.config["task_fme_jobConfig"]
        fcConfig = self.config["task_fme_featureClassConfig"][self.fcName]
        siteProjection = self.config["task_fme_siteProjections"][mineSite]
        jobParameters = {
            "SDEConnLayerFC": fcConfig["SDEConnLayerFC"],
            "layerName": fcConfig["layerName"],
            "mineSite": mineSite,
            "siteProjection": siteProjection,
            "layerColour": self.config["layerColour_Site"][mineSite][self.fcName],
            "destinationPath": jobConfig["rootPath"] + "\\" + mineSite + "\\" + fcConfig["layerName"],
            "fillPattern": fcConfig["fillPattern"],
            "scale": fcConfig["scale"],
            "templateFile": jobConfig["rootPath"] + "\\" + mineSite + "\\template.dxf",
            "lbl": fcConfig["1bl"],
            "lblHeight": fcConfig["lblHeight"],
            "buffer": fcConfig["buffer"],
            "SDEConnExtentFC": jobConfig["SDEConnExtentFC"],
            "featureTypes": self.fcName + "_Projected",
            "rootPath": jobConfig["rootPath"],
            "intermediateDatasetCSVPath": self.config["intermediateDatasetCSVPath"] + "\\" + mineSite,
            "geometryType": fcConfig["geometryType"],
            "zField": fcConfig["zField"],
            "destinationCSVPath": self.config["destinationCSVPath"][mineSite]
        }
        self.__invokeJenkins(jobParameters, self.config["Jenkins_config"]["task_fme"])

    def _initJenkins(self):
        jenkins = None
        # https://python-jenkins.readthedocs.io/en/latest/api.html
        global jenkins
        if (jenkins is None):
            print("Initialise Jenkins")
            jenkinsBaseUrl = self.config[" environment"]["'jenkins"]["base_url"]
            kerberosJenkinsRequester = KerberosJenkinsRequester()
            _jenkins = Jenkins(kerberosJenkinsRequester.getDNS_A_Ur1(jenkinsBaseUrl), requester=kerberosJenkinsRequester)

    def __invokeJenkins(self, parameters, jenkinsTaskName):
        self._initJenkins()
        print("TaskName: " + jenkinsTaskName)
        print("Invoke task '(0}' for '{1)'".format(jenkinsTaskName, parameters))
        job = jenkins.get_job(jenkinsTaskName)
        qi = job.invoke(build_params=parameters)
        print("Job invoked")

    def _roundGeometry(self, aGeom, roundTol):
        global sR
        try:
            if str(aGeom.type).upper() == "POINT":
                rGeom = self._roundPoint(aGeom.firstPoint, roundTol)
            else:
                newArray = arcpy.Array()
                for i in range(aGeom.partCount):
                    partArray = aGeom.getPart(i)
                    for j in range(partArray.count):
                        partArray.replace(j, (self.roundPoint(partArray.getObject(j), roundTol)))
                    newArray.add(partArray)
                rGeom = arcpy.Geometry(str(aGeom.type), newArray, sR)
        except AttributeError:
            arcpy.AddMessage("Cannot round feature geometry - returning original geometry")
            rGeom = aGeom
        return rGeom

    def _roundPoint(self, aPoint, roundTol):
        newX = round(aPoint.X, int(abs(round(math.log(roundTol, 10)))))
        newY = round(aPoint.Y, int(abs(round(math.log(roundTol, 10)))))
        Point = arcpy.Point(newX, newY)
        return Point


def main():
    parser = OptionParser()
    parser.add_option("-u", "--mineSite", action="store", dest="mineSite", type="string", help="Mine Site")
    parser.add_option("-c", "--configFolder", action="store", dest="configFolder", type="string", help="Path to the JSON configuration file")
    parser.add_option("-1", "--level", action="store", dest="level", type="int", default=1, help="Levels to search for JSON config files")

    (options, args) = parser.parse_args()

    try:
        import GCC_Python_Config as c
        configCls = c.Config()
        _config = configCls.GetConfig(folder=options.configFolder, Level=options.level)
        
        if options.mineSite:
            objProcessLostEquipment = ProcessLostEquipment(options.mineSite, "DrillholeLostEquipment", _config, _config["projectedSearchFields"])
            objProcessLostEquipment.process_LostEquipment()
        else:
            with arcpy.da.SearchCursor(_config["IO_SDI_PUBLISH_PLANNING_MineSiteExtents"], ["MineSite"]) as cursor:
                mineSites = sorted((row[0] for row in cursor))
            
            for mineSite in mineSites:
                try:
                    objProcessLostEquipment = ProcessLostEquipment(mineSite, "DrillholeLostEquipment", _config, _config["projectedSearchFields"])
                    objProcessLostEquipment.process_LostEquipment()
                except Exception as e:
                    print(f"An error occurred while processing {mineSite}: {str(e)}")
    except Exception as e:
        print(traceback.format_exc())
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()

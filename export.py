import arcpy

# Input Mosaic Dataset
mosaic_dataset = r"C:\path\to\your\mosaic.gdb\your_mosaic_dataset"

# Output File Geodatabase and Table
output_gdb = r"C:\path\to\your\output.gdb"
output_table = f"{output_gdb}\\FootprintTable"

# Create output table schema based on input
arcpy.env.overwriteOutput = True
desc = arcpy.Describe(mosaic_dataset)
fields = [f.name for f in desc.fields if f.type not in ("OID", "Geometry")]  # Exclude OID & Geometry fields

# Create the output table
if arcpy.Exists(output_table):
    arcpy.Delete_management(output_table)
arcpy.CreateTable_management(output_gdb, "FootprintTable")
for field in fields:
    arcpy.AddField_management(output_table, field, desc.fields[fields.index(field)].type)

# Process records efficiently
failed_records = []
batch_size = 5000  # Adjust based on performance testing

with arcpy.da.SearchCursor(mosaic_dataset, fields) as search_cursor, \
     arcpy.da.InsertCursor(output_table, fields) as insert_cursor:
    
    batch = []
    for row in search_cursor:
        try:
            batch.append(row)
            if len(batch) >= batch_size:
                insert_cursor.insertRow(batch)  # Insert in bulk
                batch.clear()
        except Exception as e:
            failed_records.append(row)
            print(f"Skipping record: {row} due to error: {str(e)}")
    
    if batch:  # Insert remaining records
        insert_cursor.insertRow(batch)

# Print failed records if any
if failed_records:
    print(f"Total failed records: {len(failed_records)}")
    for failed in failed_records:
        print(failed)
else:
    print("Export completed without any issues.")

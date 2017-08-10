# -----------------------------------------------
# Name: Create Swath Profile
# Purpose: Creates either a max, min, or mean swath profile raster
# Author: James M Roden
# Created: Sep 2016
# ArcGIS Version: 10.3
# ArcGIS Licence Requirements: Spatial Analyst, 3D Analyst
# Python Version 2.6
# PEP8
# -----------------------------------------------

try:    
    import arcpy
    import sys
    import traceback
    import os

    # Custom exception for spatial analysis and 3D analyst licenses
    class LicenseError(Exception):
        pass

    # Custom exception for number of polylines
    class MoreThanOneLine(Exception):
        pass

    # Get azimuth of polyline function
    def get_line_azimuth(line):
        """
        Return azimuthal angle of line.

        Keyword arguments:
        line    -- polyline
        """
        import math
        for row in arcpy.da.SearchCursor(line, ["SHAPE@"]):
            # Get first point (x, y) and last point (x, y)
            first_x = row[0].firstPoint.X
            last_x = row[0].lastPoint.X
            first_y = row[0].firstPoint.Y
            last_y = row[0].lastPoint.Y
        # Calculate in radians
        radians = math.atan2((last_x - first_x), (last_y - first_y))
        # Convert to degrees
        degrees = (radians * 180) / math.pi
        return degrees

    # Check out Spatial Analyst extension if available
    if arcpy.CheckExtension("spatial") == "Available":
        arcpy.CheckOutExtension("spatial")
        from arcpy.sa import NbrRectangle
        arcpy.AddMessage("Spatial Analyst extension successfully checked out.")
    else:
        # Raise custom error
        raise LicenseError

    # arcpy environment settings
    arcpy.env.workspace = r"in_memory"
    arcpy.env.scratchWorkspace = r"in_memory"
    arcpy.env.overwriteOutput = True

    # ArcGIS Tool Parameters
    profile_line = arcpy.GetParameterAsText(0)
    swath_width = int(arcpy.GetParameterAsText(1))                                       
    in_raster = arcpy.GetParameter(2)
    stat_type = arcpy.GetParameterAsText(3)
    workspace = arcpy.GetParameterAsText(4)
    interpolated_line = arcpy.GetParameter(5)

    in_raster_dataset = arcpy.Raster(in_raster.dataSource)

    # Check if profile_line is one line or one selected line
    result = arcpy.GetCount_management(profile_line)
    if int(result[0]) != 1:
        raise MoreThanOneLine(result)

    # Azimuth angle for raster rotation
    angle = get_line_azimuth(profile_line)

    # Create swath using buffer
    buffer_width = str(swath_width/2) + " meters"
    swath = arcpy.Buffer_analysis(profile_line, None, buffer_width, line_end_type="FLAT")
    arcpy.AddMessage("Swath created")    

    # Create describe object and extract extent rectangle
    desc0 = arcpy.Describe(swath)
    extent = desc0.extent
    swath_rectangle = "{} {} {} {}".format(str(extent.XMin), str(extent.YMin), str(extent.XMax), str(extent.YMax))

    # Create centroid for swath and xy for raster rotation point
    centroid = arcpy.FeatureToPoint_management(swath, None, "CENTROID")
    centroid_x = None
    centroid_y = None
    for row in arcpy.da.SearchCursor(centroid, ["SHAPE@XY"]):
        centroid_x, centroid_y = row[0]
    centroid_coords = str(centroid_x) + " " + str(centroid_y)

    # Clip raster to swatch area
    swath_raster = arcpy.Clip_management(in_raster_dataset, swath_rectangle, None, swath,
                                         clipping_geometry="ClippingGeometry")

    # Rotate raster. Negate angle for anti-clockwise rotation.
    rotated_swath_raster = arcpy.Rotate_management(swath_raster, None, "-{}".format(angle),
                                                   centroid_coords, "BILINEAR")

    # Raster cell size for focal statistics
    desc1 = arcpy.Describe(in_raster_dataset)
    cell_size = desc1.meanCellWidth
    # Double swath width to ensure statistics are run over swath area
    cells_wide = int((swath_width*2) / cell_size)

    # Run focal statistics on rotated swath raster
    # fr used to limit filename size. Classic arcpy issues...
    focal_raster = arcpy.sa.FocalStatistics(rotated_swath_raster, NbrRectangle(cells_wide, 1, "CELL"), stat_type,
                                            "DATA")
    arcpy.AddMessage("{} statistics complete".format(stat_type))

    # Re-rotate raster and re-clip to swath polygon
    rotated_focal_raster = arcpy.Rotate_management(focal_raster, None, angle, centroid_coords, "BILINEAR")
    clipped_focal_raster = arcpy.Clip_management(rotated_focal_raster, swath_rectangle, None, swath,
                                                 clipping_geometry="ClippingGeometry")
    arcpy.AddMessage("Swath raster created")

    if interpolated_line:
        if arcpy.CheckExtension("3D"):
            arcpy.CheckOutExtension("3D")
            arcpy.AddMessage("3D Analyst extension checked out.")
            profile_line_3d = arcpy.InterpolateShape_3d(clipped_focal_raster, profile_line, None)
            output_profile = os.path.join(workspace, "Profile_Line_3D")
            arcpy.CopyFeatures_management(profile_line_3d, output_profile)
        else:
            raise LicenseError

    # Construct name of final output raster
    output_swath = os.path.join(workspace, stat_type)

    # Create output feature class
    arcpy.CopyRaster_management(clipped_focal_raster, output_swath)

except LicenseError:
    error = "Spatial Analyst and/or 3D Extension Unavailable."
    arcpy.AddError(error)
    print error

except MoreThanOneLine:
    # The input has more than 1 line
    error = 'The profile line layer must be either 1 line, or 1 selected line'
    arcpy.AddError(error)
    print error

except:
    e = sys.exc_info()[1]
    arcpy.AddError(e.args[0])
    tb = sys.exc_info()[2]  # Traceback object
    tbinfo = traceback.format_tb(tb)[0]  # Traceback string
    # Concatenate error information and return to GP window
    pymsg = ('PYTHON ERRORS:\nTraceback info:\n' + tbinfo + '\nError Info: \n'
             + str(sys.exc_info()[1]))
    msgs = 'ArcPy ERRORS:\n' + arcpy.GetMessages() + '\n'
    arcpy.AddError(msgs)
    print pymsg

finally:
    # Check in spatial analysis extension
    arcpy.CheckInExtension("spatial")

    # Delete in_memory 
    arcpy.Delete_management("in_memory")

# End of script

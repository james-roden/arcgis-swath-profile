# -----------------------------------------------
# Project: arcigs-swath-profile
# Name: swathprofile
# Purpose: Creates either a max, min, or mean swath profile raster
# Version: 1.0.0
# Author: James M Roden
# Created: Apr 2020
# ArcGIS Version: 10.5
# Python Version 2.7
# PEP8
# -----------------------------------------------

import arcpy
from arcpy.sa import NbrRectangle
import sys
import traceback
import os


# Custom exception for number of polylines
class MoreThanOneLine(Exception):
    pass


# Get azimuth of polyline function
def get_line_azimuth(line):
    """Return azimuthal angle of line.

    Args:
        line - polyline

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


class Toolbox(object):
    def __init__(self):
        """ESRI Stub

        """
        self.label = "swathprofile"
        self.alias = "swathprofile"
        self.tools = [Tool]


class Tool(object):
    def __init__(self):
        """ESRI Stub

        """

        self.label = 'Swath Profile'
        self.description = ''
        self.canRunInBackground = False

    def getParameterInfo(self):
        """ESRI Stub

        """

        parameter_0 = arcpy.Parameter(
            displayName='Profile Line',
            name='profile_line',
            datatype='GPFeatureLayer',
            parameterType='Required',
            direction='Input'
        )

        parameter_0.filter.list = ['POLYLINE']

        parameter_1 = arcpy.Parameter(
            displayName='Swath Width',
            name='swath_width',
            datatype='GPLong',
            parameterType='Required',
            direction='Input'
        )

        parameter_1.value = 20000  # Default swath width

        parameter_2 = arcpy.Parameter(
            displayName='Input Raster',
            name='input_raster',
            datatype='GPRasterLayer',
            parameterType='Required',
            direction='Input'
        )

        parameter_3 = arcpy.Parameter(
            displayName='Statistic',
            name='statistic',
            datatype='GPString',
            parameterType='Required',
            direction='Output'
        )

        parameter_3.value = 'MEAN'  # Default
        parameter_3.filter.type = 'ValueList'
        parameter_3.filter.list = ['MAXIMUM', 'MEAN', 'MINIMUM']


        parameter_4 = arcpy.Parameter(
            displayName='Output Raster',
            name='output_raster',
            datatype='DERasterDataset',
            parameterType='Required',
            direction='Output'
        )

        parameters = [parameter_0, parameter_1, parameter_2, parameter_3, parameter_4]
        return parameters

    def isLicensed(self):
        """ESRI Stub

        """

        try:
            if arcpy.CheckExtension("spatial") != "Available":
                raise Exception
        except Exception:
            return False  # tool cannot be executed

        return True  # tool can be executed

    def updateParameters(self, parameters):
        """ESRI Stub

        """

        return

    def updateMessages(self, parameters):
        """"ESRI Stub

        """

        return

    def execute(self, parameters, messages):
        """

        """

        try:
            # arcpy environment settings
            arcpy.env.workspace = r'in_memory'
            arcpy.env.scratchWorkspace = r'in_memory'

            # Check out Spatial Analysis extension
            arcpy.CheckOutExtension("spatial")

            # ArcGIS tool parameters
            profile_line = parameters[0].valueAsText
            swath_width = parameters[1].value
            in_raster = parameters[2].valueAsText
            statistic = parameters[3].valueAsText
            out_raster = parameters[4].valueAsText

            in_raster = arcpy.Raster(in_raster)  # arcpy quirk

            # Check if one line
            result = arcpy.GetCount_management(profile_line)
            if int(result[0]) != 1:
                raise MoreThanOneLine(result)

            # Azimuth angle for raster rotation
            angle = get_line_azimuth(profile_line)

            # Create swath using buffer
            buffer_width = str(swath_width / 2) + " meters"
            swath = arcpy.Buffer_analysis(profile_line, None, buffer_width, line_end_type="FLAT")

            # Create describe object and extract extent rectangle
            desc0 = arcpy.Describe(swath)
            extent = desc0.extent
            swath_rectangle = "{} {} {} {}".format(str(extent.XMin), str(extent.YMin), str(extent.XMax),
                                                   str(extent.YMax))

            # Create centroid for swath and xy for raster rotation point
            centroid = arcpy.FeatureToPoint_management(swath, None, "CENTROID")
            for row in arcpy.da.SearchCursor(centroid, ["SHAPE@XY"]):
                centroid_x, centroid_y = row[0]
            centroid_coords = str(centroid_x) + " " + str(centroid_y)

            # Clip raster to swath area
            swath_raster = arcpy.Clip_management(in_raster, swath_rectangle, None, swath,
                                                 clipping_geometry="ClippingGeometry")

            # Rotate raster. Negate angle for anti-clockwise rotation.
            negative_angle = angle * -1
            rotated_swath_raster = arcpy.Rotate_management(swath_raster, None, negative_angle,
                                                           centroid_coords, "BILINEAR")

            # Raster cell size for focal statistics
            desc1 = arcpy.Describe(in_raster)
            cell_size = desc1.meanCellWidth
            # Double swath width to ensure statistics are run over swath area
            cells_wide = int((swath_width * 2) / cell_size)

            # Run focal statistics on rotated swath raster
            focal_raster = arcpy.sa.FocalStatistics(rotated_swath_raster, NbrRectangle(cells_wide, 1, "CELL"),
                                                    statistic, "DATA")

            # Re-rotate raster and re-clip to swath polygon
            rotated_focal_raster = arcpy.Rotate_management(focal_raster, None, angle, centroid_coords, "BILINEAR")
            clipped_focal_raster = arcpy.Clip_management(rotated_focal_raster, swath_rectangle, None, swath,
                                                         clipping_geometry="ClippingGeometry")

            # Create output feature class
            arcpy.CopyRaster_management(clipped_focal_raster, out_raster)

        except Exception as ex:
            _, error, tb = sys.exc_info()
            traceback_info = traceback.format_tb(tb)[0]
            arcpy.AddError("Error Type: {} \nTraceback: {} \n".format(error, traceback_info))

        finally:
            arcpy.Delete_management('in_memory')
            arcpy.AddMessage("in_memory intermediate files deleted.")
            return

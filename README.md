# ArcGIS-Swath-Profile-Tool

Version==ArcGIS 10.3

*Created by James M Roden*

ArcGIS toolbox script for creating swath profiles

[DOWNLOAD](https://github.com/GISJMR/ArcGIS-Swath-Profile-Tool/raw/master/Swath_Profiles.zip)

## Swath Profiles
Swath profiles take the average/maximum/minimum of the raster within a certain distance laterally and condense the data into a 'single profile line'.

![Swath Profiles](https://github.com/GISJMR/ArcGIS-Swath-Profile-Tool/raw/master/SWATHPROFILES.png)
*The tool outputs a swath raster with the chosen statistic*

## Workflow
* Calculate the azimuth of the polyline
* Create buffer using user specified swath width
* Rotate raster by negated azimuthal direction so the intermediate raster runs North to South
* Run focal statistics on rotated raster
* Re-rotate focal statistics raster to original azimuthal angle
* (Optional) Create interpolated z-value polyline for swath profile

### Notes
* Only works on individual lines (start and end)

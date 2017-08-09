# ArcGIS-Swath-Profile-Tool
*Created by James M Roden*

ArcGIS toolbox script for creating swath profiles

[DOWNLOAD](link)

## Swath Profiles
Swath profiles take the average/maximum/minimum of the raster within a certain distance laterally and condense the data into a single profile line.

![Swath Profiles](https://octodex.github.com/images/yaktocat.png)

## Workflow
* Calculate the azimuth of the polyline
* Create buffer using user specified swath width
* Rotate raster by negated azimuthal direction so the intermediate raster runs North to South
* Run focal statistics on rotated raster
* Re-rotate focal statistics raster to original azimuthal angle
* (Optional) Create interpolated z-value polyline for swath profile

### Notes
* Only works on individual lines (start and end)

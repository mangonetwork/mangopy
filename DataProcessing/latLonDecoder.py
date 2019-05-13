#########################################################
# Title: latLonDecoder.py                               #
# Original creation date: 01/07/2015                    #
# Project: MANGO                                        #
# Created by: Luis Vinke and Danielle Riccardi          #
# Email: lmvinke@gmail.com                              #
# Modified by:                                          #
# Modification date:                                    #
#                                                       #
# Description: Changes pixel .csv's into latitudes and  #
#   longitudes. Must run in same folder as target .csv's#
#########################################################
#### takes newi and newj .csvs and converts them to lat long ####
#### this code is based on undoing a portion of what pixelToLatLon did ####
import numpy as np

#### define image dimensions ####
ImageHeight = 519
ImageWidth = 695
newImageHeight = 500
newImageWidth = 500

#### initialize arrays ####
IMatrix = np.empty(([ImageHeight, ImageWidth]))         # creating an empty array with the same dimensions as the raw image
JMatrix = np.empty(([ImageHeight, ImageWidth]))         # creating an empty array with the same dimensions as the raw image
IMatrix[:] = np.nan          # Setting the latitude array to NANs
JMatrix[:] = np.nan         # Setting the longitude array to NANs


#### load data ####
IMatrix = np.genfromtxt('newI.csv', dtype=float, delimiter=',')
JMatrix = np.genfromtxt('newJ.csv', dtype=float, delimiter=',')
imageLatLong = np.genfromtxt('imageLatLong.csv', dtype=float, delimiter=',')


## get these values from the imageLatLon.csv
#### set bounds ####
latBounds         = imageLatLong[:,0]                           #min and max lat values from ImageLatLon.csv
latRange          = latBounds[1]-latBounds[0]                   #currently not used span of latitude values (length between max and min)

lonBounds         = imageLatLong[:,1]                           #min and max lon values from ImageLatLon.csv
lonRange          = lonBounds[1]-lonBounds[0]                   #span of longitude values (length between max and min)

scaleBounds       = np.log(np.tan(np.radians(latBounds)*0.5 + pi/4))     #two value list of scaled min and max [(scalemin), (scalemax)]
scaleRange        = scaleBounds[1]-scaleBounds[0]               #span of scale values (length between min and max)


#### initialize arrays ####
latMatrix = np.empty(([newImageHeight, newImageWidth]))          # creating an empty array with the same dimensions as the new image
lonMatrix = np.empty(([newImageHeight, newImageWidth]))         # creating an empty array with the same dimensions as the new image   
latMatrix[:] = np.nan          # Setting the lat array to NANs
lonMatrix[:] = np.nan         # Setting the lon array to NANs

#### calculate lat and lon from j and i ####
for j in range(ImageHeight):
    for i in range(ImageWidth):
        Icell = IMatrix[j][i]
        Jcell = JMatrix[j][i]
        if (not(np.isnan(Icell)) and not(np.isnan(Jcell))):
            pixLon = lonBounds[0] + ((Icell*lonRange)/np.float64(newImageWidth -1)) #perfect!
            scaleJ = scaleBounds[0] + (scaleRange)*((np.float64(newImageHeight-1)-Jcell)/(newImageHeight-1))
            pixLat = np.degrees(2*(np.arctan(np.exp(scaleJ))-(np.pi/4))) 
            #latMatrix[j-15,i-40] = pixLat #uncomment for Pescadero High School
            #lonMatrix[j-15,i-40] = pixLon #uncomment for Pescadero High School
            # latMatrix[j,i] = pixLat
            # lonMatrix[j,i] = pixLon
            latMatrix[int(Jcell),int(Icell)] = pixLat
            lonMatrix[int(Jcell),int(Icell)] = pixLon
            
#### calculate the nonnan SW and NE corners of each location
southWestLatLon = [np.nanmin(latMatrix), np.nanmin(lonMatrix)]
northEastLatLon = [np.nanmax(latMatrix), np.nanmax(lonMatrix)]
imageLatitudesLongitudes = np.array((np.vstack((southWestLatLon, northEastLatLon))))  # creates an array stacked for writing to a CSV

#### save the matricis to files in their respctive directories ####
np.savetxt('Latitudes.csv', latMatrix, delimiter=',')
np.savetxt('Longitudes.csv', lonMatrix, delimiter=',')
np.savetxt('ImageLatLongnew.csv', imageLatitudesLongitudes, delimiter=',')

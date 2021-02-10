#The purpose of this script is to automate the processing of sentinel 2b raw data.
#To work, place the script in the same folder that contains the raw satellite data.  It is
#recommended that the folder contains only the satellite data and this script file.
#The script will search for data that needs to be uncompressed, and will then
#move all original data into a folder called 'Raw_data'.  The Raw_data folder will
#then contain individual scene ID folders along with their compressed versions if they exist.
#Once the raw data has been uncompressed and organized, parameter files will be generated.
#The parameter files will be used to make a batch file, which will then be run in the
#Windows command prompt, executing ERDAS modeler.exe (the script searches for the
#proper path to this .exe file) to process the satellite data.
#Written By...Nikit Parakh
#.........parakhni@msu.edu

import sys
import os
import fnmatch
import pprint
import shutil
import zipfile

# Global constant basePath points to the data's base directory based on location of this python script
basePath = os.path.dirname(sys.argv[0]).replace("\\", "/")

# Check for data output directories and create if need be
def CheckOutputDir():
    if not os.path.exists(basePath + '/Raw_data/'):
        os.makedirs(basePath + '/Raw_data/')
    if not os.path.exists(basePath + '/Stacks/'):
        os.makedirs(basePath + '/Stacks/')
    if not os.path.exists(basePath + '/MSAVI/'):
        os.makedirs(basePath + '/MSAVI/')
    if not os.path.exists(basePath + '/NDVI/'):
        os.makedirs(basePath + '/NDVI/')
    if not os.path.exists(basePath + '/WDRI/'):
        os.makedirs(basePath + '/WDRI/')


def FindModelerExe():
    if not os.path.exists(basePath + '/modeler_location.txt'):
        f = open(basePath + '/modeler_location.txt', 'w')
        searchdir = [] #list of possible ERDAS install locations
        for root, dirs, files in os.walk('C:\Program Files\\'):
            for dir in dirs:
                if dir == 'Hexagon':
                    searchdir.append(os.path.join(root, dir))
                    print (os.path.join(root,dir))
        for i in range (0, len(searchdir)):
            for root, dirs, files in os.walk(searchdir[i]):
                for exe in fnmatch.filter(files, '*.exe'):
                    if exe == 'modeler.exe':
                        modeler = os.path.join(root, exe)
                    elif exe == 'imagecommand.exe':
                        imagecommand = os.path.join(root, exe)
                    elif exe == 'imgcopy.exe':
                        imgcopy = os.path.join(root, exe)
        modeler = '"' + modeler + '" @'
        imagecommand = '"' + imagecommand + '" @'
        imgcopy = '"' + imgcopy + '" @'

        f.write("{}\n{}\n{}".format(modeler, imagecommand, imgcopy))
        f.close()
        return modeler, imagecommand, imgcopy
    f = open(basePath + '/modeler_location.txt')
    paths = []
    for line in f:
        paths.append(line.strip())
    f.close()
    return paths[0], paths[1], paths[2]


# extract compressed data if necessary
def ExtractData():
    zipList = []
    unzipped = []
    for root, dirs, files in os.walk(basePath):
        for zip in files:
            if fnmatch.fnmatch(zip, "*.zip") and zip[:3] == "L1C":
                zipList.append(os.path.join(root, zip).replace('\\', '/'))
        for unzip in files:
            if fnmatch.fnmatch(unzip, "*.jp2"):
                if root.replace('\\', '/') not in unzipped:
                    unzipped.append(root.replace('\\', '/'))

    combineLists = zipList + unzipped
    zipList = []

    for i in combineLists:
        try:
            os.rename(i, basePath + '/Raw_data/' + os.path.basename(i))
            print(os.path.basename(i), "successfully moved to Raw_data")
            if ".zip" in  os.path.basename(i):
                zipList.append(basePath + '/Raw_data/' + os.path.basename(i))
        except WindowsError:
            pass
    print()
    for i in zipList:
        folder_path = basePath + '/Raw_data/' + os.path.basename(i)[:-4]
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        z = zipfile.ZipFile(i, 'r')
        for file in z.namelist():
            if fnmatch.fnmatch(file, "*.jp2"):
                if str(file)[-8:-4] in ["_B02", "_B03", "_B04", "_B08"]:
                    if str(file)[-8:-4] == "_B02":
                        target = open(folder_path + '/' + folder_path.split('/')[-1] + "_B02.jp2", 'wb')
                    elif str(file)[-8:-4] == "_B03":
                        target = open(folder_path + '/' + folder_path.split('/')[-1] + "_B03.jp2", 'wb')
                    elif str(file)[-8:-4] == "_B04":
                        target = open(folder_path + '/' + folder_path.split('/')[-1] + "_B04.jp2", 'wb')
                    elif str(file)[-8:-4] == "_B08":
                        target = open(folder_path + '/' + folder_path.split('/')[-1] + "_B08.jp2", 'wb')
                    target.write(z.read(file))
                    target.close()
        z.close()

    sceneIDList, scenePathList = set(), set()
    for root, dirs, files in os.walk(basePath + '/Raw_data/'):
        for file in files:
            if file.endswith('.jp2') and "L1C" in root:
                scenePathList.add(root)
                sceneIDList.add(root.split('/')[-1])

    return list(sceneIDList), list(scenePathList)


def getImageLists(namelist, pathlist):
    #create empty lists to contain image paths, image names for Sentinel 2B scenes
    S2BimagePath = []
    S2BimageName = []

    for i in range (0, len(namelist)):
        if "L1C" in pathlist[i]:
            S2BimagePath.append(pathlist[i])
            S2BimageName.append(namelist[i])

    return S2BimagePath, S2BimageName


#*******Stack bands (DN's)*******
#generate parameter files, use conditional statements to determine landsat 7 or 8 bands
def GetParameterFilesStack(imagepath, imagename, modeler):
    #determine number of individual scenes to be processed
    numImages = len(imagename)
    #create empty list that will contain parameter file info for batch file
    batchList = []
    for i in range(0, numImages):
        if not os.path.exists(basePath + '/Stacks/' + imagename[i] + '_stack.img'):

            #create parameter file for Sentinel 2B bands
            if "L1C" in imagepath[i]:
                f = open(imagepath[i] + "/" + imagename[i] + "_parameter_stackA", 'w')
                f.write('SET CELLSIZE MIN;\n'\
                    'SET WINDOW INTERSECTION;\n'\
                    'SET AOI NONE;\n'\
                    'INTEGER RASTER n1 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + '/' + str(imagename[i]) + '_B02.jp2";\n'\
                    'INTEGER RASTER n2 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + '/' + str(imagename[i]) + '_B03.jp2";\n'\
                    'INTEGER RASTER n3 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + '/' + str(imagename[i]) + '_B04.jp2";\n'\
                    'INTEGER RASTER n4 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + '/' + str(imagename[i]) + '_B08.jp2";\n'\
                    'INTEGER RASTER n5 FILE DELETE_IF_EXISTING PUBOUT USEALL ATHEMATIC 16 BIT UNSIGNED INTEGER"'+ basePath + '/Stacks/' + imagename[i] + '_stack.img";\n'
                    'n5 = STACKLAYERS (n1, n2, n3, n4);\n'\
                    'QUIT;')
                f.close()
                f = open(imagepath[i] + '/' + imagename[i] + '_parameter_stackB', 'w')
                f.write('5\n'\
                    'modeler\n'\
                    '-nq\n'\
                    + imagepath[i] + '/' + imagename[i] + '_parameter_stackA\n'\
                    '-meter\n'\
                    '-state\n')
                f.close()
                batchList.append(modeler + imagepath[i] + '/' + imagename[i] + '_parameter_stackB')

    return batchList

def MSAVI(imagepath, imagename, modeler):
    numImages = len(imagename)
    batchlist = []
    for i in range (0, numImages):
        if not os.path.exists(basePath + '/MSAVI/' + imagename[i] + '_msavi.img'):
            f = open(imagepath[i] + '/' + imagename[i] + '_msavi_paramA', 'w')
            f.write('Float RASTER n1 FILE OLD PUBINPUT "' + basePath + '/Stacks/' + imagename[i] +'_stack.img";\n'\
            'Float RASTER n4_temp;\n'\
            'Float RASTER n5_temp;\n'\
            'Float RASTER n13 FILE DELETE_IF_EXISTING PUBOUT USEALL ATHEMATIC FLOAT SINGLE "' + basePath + '/MSAVI/' + imagename[i] +'_msavi.img";\n'\
            'n5_temp = n1(4) * 1;\n'\
            'n4_temp = n1(3) * 1;\n'\
            '#define n10_memory Float(((2 * $n5_temp) + 1))\n'\
            '#define n7_memory Float( ( (2 * $n5_temp) + 1 )  POWER 2 - 8 * ($n5_temp - $n4_temp) )\n'\
            '#define n11_memory Float(SQRT ( $n7_memory ) )\n'\
            'n13 = ($n10_memory - $n11_memory) / 2;\n'\
            'QUIT;\n')
            f.close()
            f = open(imagepath[i] + '/' + imagename[i] + '_msavi_paramB', 'w')
            f.write('5\n'\
            'modeler\n'\
            +str(imagepath[i]) + '/' + str(imagename[i]) + '_msavi_paramA\n'\
            '-meter\n'\
            '-state\n'\
            '-delete_model\n')
            f.close()
            batchlist.append(modeler + str(imagepath[i]) + '/' + str(imagename[i]) + '_msavi_paramB')

    return batchlist

def NDVI(imagepath, imagename, modeler):
    numImages = len(imagename)
    batchlist = []
    for i in range(0, numImages):
        if not os.path.exists(basePath + '/NDVI/' + imagename[i] + '_ndvi.img'):
            f = open(imagepath[i] + '/' + imagename[i] + '_ndvi_paramA', 'w')
            f.write('Float RASTER n1 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE "' + basePath + '/Stacks/' + imagename[i] + '_stack.img";\n'\
                    'Float RASTER n5 FILE NEW PUBOUT USEALL ATHEMATIC FLOAT SINGLE "' + basePath + '/NDVI/' + imagename[i] + '_ndvi.img";\n'\
                    '#define n3_memory Float(EITHER 0 IF ( n1(4) + n1(3) == 0 ) OR ((n1(4) - n1(3)) / (n1(4) + n1(3)) )OTHERWISE )\n'\
                    'n5 = EITHER 0 IF ( $n3_memory < -1 OR $n3_memory > 1 ) OR $n3_memory OTHERWISE ;\n'\
                    'QUIT;\n')
            f.close()
            f = open(imagepath[i] + '/' + imagename[i] + '_ndvi_paramB', 'w')
            f.write('5\n'\
                    'modeler\n'\
                    '-nq\n'\
                    + imagepath[i] + '/' + imagename[i] + '_ndvi_paramA\n'\
                    '-meter\n'\
                    '-state\n')
            f.close()
            batchlist.append(modeler + imagepath[i] + '/' + imagename[i] + '_ndvi_paramB')

    return batchlist

def WDRI(imagepath, imagename, modeler):
    numImages = len(imagename)
    batchlist = []
    for i in range(0, numImages):
        if not os.path.exists(basePath + '/WDRI/' + imagename[i] + '_wdri.img'):
            f = open(imagepath[i] + '/' + imagename[i] + '_wdri_paramA', 'w')
            f.write('Float RASTER n1 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE "' + basePath + '/Stacks/' + imagename[i] + '_stack.img";\n'\
                    'Float RASTER n5 FILE NEW PUBOUT USEALL ATHEMATIC FLOAT SINGLE "' + basePath + '/WDRI/' + imagename[i] + '_wdri.img";\n'\
                    '#define n3_memory Float(EITHER 0 IF ( n1(4) * 0.1 + n1(3) == 0 ) OR ((n1(4) * 0.1 - n1(3)) / (n1(4) * 0.1 + n1(3)) )OTHERWISE )\n'\
                    'n5 = EITHER 0 IF ( $n3_memory < -1 OR $n3_memory > 1 ) OR $n3_memory OTHERWISE ;\n'\
                    'QUIT;\n')
            f.close()
            f = open(imagepath[i] + '/' + imagename[i] + '_wdri_paramB', 'w')
            f.write('5\n'\
                    'modeler\n'\
                    '-nq\n'\
                    + imagepath[i] + '/' + imagename[i] + '_wdri_paramA\n'\
                    '-meter\n'\
                    '-state\n')
            f.close()
            batchlist.append(modeler + imagepath[i] + '/' + imagename[i] + '_wdri_paramB')

    return batchlist

def RunBatch():
    try:
        from subprocess import Popen
        p = Popen("batch_process.bat", cwd=basePath)
        stdout, stderr = p.communicate()
    except WindowsError:
        pass

def getBatchFile(batchlist):
    f = open(basePath + '/batch_process.bat', 'w')
    for i in range (0, len(batchlist)):
        f.write(str(batchlist[i]).replace('\\', '/') + '\n')
    f.close()

def main():
    print("Script created by: Nikit Parakh")
    print("Contact: parakhni@msu.edu")
    print()
    print ('This script works for Sentinel 2B datasets\n\
and calculates MSAVI, NDVI, and WDRI Products from the dataset.\n\
Only bands 2, 3, 4, and 8 are used for this processing.\n')

    print ('The workspace directory is: ', basePath, '\n')

    CheckOutputDir()
    imageNamelist, imagePathlist = ExtractData()

    print ('Searching for ERDAS .exe file location')
    ModelerLocation, ImageCommandLocation, ImgCopyLocation = FindModelerExe()
    print ('Done Searching')
    print (ModelerLocation)
    print (ImageCommandLocation)
    print (ImgCopyLocation)

    print ("\nRaw data folders: \n")
    pprint.pprint(imagePathlist)
    print ("\nImages to be processed are: \n")
    pprint.pprint(imageNamelist)
    print ()

    imagepath, imagename = getImageLists(imageNamelist, imagePathlist)

    #Stack
    batchListStack = GetParameterFilesStack(imagePathlist, imageNamelist, ModelerLocation)
    #___MSAVI
    batchListMSAVI = MSAVI(imagePathlist, imageNamelist, ModelerLocation)
    #___NDVI
    batchListNDVI = NDVI(imagePathlist, imageNamelist, ModelerLocation)
    #___NDVI
    batchListWDRI = WDRI(imagePathlist, imageNamelist, ModelerLocation)
    # #compile all batch lists for atmospheric corrections and pass to the function that generates the batch file
    Batchlist = batchListStack + batchListMSAVI + batchListNDVI + batchListWDRI

    getBatchFile(Batchlist)
    # #run the atmospheric correction batch file
    print ('Running batch file in ERDAS modeler...')
    RunBatch()

main()

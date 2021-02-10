#The purpose of this script is to automate the processing of Landsat raw data.
#To work, place the script in the same folder that contains the raw satellite data.  It is
#recommended that the folder contains only the satellite data and this script file.
#The script will search for data that needs to be uncompressed, and will then
#move all original data into a folder called 'Raw_data'.  The Raw_data folder will
#then contain individual scene ID folders along with their compressed versions if they exist.
#Once the raw data has been uncompressed and organized, parameter files will be generated.
#The parameter files will be used to make a batch file, which will then be run in the
#Windows command prompt, executing ERDAS modeler.exe (the script searches for the
#proper path to this .exe file) to process the satellite data.  A report file is also
#generated which details the scenes being processed, which Landsat sensors they were generated from,
#and the individual scene parameters from the metadata file.
#***Currently compatible with Landsat 4 TM, 5, TM, 7 ETM+ and Landsat 8 OLI data***
#Written By...Dan Zelenak
#.............MSU GOES Lab
#.............zelenak1@msu.edu
#Modified By..Nikit Parakh
#.............parakhni@msu.edu

import sys, os, fnmatch, pprint, tarfile, shutil

#Global constant basePath points to the data's base directory based on location of this python script
basePath = os.path.dirname(sys.argv[0]).replace("\\", "/")

#Check for data output directories and create if need be
def CheckOutputDir():
	if not os.path.exists(basePath + '/Raw_data/'):
		os.makedirs(basePath + '/Raw_data/')
	if not os.path.exists(basePath + '/Stacks/'):
		os.makedirs(basePath + '/Stacks/')
	if not os.path.exists(basePath + '/Toa_ref/'):
		os.makedirs(basePath + '/Toa_ref/')
	if not os.path.exists(basePath + '/MSAVI/'):
		os.makedirs(basePath + '/MSAVI/')
	if not os.path.exists(basePath + '/NDVI/'):
		os.makedirs(basePath + '/NDVI/')
	if not os.path.exists(basePath + '/WDRI/'):
		os.makedirs(basePath + '/WDRI/')

#searches C:\ for location of ERDAS Modeler.exe and ImageCommand.exe files
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

#extract compressed data if necessary
def ExtractData():
	targzList, tarFileList, tarFolderList, untarFolderList = [], [], [], []

	if not os.path.exists(basePath + '/Raw_data/'):
		os.makedirs(basePath + '/Raw_data/')

	for root, dirs, files in os.walk(basePath):
		for targz in files:
			if fnmatch.fnmatch(targz, '*.tar.gz'):
				targzList.append(os.path.join(root, targz).replace('\\', '/'))
		for tars in files:
			if fnmatch.fnmatch(tars, '*.tar'):
				tarFileList.append(os.path.join(root,tars).replace('\\', '/'))
		for tars in dirs:
			if fnmatch.fnmatch(tars, '*.tar'):
				tarFolderList.append(os.path.join(root, tars).replace('\\', '/'))
		for untar in dirs: #find folders containing uncompressed data to move to the raw data folder
			if os.path.exists(basePath + '/' + untar + '/' + str(untar) + '_B1.TIF'):
				untarFolderList.append(os.path.join(root, untar).replace('\\', '/'))


	# print(targzList,"\n", tarFileList,"\n", tarFolderList,"\n", untarFolderList)

	combineLists = targzList + tarFileList + tarFolderList + untarFolderList
	# print(combineLists)
	for i in range(0, len(combineLists)):
		try:
			os.rename(combineLists[i], basePath + '/Raw_data/' + os.path.basename(combineLists[i]))
			print(os.path.basename(combineLists[i]), "successfully moved to Raw_data")
		except WindowsError:
			pass
	print()
	for i in targzList:
		# print(targzList[i])
		if not os.path.exists(basePath + '/Raw_data/' + os.path.basename(i)[:-7]):
			os.makedirs(basePath + '/Raw_data/' + os.path.basename(i)[:-7])
			tar = tarfile.open(basePath + '/Raw_data/' + os.path.basename(i), 'r:gz')
			tar.extractall(basePath + '/Raw_data/' + os.path.basename(i)[:-7])
			tar.close()

	sceneIDList, scenePathList = [], []
	for root, dirs, files in os.walk(basePath + '/Raw_data/'):
		for sceneID in dirs:
			if os.path.exists(basePath + '/Raw_data/' + sceneID + '/' + str(sceneID) + '_B1.TIF'):
				sceneIDList.append(sceneID)
				scenePathList.append(os.path.join(root, sceneID).replace('\\','/') + '/')
	print(sceneIDList, scenePathList)
	return sceneIDList, scenePathList


#create list of landsat 7 and landsat 8 images, paths, metadata
def getImageLists(namelist, pathlist):
	#create empty lists to contain image/metadata paths, image names for Landsat 8 scenes
	L8imagePath = []
	L8imageName = []
	L8metaData = []
	#create empty lists to contain image/metadata paths, image names for Landsat 7 scenes
	L7imagePath = []
	L7imageName = []
	L7metaData = []
	#Landsat 5
	L5imagePath = []
	L5imageName = []
	L5metaData = []
	#Landsat 4
	L4imagePath = []
	L4imageName = []
	L4metaData = []
	for i in range (0, len(namelist)):
		if "LC08" in pathlist[i]:
			L8imagePath.append(pathlist[i])
			L8imageName.append(namelist[i])
			L8metaData.append(pathlist[i] + namelist[i] + '_MTL.txt')
		elif "LE7" in pathlist[i]:
			L7imagePath.append(pathlist[i])
			L7imageName.append(namelist[i])
			L7metaData.append(pathlist[i] + namelist[i] + '_MTL.txt')
		elif "LT5" in pathlist [i]:
			L5imagePath.append(pathlist[i])
			L5imageName.append(namelist[i])
			L5metaData.append(pathlist[i] + namelist[i] + '_MTL.txt')
		elif "LT4" in pathlist[i]:
			L4imagePath.append(pathlist[i])
			L4imageName.append(namelist[i])
			L4metaData.append(pathlist[i] + namelist[i] + '_MTL.txt')

	return L8imagePath, L8imageName, L8metaData, L7imagePath, L7imageName, L7metaData,\
			L5imagePath, L5imageName, L5metaData, L4imagePath, L4imageName, L4metaData


# Get DOY Value from imagename
def getDOY(imagename):
	year = int(imagename[17:21])
	month = int(imagename[21:23])
	day = int(imagename[23:25])

	num_days = [0,31,28,31,30,31,30,31,31,30,31,30,31]
	num_days_leap = [0,31,29,31,30,31,30,31,31,30,31,30,31]

	if year % 4 == 0:
		DOY = sum(num_days_leap[:month]) + day
	else:
		DOY = sum(num_days[:month]) + day
	return DOY
#*******Stack bands (DN's)*******
#generate parameter files, use conditional statements to determine landsat 7 or 8 bands
def GetParameterFilesStack(imagepath, imagename, modeler):
	#determine number of individual scenes to be processed
	numImages = len(imagename)
	#create empty list that will contain parameter file info for batch file
	batchList = []
	for i in range(0, numImages):
		if not os.path.exists(basePath + '/Stacks/' + imagename[i] + '_stack.img'):

			#create parameter file for landsat 8 bands
			if fnmatch.fnmatch(imagename[i], "LC08*"):
				f = open(imagepath[i] + "/" + imagename[i] + "_parameter_stackA", 'w')
				f.write('SET CELLSIZE MIN;\n'\
					'SET WINDOW INTERSECTION;\n'\
					'SET AOI NONE;\n'\
					'INTEGER RASTER n1 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b1.tif";\n'\
					'INTEGER RASTER n2 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b2.tif";\n'\
					'INTEGER RASTER n3 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b3.tif";\n'\
					'INTEGER RASTER n4 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b4.tif";\n'\
					'INTEGER RASTER n5 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b5.tif";\n'\
					'INTEGER RASTER n6 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b6.tif";\n'\
					'INTEGER RASTER n7 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b7.tif";\n'\
					'INTEGER RASTER n8 FILE DELETE_IF_EXISTING PUBOUT USEALL ATHEMATIC 16 BIT UNSIGNED INTEGER"'+ basePath + '/Stacks/' + imagename[i] + '_stack.img";\n'
					'n8 = STACKLAYERS (n1, n2, n3, n4, n5, n6, n7);\n'\
					'QUIT;')
				f.close()
				f = open(imagepath[i] + '/' + imagename[i] + '_parameter_stackB', 'w')
				f.write('5\n'\
					'modeler\n'\
					'-nq\n'\
					+ imagepath[i] + imagename[i] + '_parameter_stackA\n'\
					'-meter\n'\
					'-state\n')
				f.close()
				batchList.append(modeler + imagepath[i] + imagename[i] + '_parameter_stackB')
			#create parameter file for landsat 7 bands
			elif fnmatch.fnmatch(imagename[i], "LE7*"):
				f = open(imagepath[i] + "/" + imagename[i] + "_parameter_stackA", 'w')
				f.write('SET CELLSIZE MIN;\n'\
					'SET WINDOW INTERSECTION;\n'\
					'SET AOI NONE;\n'\
					'INTEGER RASTER n1 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b1.tif";\n'\
					'INTEGER RASTER n2 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b2.tif";\n'\
					'INTEGER RASTER n3 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b3.tif";\n'\
					'INTEGER RASTER n4 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b4.tif";\n'\
					'INTEGER RASTER n5 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b5.tif";\n'\
					'INTEGER RASTER n7 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b7.tif";\n'\
					'INTEGER RASTER n8 FILE DELETE_IF_EXISTING PUBOUT USEALL ATHEMATIC 8 BIT UNSIGNED INTEGER"'+ basePath + '/Stacks/' + imagename[i] + '_stack.img";\n'
					'n8 = STACKLAYERS (n1, n2, n3, n4, n5, n7);\n'\
					'QUIT;')
				f.close()
				f = open(imagepath[i] + '/' + imagename[i] + '_parameter_stackB', 'w')
				f.write('5\n'\
					'modeler\n'\
					'-nq\n'\
					+ imagepath[i] + imagename[i] + '_parameter_stackA\n'\
					'-meter\n'\
					'-state\n')
				f.close()
				batchList.append(modeler + imagepath[i] + imagename[i] + '_parameter_stackB')
			elif fnmatch.fnmatch(imagename[i], 'LT5*'):
				f = open(imagepath[i] + "/" + imagename[i] + "_parameter_stackA", 'w')
				f.write('SET CELLSIZE MIN;\n'\
					'SET WINDOW INTERSECTION;\n'\
					'SET AOI NONE;\n'\
					'INTEGER RASTER n1 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b1.tif";\n'\
					'INTEGER RASTER n2 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b2.tif";\n'\
					'INTEGER RASTER n3 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b3.tif";\n'\
					'INTEGER RASTER n4 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b4.tif";\n'\
					'INTEGER RASTER n5 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b5.tif";\n'\
					'INTEGER RASTER n7 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b7.tif";\n'\
					'INTEGER RASTER n8 FILE DELETE_IF_EXISTING PUBOUT USEALL ATHEMATIC 8 BIT UNSIGNED INTEGER"'+ basePath + '/Stacks/' + imagename[i] + '_stack.img";\n'
					'n8 = STACKLAYERS (n1, n2, n3, n4, n5, n7);\n'\
					'QUIT;')
				f.close()
				f = open(imagepath[i] + '/' + imagename[i] + '_parameter_stackB', 'w')
				f.write('5\n'\
					'modeler\n'\
					'-nq\n'\
					+ imagepath[i] + imagename[i] + '_parameter_stackA\n'\
					'-meter\n'\
					'-state\n')
				f.close()
				batchList.append(modeler + imagepath[i] + imagename[i] + '_parameter_stackB')
			elif fnmatch.fnmatch(imagename[i], 'LT4*'):
				f = open(imagepath[i] + "/" + imagename[i] + "_parameter_stackA", 'w')
				f.write('SET CELLSIZE MIN;\n'\
					'SET WINDOW INTERSECTION;\n'\
					'SET AOI NONE;\n'\
					'INTEGER RASTER n1 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b1.tif";\n'\
					'INTEGER RASTER n2 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b2.tif";\n'\
					'INTEGER RASTER n3 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b3.tif";\n'\
					'INTEGER RASTER n4 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b4.tif";\n'\
					'INTEGER RASTER n5 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b5.tif";\n'\
					'INTEGER RASTER n7 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE EDGE FILL"'+ str(imagepath[i]) + str(imagename[i]) + '_b7.tif";\n'\
					'INTEGER RASTER n8 FILE DELETE_IF_EXISTING PUBOUT USEALL ATHEMATIC 8 BIT UNSIGNED INTEGER"'+ basePath + '/Stacks/' + imagename[i] + '_stack.img";\n'
					'n8 = STACKLAYERS (n1, n2, n3, n4, n5, n7);\n'\
					'QUIT;')
				f.close()
				f = open(imagepath[i] + '/' + imagename[i] + '_parameter_stackB', 'w')
				f.write('5\n'\
					'modeler\n'\
					'-nq\n'\
					+ imagepath[i] + imagename[i] + '_parameter_stackA\n'\
					'-meter\n'\
					'-state\n')
				f.close()
				batchList.append(modeler + imagepath[i] + imagename[i] + '_parameter_stackB')

	return batchList


#---LANDSAT 8---
#Obtain parameters for Landsat 8 DNs to At-sensor spectral radiance
def L8GetValuesRads(metadata):
	numImages = len(metadata)
	radMultBand = []
	radAddBand = []
	for i in range (0, numImages):
		try:
			openfile = str(metadata[i])
			f = open(openfile, "r")
			for line in f:
				for i in range(2,8):
					if "RADIANCE_MULT_BAND_"+str(i)+" " in line: radMultBand.append(str.lstrip(line[-11:-1]))
					if "RADIANCE_ADD_BAND_"+str(i)+" " in line: radAddBand.append(str.lstrip(line[-10:-1]))
			f.close()
		except IOError:
			pass
	return radMultBand, radAddBand


#Obtain parameters for Landsat 8 Rads to TOA model from metadata files
def L8GetValuesToa(metadata):
	numImages = len(metadata)
	sunElev = [] #sun elevation
	ESdist = [] #earth-sun distance in AU
	for i in range (0, numImages):
		try:
			openfile = str(metadata[i])
			f = open(openfile, "r")
			for line in f:
				if "SUN_ELEVATION" in line: sunElev.append(str.lstrip(line[-12:-1]))
				if "EARTH_SUN_DISTANCE" in line: ESdist.append(str.lstrip(line[-10:-1]))
			f.close()
		except IOError:
			pass
	return sunElev, ESdist


#---LANDSAT 7---
#Check for low or high gain for DNs to at-sensor spectral radiance
def L7checkGainRads(metadata):
	numImages = len(metadata)
	GainValue = []
	for i in range (0, numImages):
		try:
			openfile = str(metadata[i])
			f = open(openfile, "r")
			for line in f:
				for i in [1,2,3,4,5,7]:
					if "RADIANCE_MAXIMUM_BAND_" + str(i) + " " in line: GainValue.append(str.lstrip((line[-8:-2])))
			f.close()
		except IOError:
			pass
	return GainValue


#Obtain appropriate Grescale and Brescale values for Landsat 7
def L7GetRescaleRads(gainvalue):
	numImages = int(len(gainvalue) / 6)
	#Post-calibration dynamic ranges
	HighGain = ['191.60', '196.50', '152.90', '157.40', '31.06', '10.80'] * numImages
	GrescaleLow = ['1.180709', '1.209843', '0.942520', '0.969291', '0.191220', '0.066496'] * numImages
	GrescaleHigh = ['0.778740', '0.798819', '0.621654', '0.639764', '0.126220', '0.043898'] * numImages
	BrescaleLow = ['-7.38', '-7.61', '-5.94', '-6.07', '-1.19', '-0.42'] * numImages
	BrescaleHigh = ['-6.98', '-7.20', '-5.62', '-5.74', '-1.13', '-0.39'] * numImages

	#create empty lists to contain values to use based on high or low gain
	GUseValue = []
	BUseValue = []

	count = numImages * 6
	for i in range (0, count):
		#check for high or low gain and collect appropriate values
		if gainvalue[i] == HighGain[i]:
			GUseValue.append(GrescaleHigh[i])
			BUseValue.append(BrescaleHigh[i])
		else:
			GUseValue.append(GrescaleLow[i])
			BUseValue.append(BrescaleLow[i])
	return GUseValue, BUseValue


#Obtain parameters for Landsat 7 Rads to TOA model from metadata files
def L7GetValuesToa(metadata, imagename):
	numImages = len(metadata)
	DOY = [] #day of year used to obtain sun earth distance
	sunElev = [] #sun elevation
	for i in range (0, numImages):
		try:
			openfile = str(metadata[i])
			f = open(openfile, "r")
			for line in f:
				if "SUN_ELEVATION" in line: sunElev.append(str.lstrip(line[-12:-1]))
			f.close()
			DOY.append(getDOY(str(imagename[i])))
		except IOError:
			pass
	return DOY, sunElev


#Obtain earth sun distance by matching with appropriate DOY value
def GetESdistToa(DOY):
	ESdist = []
	DOYlist =['0.98331', '0.98330', '0.98330', '0.98330', '0.98330', '0.98332', '0.98333', \
	'0.98335', '0.98338', '0.98341', '0.98345', '0.98349', '0.98354', '0.98359',\
	'0.98365', '0.98371', '0.98378', '0.98385', '0.98393', '0.98401', '0.98410', \
	'0.98419', '0.98428', '0.98439', '0.98449', '0.98460', '0.98472', '0.98484', \
	'0.98496', '0.98509', '0.98523', '0.98536', '0.98551', '0.98565', '0.98580', \
	'0.98596', '0.98612', '0.98628', '0.98645', '0.98662', '0.98680', '0.98698', \
	'0.98717', '0.98735', '0.98755', '0.98774', '0.98794', '0.98814', '0.98835', \
	'0.98856', '0.98877', '0.98899', '0.98921', '0.98944', '0.98966', '0.98989', \
	'0.99012', '0.99036', '0.99060', '0.99084', '0.99108', '0.99133', '0.99158', \
	'0.99183', '0.99208', '0.99234', '0.99260', '0.99286', '0.99312', '0.99339', \
	'0.99365', '0.99392', '0.99419', '0.99446', '0.99474', '0.99501', '0.99529', \
	'0.99556', '0.99584', '0.99612', '0.99640', '0.99669', '0.99697', '0.99725', \
	'0.99754', '0.99782', '0.99811', '0.99840', '0.99868', '0.99897', '0.99926', \
	'0.99954', '0.99983', '1.00012', '1.00041', '1.00069', '1.00098', '1.00127', \
	'1.00155', '1.00184', '1.00212', '1.00240', '1.00269', '1.00297', '1.00325', \
	'1.00353', '1.00381', '1.00409', '1.00437', '1.00464', '1.00492', '1.00519', \
	'1.00546', '1.00573', '1.00600', '1.00626', '1.00653', '1.00679', '1.00705', \
	'1.00731', '1.00756', '1.00781', '1.00806', '1.00831', '1.00856', '1.00880', \
	'1.00904', '1.00928', '1.00952', '1.00975', '1.00998', '1.01020', '1.01043', \
	'1.01065', '1.01087', '1.01108', '1.01129', '1.01150', '1.01170', '1.01191', \
	'1.01210', '1.01230', '1.01249', '1.01267', '1.01286', '1.01304', '1.01321', \
	'1.01338', '1.01355', '1.01371', '1.01387', '1.01403', '1.01418', '1.01433', \
	'1.01447', '1.01461', '1.01475', '1.01488', '1.01500', '1.01513', '1.01524', \
	'1.01536', '1.01547', '1.01557', '1.01567', '1.01577', '1.01586', '1.01595', \
	'1.01603', '1.01610', '1.01618', '1.01625', '1.01631', '1.01637', '1.01642', \
	'1.01647', '1.01652', '1.01656', '1.01659', '1.01662', '1.01665', '1.01667', \
	'1.01668', '1.01670', '1.01670', '1.01670', '1.01670', '1.01669', '1.01668', \
	'1.01666', '1.01664', '1.01661', '1.01658', '1.01655', '1.01650', '1.01646', \
	'1.01641', '1.01635', '1.01629', '1.01623', '1.01616', '1.01609', '1.01601', \
	'1.01592', '1.01584', '1.01575', '1.01565', '1.01555', '1.01544', '1.01533', \
	'1.01522', '1.01510', '1.01497', '1.01485', '1.01471', '1.01458', '1.01444', \
	'1.01429', '1.01414', '1.01399', '1.01383', '1.01367', '1.01351', '1.01334', \
	'1.01317', '1.01299', '1.01281', '1.01263', '1.01244', '1.01225', '1.01205', \
	'1.01186', '1.01165', '1.01145', '1.01124', '1.01103', '1.01081', '1.01060', \
	'1.01037', '1.01015', '1.00992', '1.00969', '1.00946', '1.00922', '1.00898', \
	'1.00874', '1.00850', '1.00825', '1.00800', '1.00775', '1.00750', '1.00724', \
	'1.00698', '1.00672', '1.00646', '1.00620', '1.00593', '1.00566', '1.00539', \
	'1.00512', '1.00485', '1.00457', '1.00430', '1.00402', '1.00374', '1.00346', \
	'1.00318', '1.00290', '1.00262', '1.00234', '1.00205', '1.00177', '1.00148', \
	'1.00119', '1.00091', '1.00062', '1.00033', '1.00005', '0.99976', '0.99947', \
	'0.99918', '0.99890', '0.99861', '0.99832', '0.99804', '0.99775', '0.99747', \
	'0.99718', '0.99690', '0.99662', '0.99634', '0.99605', '0.99577', '0.99550', \
	'0.99522', '0.99494', '0.99467', '0.99440', '0.99412', '0.99385', '0.99359', \
	'0.99332', '0.99306', '0.99279', '0.99253', '0.99228', '0.99202', '0.99177', \
	'0.99152', '0.99127', '0.99102', '0.99078', '0.99054', '0.99030', '0.99007', \
	'0.98983', '0.98961', '0.98938', '0.98916', '0.98894', '0.98872', '0.98851', \
	'0.98830', '0.98809', '0.98789', '0.98769', '0.98750', '0.98731', '0.98712', \
	'0.98694', '0.98676', '0.98658', '0.98641', '0.98624', '0.98608', '0.98592', \
	'0.98577', '0.98562', '0.98547', '0.98533', '0.98519', '0.98506', '0.98493', \
	'0.98481', '0.98469', '0.98457', '0.98446', '0.98436', '0.98426', '0.98416', \
	'0.98407', '0.98399', '0.98391', '0.98383', '0.98376', '0.98370', '0.98363', \
	'0.98358', '0.98353', '0.98348', '0.98344', '0.98340', '0.98337', '0.98335', \
	'0.98333', '0.98331']
	numImages = len(DOY)
	for i in range(0, numImages):
		DOYindex = int(DOY[i]) - 1
		ESdist.append(DOYlist[DOYindex])

	return ESdist


def getL5Parameters(imagepath, imagename, metadata):
	Year = []
	DOY = []
	sunElev = []
	Grescale = []
	Brescale = []
	Glistold = ['0.671339', '0.1322205']
	Glistnew = ['0.765827', '1.448189']
	Glistsame = ['1.043976', '0.876024', '0.120354', '0.065551']
	Blistold = ['-2.19', '-4.16']
	Blistnew = ['-2.29', '-4.29']
	Blistsame = ['-2.21', '-2.39', '-0.49', '-0.22']
	for i in range(0, len(imagename)):
		try:
			openfile = metadata[i]
			f = open(openfile, 'r')
			for line in f:
				if "DATE_ACQUIRED" in line: Year.append(str.lstrip(line[-11:-7]))
				if "SUN_ELEVATION" in line: sunElev.append(str.lstrip(line[-12:-1]))
			f.close()
			DOY.append(getDOY(str(imagename[i])))
		except IOError:
			pass
	#determine if using pre or post-calibration dynamic range for bands 1 and 2
	yearrange = []
	for j in range(1984, 1992):
		yearrange.append(j)
	for i in range(0, len(imagename)):
		try:
			for j in range(1984, 1992):
				if Year[i] == str(j):
					Grescale.append(Glistold + Glistsame)
					Brescale.append(Blistold + Blistsame)
					break
				else:
					Grescale.append(Glistnew + Glistsame)
					Brescale.append(Blistnew + Blistsame)
					break
		except IndexError:
			pass
	return DOY, sunElev, Grescale, Brescale


def getL4Parameters(imagepath, imagename, metadata):
	DOY = []
	sunElev = []
	Lmax = []
	grescaleold = ['0.647717']
	grescalenew = ['0.679213']
	brescaleold = ['-2.17']
	brescalenew = ['-2.20']
	grescalesame = ['1.334016', '1.004606', '0.876024', '0.125079', '0.065945']
	brescalesame = ['-4.17', '-2.17', '-2.39', '-0.50', '-0.22']
	Grescale = []
	Brescale = []
	for i in range(0 , len(imagename)):
		try:
			openfile = metadata[i]
			f = open(openfile, 'r')
			for line in f:
				if "SUN_ELEVATION" in line: sunElev.append(str.lstrip(line[-12:-1]))
				if "RADIANCE_MAXIMUM_BAND_1" in line: Lmax.append(str.lstrip(line[-8:-5]))
			f.close()
			DOY.append(getDOY(str(imagename[i])))
		except IOError:
			pass
	for i in range(0, len(imagename)):
		try:
			if int(Lmax[i]) == 163:
				Grescale.append(grescaleold + grescalesame)
				Brescale.append(brescaleold + brescalesame)
			else:
				Grescale.append(grescalenew + grescalesame)
				Brescale.append(brescalenew + brescalesame)
		except IndexError:
			pass
	return DOY, sunElev, Grescale, Brescale


def getL4DNtoTOA(imagepath, imagename, grescale, brescale, sunelev, esdist, modeler):

	batchlist = []
	for i in range(0, len(imagename)):
		if not os.path.exists(basePath + '/Toa_ref/' + imagename[i] + '_toa.img'):
			try:
				Grescale = grescale[i]
				Brescale = brescale[i]
				strGrescale = ", ".join(Grescale)
				strBrescale = ", ".join(Brescale)
				toasunelev = sunelev[i]
				toaesdist = esdist[i]
				f = open(imagepath[i] + '/' + imagename[i] + '_atmcorrParamA', 'w')
				f.write('Integer RASTER n1 FILE OLD PUBINPUT "' + basePath + '/Stacks/' + imagename[i] + '_stack.img";\n'\
				'Float RASTER n32 FILE DELETE_IF_EXISTING PUBOUT IGNORE 0 ATHEMATIC FLOAT SINGLE "' + basePath + '/Toa_ref/' + imagename[i] + '_toa.img";\n'\
				'FLOAT TABLE g_rescale [6];\n'\
				'FLOAT TABLE b_rescale [6];\n'\
				'FLOAT TABLE ESUN_values [6];\n'\
				'FLOAT SCALAR distance;\n'\
				'FLOAT SCALAR sun_elev;\n'\
				'g_rescale = TABLE(' + strGrescale + ');\n'\
				'b_rescale = TABLE(' + strBrescale + ');\n'\
				'distance = ' + toaesdist + ';\n'\
				'sun_elev = ' + toasunelev + ';\n'\
				'ESUN_values = TABLE(1983, 1795, 1539, 1028, 219.8, 83.49);\n'\
				'#define n15_memory Float(EITHER 0 IF ( n1(6) == 0 ) OR ((n1(6) * g_rescale[5]) + (b_rescale[5])) OTHERWISE )\n'\
				'#define n30_memory Float(EITHER 0 IF ( n15_memory == 0 OR (ESUN_values [5] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n15_memory) * (distance POWER (2)) /  (ESUN_values [5] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n14_memory Float(EITHER 0 IF ( n1(5) == 0 ) OR ((n1(5) * g_rescale[4]) + (b_rescale[4])) OTHERWISE )\n'\
				'#define n29_memory Float(EITHER 0 IF ( n14_memory == 0 OR (ESUN_values [4] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n14_memory) * (distance POWER (2)) /  (ESUN_values [4] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n13_memory Float(EITHER 0 IF ( n1(4) == 0 ) OR ((n1(4) * g_rescale[3]) + (b_rescale[3])) OTHERWISE )\n'\
				'#define n28_memory Float(EITHER 0 IF ( n13_memory == 0 OR (ESUN_values [3] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n13_memory) * (distance POWER (2)) /  (ESUN_values [3] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n12_memory Float(EITHER 0 IF ( n1(3) == 0 ) OR ((n1(3) * g_rescale[2]) + (b_rescale[2])) OTHERWISE )\n'\
				'#define n27_memory Float(EITHER 0 IF ( n12_memory == 0 OR (ESUN_values [2] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n12_memory) * (distance POWER (2)) /  (ESUN_values [2] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n11_memory Float(EITHER 0 IF ( n1(2) == 0 ) OR ( (n1(2) * g_rescale[1]) + (b_rescale[1]) )OTHERWISE )\n'\
				'#define n26_memory Float(EITHER 0 IF ( n11_memory == 0 OR (ESUN_values [1] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n11_memory) * (distance POWER (2)) /  (ESUN_values [1] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n10_memory Float(EITHER 0 IF ( n1(1) == 0 ) OR ( (n1(1) * g_rescale[0]) + (b_rescale[0])) OTHERWISE )\n'\
				'#define n25_memory Float(EITHER 0 IF ( n10_memory == 0 OR (ESUN_values [0] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n10_memory) * (distance POWER (2)) /  (ESUN_values [0] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE    )\n'\
				'n32 = STACKLAYERS ( n25_memory , n26_memory , n27_memory ,n28_memory, n29_memory, n30_memory ) ;\n'\
				'QUIT;\n')
				f.close()

				f = open(imagepath[i] + "/" + imagename[i] + '_atmcorrParamB', 'w')
				f.write('5\n'\
				'modeler\n'\
				+ imagepath[i] + '/' + imagename[i] + '_atmcorrParamA\n'\
				'-meter\n'\
				'-state\n'\
				'-delete_model\n')
				f.close()
				batchlist.append(modeler + imagepath[i] + imagename[i] + '_atmcorrParamB')
			except IndexError:
				pass
	return batchlist


def getL5DNtoTOA(imagepath, imagename, grescale, brescale, sunelev, esdist, modeler):
	batchlist = []
	for i in range(0, len(imagename)):
		if not os.path.exists(basePath + '/Toa_ref/' + imagename[i] + '_toa.img'):
			try:
				Grescale = grescale[i]
				Brescale = brescale[i]
				strGrescale = ", ".join(Grescale)
				strBrescale = ", ".join(Brescale)
				toasunelev = str(sunelev[i])
				toaesdist = str(esdist[i])
				f = open(imagepath[i] + '/' + imagename[i] + '_atmcorrParamA', 'w')
				f.write('Integer RASTER n1 FILE OLD PUBINPUT "' + basePath + '/Stacks/' + imagename[i] + '_stack.img";\n'\
				'Float RASTER n32 FILE DELETE_IF_EXISTING PUBOUT IGNORE 0 ATHEMATIC FLOAT SINGLE "' + basePath + '/Toa_ref/' + imagename[i] + '_toa.img";\n'\
				'FLOAT TABLE g_rescale [6];\n'\
				'FLOAT TABLE b_rescale [6];\n'\
				'FLOAT TABLE ESUN_values [6];\n'\
				'FLOAT SCALAR distance;\n'\
				'FLOAT SCALAR sun_elev;\n'\
				'g_rescale = TABLE(' + strGrescale + ');\n'\
				'b_rescale = TABLE(' + strBrescale + ');\n'\
				'distance = ' + toaesdist + ';\n'\
				'sun_elev = ' + toasunelev + ';\n'\
				'ESUN_values = TABLE(1983, 1796, 1536, 1031, 220.0, 83.44);\n'\
				'#define n15_memory Float(EITHER 0 IF ( n1(6) == 0 ) OR ((n1(6) * g_rescale[5]) + (b_rescale[5])) OTHERWISE )\n'\
				'#define n30_memory Float(EITHER 0 IF ( n15_memory == 0 OR (ESUN_values [5] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n15_memory) * (distance POWER (2)) /  (ESUN_values [5] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n14_memory Float(EITHER 0 IF ( n1(5) == 0 ) OR ((n1(5) * g_rescale[4]) + (b_rescale[4])) OTHERWISE )\n'\
				'#define n29_memory Float(EITHER 0 IF ( n14_memory == 0 OR (ESUN_values [4] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n14_memory) * (distance POWER (2)) /  (ESUN_values [4] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n13_memory Float(EITHER 0 IF ( n1(4) == 0 ) OR ((n1(4) * g_rescale[3]) + (b_rescale[3])) OTHERWISE )\n'\
				'#define n28_memory Float(EITHER 0 IF ( n13_memory == 0 OR (ESUN_values [3] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n13_memory) * (distance POWER (2)) /  (ESUN_values [3] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n12_memory Float(EITHER 0 IF ( n1(3) == 0 ) OR ((n1(3) * g_rescale[2]) + (b_rescale[2])) OTHERWISE )\n'\
				'#define n27_memory Float(EITHER 0 IF ( n12_memory == 0 OR (ESUN_values [2] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n12_memory) * (distance POWER (2)) /  (ESUN_values [2] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n11_memory Float(EITHER 0 IF ( n1(2) == 0 ) OR ( (n1(2) * g_rescale[1]) + (b_rescale[1]) )OTHERWISE )\n'\
				'#define n26_memory Float(EITHER 0 IF ( n11_memory == 0 OR (ESUN_values [1] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n11_memory) * (distance POWER (2)) /  (ESUN_values [1] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n10_memory Float(EITHER 0 IF ( n1(1) == 0 ) OR ( (n1(1) * g_rescale[0]) + (b_rescale[0])) OTHERWISE )\n'\
				'#define n25_memory Float(EITHER 0 IF ( n10_memory == 0 OR (ESUN_values [0] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n10_memory) * (distance POWER (2)) /  (ESUN_values [0] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE    )\n'\
				'n32 = STACKLAYERS ( n25_memory , n26_memory , n27_memory ,n28_memory, n29_memory, n30_memory ) ;\n'\
				'QUIT;\n')
				f.close()

				f = open(imagepath[i] + "/" + imagename[i] + '_atmcorrParamB', 'w')
				f.write('5\n'\
				'modeler\n'\
				+ imagepath[i] + '/' + imagename[i] + '_atmcorrParamA\n'\
				'-meter\n'\
				'-state\n'\
				'-delete_model\n')
				f.close()
				batchlist.append(modeler + imagepath[i] + imagename[i] + '_atmcorrParamB')
			except IndexError:
				pass
	return batchlist


#--Convert DNs directly to Top-of-atmosphere reflectance--
def getL8DNtoTOA(imagepath, imagename, radmultband, radaddband, sunelev, esdist, modeler):
	batchlist = []
	for i in range (0, len(imagename)):
		if not os.path.exists(basePath + '/Toa_ref/' + imagename[i] + '_toa.img'):
			try:
				radmult = radmultband[(i*6):(i*6+6)]
				radadd = radaddband[(i*6):(i*6+6)]
				strmult = ", ".join(radmult)
				stradd = ", ".join(radadd)
				toasunelev = sunelev[i]
				toaesdist = esdist[i]
				f = open(imagepath[i] + '/' + imagename[i] + '_atmcorrParamA', 'w')
				f.write('Integer RASTER n1 FILE OLD PUBINPUT "' + basePath + '/Stacks/' + imagename[i] + '_stack.img";\n'\
				'Float RASTER n32 FILE DELETE_IF_EXISTING PUBOUT IGNORE 0 ATHEMATIC FLOAT SINGLE "' + basePath + '/Toa_ref/' + imagename[i] + '_toa.img";\n'\
				'FLOAT TABLE rad_mult [6];\n'\
				'FLOAT TABLE rad_add [6];\n'\
				'FLOAT TABLE ESUN_values [6];\n'\
				'FLOAT SCALAR distance;\n'\
				'FLOAT SCALAR sun_elev;\n'\
				'rad_mult = TABLE(' + strmult + ');\n'\
				'rad_add = TABLE(' + stradd + ');\n'\
				'distance = ' + toaesdist + ';\n'\
				'sun_elev = ' + toasunelev + ';\n'\
				'ESUN_values = TABLE(2067, 1893, 1603, 972.6, 245, 79.72);\n'\
				'#define n15_memory Float(EITHER 0 IF ( n1(7) == 0 ) OR ((n1(7) * rad_mult[5]) + (rad_add[5])) OTHERWISE )\n'\
				'#define n30_memory Float(EITHER 0 IF ( n15_memory == 0 OR (ESUN_values [5] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n15_memory) * (distance POWER (2)) /  (ESUN_values [5] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n14_memory Float(EITHER 0 IF ( n1(6) == 0 ) OR ((n1(6) * rad_mult[4]) + (rad_add[4])) OTHERWISE )\n'\
				'#define n29_memory Float(EITHER 0 IF ( n14_memory == 0 OR (ESUN_values [4] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n14_memory) * (distance POWER (2)) /  (ESUN_values [4] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n13_memory Float(EITHER 0 IF ( n1(5) == 0 ) OR ((n1(5) * rad_mult[3]) + (rad_add[3])) OTHERWISE )\n'\
				'#define n28_memory Float(EITHER 0 IF ( n13_memory == 0 OR (ESUN_values [3] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n13_memory) * (distance POWER (2)) /  (ESUN_values [3] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n12_memory Float(EITHER 0 IF ( n1(4) == 0 ) OR ((n1(4) * rad_mult[2]) + (rad_add[2])) OTHERWISE )\n'\
				'#define n27_memory Float(EITHER 0 IF ( n12_memory == 0 OR (ESUN_values [2] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n12_memory) * (distance POWER (2)) /  (ESUN_values [2] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n11_memory Float(EITHER 0 IF ( n1(3) == 0 ) OR ( (n1(3) * rad_mult[1]) + (rad_add[1]) )OTHERWISE )\n'\
				'#define n26_memory Float(EITHER 0 IF ( n11_memory == 0 OR (ESUN_values [1] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n11_memory) * (distance POWER (2)) /  (ESUN_values [1] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n10_memory Float(EITHER 0 IF ( n1(2) == 0 ) OR ( (n1(2) * rad_mult[0]) + (rad_add[0])) OTHERWISE )\n'\
				'#define n25_memory Float(EITHER 0 IF ( n10_memory == 0 OR (ESUN_values [0] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n10_memory) * (distance POWER (2)) /  (ESUN_values [0] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE    )\n'\
				'n32 = STACKLAYERS ( n25_memory , n26_memory , n27_memory ,n28_memory, n29_memory, n30_memory ) ;\n'\
				'QUIT;\n')
				f.close()

				f = open(str(imagepath[i]) + "/" + str(imagename[i]) + '_atmcorrParamB', 'w')
				f.write('5\n'\
				'modeler\n'\
				+str(imagepath[i]) + '/' + str(imagename[i]) + '_atmcorrParamA\n'\
						'-meter\n'\
				'-state\n'\
				'-delete_model\n')
				f.close()
				batchlist.append(modeler + str(imagepath[i]) + str(imagename[i]) + '_atmcorrParamB')
			except IndexError:
				pass
	return batchlist


def getL7DNtoTOA(imagepath, imagename, grescale, brescale, sunelev, esdist, modeler):
	batchlist = []

	for i in range(0, len(imagename)):
		if not os.path.exists(basePath + '/Toa_ref/' + imagename[i] + '_toa.img'):
			try:
				Grescale = grescale[(i*6):(i*6+6)]
				Brescale = brescale[(i*6):(i*6+6)]
				strGrescale = ", ".join(Grescale)
				strBrescale = ", ".join(Brescale)
				toasunelev = sunelev[i]
				toaesdist = esdist[i]
				f = open(imagepath[i] + '/' + imagename[i] + '_atmcorrParamA', 'w')
				f.write('Integer RASTER n1 FILE OLD PUBINPUT "' + basePath + '/Stacks/' + imagename[i] + '_stack.img";\n'\
				'Float RASTER n32 FILE DELETE_IF_EXISTING PUBOUT IGNORE 0 ATHEMATIC FLOAT SINGLE "' + basePath + '/Toa_ref/' + imagename[i] + '_toa.img";\n'\
				'FLOAT TABLE g_rescale [6];\n'\
				'FLOAT TABLE b_rescale [6];\n'\
				'FLOAT TABLE ESUN_values [6];\n'\
				'FLOAT SCALAR distance;\n'\
				'FLOAT SCALAR sun_elev;\n'\
				'g_rescale = TABLE(' + strGrescale + ');\n'\
				'b_rescale = TABLE(' + strBrescale + ');\n'\
				'distance = ' + toaesdist + ';\n'\
				'sun_elev = ' + toasunelev + ';\n'\
				'ESUN_values = TABLE(1997, 1812, 1533, 1039, 230.8, 84.90000000000001);\n'\
				'#define n15_memory Float(EITHER 0 IF ( n1(6) == 0 ) OR ((n1(6) * g_rescale[5]) + (b_rescale[5])) OTHERWISE )\n'\
				'#define n30_memory Float(EITHER 0 IF ( n15_memory == 0 OR (ESUN_values [5] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n15_memory) * (distance POWER (2)) /  (ESUN_values [5] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n14_memory Float(EITHER 0 IF ( n1(5) == 0 ) OR ((n1(5) * g_rescale[4]) + (b_rescale[4])) OTHERWISE )\n'\
				'#define n29_memory Float(EITHER 0 IF ( n14_memory == 0 OR (ESUN_values [4] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n14_memory) * (distance POWER (2)) /  (ESUN_values [4] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n13_memory Float(EITHER 0 IF ( n1(4) == 0 ) OR ((n1(4) * g_rescale[3]) + (b_rescale[3])) OTHERWISE )\n'\
				'#define n28_memory Float(EITHER 0 IF ( n13_memory == 0 OR (ESUN_values [3] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n13_memory) * (distance POWER (2)) /  (ESUN_values [3] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n12_memory Float(EITHER 0 IF ( n1(3) == 0 ) OR ((n1(3) * g_rescale[2]) + (b_rescale[2])) OTHERWISE )\n'\
				'#define n27_memory Float(EITHER 0 IF ( n12_memory == 0 OR (ESUN_values [2] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n12_memory) * (distance POWER (2)) /  (ESUN_values [2] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n11_memory Float(EITHER 0 IF ( n1(2) == 0 ) OR ( (n1(2) * g_rescale[1]) + (b_rescale[1]) )OTHERWISE )\n'\
				'#define n26_memory Float(EITHER 0 IF ( n11_memory == 0 OR (ESUN_values [1] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n11_memory) * (distance POWER (2)) /  (ESUN_values [1] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE )\n'\
				'#define n10_memory Float(EITHER 0 IF ( n1(1) == 0 ) OR ( (n1(1) * g_rescale[0]) + (b_rescale[0])) OTHERWISE )\n'\
				'#define n25_memory Float(EITHER 0 IF ( n10_memory == 0 OR (ESUN_values [0] * (COS ( (90 - sun_elev) * (PI)/180 ) ) ) == 0  )'\
				'OR (((PI) * n10_memory) * (distance POWER (2)) /  (ESUN_values [0] * (COS ( (90 - sun_elev) * (PI)/180 ) ) )) OTHERWISE    )\n'\
				'n32 = STACKLAYERS ( n25_memory , n26_memory , n27_memory ,n28_memory, n29_memory, n30_memory ) ;\n'\
				'QUIT;\n')
				f.close()

				f = open(str(imagepath[i]) + "/" + str(imagename[i]) + '_atmcorrParamB', 'w')
				f.write('5\n'\
				'modeler\n'\
				+str(imagepath[i]) + '/' + str(imagename[i]) + '_atmcorrParamA\n'\
				'-meter\n'\
				'-state\n'\
				'-delete_model\n')
				f.close()
				batchlist.append(modeler + str(imagepath[i]) + str(imagename[i]) + '_atmcorrParamB')
			except IndexError:
				pass
	return batchlist

def setNodata(imagepath, imagename, imgcommand):
	batchlist = []
	for i in range(0, len(imagename)):
		f = open(imagepath[i] + imagename[i] + '_nodataParam', 'w')
		f.write('6\n'\
		'imagecommand\n'\
		+ basePath + '/Masked_data/' + imagename[i] + '_toam.img\n'\
		'-nodata\n'\
		'0\n'\
		'-meter\n'\
		'imagecommand\n')
		f.close()
		batchlist.append(imgcommand + imagepath[i] + imagename[i] + '_nodataParam')
		f = open(imagepath[i] + imagename[i] + '_nodataMSAVIparam', 'w')
		f.write('6\n'\
		'imagecommand\n'\
		+ basePath + '/Masked_data/' + imagename[i] + '_msavim.img\n'\
		'-nodata\n'\
		'0\n'\
		'-meter\n'\
		'imagecommand\n')
		f.close()
		batchlist.append(imgcommand + imagepath[i] + imagename[i] + '_nodataMSAVIparam')
	return batchlist

#generate parameter files for MSAVI process
def MSAVI(imagepath, imagename, modeler):
	numImages = len(imagename)
	batchlist = []
	for i in range (0, numImages):
		if not os.path.exists(basePath + '/MSAVI/' + imagename[i] + '_msavi.img'):
			f = open(imagepath[i] + '/' + imagename[i] + '_msavi_paramA', 'w')
			f.write('Float RASTER n1 FILE OLD PUBINPUT "' + basePath + '/Toa_ref/' + imagename[i] +'_toa.img";\n'\
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
			f = open(imagepath[i] + imagename[i] + '_msavi_paramB', 'w')
			f.write('5\n'\
			'modeler\n'\
			+str(imagepath[i]) + str(imagename[i]) + '_msavi_paramA\n'\
			'-meter\n'\
			'-state\n'\
			'-delete_model\n')
			f.close()
			batchlist.append(modeler + str(imagepath[i]) + str(imagename[i]) + '_msavi_paramB')
	return batchlist

def NDVI(imagepath, imagename, modeler):
	numImages = len(imagename)
	batchlist = []
	for i in range(0, numImages):
		if not os.path.exists(basePath + '/NDVI/' + imagename[i] + '_ndvi.img'):
			f = open(imagepath[i] + imagename[i] + '_ndvi_paramA', 'w')
			f.write('Float RASTER n1 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE "' + basePath + '/Toa_ref/' + imagename[i] + '_toa.img";\n'\
					'Float RASTER n5 FILE NEW PUBOUT USEALL ATHEMATIC FLOAT SINGLE "' + basePath + '/NDVI/' + imagename[i] + '_ndvi.img";\n'\
					'#define n3_memory Float(EITHER 0 IF ( n1(4) + n1(3) == 0 ) OR ((n1(4) - n1(3)) / (n1(4) + n1(3)) )OTHERWISE )\n'\
					'n5 = EITHER 0 IF ( $n3_memory < -1 OR $n3_memory > 1 ) OR $n3_memory OTHERWISE ;\n'\
					'QUIT;\n')
			f.close()
			f = open(imagepath[i] + imagename[i] + '_ndvi_paramB', 'w')
			f.write('5\n'\
					'modeler\n'\
					'-nq\n'\
					+ imagepath[i] + imagename[i] + '_ndvi_paramA\n'\
					'-meter\n'\
					'-state\n')
			f.close()
			batchlist.append(modeler + imagepath[i] + imagename[i] + '_ndvi_paramB')
	return batchlist

def WDRI(imagepath, imagename, modeler):
	numImages = len(imagename)
	batchlist = []
	for i in range(0, numImages):
		if not os.path.exists(basePath + '/WDRI/' + imagename[i] + '_wdri.img'):
			f = open(imagepath[i] + imagename[i] + '_wdri_paramA', 'w')
			f.write('Float RASTER n1 FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE "' + basePath + '/Toa_ref/' + imagename[i] + '_toa.img";\n'\
					'Float RASTER n5 FILE NEW PUBOUT USEALL ATHEMATIC FLOAT SINGLE "' + basePath + '/WDRI/' + imagename[i] + '_wdri.img";\n'\
					'#define n3_memory Float(EITHER 0 IF ( n1(4) * 0.1 + n1(3) == 0 ) OR ((n1(4) * 0.1 - n1(3)) / (n1(4) * 0.1 + n1(3)) )OTHERWISE )\n'\
					'n5 = EITHER 0 IF ( $n3_memory < -1 OR $n3_memory > 1 ) OR $n3_memory OTHERWISE ;\n'\
					'QUIT;\n')
			f.close()
			f = open(imagepath[i] + imagename[i] + '_wdri_paramB', 'w')
			f.write('5\n'\
					'modeler\n'\
					'-nq\n'\
					+ imagepath[i] + imagename[i] + '_wdri_paramA\n'\
					'-meter\n'\
					'-state\n')
			f.close()
			batchlist.append(modeler + imagepath[i] + imagename[i] + '_wdri_paramB')
	return batchlist

#generate report.txt that displays parameter values used for each image
def ParametersReport(L8name, L7name, L5name, L4name, radmult, radadd, L7grescale, L7brescale, \
	L5grescale, L5brescale, L4grescale, L4brescale, sunelev, esdist):
	f = open(basePath + '/Report.txt', 'w')
	imageCount = len(L8name) + len(L7name) + len(L5name) + len(L4name)
	f.write('The number of images being processed = ' + str(imageCount) + '\n')
	f.write(str(len(L8name)) + ' Landsat-8 OLI images\n' + str(len(L7name)) + ' Landsat-7 ETM+ images\n')
	f.write(str(len(L5name)) + ' Landsat-5 TM images\n' + str(len(L4name)) + ' Landsat-4 TM images\n')
	f.write('\n\nImage IDs: \n')
	imagenames = L8name + L7name + L5name + L4name
	for i in range (0, len(imagenames)):
		f.write(imagenames[i] + '\n')
	for i in range (0, len(L8name)):
		try:
			f.write('\n' + '\n' + L8name[i] + ' Parameters are...\n')
			radmultP = radmult[(i*6):(i*6+6)]
			radaddP = radadd[(i*6):(i*6+6)]
			f.write('Radiance multiplicative rescaling factors: \n')
			for p in range(1, 7):
				f.write('Band ' + str(p + 1) + ': ')
				f.write(str(radmultP[p-1]) + '\n')
			f.write('\n' + 'Radiance additive rescaling factors: \n')
			for p in range (1, 7):
				f.write('Band ' + str(p + 1) + ': ')
				f.write(str(radaddP[p-1]) + '\n')
			f.write('\n'+'Sun elevation angle = ' + sunelev[i] + '\n')
			f.write('Earth-sun distance = ' + esdist[i] + '\n')
		except IndexError:
			pass
	for i in range(0, len(L7name)):
		try:
			f.write('\n' + '\n' + L7name[i] + ' Parameters are...\n')
			Grescale = L7grescale[(i*6):(i*6+6)]
			Brescale = L7brescale[(i*6):(i*6+6)]
			f.write('Gain rescaling factors: \n')
			for p in range (0, 5):
				f.write('Band ' + str(p + 1) + ': ')
				f.write(str(Grescale[p]) + '\n')
			f.write('Band 7: ')
			f.write(str(Grescale[5]) + '\n')
			f.write('\n' + 'Bias rescaling factors: \n')
			for p in range (0, 5):
				f.write('Band ' + str(p + 1) + ': ')
				f.write(str(Brescale[p]) + '\n')
			f.write('Band 7: ')
			f.write(str(Brescale[5]) + '\n')
			f.write('\n' + 'Sun elevation angle = ' + sunelev[len(L8name) + i] + '\n')
			f.write('Earth-sun distance = ' + esdist[len(L8name) + i] + '\n')
		except IndexError:
			pass
	for i in range(0, len(L5name)):
		try:
			f.write('\n' + '\n' + L5name[i] + ' Parameters are...\n')
			Grescale = L5grescale[i]
			Brescale = L5brescale[i]
			f.write('Gain rescaling factors: \n')
			for p in range (0, 5):
				f.write('Band ' + str(p + 1) + ': ')
				f.write(str(Grescale[p]) + '\n')
			f.write('Band 7: ')
			f.write(str(Grescale[5]) + '\n')
			f.write('\n' + 'Bias rescaling factors: \n')
			for p in range (0, 5):
				f.write('Band ' + str(p + 1) + ': ')
				f.write(str(Brescale[p]) + '\n')
			f.write('Band 7: ')
			f.write(str(Brescale[5]) + '\n')
			f.write('\n' + 'Sun elevation angle = ' + sunelev[len(L8name) + len(L7name) + i] + '\n')
			f.write('Earth-sun distance = ' + esdist[len(L8name) +len(L7name) + i] + '\n')
		except IndexError:
			pass

	for i in range(0, len(L4name)):
		try:
			f.write('\n' + '\n' + L4name[i] + ' Parameters are...\n')
			Grescale = L4grescale[i]
			Brescale = L4brescale[i]
			f.write('Gain rescaling factors: \n')
			for p in range (0, 5):
				f.write('Band ' + str(p + 1) + ': ')
				f.write(str(Grescale[p]) + '\n')
			f.write('Band 7: ')
			f.write(str(Grescale[5]) + '\n')
			f.write('\n' + 'Bias rescaling factors: \n')
			for p in range (0, 5):
				f.write('Band ' + str(p + 1) + ': ')
				f.write(str(Brescale[p]) + '\n')
			f.write('Band 7: ')
			f.write(str(Brescale[5]) + '\n')
			f.write('\n' + 'Sun elevation angle = ' + sunelev[len(L8name) + len(L7name) + len(L5name) + i] + '\n')
			f.write('Earth-sun distance = ' + esdist[len(L8name) +len(L7name) +len(L5name) + i] + '\n')
		except IndexError:
			pass

	f.close()

#generate the batch file from the batch lists for atmospheric corrections
def getAtmCorrectBatchFile(batchlist):
	f = open(basePath + '/atm_batch_process.bat', 'w')
	for i in range (0, len(batchlist)):
		f.write(str(batchlist[i]).replace('\\', '/') +'\n')
	f.close()


def RunAtmCorrectBatch():
	try:
		from subprocess import Popen
		p = Popen("atm_batch_process.bat", cwd=basePath)
		stdout, stderr = p.communicate()
	except WindowsError:
		pass

def getBatchFile(batchlist):
	f = open(basePath + '/batch_process.bat', 'w')
	for i in range (0, len(batchlist)):
		f.write(str(batchlist[i]).replace('\\', '/') + '\n')
	f.close()


def main():
	print ('This script works for Landsat 4 TM, 5 TM, 7 ETM+, and 8 OLI datasets\n\
that have been downloaded from GLOVIS after August 29, 2012.  Data that has\n\
been aquired prior to this date may potentially have incompatible filenames and \n\
metadata fields and will not work with this script.\n')

	print ('the workspace directory is: ', basePath, '\n')

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
	#
	L8Path, L8Name, L8Meta, L7Path, L7Name, L7Meta, L5Path, L5Name, L5Meta, \
		L4Path, L4Name, L4Meta = getImageLists(imageNamelist, imagePathlist)
	imagepath = L8Path + L7Path + L5Path + L4Path
	imagename = L8Name + L7Name + L5Name + L4Name
	meta = L8Meta+L7Meta+L5Meta+L4Meta
	#Stack
	batchListStack = GetParameterFilesStack(imagePathlist, imageNamelist, ModelerLocation)
	#
	# #___Rads Parameters
	L8radMultBand, L8radAddBand = L8GetValuesRads(L8Meta)
	L7GainValue = L7checkGainRads(L7Meta)
	L7Grescale, L7Brescale = L7GetRescaleRads(L7GainValue)

	# # #___TOA Parameters
	L8sunElev, L8ESdist = L8GetValuesToa(L8Meta)
	L7DOY, L7sunElev = L7GetValuesToa(L7Meta, L7Name)
	L7ESdist = GetESdistToa(L7DOY)
	#
	#
	# #___Landsat 5 Parameters
	L5DOY, L5sunElev, L5Grescale, L5Brescale = getL5Parameters(L5Path, L5Name, L5Meta)
	L5ESdist = GetESdistToa(L5DOY) #use same function as landsat 7 to get earth-sun distance

	#___Landsat 4 Parameters
	L4DOY, L4sunElev, L4Grescale, L4Brescale = getL4Parameters(L4Path, L4Name, L4Meta)
	L4ESdist = GetESdistToa(L4DOY)

	# #___Atmospheric Correction
	L8AtmCorBatchlist = getL8DNtoTOA(L8Path, L8Name, L8radMultBand, L8radAddBand, L8sunElev, L8ESdist, ModelerLocation)
	L7AtmCorBatchlist = getL7DNtoTOA(L7Path, L7Name, L7Grescale, L7Brescale, L7sunElev, L7ESdist, ModelerLocation)
	L5AtmCorBatchlist = getL5DNtoTOA(L5Path, L5Name, L5Grescale, L5Brescale, L5sunElev, L5ESdist, ModelerLocation)
	L4AtmCorBatchlist = getL4DNtoTOA(L4Path, L4Name, L4Grescale, L4Brescale, L4sunElev, L4ESdist, ModelerLocation)

	# #___MSAVI
	batchListMSAVI = MSAVI(imagePathlist, imageNamelist, ModelerLocation)
	#
	# #___NDVI
	batchListNDVI = NDVI(imagePathlist, imageNamelist, ModelerLocation)

	# #___WDRI
	batchListWDRI = WDRI(imagePathlist, imageNamelist, ModelerLocation)

	#compile all batch lists for atmospheric corrections and pass to the function that generates the batch file
	AtmCorrectBatchlist = batchListStack + L8AtmCorBatchlist + L7AtmCorBatchlist + \
		L5AtmCorBatchlist + L4AtmCorBatchlist + batchListMSAVI + batchListNDVI + batchListWDRI
	getAtmCorrectBatchFile(AtmCorrectBatchlist)

	#Generate Parameters Report
	SunElev = L8sunElev + L7sunElev + L5sunElev  #values for parameter report
	ESdist = L8ESdist + L7ESdist + L5ESdist    #values for parameter report
	ParametersReport(L8Name, L7Name, L5Name, L4Name, L8radMultBand, L8radAddBand, \
		L7Grescale, L7Brescale, L5Grescale, L5Brescale, L4Grescale, L4Brescale, SunElev, ESdist)

	#run the atmospheric correction batch file
	print ('Running atmospheric corrections batch file in ERDAS modeler...')
	RunAtmCorrectBatch()

main()

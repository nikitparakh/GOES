import sys, os, fnmatch, shutil, pprint
from pathlib import Path

basePath = os.path.dirname(sys.argv[0]).replace("\\", "/")

header = '''# Input Layers: fC Integer, mosaic, gapfilled (modify to add or delete layers)
#
# set cell size for the model
#
SET CELLSIZE MIN;
#
# set window for the model
#
SET WINDOW INTERSECTION;
#
# set area of interest for the model
#
SET AOI NONE;
#
# declarations
#
'''

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

def CheckOutputDir():
    if not os.path.exists(basePath + '/NDVI/ndvi_sd_mean_stack'):
        os.makedirs(basePath + '/NDVI/ndvi_sd_mean_stack')

def get_ndvi_mos_gp_files():
    ndvi_mos_gp_files = []

    for root, dirs, files in os.walk(basePath + '/NDVI/ndvi_mos_gp/'):
        for img in fnmatch.filter(files, "*.img"):
            ndvi_mos_gp_files.append((os.path.join(root, img).replace("\\", "/"), img[:img.find('.img')]))
        break

    return ndvi_mos_gp_files

def generate_param(files, modeler):

    f = open(basePath + '/NDVI/ndvi_mos_gp/' + "paramA", 'w')
    f.write(header)
    counter = 1
    for path, name in files:
        f.write('Integer RASTER n{}_{} FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE "{}";\n'.format(counter, name, path.lower()))
        counter += 1
    stack_name = name[:name.find('_')]
    f.write("Integer RASTER n25_temp;\n")
    f.write('Integer RASTER n26_{}_ndvi_fc_stack_mean FILE DELETE_IF_EXISTING PUBOUT USEALL ATHEMATIC 8 BIT UNSIGNED INTEGER "{}/ndvi/ndvi_sd_mean_stack/{}_ndvi_fc_stack_mean.img";\n'.format(stack_name, basePath, stack_name))
    f.write('Integer RASTER n27_{}_ndvi_fc_stack_sd FILE DELETE_IF_EXISTING PUBOUT USEALL ATHEMATIC 8 BIT UNSIGNED INTEGER "{}/ndvi/ndvi_sd_mean_stack/{}_ndvi_fc_stack_sd.img";\n'.format(stack_name, basePath, stack_name))
    f.write('Integer RASTER n28_{}_ndvi_fc_stack_10_mean_sd FILE DELETE_IF_EXISTING PUBOUT USEALL ATHEMATIC 8 BIT UNSIGNED INTEGER "{}/ndvi/ndvi_sd_mean_stack/{}_ndvi_fc_stack_10_mean_sd.img";\n'.format(stack_name, basePath.lower(), stack_name.lower()))
    f.write('''#
# function definitions
#\n''')
    counter = 1
    layers = ""
    for path, name in files:
        layers += 'n{}_{}, '.format(counter, name)
        counter += 1
    layers = layers[:-2]
    f.write('n25_temp = STACKLAYERS ( {} ) ;\n'.format(layers))
    f.write('n26_{}_ndvi_fc_stack_mean = STACK MEAN ( $n25_temp ) ;\n'.format(stack_name))
    f.write('n27_{}_ndvi_fc_stack_sd = STACK SD ( $n25_temp ) ;\n'.format(stack_name))
    f.write('n28_{}_ndvi_fc_stack_10_mean_sd = STACKLAYERS ( $n25_temp, $n26_{}_ndvi_fc_stack_mean, n27_{}_ndvi_fc_stack_sd ) ;\n'.format(stack_name, stack_name, stack_name))
    f.write('QUIT;')
    f.close()
    f = open(basePath + '/NDVI/ndvi_mos_gp/' + "paramB", 'w')
    f.write('5\n'\
        'modeler\n'\
        '-nq\n'\
        + basePath + '/NDVI/ndvi_mos_gp/' + 'paramA\n'\
        '-meter\n'\
        '-state\n')
    f.close()
    return modeler + basePath + '/NDVI/ndvi_mos_gp/paramB'

def getBatchFile(param):
    f = open(basePath + '/NDVI/ndvi_mos_gp/' + 'batch_process.bat', 'w')
    f.write(str(param).replace('\\', '/') + '\n')
    f.close()

def RunBatch():
    try:
        os.chdir(basePath + '/NDVI/ndvi_mos_gp/')
        os.system('batch_process.bat')
    except WindowsError:
        print('error')

def main():
    print("Script created by: Nikit Parakh")
    print("Contact: parakhni@msu.edu")
    print()
    print ('The workspace directory is: ', basePath, '\n')

    CheckOutputDir()

    print ('Searching for ERDAS .exe file location')
    ModelerLocation, ImageCommandLocation, ImgCopyLocation = FindModelerExe()
    print ('Done Searching\n')

    file_details = get_ndvi_mos_gp_files()
    if len(file_details) != 0:
        print('Files to be processed:')
        pprint.pprint([i[1] for i in file_details])
        print()
        print('Generating batchlist for processing')
        batchList = generate_param(file_details, ModelerLocation)
        print('\nCreating Batch File')
        getBatchFile(batchList)

        print ('Running batch file in ERDAS modeler...')
        RunBatch()


if __name__ == '__main__':
    main()

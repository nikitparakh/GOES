import sys, os, fnmatch, shutil
from pathlib import Path
import zipfile
import pprint

basePath = os.path.dirname(sys.argv[0]).replace("\\", "/")

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

def findFmaskExe():
    searchdir = []
    for root, dirs, files in os.walk(basePath):
        for exe in fnmatch.filter(files, '*.exe'):
            if exe == 'Fmask.exe':
                return os.path.join(root, exe).replace("\\", "/")

def CheckOutputDir():
    if not os.path.exists(basePath + '/external_files/'):
        os.makedirs(basePath + '/external_files/')
    if not os.path.exists(basePath + '/FMask_data/'):
        os.makedirs(basePath + '/FMask_data/')
    if not os.path.exists(basePath + '/NDVI/ndvi_masked'):
        os.makedirs(basePath + '/NDVI/ndvi_masked')

def getImageList():
    return [f.path for f in os.scandir(basePath + '/Raw_data/') if f.is_dir()]


def copyFMask(dirs, fmaskPath):
    exePaths = []
    for i in dirs:
        temp_path = i + '/Fmask.exe'
        if not Path(temp_path).is_file():
            shutil.copy2(fmaskPath, i)
        exePaths.append(temp_path)
    return exePaths


def move_other_files(images):
    for image in images:
        imagename = image[image.rfind("/") + 1:]
        for root, dirs, files in os.walk(image):
            if 'LC08' in image:
                for aux in fnmatch.filter(files, "*.aux"):
                    auxpath = os.path.join(root, aux).replace("\\", "/")
                    os.rename(auxpath, basePath + '/external_files/' + aux)
            for file in files:
                if 'ndvi' in file or 'parameter' in file or 'wdri' in file or 'README' in file or 'GCP' in file:
                    filepath = os.path.join(root, file).replace("\\", "/")
                    os.rename(filepath, basePath + '/external_files/' + file)


def move_fmask_files(images):
    for image in images:
        imagename = image[image.rfind("/") + 1:]
        for root, dirs, files in os.walk(image):
            for file in files:
                if 'mask' in file:
                    filepath = os.path.join(root, file).replace("\\", "/")
                    try:
                        os.rename(filepath, basePath + '/FMask_data/' + file)
                    except:
                        pass

def find_hdr_files():
    file_hdr = []

    for root, dirs, files in os.walk(basePath + '/FMask_data'):
        for file in fnmatch.filter(files, '*.hdr'):
            file_hdr.append(os.path.join(root, file).replace("\\", "/"))

    return file_hdr

def get_ndvi_fmask_files():
    ndvi_files = []
    fmask_files = []
    ndvi_names = []
    fmask_names = []

    for root, dirs, files in os.walk(basePath + '/NDVI/'):
        for img in fnmatch.filter(files, "*.img"):
            ndvi_files.append(os.path.join(root, img).replace("\\", "/"))
            ndvi_names.append(img[:img.rfind('_')])
        break

    for root, dirs, files in os.walk(basePath + '/FMask_data/'):
        for img in fnmatch.filter(files, "*.img"):
            fmask_files.append(os.path.join(root, img).replace("\\", "/"))
            fmask_names.append(img[:img.rfind('_')].upper())
        break

    common_files = []

    print(fmask_names, ndvi_names)

    for index, i in enumerate(ndvi_names):
        if i in fmask_names:
            common_files.append((ndvi_files[index], fmask_files[fmask_names.index(i)], i))

    return common_files


def generate_batchlist(files, modeler):

    batchList = []

    for ndvi, fmask, name in files:
        if not os.path.exists(basePath + '/NDVI/ndvi_masked/' + name + '_ndvi_masked.img'):
            f = open(basePath + '/NDVI/ndvi_masked/' + name + '_ndvi_masked_paramA', 'w')
            f.write('SET CELLSIZE MIN;\n'\
                    'SET WINDOW INTERSECTION;\n'\
                    'SET AOI NONE;\n')
            f.write('Float RASTER n1_{}_ndvi FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE "{}";\n'.format(name, ndvi))
            f.write('Integer RASTER n2_{}_mtlfmask FILE OLD PUBINPUT NEAREST NEIGHBOR AOI NONE "{}";\n'.format(name, fmask))
            f.write('Float RASTER n4_{}_ndvi_masked FILE NEW PUBOUT USEALL ATHEMATIC FLOAT SINGLE "{}";\n'.format(name, basePath + '/NDVI/ndvi_masked/' + name + '_ndvi_masked.img'))
            f.write('n4_{}_ndvi_masked = EITHER $n1_{}_ndvi IF ( $n2_{}_mtlfmask == 0 ) OR 0 OTHERWISE ;\nQUIT;'.format(name, name, name))
            f.close()
            f = open(basePath + '/NDVI/ndvi_masked/' + name + '_ndvi_masked_paramB', 'w')
            f.write('5\n'\
                'modeler\n'\
                '-nq\n'\
                + basePath + '/NDVI/ndvi_masked/' + name + '_ndvi_masked_paramA\n'\
                '-meter\n'\
                '-state\n')
            f.close()
            batchList.append(modeler + basePath + '/NDVI/ndvi_masked/' + name + '_ndvi_masked_paramB')
    return batchList

def getBatchFile(batchlist):
    f = open(basePath + '/NDVI/ndvi_masked/' + '/batch_process.bat', 'w')
    for i in range (0, len(batchlist)):
        f.write(str(batchlist[i]).replace('\\', '/') + '\n')
    f.close()


def RunBatch():
    try:
        os.chdir(basePath + '/NDVI/ndvi_masked/')
        os.system('batch_process.bat')
    except WindowsError:
        print('error')


def main():
    FMask_path = findFmaskExe()
    if not FMask_path:
        print("FMask Executable not found! Please copy it to the directory.")
    else:
        CheckOutputDir()

        list_of_images = getImageList()

        subDirFmaskPath = copyFMask(list_of_images, FMask_path)

        move_other_files(list_of_images)

        for i in list_of_images:
            os.chdir(i)
            print("Running Fmask for", os.path.basename(i))
            print()
            os.system('Fmask.exe')
            print()

        for i in subDirFmaskPath:
            os.remove(i)
        move_fmask_files(list_of_images)

    hdr_files = find_hdr_files()
    print('\nConverting hdr files to img\n')

    print ('Searching for ERDAS.exe file location')
    ModelerLocation, ImageCommandLocation, ImgCopyLocation = FindModelerExe()
    print ('Done Searching\n')

    print('\nFiles to be converted:')
    for file in hdr_files:
        print(os.path.basename(file), end=" - ")
        try:
            command = "{} -w 'Importing ENVI/AISA Hyperspectral Data' -t 'IMAGINE Image' -g FALSE -p FALSE -s 1 '{}' '{}'".format(ImgCopyLocation[:-2], file, file.replace('.hdr', '.img'))
            os.system(command)
            print("Success!")
        except:
            print("Failed!")


    file_details = get_ndvi_fmask_files()
    if len(file_details) != 0:
        print('Files to be processed:')
        pprint.pprint([i[2] for i in file_details])
        print()

        print('Generating batchlist for processing')
        batchList = generate_batchlist(file_details, ModelerLocation)

        if len(batchList) == 0:
            print('\nFiles have already been processed!')
        else:
            print('\nCreating Batch File')
            getBatchFile(batchList)

            print ('Running batch file in ERDAS modeler...')
            RunBatch()
    else:
        print('No valid files found for processing')

if __name__ == "__main__":
    main()

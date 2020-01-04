import os
import sys
import json

from PIL import Image, ImageOps
import cv2
import uuid
import time


# Instructions:
# 1. Make sure mediapipe_feed_data.py is in same directory
# 2. Put all images in folders in current directory, name folder after what image represents
# 3. run "python3 mediapipe_mass_feed_data.py"

# These parameters may be set by human
OUTPUT_FILE = "training_data.json"
BASE_RESOLUTION = (1920, 1920)

# Below parameters are set by script
SCRIPT_PATH = None 


def setResolution(path, resolution):
    assert isinstance(path, str), "Is actually {} with value {}".format(type(path), path)
    assert isinstance(resolution, tuple)
    assert len(resolution) == 2
    im = Image.open(path)
    if im.size == resolution:
        return
    im = ImageOps.fit(im, resolution)
    im.save(path, dpi=resolution)

def runMediapipe(filename, mediapipe_directory, outputname):
    command = "python mediapipe_feed_data.py --input={} --mediapipe_directory={}".format(filename, mediapipe_directory)
    stream = os.popen(command)
    output = stream.read()
    if output:
        result = json.loads(output)
        return [x for x in result[1::2] if any(y for y in x)]
    return []

class TrainingImage():
    def __init__(self, path):
        assert isinstance(path, str)

        self.path = path
    def testBad(self, output_file, primer, mediapipeDirectory):
        testVideo = createVideoFromImages([self,], output_file, primer)
        result = runMediapipe(testVideo, mediapipeDirectory, output_file)
        if len(result) != 1:
            print("{} had {} hands in it".format(self.path, len(result)))
            self.destroy()
            return True
        return False
    def destroy(self):
        print("{} destroyed".format(self.path))
        os.remove(self.path)
        del self

    def __hash__(self):
        return int(os.path.getmtime(self.path) * 10000000)

    def __str__(self):
        return self.path

    def __repr__(self):
        return self.path
        
def checkAlreadyRenamed(file_name):
    def checkValidUUID(givenStr):
        assert isinstance(givenStr, str)
        try:
            uuid.UUID(givenStr)
            return True
        except ValueError:
            return False

    assert isinstance(file_name, str)
    try:
        file_name = os.path.splitext(file_name)[0]
        if any(checkValidUUID(x) for x in file_name.split("_")):
            return True
        return False
    except Exception as e:
        print("Check process exception:", e)
        return False

def renameImageUUID(absolutePath, file_name, forName):
    if checkAlreadyRenamed(file_name) or os.path.isdir(file_name):
        return file_name
    newname = forName + "_" + str(uuid.uuid4()) + os.path.splitext(file_name)[1]
    os.rename(os.path.join(absolutePath, file_name), os.path.join(absolutePath, newname))
    return newname

def getImagesInFolder(absolutePath, forName):
    assert isinstance(absolutePath, str)
    assert isinstance(forName, str)
    image_names = [renameImageUUID(absolutePath, img, forName) for img in os.listdir(absolutePath) if img.endswith(".jpg") or img.endswith(".jpeg") or img.endswith(".png")]
    images = [TrainingImage(os.path.join(absolutePath, img)) for img in image_names]
    returnImages = []
    for img in images:
        try:
            setResolution(img.path, BASE_RESOLUTION)
            returnImages.append(img)
        except:
            print("{} is not a readable image".format(img))
            img.destroy()
    return returnImages

def createVideoFromImages(images, output_name, primer=None):
    assert isinstance(images, list)
    assert all(isinstance(x, TrainingImage) for x in images)
    assert isinstance(output_name, str)
    assert primer is None or isinstance(primer, str)
    video = cv2.VideoWriter(output_name, 0, 1, BASE_RESOLUTION)
    for image in images:
        video.write(cv2.imread(primer))
        video.write(cv2.imread(image.path))
    cv2.destroyAllWindows()
    video.release()
    return output_name


class Hash:
    HASH_FILE = "hash.txt"
    @staticmethod
    def getSavedHash(absolutePath):
        path = os.path.join(absolutePath, Hash.HASH_FILE)
        try:
            file = open(path)
            result = file.read()
            file.close()
            return result
        except:
            return False

    @staticmethod
    def getHash(images):
        if isinstance(images, list):
            images = tuple(images)
        return hash(images)

    @staticmethod
    def saveHash(absolutePath, images):
        newhash = Hash.getHash(images)
        path = os.path.join(absolutePath, Hash.HASH_FILE)
        file = open(path, "w")
        file.write(str(newhash))
        file.close()
        return newhash



def photoToJSON(absolutePath, word, mediapipeDirectory, PREVIOUS_DATA):
    ALL_IMAGES = getImagesInFolder(absolutePath)
    
    if PREVIOUS_DATA and word in PREVIOUS_DATA.keys() and str(Hash.getHash(ALL_IMAGES)) == Hash.getSavedHash(absolutePath) and len(ALL_IMAGES) == len(PREVIOUS_DATA[word]):
        print("{} unmodified, using previous data".format(word))
        return PREVIOUS_DATA[word]
    # if PREVIOUS_DATA:
    #     if word in PREVIOUS_DATA.keys():
    #         print("Previous data found!")
    #         currentHash = Hash.getHash(ALL_IMAGES)
    #         savedHash = Hash.getSavedHash(absolutePath)
    #         print("CURRENT HASH: {}".format(currentHash))
    #         print("PREVIOUS HASH: {}".format(savedHash))
    #         if str(currentHash) == savedHash:
    #             currentDataLength = len(ALL_IMAGES)
    #             savedDataLength = len(PREVIOUS_DATA[word])
    #             print("CURRENT DATA LENGTH: {}".format(currentDataLength))
    #             print("SAVED DATA LENGTH: {}".format(savedDataLength))
    #             if currentDataLength == savedDataLength:
    #                 print("Using hash for {}".format(word))
    #                 return PREVIOUS_DATA[word]
    #     else:
    #         print("{} not in {}".format(word, PREVIOUS_DATA.keys()))
    # else:
    #     print("NO PREVIOUS DATA")


    output_file = word + ".avi"
    output_file = os.path.join(absolutePath, output_file)
    original_image_count = len(ALL_IMAGES)

    primer = os.path.join(SCRIPT_PATH, "primer.jpg")
    video = createVideoFromImages(ALL_IMAGES, output_file, primer)
    result = runMediapipe(video, mediapipeDirectory, word)
    if len(ALL_IMAGES) != len(result):
        ALL_IMAGES = [x for x in ALL_IMAGES if not x.testBad(output_file, primer, mediapipeDirectory)]
        video = createVideoFromImages(ALL_IMAGES, output_file, primer)
        result = runMediapipe(video, mediapipeDirectory, word)
            
    if original_image_count != len(ALL_IMAGES):
        print("{} images used out of {}".format(len(ALL_IMAGES), original_image_count))
    else:
        print("{} images used".format(original_image_count))

    Hash.saveHash(absolutePath, ALL_IMAGES)

    return result

def getMediapipeDirectory():
    MEDIAPIPE_DIRECTORY = None
    while MEDIAPIPE_DIRECTORY is None or not os.path.isdir(MEDIAPIPE_DIRECTORY):
        if MEDIAPIPE_DIRECTORY:
            print("Invalid directory!")
        MEDIAPIPE_DIRECTORY = input("Please enter mediapipe absolute directory:\n")  
        # if not os.path.isabs(MEDIAPIPE_DIRECTORY):
        #     MEDIAPIPE_DIRECTORY = None
        #     print("Must be an absolute path!")
        if MEDIAPIPE_DIRECTORY and MEDIAPIPE_DIRECTORY[-1] != "/":
            MEDIAPIPE_DIRECTORY += "/"      
    return MEDIAPIPE_DIRECTORY

def sudoActivator():
    stream = os.popen("sudo echo 'Sudo mode activated'")
    output = stream.read()
    return True

def main():
    global SCRIPT_PATH
    sudoActivator()
    pathname = os.path.dirname(sys.argv[0]) 
    SCRIPT_PATH = os.path.abspath(pathname)
    try:
        file = open(OUTPUT_FILE, "r")
        PREVIOUS_DATA = json.load(file)
        print("Previous data loaded with {} symbols in {} total data points".format(len(PREVIOUS_DATA), sum(len(x) for x in PREVIOUS_DATA.values())))
    except:
        print("No previous {} found".format(OUTPUT_FILE))
        PREVIOUS_DATA = None

    MEDIAPIPE_DIRECTORY = getMediapipeDirectory()
    
    CURRENT_PATH = os.getcwd()
    RESULTS = {}
    for file in os.listdir(CURRENT_PATH):
        full_path = os.path.join(CURRENT_PATH, file)
        if os.path.isdir(full_path):
            RESULTS[file] = photoToJSON(full_path, file, MEDIAPIPE_DIRECTORY, PREVIOUS_DATA)
            print("{} done".format(file))
            

    file = open(OUTPUT_FILE, "w+")
    json.dump(RESULTS, file)


if __name__ == "__main__":
    main()
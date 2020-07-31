import json
import os, sys
from statistics import mean, stdev
from string import ascii_uppercase
from uuid import uuid4

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.mlab as mlab
import matplotlib.animation as animation
from mpl_toolkits.mplot3d import Axes3D

# PATH = "/home/ari/Desktop/SigNN/training_data/"

def norm(hands):
    assert isinstance(hands, list)
    assert all(isinstance(hand, list) for hand in hands)
    normHands = []
    for hand in hands:
        xCoords = [x for x in hand[::2]]
        yCoords = [y for y in hand[1::2]]

        normXCoords = [x / max(xCoords) for x in xCoords]
        normYCoords = [y / max(yCoords) for y in yCoords]

        normHand = [None]*(len(normXCoords)+len(normYCoords))
        normHand[::2] = normXCoords
        normHand[1::2] = normYCoords
        normHands.append(normHand)

    return normHands


def loadHandsVideo(jsonFile):
    assert ".json" in jsonFile, 'Must be a json file!'
    file = open(os.path.join(SCRIPT_PATH, jsonFile))
    hand_frames = []
    jsonData = json.load(file)
    for frame in jsonData:
        if frame:
            hand_frames.append(frame[0])
    return hand_frames

def loadHands(jsonFile):
    assert ".json" in jsonFile, 'Must be a json file!'
    file = open(os.path.join(SCRIPT_PATH, jsonFile))
    jsonData = json.load(file)
    return jsonData

def analyzeHands(hands):
    assert isinstance(hands, list)
    assert all(isinstance(hand, list) for hand in hands)
    try:
        VALUES_PER_HAND = len(hands[0])
    except:
        return {
            "mean" : None,
            'stdev' : None,
            'max' : None,
            'min' : None
        }
    assert all(len(hand) == VALUES_PER_HAND for hand in hands), "Not all hands have {} points".format(VALUES_PER_HAND)

    averagePoints = []
    stDevs = []
    minPoints = []
    maxPoints = []
    
    for point in range(0, VALUES_PER_HAND):
        means = mean(x[point] for x in hands)
        try:
            devs = stdev(x[point] for x in hands)
        except:
            devs = 0
        mins = min(x[point] for x in hands)
        maxs = max(x[point] for x in hands)
        averagePoints.append(means)
        stDevs.append(devs)
        minPoints.append(mins)
        maxPoints.append(maxs)


    return {
        "mean" : averagePoints,
        "stdev" : stDevs,
        'max' : maxPoints,
        'min' : minPoints
    }


def plot(hand, word, save=False, temp=False, **kwargs):
    limits = kwargs.get("limits", None)
    assert isinstance(save, bool)
    COLORS = ['red', 'blue', 'green', 'purple', 'black']
    if len(hand) == 63:
        x = [max(xx for xx in hand[::3]) - x for x in hand[::3]]
        y = [max(yy for yy in hand[1::3]) - y for y in hand[1::3]]
    else:
        x = [max(xx for xx in hand[::2]) - x for x in hand[::2]]
        y = [max(yy for yy in hand[1::2]) - y for y in hand[1::2]]

    text = [z for z in range(0, len(x))]
    assert len(x) == len(y), "Uneven x and y coordnates. {} x and {} y".format(len(x), len(y))
    plt.scatter(x, y)
    plt.xlabel('x')
    plt.ylabel('y')
    plt.axis('square')
    plt.title(word)

    if limits:
        plt.xlim(right=limits['xmax'])
        plt.xlim(left=limits['xmin'])
        plt.ylim(top=limits['ymax'])
        plt.ylim(bottom=limits['ymin'])

    for i, txt in enumerate(text):
        plt.annotate(txt, (x[i], y[i]))

    for finger, color in zip(range(1, 21, 4), COLORS):
        plt.plot(x[finger:finger+4], y[finger:finger+4], 'ro-', color=color)

    if save:
        if temp:
            folder = "images"
        else:
            folder = "image_means"
        path = os.path.join(folder, word + '.png')
        plt.savefig(path)
        plt.close()
        return path
    else:
        plt.show()
    plt.close()
        

def getMeansToTxt(saveFile):
    assert isinstance(saveFile, str)
    assert "." not in saveFile, "Cannot specify extension. Will always be .txt file"
    result = ""
    file = open("data_creation/training_data.json")
    # for key, value in json.load(file).items():
    #     results[key] = {
    #         'mean' : analyzeHands(value)['mean'],
    #         'stdev' : analyzeHands(value)['stdev'],
    #         'n' : len(value)
    #     }
    for key, value in json.load(file).items():
        entry = "Word: " + key
        entry += "\nMeans: " + str(analyzeHands(value)['mean']).replace("[", "").replace("]", "")
        entry += "\nStdevs: " + str(analyzeHands(value)['stdev']).replace("[", "").replace("]", "")
        entry += "\nn: " + str(len(value))
        result += entry + "\n"
    file.close()
    file = open(saveFile + ".txt", "w+")
    file.write(result)
    file.close()
    return result

def saveMeansImages(data):
    assert isinstance(data, dict)
    data = list(data.items())
    data.sort()
    for key, value in data:
        plot(analyzeHands(value)['mean'], key, True)


def Plot3D(hand, word, save=False, temp=False):
    assert isinstance(hand, list)
    assert len(hand) == 63
    COLORS = ['red', 'blue', 'green', 'purple', 'black']
    x = [x for x in hand[::3]]
    y = [y for y in hand[1::3]]
    z = [z for z in hand[2::3]]
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    # ax.scatter(x, y, z)
    plt.title(word)
    for finger, color in zip(range(1, 21, 4), COLORS):
        plt.plot(x[finger:finger+4], y[finger:finger+4], z[finger:finger+4], 'ro-', color=color)
    if save:
        if temp:
            folder = "images"
        else:
            folder = "image_means"
        path = os.path.join(folder, word + '.png')
        plt.savefig(path)
        plt.close()
        return path
    plt.show()
    plt.close()
    return x, y, z



def plotVideo(hand_series, word, third_dimention):
    i = 0
    xmin = 0
    xmax = 0
    ymin = 0
    ymax = 0
    for hand in hand_series:
        x = [x for x in hand[::3]]
        y = [y for y in hand[1::3]]
        z = [z for z in hand[2::3]]

        xmax = max(x)
        xmin = 0
        ymax = max(y)
        ymin = 0
        zmax = max(z)
        zmin = 0

        xmax = max(xmax, ymax)
        ymax = xmax

    limits = {
        "xmax" : xmax, "xmin" : xmin,
        "ymax" : ymax, "ymin" : ymin,
        "zmax" : zmax, "zmin" : zmin
    }

    for image in os.listdir("images"):
        os.remove(os.path.join("images", image))
    for hand in hand_series:
        i += 1
        if third_dimention:
            Plot3D(hand, word + str(i).zfill(2), True, True)
        else:
            plot(hand, word + str(i).zfill(2), True, True, limits=limits)
    os.system('ffmpeg -framerate 10 -pattern_type glob -i "images/*.png" -c:v libx264 -r 10 -pix_fmt yuv420p {} -loglevel error -y'.format(word + ".mp4"))





global SCRIPT_PATH
pathname = os.path.dirname(sys.argv[0]) 
SCRIPT_PATH = os.path.abspath(pathname)
video = loadHandsVideo("J_07-30-2020_21_54_57.json")
plotVideo(video, "J", False)
# DATA = loadHands("data_creation/training_data.json")
# plot(analyzeHands(DATA['A'])['mean'], "A")
# analyzeHands(DATA['A']['stdev'])
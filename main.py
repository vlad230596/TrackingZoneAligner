import json
import cv2
import numpy as np

from enum import Enum
from dataclasses import dataclass

from zoom import PanZoomWindow


@dataclass
class ScreenPoint:
    x: float
    y: float

class Colors(Enum):
    RED = (0, 0, 255)
    BLUE = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLACK = (0, 0, 0)

def readJson(filename):
    f = open(filename)
    data = json.load(f)
    f.close()
    return data

def writeJson(filename, obj):
    f = open(filename, "w")
    f.write(json.dumps(obj, indent=4))
    f.close()
    pass

def getMovedPoint(point, width, height):
    result = ScreenPoint(point['x'] + width / 2, height / 2 - point['z'])
    return result

def toPixelCoordinate(value, scale):
    return int(value * scale)

#def warpTargetRegion(src, dst, lb, lt, rt, rb):
def warpTargetRegion(src, dst, roiPoints):
    srcWidth = src.shape[1]
    srcHeight = src.shape[0]

    #pts1 = np.float32([lb, lt, rb, rt])
    #pts1 = np.float32([lt, rt, lb, rb])
    #pts2 = np.float32([[0, 0], [srcWidth, 0], [0, srcHeight], [srcWidth, srcHeight]])

    pts1 = np.float32(roiPoints)
    pts2 = np.float32([[0, srcHeight],[0, 0], [srcWidth, 0], [srcWidth, srcHeight]])


    #M = cv2.getPerspectiveTransform(pts1, pts2)
    h, status = cv2.findHomography(pts1, pts2)
    result = cv2.warpPerspective(dst, h, (srcWidth, srcHeight), cv2.INTER_CUBIC)

    return result


mousePoint = ()

def onLeftClick(y,x):
    global mousePoint
    mousePoint = (x, y)
    print(f'p ({x}, {y})')


if __name__ == '__main__':
    outputFilename = 'data/ssfilmz/blended.png'
    roiFilename = 'data/ssfilmz/Roi.json'

    description = readJson('data/ssfilmz/ZoneDescription.json')
    print(f'loaded {len(description["Markers"])} markers')
    realFoto = cv2.imread('data/ssfilmz/full.jpg')

    roi = readJson(roiFilename)
    roiPoints = roi['Points']
    boarderSize = 0
    if(roi['BoarderSize']):
        boarderSize = roi['BoarderSize']
    realFoto = cv2.copyMakeBorder(realFoto, boarderSize, boarderSize, boarderSize, boarderSize, cv2.BORDER_CONSTANT, value=Colors.BLACK.value)


    baseScale = 2
    scale = baseScale * 100

    width = description["Width"]
    height = description["Height"]
    cellSize = description["CellSize"]

    screenWidth = int(width * scale)
    screenHeight = int(height * scale)


    blank_image = np.zeros((screenHeight, screenWidth, 3), np.uint8)

    for marker in description["Markers"]:
        point = getMovedPoint(marker, width, height)
        center = (toPixelCoordinate(point.x, scale), toPixelCoordinate(point.y, scale))
        cv2.circle(blank_image, center, int(baseScale * 2), Colors.RED.value, int(baseScale / 2))

    for lineX in np.arange(cellSize, width, cellSize):
        cv2.line(blank_image, (toPixelCoordinate(lineX, scale), 0), (toPixelCoordinate(lineX, scale), screenHeight), Colors.RED.value, 1)

    for lineY in np.arange(cellSize, height, cellSize):
        cv2.line(blank_image, (0, toPixelCoordinate(lineY, scale)), (screenWidth, toPixelCoordinate(lineY, scale)), Colors.RED.value, 1)

    cv2.imshow('test', blank_image)


    view = realFoto.copy()
    window = PanZoomWindow(img=view, windowName="RR", onLeftClickFunction=onLeftClick)


    dummy = realFoto.copy()
    dummy[:] = Colors.BLACK.value




    blendK = 0.5
    while True:
        view = realFoto.copy()
        for p in roiPoints:
            cv2.circle(view, tuple(p), 20, Colors.RED.value, 5)
        window.replaceImage(view)

        warped = warpTargetRegion(blank_image, realFoto, roiPoints)
        blended = cv2.addWeighted(warped, 0.8, blank_image, blendK, 0)
        cv2.imshow('blended', blended)

        c = cv2.waitKey(0)
        selectedIndex = -1

        if (c == 27):
            break

        if(c == ord('0')):
            selectedIndex = 0
        if (c == ord('1')):
            selectedIndex = 1
        if (c == ord('2')):
            selectedIndex = 2
        if (c == ord('3')):
            selectedIndex = 3
        if(selectedIndex != -1):
            roiPoints[selectedIndex] = mousePoint

        if(c == ord('+')):
            blendK += 0.2
            if(blendK > 1.0):
                blendK = 1.0

        if (c == ord('-')):
            blendK -= 0.2
            if (blendK < 0.0):
                blendK = 0.0

        if (c == ord('s') or c == ord('S')):
            print(f'save file to {outputFilename}')
            cv2.imwrite(outputFilename, blended)

        if (c == ord('p') or c == ord('P')):
            print(f'save points to {roiFilename}')
            roi['Points'] = roiPoints
            writeJson(f'{roiFilename}', roi)

    # dummy = np.zeros((realFoto.height, realFoto.width, 3), np.uint8)
    # dummy[:] = Colors.BLACK.value





    cv2.destroyAllWindows()


import json
import cv2
import numpy as np
import glob
import os

from dataclasses import dataclass

#from Eni.Py.zoom import PanZoomWindow
from EniPy import zoom
from EniPy import colors
from EniPy import eniUtils


from tkinter import *
from tkinter import ttk


@dataclass
class ScreenPoint:
    x: float
    y: float

def getDirectories(path):
    result = []
    for root, dirs, files in os.walk(path, topdown=False):
        for name in dirs:
            result.append(name)
    return result
def getMovedPoint(point, width, height):
    global flipX
    global flipZ

    signX = 1
    signZ = -1

    if(flipX.get()):
        signX = signX * -1

    if(flipZ.get()):
        signZ = signZ * -1

    result = ScreenPoint((signX * point['x']) + width / 2, height / 2 + (signZ * point['z']))
    return result

def toPixelCoordinate(value, scale):
    return int(value * scale)

def warpTargetRegion(src, dst, roiPoints):
    srcWidth = src.shape[1]
    srcHeight = src.shape[0]

    pts1 = np.float32(roiPoints)
    pts2 = np.float32([[0, srcHeight], [0, 0], [srcWidth, 0], [srcWidth, srcHeight]])

    h, status = cv2.findHomography(pts1, pts2)
    result = cv2.warpPerspective(dst, h, (srcWidth, srcHeight), cv2.INTER_CUBIC)

    return result


mousePoint = ()
newClick = False
selectedCase = ""

flipX = ()
flipZ = ()



def onLeftClick(y,x):
    global mousePoint
    global newClick
    mousePoint = (x, y)
    newClick = True
    print(f'p ({x}, {y})')

def selected(event):
    global selectedCase

    selectedCase = combobox.get()
    print(f'selectedCase: {selectedCase}')


def onDrawClick():
    draw(selectedCase)

def draw(caseName):
    global newClick



    outputFilename = f'data/{caseName}/blended.png'
    roiFilename = f'data/{caseName}/Roi.json'

    description = eniUtils.readJson(f'data/{caseName}/ZoneDescription.json')
    print(f'loaded {len(description["Markers"])} markers')
    realFoto = cv2.imread(glob.glob(f'data/{caseName}/full.*')[0])

    roi = eniUtils.readJson(roiFilename)
    roiPoints = roi['Points']
    boarderSize = 0
    if "BoarderSize" in roi:
        boarderSize = roi['BoarderSize']
    realFoto = cv2.copyMakeBorder(realFoto, boarderSize, boarderSize, boarderSize, boarderSize, cv2.BORDER_CONSTANT,
                                  value=colors.Black)

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
        cv2.circle(blank_image, center, int(baseScale * 2), colors.Red, int(baseScale))

    for lineX in np.arange(cellSize, width, cellSize):
        cv2.line(blank_image, (toPixelCoordinate(lineX, scale), 0), (toPixelCoordinate(lineX, scale), screenHeight),
                 colors.Red, 1)

    for lineY in np.arange(cellSize, height, cellSize):
        cv2.line(blank_image, (0, toPixelCoordinate(lineY, scale)), (screenWidth, toPixelCoordinate(lineY, scale)),
                 colors.Red, 1)

    cv2.imshow('test', blank_image)

    view = realFoto.copy()
    window = zoom.PanZoomWindow(img=view, windowName="RR", onLeftClickFunction=onLeftClick)

    dummy = realFoto.copy()
    dummy[:] = colors.Black

    blendK = 0.5
    selectedIndex = -1

    while True:
        view = realFoto.copy()
        for p in roiPoints:
            cv2.circle(view, tuple(p), 20, colors.Red, 15)
        cv2.putText(view, f'{selectedIndex}', (0, 50), cv2.FONT_HERSHEY_SIMPLEX, 2, colors.Red, 4)
        window.replaceImage(view)

        warped = warpTargetRegion(blank_image, realFoto, roiPoints)
        blended = cv2.addWeighted(warped, 0.8, blank_image, blendK, 0)
        cv2.imshow('blended', blended)

        c = cv2.waitKeyEx(1)

        if (c == 27):
            break

        if (c == ord('0')):
            selectedIndex = 0
        if (c == ord('1')):
            selectedIndex = 1
        if (c == ord('2')):
            selectedIndex = 2
        if (c == ord('3')):
            selectedIndex = 3

        if (selectedIndex != -1):
            targetPoint = roiPoints[selectedIndex]

        if (c == 0x10000 * 0x25):
            print('L')
            if (targetPoint):
                targetPoint[0] = targetPoint[0] - 1

        if (c == 0x10000 * 0x27):
            print('R')
            if (targetPoint):
                targetPoint[0] = targetPoint[0] + 1

        if (c == 0x10000 * 0x26):
            print('U')
            if (targetPoint):
                targetPoint[1] = targetPoint[1] - 1

        if (c == 0x10000 * 0x28):
            print('D')
            if (targetPoint):
                targetPoint[1] = targetPoint[1] + 1

        if (newClick):
            print('New click detected')
            if (selectedIndex != -1):
                roiPoints[selectedIndex] = list(mousePoint)
            newClick = False

        if (c == ord('+')):
            blendK += 0.2
            if (blendK > 1.0):
                blendK = 1.0

        if (c == ord('-')):
            blendK -= 0.2
            if (blendK < 0.0):
                blendK = 0.0

        if (c == ord('r') or c == ord('R')):
            print(f'rotate')
            roiPoints[:] = roiPoints[1:] + roiPoints[0:1]

        if (c == ord('s') or c == ord('S')):
            print(f'save file to {outputFilename}')
            cv2.imwrite(outputFilename, blended)

        if (c == ord('p') or c == ord('P')):
            print(f'save points to {roiFilename}')
            roi['Points'] = roiPoints
            eniUtils.writeJson(f'{roiFilename}', roi)

    cv2.destroyAllWindows()

if __name__ == '__main__':


    root = Tk()
    root.title("TrackingZoneAligner")
    root.geometry("480x640")

    flipX = IntVar(value=0)
    flipZ = IntVar(value=0)

    #root, dirs, files = os.walk("./data/", topdown=False)
    cases = getDirectories("./data/")
    label = ttk.Label()
    label.pack(anchor=NW, fill=X, padx=5, pady=5)

    combobox = ttk.Combobox(values=cases, state="readonly")
    combobox.pack(anchor=NW, fill=X, padx=5, pady=5)
    combobox.bind("<<ComboboxSelected>>", selected)

    flipXCheckbutton = ttk.Checkbutton(text="FlipX", variable=flipX)
    flipXCheckbutton.pack()

    flipZCheckbutton = ttk.Checkbutton(text="FlipZ", variable=flipZ)
    flipZCheckbutton.pack()

    drawButton = ttk.Button(root, text="Draw", command=onDrawClick)
    drawButton.pack()


    root.mainloop()
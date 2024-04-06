#!/usr/bin/env python

import numpy as np
import cv2, sys, getopt
from copy import deepcopy

# returns 2 objects :
# - A 9x9 list of cells, each cell being a number if it's a known number, or a list of possibilities which default to a list of numbers from 1 to 9
# - A list of positions (list row, column) where cells are unknown
def readTextGrid(infile):
    grid = []
    toFind = []
    l = 0
    for i, line in enumerate(infile):
        if line.startswith('---'):
            continue
        r = 0
        gridLine = []
        for c in line.strip('\n'):
            if c == '|':
                continue
            if c == ' ':
                gridLine.append([ n+1 for n in range(9) ])
                toFind.append((l, r))
            else:
                gridLine.append(int(c))
            r += 1
        grid.append(gridLine)
        l += 1

    return grid, toFind


def waitKey():
    key = cv2.waitKey()
    if key == ord('q') or key == ord('Q'):
        sys.exit(0)
    return key

gray  = (160, 160, 160)
black = (0, 0, 0)
blue  = (200, 0, 0)

def putNumber(img, x, y, value):
    if value < 0:
        color = blue
        value = abs(value)
    else:
        color = black
    ((w, h), z) = (cv2.getTextSize(str(value), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=3, thickness=5))
    pos = (50 + 100*x - w//2, 50 + 100*y + h//2)
    cv2.putText(img, str(value), pos, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=3, color=color, thickness=5, lineType=cv2.FILLED)

def putList(img, x, y, value):
    x0=100*x
    y0=100*y
    for i in range(0,9):
        if (i+1 in value):
            ((w, h), z) = (cv2.getTextSize(str(i+1), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, thickness=2))
            pos = (x0 + (i%3)*33 + 16 - w//2 , y0 + (i//3)*33 + 16 + h//2)
            cv2.putText(img, str(i+1), pos, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1, color=blue, thickness=2, lineType=cv2.FILLED)


def displayGrid():
    global grid

    # create blank grid
    img = np.full((900, 900, 3), gray, np.uint8)
    for i in range(0, 900, 100):
        t = 5 if i % 300 == 0 else 2
        cv2.line(img, (i, 0), (i, 900), color = black, thickness = t)
        cv2.line(img, (0, i), (900, i), color = black, thickness = t)

    for y, row in enumerate(grid):
        for x, cell in enumerate(row):
            if type(cell) is int:
                putNumber(img, x, y, cell)
            else:
                putList(img, x, y, cell)
    # ((w, h), z) = (cv2.getTextSize(t, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=3, thickness=5))
    # cv2.putText(img, t, (20, 85), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=3, color=(0, 0, 0), thickness=5, lineType=cv2.FILLED)
    # cv2.rectangle(img, (20, 85), (20+w, 85-h), color=(0, 200, 0))

    cv2.imshow("grid", img)


def removeValue(value, x, y):
    cell = grid[y][x]
    if type(cell) is list and value in cell:
        cell.remove(value)


def onMouseEvent(event, x, y, flags, param):
    if event == cv2.EVENT_MOUSEMOVE:
        return
    
    global history, grid

    # print(event, x, y, flags)

    cellX = x // 100
    cellY = y // 100
    subCellX = (x % 100) // 33
    subCellY = (y % 100) // 33
    subCell = 1 + subCellX + subCellY*3

    if event == cv2.EVENT_LBUTTONUP:
        history.append(deepcopy(grid))
        cell = grid[cellY][cellX]
        if type(cell) is int:
            # remove dependencies
            for x in range(0,9):
                removeValue(abs(cell), x, cellY)
            for y in range(0,9):
                removeValue(abs(cell), cellX, y)
            x0 = cellX-cellX%3
            y0 = cellY-cellY%3
            for x in range(x0, x0+3):
                for y in range(y0, y0+3):
                    removeValue(abs(cell), x, y)
        else:
            # select digit
            grid[cellY][cellX] = -subCell

        displayGrid()



def main(args):
    global history, grid

    if len(args) == 0:
        inFile = sys.stdin
    else:
        inFile = open(args[0], 'r')
    grid, toFind = readTextGrid(inFile)
    history = []

    displayGrid()
    cv2.setMouseCallback("grid", onMouseEvent)
    while True:
        key = cv2.waitKey(20)
        if key in (ord('q'), ord('Q')):
            break
        if key == 8 or key in (ord('u'), ord('U')):
            if len(history) >= 1:
                print("undo")
                grid = history.pop()
                displayGrid()
        if key in (ord('h'), ord('H')):
            for h in history:
                print(h)

if __name__ == "__main__":
    main(sys.argv[1:])

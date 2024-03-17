#!/usr/bin/env python

import numpy as np
import cv2, sys, getopt

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


def displayGrid(grid):
    # create blank grid
    img = np.full((900, 900, 3), (160, 160, 160), np.uint8)
    for i in range(0, 900, 100):
        t = 5 if i %300 == 0 else 2
        cv2.line(img, (i, 0), (i, 900), color = (0, 0, 0), thickness = t)
        cv2.line(img, (0, i), (900, i), color = (0, 0, 0), thickness = t)

    t = '123'
    ((w, h), z) = (cv2.getTextSize(t, fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=3, thickness=5))
    cv2.putText(img, t, (20, 85), fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=3, color=(0, 0, 0), thickness=5, lineType=cv2.FILLED)
    cv2.rectangle(img, (20, 85), (20+w, 85-h), color=(0, 200, 0))

    cv2.imshow("grid", img)
    waitKey()

    # for line in grid:
    #     print(line)


def main(args):
    if len(args) == 0:
        # read stdin as input text
        grid, toFind = readTextGrid(sys.stdin)
        print("to find : ", toFind)
        displayGrid(grid)

if __name__ == "__main__":
    main(sys.argv[1:])

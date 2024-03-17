#!/usr/bin/env python

import numpy as np
import cv2, sys, getopt
import pytesseract

threshold = None
showSteps = False

def parseArgs(argv, specs):
    global showSteps
    opts, args = getopt.getopt(argv, 's' + specs)

    result = {}
    for o, v in opts:
        if o == '-s':
            showSteps = True
        else:
            result[o[1]] = v

    return result, args


# TODO : plutot voir pour selectionner un carré :
#   afficher une grille de 9x9 avec des traits plus épais à 3x3
#   gérer un drag&drop des 4 coins pour aligner avec l'image
#   en déduire les zones des chiffres et faire du tesseract dessus s'il y a qqch dedans
#    = trouver un filtre pour juger si c'est une case vide ou pas (revoir comment c'est fait dans le script crossword)

def waitKey():
    key = cv2.waitKey()
    if key == ord('q') or key == ord('Q'):
        sys.exit(0)
    return key

outputWindowCreated = False
def showStep(image, title, force = False, wait = True):
    global showSteps, outputWindowCreated
    if not force and not showSteps:
        return

    if not outputWindowCreated:
        cv2.namedWindow("output", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("output", 800, 800)
        outputWindowCreated = True
    cv2.imshow("output", image)
    cv2.setWindowTitle("output", title)
    if wait:
        waitKey()

def boundingPolygon(contour, xc, yc):
    ul = (None, None, 0)
    ur = (None, None, 0)
    br = (None, None, 0)
    bl = (None, None, 0)

    for point in contour:
        x, y = point[0]
        d2 = (xc-x)*(xc-x) + (yc-y)*(yc-y)
        # print(f'{x},{y} -> {xc},{yc} = {d2}')
        if x <= xc and y <= yc:
            if ul[2] < d2:
                ul = (x, y, d2)
        if x > xc and y <= yc:
            if ur[2] < d2:
                ur = (x, y, d2)
        if x <= xc and y > yc:
            if bl[2] < d2:
                bl = (x, y, d2)
        if x > xc and y > yc:
            if br[2] < d2:
                br = (x, y, d2)
    if ul[2] == 0 or ur[2] == 0 or br[2] == 0 or bl[2] == 0:
        return None, None
    return (ul[:2], ur[:2], br[:2], bl[:2]), ul[2]+ur[2]+br[2]+bl[2]

def detectSquare(img, threshold1, threshold2):
    imgW, imgH = img.shape[0:2]

    # sobelx  = cv2.Sobel(src=img, ddepth=cv2.CV_64F, dx=1, dy=0, ksize=15) # Sobel Edge Detection on the X axis
    # sobely  = cv2.Sobel(src=img, ddepth=cv2.CV_64F, dx=0, dy=1, ksize=15) # Sobel Edge Detection on the Y axis
    # # Display Sobel Edge Detection Images
    # showStep(sobelx, 'Sobel X')
    # showStep(sobely, 'Sobel Y')

    # detect edges
    if threshold1 is None or threshold2 is None:
        threshold1=100
        threshold2=200
        print(f'adjust threshold1 with up/down keys, threshold2 with left/right, hit enter when ok')
        while True:
            print(f'threshold1 = {threshold1} , threshold2 = {threshold2}')
            canny = cv2.Canny(image=img, threshold1=threshold1, threshold2=threshold2) # Canny Edge Detection
            showStep(canny, 'Canny', force = True, wait = False)

            key = waitKey()
            if key == 13:
                break
            elif key == 82:
                threshold1 += 5
            elif key == 84:
                threshold1 -= 5
            elif key == 83:
                threshold2 += 5
            elif key == 81:
                threshold2 -= 5
    else:
        canny = cv2.Canny(image=img, threshold1=threshold1, threshold2=threshold2) # Canny Edge Detection
        showStep(canny, 'Canny')

    # detect outer contours
    contours, hierarchy = cv2.findContours(canny, method = cv2.CHAIN_APPROX_SIMPLE, mode = cv2.RETR_EXTERNAL)
    # print('found', len(contours), 'contours')
    if showSteps:
        cnt=0
        print(f'select contour with up/down keys between 0 and {len(contours)-1}, hit enter when ok')
        while True:
            contour = img.copy()
            cv2.drawContours(contour, contours, cnt, (0,255,0), 1)
            showStep(contour, f'contours {cnt}', force=True, wait=False)
            key = waitKey()
            if key == 13:
                break
            elif key == 82 and cnt < len(contours)-1:
                cnt += 1
            elif key == 84 and cnt > 0:
                cnt -= 1

    # find largest contour and it's bounding polygon
    contour = img.copy()
    ulMax, urMax, brMax, blMax = None, None, None, None
    sizeMax = 0
    for cnt in contours:
        poly, size = boundingPolygon(cnt, imgW // 2, imgH // 2)
        if poly is not None:
            # print(f'found polygon {poly}')
            pts = np.array(poly, np.int32)
            pts = pts.reshape((-1,1,2))
            cv2.polylines(contour, [pts], isClosed = True, color = (0,255,0), thickness =  1)
            if size > sizeMax:
                ulMax, urMax, brMax, blMax = poly
                sizeMax = size

    if sizeMax == 0:
        return None
    showStep(contour, 'contours')
    return ulMax, urMax, brMax, blMax

def findDigits(img, square):
    # find digits in grid :
    # for each cell, extract half size square, blur it and look at gray level of center point
    # if < 140, extract full square and mark this cell as nth digit
    # else, consider it as blank

    (ulx, uly), (urx, ury), (brx, bry), (blx, bly) = square

    grid = []
    digits = []
    digit = 0

    w = (urx-ulx)//9
    h = (bly-uly)//9
    gridImg = img.copy()
    for line in range(0,9):
        leftx, lefty    = int(ulx + (blx-ulx)/9 * line), int(uly + (bly-uly)/9 * line)
        rightx, righty  = int(urx + (brx-urx)/9 * line), int(ury + (bry-ury)/9 * line)
        gridLine = []
        for row in range(0,9):
            x = int(leftx + (rightx-leftx)/9 * row)
            y = int(lefty + (righty-lefty)/9 * row)
            subcell = img[y+h//4:y+h//4+h//2, x+w//4:x+w//4+w//2]
            blur = cv2.GaussianBlur(subcell, (w//4 | 1 , h//4 | 1), 0)
            # print(blur[h//4][w//4], blur[2][2])
            if blur[h//4][w//4] < 140:
                digits.append(img[y+3:y+h-6, x+3:x+w-6])
                cv2.rectangle(gridImg, (x,y), (x+w,y+h), 0, 1)
                gridLine.append(digit)
                digit+=1
            else:
                gridLine.append(' ')
        grid.append(gridLine)
    showStep(gridImg, "grid")

    # concatenate all digits and send result to tesseract
    digits = np.concatenate(digits, axis=1)
    showStep(digits, "digits")
    # cv2.imwrite("data/digits.png", digits)

    config = ("-c tessedit_char_whitelist=123456789 -c tessedit_enable_doc_dict=0")
    text = pytesseract.image_to_string(digits, config=config).strip()
    if len(text) != digit:
        print(f'OCR failed : found "{text}" -> {len(text)} instead of {digit}', file=sys.stderr)
        sys.exit(1)

    for line in range(0,9):
        for row in range(0,9):
            if grid[line][row] != ' ':
                grid[line][row] = text[grid[line][row]]

    return grid

def main(argv):
    opts, args = parseArgs(argv, '1:2:')
    threshold1 = int(opts['1']) if '1' in opts else None
    threshold2 = int(opts['2']) if '2' in opts else None

    # 1. Loading the Image
    img = cv2.imread(args[0])
    imgW, imgH = img.shape[0:2]
    # print(f'Image size : {imgW}x{imgH}')
    showStep(img, "raw image")

    # resize
    imgSize = 300
    if imgW > imgH:
        ratio = imgW / imgH
        imgW = imgSize
        imgH = int(imgSize * ratio)
    else:
        ratio = imgH / imgW
        imgW = int(imgSize * ratio)
        imgH = imgSize
    resize = cv2.resize(img, (imgW, imgH))

    # convert to gray and blur
    gray = cv2.cvtColor(resize, cv2.COLOR_BGR2GRAY)
    showStep(gray, "gray")

    blur = cv2.GaussianBlur(gray, (5,5), 0) 
    showStep(blur, "blur")

    # detect grid position
    square = detectSquare(blur, threshold1, threshold2)

    if showSteps:
        (ulx, uly), (urx, ury), (brx, bry), (blx, bly) = square
        grid = resize.copy()
        for i in range(0,10):
            thickness = 2 if i%3 == 0 else 1
            top    = (int(ulx + (urx-ulx)/9*i), int(uly + (ury-uly)/9*i))
            bottom = (int(blx + (brx-blx)/9*i), int(bly + (bry-bly)/9*i))
            left   = (int(ulx + (blx-ulx)/9*i), int(uly + (bly-uly)/9*i))
            right  = (int(urx + (brx-urx)/9*i), int(ury + (bry-ury)/9*i))
            cv2.line(grid, top, bottom, color = (0,255,0), thickness =  thickness)
            cv2.line(grid, left, right, color = (0,255,0), thickness =  thickness)
        showStep(grid, "grid")

    # find digits and parse them
    grid = findDigits(gray, square)

    # output result
    y = 0
    for line in grid:
        print(''.join(line[0:3]) + '|' + ''.join(line[3:6]) + '|' + ''.join(line[6:9]))
        if y == 2 or y == 5:
            print('--- --- ---')
        y += 1
    # showStep(gridImg, "grid", force = True)

    return grid

if __name__ == "__main__":
    main(sys.argv[1:])

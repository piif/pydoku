#!/usr/bin/env python

import numpy as np
import cv2, sys, getopt

threshold = None
showSteps = False

def parseArgs(specs):
    global showSteps
    opts, args = getopt.getopt(sys.argv[1:], 's' + specs)

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

cv2.namedWindow("output", cv2.WINDOW_NORMAL) 
cv2.resizeWindow("output", 800, 800)

def showStep(image, title, force = False, wait = True):
    global showSteps, outputWindowCreated, imgW, imgH
    if not force and not showSteps:
        return

    cv2.imshow("output", image)
    cv2.setWindowTitle("output", title)
    if wait:
        key = cv2.waitKey()
        if key == ord('q') or key == ord('Q'):
            sys.exit(0)

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

    # convert to gray and blur
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    showStep(gray, "gray")

    blur = cv2.GaussianBlur(gray, (5,5), 0) 
    showStep(blur, "blur")

    # sobelx  = cv2.Sobel(src=blur, ddepth=cv2.CV_64F, dx=1, dy=0, ksize=15) # Sobel Edge Detection on the X axis
    # sobely  = cv2.Sobel(src=blur, ddepth=cv2.CV_64F, dx=0, dy=1, ksize=15) # Sobel Edge Detection on the Y axis
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
            canny = cv2.Canny(image=blur, threshold1=threshold1, threshold2=threshold2) # Canny Edge Detection
            showStep(canny, 'Canny', force = True, wait = False)

            key = cv2.waitKey()
            print(key)
            if key == 13:
                break
            elif key == ord('q') or key == ord('Q'):
                sys.exit(0)
            elif key == 82:
                threshold1 += 5
            elif key == 84:
                threshold1 -= 5
            elif key == 83:
                threshold2 += 5
            elif key == 81:
                threshold2 -= 5
    else:
        canny = cv2.Canny(image=blur, threshold1=threshold1, threshold2=threshold2) # Canny Edge Detection
        showStep(canny, 'Canny')

    # detect outer contours
    contours, hierarchy = cv2.findContours(canny, method = cv2.CHAIN_APPROX_SIMPLE, mode = cv2.RETR_EXTERNAL)
    print('found', len(contours), 'contours')
    if showSteps:
        cnt=0
        print(f'select contour with up/down keys between 0 and {len(contours)-1}, hit enter when ok')
        while True:
            contour = img.copy()
            cv2.drawContours(contour, contours, cnt, (0,255,0), 1)
            showStep(contour, f'contours {cnt}', force=True, wait=False)
            key = cv2.waitKey()
            if key == 13:
                break
            elif key == ord('q') or key == ord('Q'):
                sys.exit(0)
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
            print(f'found polygon {poly}')
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

def main():
    opts, args = parseArgs('1:2:')
    print(opts, args)
    threshold1 = int(opts['1']) if '1' in opts else None
    threshold2 = int(opts['2']) if '2' in opts else None

    # 1. Loading the Image
    img = cv2.imread(args[0])
    imgW, imgH = img.shape[0:2]
    print(f'Image size : {imgW}x{imgH}')
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

    (ulx, uly), (urx, ury), (brx, bry), (blx, bly) = detectSquare(resize, threshold1, threshold2)

    grid = resize.copy()
    for i in range(0,10):
        thickness = 2 if i%3 == 0 else 1
        top    = (int(ulx + (urx-ulx)/9*i), int(uly + (ury-uly)/9*i))
        bottom = (int(blx + (brx-blx)/9*i), int(bly + (bry-bly)/9*i))
        left   = (int(ulx + (blx-ulx)/9*i), int(uly + (bly-uly)/9*i))
        right  = (int(urx + (brx-urx)/9*i), int(ury + (bry-ury)/9*i))
        cv2.line(grid, top, bottom, color = (0,255,0), thickness =  thickness)
        cv2.line(grid, left, right, color = (0,255,0), thickness =  thickness)

    showStep(grid, "grid", force = True)

main()

#!/usr/bin/env python

import numpy as np
import cv2, sys, getopt

threshold = None
showSteps = False

opts, args = getopt.getopt(sys.argv[1:], "st:")
for o,v in opts:
    if o == '-t':
        threshold = int(v)
    elif o == '-s':
        showSteps = True
inFile = args[0]

outputWindowCreated = False
imgW, imgH = None, None
def showStep(image, title, force = False, wait = True):
    global outputWindowCreated, imgW, imgH
    if not force and not showSteps:
        return

    if not outputWindowCreated:
        cv2.namedWindow("output", cv2.WINDOW_NORMAL) 
        winSize = 800
        if imgW > imgH:
            ratio = imgW/imgH
            cv2.resizeWindow("output", winSize, int(winSize/ratio))
        else:
            ratio = imgH/imgW
            cv2.resizeWindow("output", int(winSize/ratio), winSize)
        outputWindowCreated = True

    cv2.imshow("output", image)
    cv2.setWindowTitle("output", title)
    if wait:
        cv2.waitKey()


# 1. Loading the Image
img = cv2.imread(inFile)
imgW, imgH = img.shape[0:2]
print(f'Image size : {imgW}x{imgH}')

showStep(img, "raw image")

# 2. Grayscale converstion
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
showStep(gray, "gray")

# 3. Thresholding
if threshold is None:
    threshold = 127
    print(f'adjust gray threshold with up/down keys, hit enter when ok')
    while True:
        print(f'gray threshold = {threshold}')
        ret, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV) 
        bw = cv2.bitwise_not(thresh)
        showStep(bw, "b&w", force = True, wait = False)
        key = cv2.waitKey()
        if key == 13:
            break
        elif key == 82:
            threshold += 1
        elif key == 84:
            threshold -= 1
else:
    ret, thresh = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY_INV) 
    bw = cv2.bitwise_not(thresh)
    showStep(bw, "b&w")

lines = cv2.HoughLinesP(gray, 1, np.pi/180, 100)
print(len(lines))

# # 4. Finding Countours
# contours, hierarchy = cv2.findContours(bw, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
# print('found', len(contours), 'contours')
# cnt=0
# print(f'select contour with up/down keys between 0 and {len(contours)-1}, hit enter when ok')
# while True:
#     contour = img.copy()
#     cv2.drawContours(contour, contours, cnt, (0,255,0), 10)
#     showStep(contour, f'contours {cnt}', force=True, wait=False)
#     key = cv2.waitKey()
#     if key == 13:
#         break
#     elif key == 82 and cnt < len(contours)-1:
#         cnt += 1
#     elif key == 84 and cnt > 0:
#         cnt -= 1

# print(contours[0], contours[1], contours[-1])
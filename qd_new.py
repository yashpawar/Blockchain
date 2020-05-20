import cv2
from keras.models import load_model
import numpy as np
from collections import deque
import os

# hsv values corresponding to green
hsv_color = cv2.cvtColor(np.uint8([[[255, 0, 0]]]), cv2.COLOR_BGR2HSV)
Lower_color=np.array([hsv_color[0][0][0]-10,50,50])
Upper_color=np.array([hsv_color[0][0][0]+10,255,255])

def clear():
    global pts
    global blackboard
    # Double ended queue that supports maximum length of queue 
    pts = deque(maxlen=250)
    blackboard = np.zeros((480, 640, 3), dtype=np.uint8)
clear()

def drawpts(img):
    global blackboard
    for i in range(1, len(pts)):
        # if there are less than 2 points dont draw the circle
        #if pts[i - 1] is None or pts[i] is None:
        #    continue
        # draw a white line between two points on blackboard
        cv2.circle(blackboard, pts[i],10 ,(255, 255, 255), -1)
        # Draw red line on image between two points
        cv2.circle(img, pts[i], 10,(0, 0, 255), -1)
    # kernel used as structuring element
    kernel = np.ones((5, 5), np.uint8)
    # closing
    blackboard = cv2.dilate(blackboard, kernel)
    blackboard = cv2.erode(blackboard, kernel)
    return img

model = load_model('test.h5')

def ip(img):
    global pts
    global blackboard
    # Convert image to hsv for tracking
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    # Threshold the HSV image to get only specific colors
    mask = cv2.inRange(hsv, Lower_color, Upper_color)
    # kernel used as structuring element
    kernel = np.ones((5, 5), np.uint8)
    # erode the mask by kernel (Thin It) and then dilate it
    mask = cv2.erode(mask, kernel,iterations=2)
    mask = cv2.dilate(mask, kernel,iterations=2)
    # Bitwise-AND mask and original image
    res = cv2.bitwise_and(img, img, mask=mask)
    # Find contours of mask
    cnts= cv2.findContours(mask.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    center = None

    if (len(cnts) > 0) and (len(pts)< 200):
        cnt = max(cnts, key=cv2.contourArea)
        if cv2.contourArea(cnt) > 625 :
            #cv2.drawContours(img,cnt,-1,(0,255,0),1)
            # Finds a circle of the minimum area enclosing a 2D point set.
            ((x, y), radius) = cv2.minEnclosingCircle(cnt)
            # Draw Circle around contour
            cv2.circle(img, (int(x), int(y)), int(radius), (0, 255, 255), 2)
            # draw the dots which notes points traced by target
            # cv2.circle(img, center, 5, (0, 0, 255), -1)
            # Calculating Moments of contour 
            M = cv2.moments(cnt)
            # centre of contour
            center = (int(M['m10'] / M['m00']), int(M['m01'] / M['m00']))
            # this point is path taken by target and we append it to left of double sided queue
            pts.appendleft(center)
            # Draw lines connecting consecutive points where object was observed
    img=drawpts(img)
    return img

def cv():
    global blackboard           
    # take graysacle image of blackboard(white line joining points)
    blackboard_gray = cv2.cvtColor(blackboard, cv2.COLOR_BGR2GRAY)
    # Every non-zero pixel is made white
    thresh1 = cv2.threshold(blackboard_gray, 0, 255, cv2.THRESH_BINARY)[1]
           
    # find contour to image on blackboard
    blackboard_cnts = cv2.findContours(thresh1.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)[0]
    # if there exists a contour
    if len(blackboard_cnts) > 0:
        # Get the contour with maximum area
        cnt = max(blackboard_cnts, key=cv2.contourArea)
        #print(cv2.contourArea(cnt))
        # if contour is big enough in area
        if cv2.contourArea(cnt) > 2000:
            # Draw bounding box to contour to extract the image from blackboard
            x, y, w, h = cv2.boundingRect(cnt)
            # get the image from blackboard
            digit = blackboard_gray[y:y + h, x:x + w]
            # recognise the image using trained model
            digit,pred_probab, pred_class = keras_predict(model, digit)
            if pred_probab>0.9999:
                # print(pred_class, pred_probab)
                # img = overlay(img, emojis[pred_class], 400, 250, 100, 100)
                return digit,pred_class
                #cv2.putText(img, str(pred_class), (100,50) , cv2.FONT_HERSHEY_SIMPLEX ,2, (0,255,0), 2)
    return -1,-1    
     
        

def keras_predict(model, image):
    a,processed = keras_process_image(image)
    pred_probab = model.predict(processed)[0]
    pred_class = list(pred_probab).index(max(pred_probab))
    return a,max(pred_probab), pred_class


def keras_process_image(img):
    image_x = 28
    image_y = 28
    img = cv2.resize(img, (image_x, image_y))
    a=img
    img = np.array(img, dtype=np.float32)
    img = np.reshape(img, (-1, image_x, image_y, 1))
    return a,img



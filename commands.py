from VideoCapture import Record
import cv2
import numpy as np
import math


def dist(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def get_angle(x1, y1, x2, y2):
    if x1 == x2:
        return 90
    if y1 > y2:
        return math.degrees(math.atan((y1 - y2)/ (x1 - x2)))
    else:
        return math.degrees(math.atan((y2 - y1)/ (x2 - x1)))
    

def swipe_scroll(record, coords):
    last_finger_info = record.get_last_frame_finger_info()
    if len(last_finger_info) == 1 and len(coords) == 1:
        x1, y1 = last_finger_info[0][1]
        x2, y2 = coords[0]
        if abs(x2 - x1) > abs(y2 - y1):
            if x2 > x1:
                return 'right'
            else:
                return 'left'
        else:
            if y2 > y1:
                return 'up'
            else:
                return 'down'
                
    else:
        return 'non'
    
def commands(record, coords):
    last_finger_info = record.get_last_frame_finger_info()
    
    #track previous 10 frames more than 4 frames = long otherwise track if tap or double tap
    
    if len(last_finger_info) == 1 and len(coords) == 1:
        streak1 = 0
        streak2 = 0
        flag = False
        for i in range(10):
            a = np.nonzero(record.records[-1 - i][:][:])
            if len(a) == 1 and not flag:
                streak1 += 1
            elif  len(a) == 1 and flag:
                streak2 += 1
            elif len(a) == 0:
                flag = True
            else:
                return 'non', 0, 0
        if streak1 > 4:
            return 'long', 0, 0
        elif streak1 > 0 and streak2 > 0:
            return 'double', 0, 0
        elif streak1 > 0:
            return 'tap', 0, 0
        else:
            return 'non', 0, 0
    
    #rotate + zoom
    elif len(last_finger_info) == 2  and len(coords) == 2:
        x1, y1 = last_finger_info[0][1]
        x2, y2 = last_finger_info[1][1]
        #scale of image resizing
        scale  = 1
        #rotation angle in degrees
        angle = 0
        
        #get scale
        dist_curr = dist(coords[0][0], coords[0][1], coords[1][0], coords[1][1])
        dist_prev = dist(x1, y1, x2, y2)
        
        scale = dist / dist_prev
        
        #get angle
        angle_curr = get_angle(coords[0][0], coords[0][1], coords[1][0], coords[1][1])
        angle_prev = get_angle(x1, y1, x2, y2)
        
        angle = angle_curr - angle_prev
        
        return 'rot+zoom', angle, scale
    else:
        return 'non', 0, 0
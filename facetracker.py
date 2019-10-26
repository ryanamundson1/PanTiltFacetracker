#!/usr/bin/env python

import cv2, sys, time, os
from datetime import datetime, timedelta
from pantilthat import *


# Frame Size. Smaller is faster, but less accurate.
# Wide and short is better, since moving your head
# vertically is kinda hard!
FRAME_W = 320
FRAME_H = 200

# Default Pan/Tilt for the camera in degrees.
# Camera range is from -90 to 90
cam_pan = 90
cam_tilt = 90

current_pan = 0
current_tilt = 0

# Load the BCM V4l2 driver for /dev/video0
os.system('sudo modprobe bcm2835-v4l2')
# Set the framerate ( not sure this does anything! )
os.system('v4l2-ctl -p 8')

# Set up the CascadeClassifier for face tracking
cascPath = '/usr/share/opencv/haarcascades/haarcascade_frontalface_default.xml' # sys.argv[1]
#cascPath = '/usr/share/opencv/haarcascades/haarcascade_eye.xml' 
#cascPath = '/usr/share/opencv/lbpcascades/lbpcascade_frontalface.xml'
faceCascade = cv2.CascadeClassifier(cascPath)

# Set up the capture with our frame size
video_capture = cv2.VideoCapture(0)
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH,  FRAME_W)
video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_H)
time.sleep(2)

# Turn the camera to the default position
pan(current_pan)
tilt(current_tilt)
#light_mode(WS2812)

def lights(r,g,b,w):
    for x in range(18):
        set_pixel_rgbw(x,r if x in [3,4] else 0,g if x in [3,4] else 0,b,w if x in [0,1,6,7] else 0)
    show()

#lights(0,0,0,50)

while True:
    # Capture frame-by-frame
    ret, frame = video_capture.read()
    # This line lets you mount the camera the "right" way up, with neopixels above
    frame = cv2.flip(frame, -1)
    
    if ret == False:
      print("Error getting image")
      continue

    # Convert to greyscale for detection
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist( gray )

    # Do face detection
    #faces = faceCascade.detectMultiScale(frame, 1.1, 3, 0, (5, 5))
   
    # Slower method 
    faces = list(faceCascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=5,
            minSize=(20,20)
            #flags = cv2.CASCADE_SCALE_IMAGE
        ))
    
    #lights(50 if len(faces) == 0 else 0, 50 if len(faces) > 0 else 0,0,50)

    face = None
    
    faceFound = True
    faceTime = None
    
    if faces:
        face = faces[0]
        
        faceFound = True
        
        faceTime = datetime.now() #- timedelta(days=N)
    
        x, y, w, h = face
        
        # Draw a green rectangle around the face
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Track first face
        
        # Get the center of the face
        x = x + (w/2)
        y = y + (h/2)

        # Correct relative to center of image
        turn_x  = float(x - (FRAME_W/2))
        turn_y  = float(y - (FRAME_H/2))

        # Convert to percentage offset
        turn_x  /= float(FRAME_W/2)
        turn_y  /= float(FRAME_H/2)

        # Scale offset to degrees
        turn_x   *= 2.5 # VFOV
        turn_y   *= 2.5 # HFOV
        
        #print (turn_x, turn_y)
        #cam_pan  += -turn_x
        #cam_tilt += turn_y
        
        #Cam seemed to be turning away, switch this
        current_pan += turn_x
        current_pan += turn_y

        #print(cam_pan-90, cam_tilt-90)

        # Clamp Pan/Tilt to 0 to 180 degrees
        current_pan = max(-90,min(90, current_pan))
        current_pan = max(-90,min(90, current_pan))
        
        print(current_pan, current_pan)

        # Update the servos
        pan(int(current_pan))
        tilt(int(current_pan))
    
    else:
        faceFound = False
        currenttime = datetime.now()
        
        if faceTime:
            
            endtime = faceTime + timedelta(seconds=5)

            if currenttime > endtime:
                # if we havent found faces for 5 seconds, reset the pan
                current_pan = 0
                current_tilt = 0
                pan(current_pan)
                tilt(current_tilt)

    frame = cv2.resize(frame, (540,300))
    frame = cv2.flip(frame, 1)
   
    # Display the image, with rectangle
    # on the Pi desktop 
    cv2.imshow('Video', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# When everything is done, release the capture
video_capture.release()
cv2.destroyAllWindows()

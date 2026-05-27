import os
import time
import cv2
import numpy as np
import pyglet
from pyglet import shapes
from PIL import Image
import sys
import cv2.aruco as aruco
import random
from enum import IntEnum

#Notes:
# - contour detection depends on the lighting, i found it works best when no shadow gets cast
# - it even worked great in a almost completly dark room
# - left contours in the frame to show how well detection works
# - I hope this contour-detection works for you as well as it does for me, in my room it was quite perfect
# - the main problem was, that my finger and its shadow have the almost exact same color in grey-scale so its increasingly difficult to filter out. If lighting is adjusted to not show shadows it works quite good
# - i really tried alot, normalizing background, LAB-colorspace, cv2.THRESH_OTSU, diffrent masks, bitwise operations, ..., ... and many combinations of those, but shadows stayed strong

class HitDirection(IntEnum):
    LEFT = 0
    RIGHT = 1
    BOTTOM = 2
    RIGHT_BOTTOM = 3
    LEFT_BOTTOM = 4

class Ballon():
    def __init__(self, x, y, batch, winwidth, winheight):
        scale_x = winwidth / 1920
        scale_y = winheight / 1080

        self.radius = random.randint(50, 100)* min(scale_x, scale_y)
        self.color = (random.randint(0, 200), random.randint(0, 200), random.randint(0, 200))
        self.x = x * scale_x
        self.y = y *scale_y
        self.speed_x = random.uniform(-10, 10)* scale_x
        self.speed_y = random.uniform(13, 20) * scale_y
        self.shape = shapes.Circle(x, y, self.radius, color=self.color, batch=batch)
        self.out_of_bounds = False
        self.gravity = random.uniform(0.18, 0.28)* scale_y

    def update_position(self):
        if self.out_of_bounds:
            return

        self.x += self.speed_x
        self.y += self.speed_y
        self.shape.y += self.speed_y
        self.shape.x += self.speed_x
        if self.shape.y + self.radius <= 0:
            self.out_of_bounds = True
            self.destroy()
    
    def update_position_x(self):
        if self.out_of_bounds:
            return
        self.x += self.speed_x
        self.shape.x += self.speed_x
    
    def destroy(self):
        self.shape.delete()


BALLON_HIT_SPEED = 10

video_id = 0
# Define the ArUco dictionary, parameters, and detector
aruco_dict = aruco.getPredefinedDictionary(aruco.DICT_6X6_250)
aruco_params = aruco.DetectorParameters()
detector = aruco.ArucoDetector(aruco_dict, aruco_params)
# Create a video capture object for the webcam
cap = cv2.VideoCapture(video_id)#

#My 1080p webcam somehow got set to 640x480 in opencv, so i set it back to 1080p, i sadly havent got a worse webcam to test if this causes problems 
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)

webcam_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
webcam_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
print(f"Webcam resolution: {webcam_width}x{webcam_height}")
window = pyglet.window.Window(webcam_width, min(980, webcam_height)) #for some reason 1080p height cut of the bottom of the window on a 1080p screen

if len(sys.argv) > 1:
    video_id = int(sys.argv[1])

class Game():
    def __init__(self):
        self.ballon_batch = pyglet.graphics.Batch()
        self.ballons = self.initBallons()
        self.image_Found = False

        self.time_counter = 0
        self.hardMode = True
        self.game_over = True
        self.show_Contours = False
        self.time_counter_label = pyglet.text.Label(
            "Mode: Hard | Time: 0.00s", 
            x=0, 
            y=10,
            width=window.width,
            height=window.height,
            align="center",
            font_size=36, 
            color=(0, 0, 0)
            )
        self.game_over_label = pyglet.text.Label(
            "Press 'S' to Start\nPress 'M' to select difficulty!\n Press 'C' to show contours",
            x=window.width//2,
            y=window.height//2,
            width=window.width,
            height=window.height,
            anchor_x='center',
            anchor_y='center',
            align='center',
            color=(0, 0, 0),
            font_size=36,
            multiline=True
        )    

        
        window.event(self.on_draw)
        window.event(self.on_key_press)
        window.event(self.on_close)

        time.sleep(1)
        pyglet.clock.schedule_interval(self.update, 1/60)


    def initBallons(self) -> list[Ballon]:
        ballons = []
        for i in range(4):
            ballon = Ballon(x=300 + i*200, y=120 + i*20, batch=self.ballon_batch, winwidth=window.width, winheight=window.height)
            ballons.append(ballon)
        return ballons


    # converts OpenCV image to PIL image and then to pyglet texture
    # https://gist.github.com/nkymut/1cb40ea6ae4de0cf9ded7332f1ca0d55
    def cv2glet(self, img, fmt):
        '''Assumes image is in BGR color space. Returns a pyimg object'''
        if fmt == 'GRAY':
            rows, cols = img.shape
            channels = 1
        else:
            rows, cols, channels = img.shape

        raw_img = Image.fromarray(img).tobytes()

        top_to_bottom_flag = -1
        bytes_per_row = channels*cols
        pyimg = pyglet.image.ImageData(
            width=cols,
            height=rows,
            fmt=fmt,
            data=raw_img,
            pitch=top_to_bottom_flag*bytes_per_row
        )
        return pyimg

    def get_Transformed_Image(self, frame):
        points = np.zeros((4, 2), dtype=int)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        corners, ids, rejectedImgPoints = detector.detectMarkers(gray)

        if ids is not None and len(ids) >= 4:
            aruco.drawDetectedMarkers(frame, corners)

            for i in range(len(ids)):
                c = corners[i][0]
                #decided to use center of pointers for the playing field, but causes the corners to be detected as contours
                #else could just use the inner corners of the markers, but i liked it visually better since it kinda "frames" the playing field
                center_x = int(np.mean(c[:,0]))
                center_y = int(np.mean(c[:,1]))

                point = (center_x, center_y)
                points[ids[i][0]] = point #I hope all the ids were glued on in the right order, it works great for me at least

            if(len(points) == 4):
                return self.transform(points, frame)
        else:
            return None


    #Code from notebook example
    def transform(self, sorted_points, frame) -> np.ndarray:
        np_points = np.float32(np.array(sorted_points))
        destination = np.float32(np.array([[0, 0], [webcam_width, 0], [webcam_width, webcam_height], [0, webcam_height]]))
        # get matrix for perspective transformation
        mat = cv2.getPerspectiveTransform(np_points, destination)
        # to transform whole images, use:
        return cv2.warpPerspective(frame, mat, (webcam_width, webcam_height), flags=cv2.INTER_LINEAR)

    def get_Game_Object_Contours(self, trans_frame):
        #The top if-statement was the first approach and it did already work really well, but is heavily reliant on the lighting
        #So after alot of testing with different approaches, i asked ChatGPT and it suggested to use HSV color space and filter for skin which works great in direct/white lighting, but not at all in dim lighting
        #So I decided to combine both so low light uses grayscale and thresholding while bright lighting uses HSV and color filtering
        # I tried with ALOT of diffrenz lighting and most were really well, the biggest problem was the shadow of the finger getting picked up as contour
        blur = cv2.GaussianBlur(trans_frame, (5,5), 0)
        img_gray = cv2.cvtColor(blur, cv2.COLOR_BGR2GRAY)
        
        #found the culprit here, shadow and my finger practicaly have the exact same color
        #cv2.imshow("TESTWINDOW", img_gray)
        
        mean = np.mean(img_gray)
        threshold = mean - 40
        
        if mean < 205: #210 was the mean when i put a (white) light above the playing field
            #thresh = cv2.adaptiveThreshold(img_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, blockSize=69, C=15) #is much better for shadows, but doesn't get the whole finger and has a big delay, but outline and tip get detected quite well (but too slow)
            ret, thresh = cv2.threshold(img_gray, threshold, 255, cv2.THRESH_BINARY_INV) #inverse since without the border of the window gets picked up as contour, i also tried with + cv2.THRESH_OTSU and the results werent as good
            kernel = np.ones((5, 5), np.uint8)
            cleaned = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=2)
            cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_CLOSE, kernel, iterations=2)
            contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            return contours
        else:
            #This part was suggested by ChatGPT (works best in bright white light)
            hsv = cv2.cvtColor(trans_frame, cv2.COLOR_BGR2HSV)
            lower = np.array([0, 20, 60])
            upper = np.array([25, 255, 255])
            mask = cv2.inRange(hsv, lower, upper)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            return contours

    def ballon_hit_contour(self, contours, ballon, trans_frame):
        y = self.get_Circle_Y(ballon, trans_frame)

        #left/right bottom isnt exactly the border, but just an estimation
        left_bottom = (ballon.x - ballon.radius*0.5, y + ballon.radius * 0.5)
        bottom_middle = (ballon.x, y+ballon.radius)
        right_bottom = (ballon.x + ballon.radius * 0.5, y + ballon.radius * 0.5)

        left = (ballon.x - ballon.radius, y)
        right = (ballon.x + ballon.radius, y)

        for c in contours:
            if cv2.pointPolygonTest(c, bottom_middle, False) >= 0:#bottom middle
                print("Hit bottom middle!")
                return HitDirection.BOTTOM   
            if cv2.pointPolygonTest(c, left_bottom, False) >= 0: #left bottom
                print("Hit left bottom!")
                return HitDirection.LEFT_BOTTOM  
            if cv2.pointPolygonTest(c, right_bottom, False) >= 0: #right bottom
                print("Hit right bottom!")
                return HitDirection.RIGHT_BOTTOM
            if cv2.pointPolygonTest(c, left, False) >= 0:#left
                print("Hit left!")
                return HitDirection.LEFT
            if cv2.pointPolygonTest(c, right, False) >= 0:#right
                print("Hit right!")
                return HitDirection.RIGHT
        return None

    def move_Ballons(self):
        for ballon in self.ballons:
            ballon.speed_y -= ballon.gravity
            ballon.update_position()
            if ballon.y + ballon.radius >= window.height:
                ballon.speed_y = -2
            if ballon.x - ballon.radius <= 0:
                ballon.speed_x = abs(ballon.speed_x)
            if ballon.x + ballon.radius >= window.width:
                ballon.speed_x = -abs(ballon.speed_x)
        for ballon in self.ballons:
            for other in self.ballons:
                if ballon != other and ((ballon.x - other.x) ** 2 + (ballon.y - other.y) ** 2) < (ballon.radius + other.radius) ** 2:
                    if ballon.x < other.x:
                        ballon.speed_x = -abs(ballon.speed_x)
                        other.speed_x = abs(other.speed_x)
                    else:
                        ballon.speed_x = abs(ballon.speed_x)
                        other.speed_x = -abs(other.speed_x)

                    ballon.update_position_x()
                    other.update_position_x()

        if self.hardMode:
            for ballon in self.ballons:
                if ballon.out_of_bounds:
                    self.game_over = True
                    self.game_over_label.text = f"Game Over!\nYou survived {self.time_counter:.2f}s!\nPress 'S' to restart!"
                    print("Game Over!")
        else:
            out_COunter = 0
            for ballon in self.ballons:
                if ballon.out_of_bounds:
                    out_COunter += 1

            if out_COunter >= len(self.ballons) and not self.game_over: 
                self.game_over = True
                self.game_over_label.text = f"Game Over!\nYou survived {self.time_counter:.2f}s!\nPress 'S' to restart!"
                print("Game Over!")

    def get_Circle_Y(self, ballon, trans_frame):
        return trans_frame.shape[0] - ballon.y

    def on_draw(self):
        window.clear()
        ret, frame = cap.read()
        if not ret or frame is None:
            self.image_Found = False
            return
        trans_frame = self.get_Transformed_Image(frame)

        if trans_frame is not None:
            self.image_Found = True
            contours = self.get_Game_Object_Contours(trans_frame)
            if self.show_Contours:
                trans_frame = cv2.drawContours(trans_frame, contours, -1, (200, 50, 50), 3) #couldn't decide if contours should be drawn..


            for ballon in self.ballons:
                hit = self.ballon_hit_contour(contours, ballon, trans_frame)
                if not ballon.out_of_bounds and hit is not None:
                    ballon.speed_y = BALLON_HIT_SPEED
                    if hit == HitDirection.LEFT or hit == HitDirection.LEFT_BOTTOM:
                        ballon.speed_x = 7
                    elif hit == HitDirection.RIGHT or hit == HitDirection.RIGHT_BOTTOM:
                        ballon.speed_x = -7
            img = self.cv2glet(trans_frame, 'BGR')
            img.blit(0, 0, 0)
        else:
            self.image_Found = False
            img = self.cv2glet(frame, 'BGR')
            img.blit(0, 0, 0)

        self.ballon_batch.draw()
        self.time_counter_label.draw()
        self.game_over_label.draw()


    def on_key_press(self, symbol, modifiers):
        if symbol == pyglet.window.key.S: #decided to allow restart while game is still running
            self.game_over_label.text = ""
            self.game_over = False
            self.ballons = self.initBallons()
            self.time_counter = 0
        if symbol == pyglet.window.key.M and self.game_over:
            self.hardMode = not self.hardMode
            mode_string = "Hard" if self.hardMode else "Easy"
            self.time_counter_label.text = f"Mode: {mode_string} | Time: {self.time_counter:.2f}s"
        if symbol == pyglet.window.key.C:
            self.show_Contours = not self.show_Contours
        if symbol == pyglet.window.key.Q:
            pyglet.app.exit()
            os._exit(0)
    
    def on_close(self):
        pyglet.app.exit()
        os._exit(0)

    def update(self, dt):
        if self.image_Found and not self.game_over:
            self.time_counter += dt
            mode_string = "Hard" if self.hardMode else "Easy"
            self.time_counter_label.text = f"Mode: {mode_string} | Time: {self.time_counter:.2f}s"
            self.move_Ballons()


game = Game()
pyglet.app.run()
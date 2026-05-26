import argparse
import os
import cv2
import numpy as np
from tkinter.filedialog import askopenfilename, asksaveasfilename, askdirectory
import math

#Notes:
# - didn't know if commandline parameters are required to be non-optional, but for ease of testing made them optional and added file-dialogs and a logical resolution for the transformed image

WINDOW_NAME = "Preview Window"
TRANFORMED_WINDOW_NAME = "Transformed Image"

class ImageTransformer:
    def __init__(self):
        parser = argparse.ArgumentParser()

        parser.add_argument("--input_path", type=str, default=None)
        parser.add_argument("--output_path", type=str, default=None)

        parser.add_argument("--width", type=int, default=None)
        parser.add_argument("--height", type=int, default=None)

        args = parser.parse_args()

        self.input_path = args.input_path
        if self.input_path is None or not os.path.exists(self.input_path):
            print("Input path is not valid, select an image conveniently...")
            self.input_path = self.select_Image_Path_Convenient()
        self.output_path = args.output_path
        if self.output_path is None or not os.path.isdir(os.path.dirname(self.output_path)):
            print("Output path is not a valid directory, select a save path conveniently...")
            self.output_path = self.select_Save_Path_Convenient()
        self.save_width = args.width
        self.save_height = args.height

        self.img = cv2.imread(self.input_path)
        self.img_copy = self.img.copy()
        self.trans_img = None
        self.points = []

        cv2.namedWindow(WINDOW_NAME, cv2.WINDOW_NORMAL)

        #if image is bigger than half of 1080p(most common screen size) resize it to fit
        self.resizing_factor = 1
        while self.img.shape[0]*self.resizing_factor > 1080/2 or self.img.shape[1]*self.resizing_factor > 1920/2:
            self.resizing_factor -= 0.05

       
        cv2.resizeWindow(WINDOW_NAME, (int(self.img.shape[1] * self.resizing_factor), int(self.img.shape[0] * self.resizing_factor)))
        cv2.moveWindow(WINDOW_NAME, 10, 100)
        cv2.imshow(WINDOW_NAME, self.img)

        cv2.setMouseCallback(WINDOW_NAME, self.mouse_callback)


    def select_Image_Path_Convenient(self):
        file_path = askopenfilename(title="Select an Image", filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")])
        if file_path:
            return file_path
        else:
            print("No file selected, exiting")
            os._exit(1)
    
    def select_Save_Path_Convenient(self):
        save_path = asksaveasfilename(title="Select Path and Name to save", filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")], defaultextension=".jpg")
        if save_path:
            return save_path
        else:
            print("No file selected, exiting")
            os._exit(1)

    def sort_Points(self, points):
        sorted_points = []

        #sort by x so index 0,1 is left and 2,3 is right
        points = sorted(points)

        #took some time to figure out in open-cv the y axis goes top to bottom and from top left corner clockwise for transformation...
        sorted_points.append(points[0] if points[0][1] < points[1][1] else points[1]) #top left
        sorted_points.append(points[2] if points[2][1] < points[3][1] else points[3]) #top right
        sorted_points.append(points[2] if points[2][1] > points[3][1] else points[3]) #bottom right
        sorted_points.append(points[0] if points[0][1] > points[1][1] else points[1]) #bottom left

        return sorted_points

    def draw_points(self):
        img_copy = self.img.copy()

        for x, y in self.points:
            cv2.circle(img_copy, (x, y), 7, (255, 0, 0), -1)
        cv2.imshow(WINDOW_NAME, img_copy)

        if(len(self.points) == 4):
            sorted_points = self.sort_Points(self.points)
            self.transform(sorted_points)

    #includes Code from notebook example
    def transform(self, sorted_points):
        np_points = np.float32(np.array(sorted_points))
        destination = np.float32(np.array([[0, 0], [self.img.shape[1], 0], [self.img.shape[1], self.img.shape[0]], [0, self.img.shape[0]]]))

        # get matrix for perspective transformation
        mat = cv2.getPerspectiveTransform(np_points, destination)

        # to transform whole images, use:
        self.trans_img = cv2.warpPerspective(self.img, mat, (self.img.shape[1], self.img.shape[0]), flags=cv2.INTER_LINEAR)

        cv2.namedWindow(TRANFORMED_WINDOW_NAME, cv2.WINDOW_NORMAL)
        cv2.moveWindow(TRANFORMED_WINDOW_NAME, int(self.img.shape[1]*self.resizing_factor) + 50, 100)

        if self.save_width is None:
            self.save_width = int(math.dist(sorted_points[0], sorted_points[1])) #leftTop -> rightTop
            #self.save_width = self.img.shape[1]
        if self.save_height is None:
            self.save_height = int(math.dist(sorted_points[0], sorted_points[3])) #leftTop -> leftBottom
            #self.save_height = self.img.shape[0]

        #same as main image, since i additionally wanted to display them side by side, so width should be smaller than half of 1080. Image still gets saved in right dimension, only displaywindow size changes
        preview_resize_factor = 1
        while self.save_width*preview_resize_factor > 1920/2 or self.save_height*preview_resize_factor > 1080/2:
            preview_resize_factor -= 0.05
       
        cv2.resizeWindow(TRANFORMED_WINDOW_NAME, (int(self.save_width*preview_resize_factor), int(self.save_height*preview_resize_factor)))
        
        self.trans_img = cv2.resize(self.trans_img, (self.save_width, self.save_height), interpolation=cv2.INTER_AREA)
        cv2.imshow(TRANFORMED_WINDOW_NAME, self.trans_img)

    def mouse_callback(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.points.append((x, y))

            if len(self.points) > 4:
                self.points.pop(0)

            self.draw_points()

    def check_Path(self, path):
        existing_files = os.listdir(path)
        nameCounter = 1
        while f"transformed_image_{nameCounter}.jpg" in existing_files:
            nameCounter += 1
        return f"{path}/transformed_image_{nameCounter}.jpg"

    def handle_save(self, img_to_save):
        if os.path.isdir(self.output_path):
            path = self.check_Path(self.output_path)
        else:
            path = self.output_path

        try:
            cv2.imwrite(path,img_to_save)
            print("Saved to", self.output_path)
        except:
            print("Failed to save, select save location manually")
            self.output_path = self.select_Save_Path_Convenient()
            self.handle_save(img_to_save)
       

    def run(self):
        while True:
            key = cv2.waitKey(1) & 0xFF

            if key == 27: #27 is escape
                #destoryWindow throws error if window isnt open
                try:
                    cv2.destroyWindow(TRANFORMED_WINDOW_NAME)
                except:
                    pass
                self.trans_img = None
                self.points.clear()
                self.draw_points()

            if key == ord("s"):         
                if self.trans_img is not None:
                    print("Saving image")
                    img_to_save = self.trans_img.copy()
                    self.handle_save(img_to_save)
                else:
                    print("No transformed image to save")
            if key == ord("q") or cv2.getWindowProperty(WINDOW_NAME, cv2.WND_PROP_VISIBLE) < 1:
                os._exit(0)


transformer = ImageTransformer()
transformer.run()
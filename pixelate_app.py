import cv2
import numpy as np
import math
import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
from pathlib import Path

IMAGE_FORMATS = [".png", ".jpg", ".jpeg", ".bmp", ".ppm", ".pbm", ".pgm", ".tiff", ".tif"]

class ImageProcessingApp:

    MAX_IMG_DISP_SIZE = 720
    INPUT_COL = 0
    OUTPUT_COL = 2
    UI_COL = 1
    IMG_ROW = 0
    SIZE_ROW = 12

    def __init__(self, root):
        self.root = root
        self.root.title("Pixelator4200 by Chrispy")

        # Create labels to display images
        self.img_label = tk.Label(root)
        self.img_label.grid(row=self.IMG_ROW, column=self.INPUT_COL, padx=10, pady=10, rowspan=self.SIZE_ROW)
        self.img_size_label = tk.Label(root, text="")
        self.img_size_label.grid(row=self.SIZE_ROW, column=self.INPUT_COL, padx=10, pady=(0, 10))

        self.processed_label = tk.Label(root)
        self.processed_label.grid(row=self.IMG_ROW, column=self.OUTPUT_COL, padx=10, pady=10, rowspan=self.SIZE_ROW)
        self.processed_size_label = tk.Label(root, text="")
        self.processed_size_label.grid(row=self.SIZE_ROW, column=self.OUTPUT_COL, padx=10, pady=(0, 10))

        # Button to select an image file
        self.select_button = tk.Button(root, text="Select Image", command=self.select_image)
        self.select_button.grid(row=0, column=self.UI_COL, pady=10)

        # Button to process the image
        self.process_button = tk.Button(root, text="Process Image", command=self.process_image, state=tk.DISABLED)
        self.process_button.grid(row=1, column=self.UI_COL, pady=10)

        self.selected_file = None
        self.pixel_sizing = 16 # Initial value for pixel sizing

        # Slider to adjust pixel sizing
        self.pixel_slider = tk.Scale(root, from_=2, to=100, orient=tk.HORIZONTAL, length=200,
                                      command=self.update_pixel_size, state=tk.DISABLED, label="Adjust Pixel Size:")
        self.pixel_slider.grid(row=2, column=self.UI_COL, pady=(0, 0), padx=10)
        self.slider_hint = tk.Label(root)
        self.slider_hint.grid(row=3, column=self.UI_COL, pady=(0, 10))

        # Var to store the pixelation method
        self.by_pixel_size = tk.BooleanVar()
        self.by_pixel_size.set(True)  # Default method is by pixel size
        # Radio buttons to select pixelation method
        self.pixel_method_label = tk.Label(root, text="Pixelation Method:")
        self.pixel_method_label.grid(row=4, column=self.UI_COL, pady=(10, 0))
        self.pixel_method_radio1 = tk.Radiobutton(root, text="By Pixel Size", variable=self.by_pixel_size, value=True, command=self.update_slider_label)
        self.pixel_method_radio1.grid(row=5, column=self.UI_COL, pady=(0, 0))
        self.pixel_method_radio2 = tk.Radiobutton(root, text="To Size", variable=self.by_pixel_size, value=False, command=self.update_slider_label)
        self.pixel_method_radio2.grid(row=6, column=self.UI_COL, pady=(0, 10))

        # Var to store the pixelation reference dimension (width or height) when pixelating to a size
        self.pixel_ref_width = tk.BooleanVar(value=True)
        # Radio buttons to select pixelation reference dimension
        self.pixel_ref_label = tk.Label(root, text="Pixelation Reference Dimension:")
        self.pixel_ref_label.grid(row=7, column=self.UI_COL, pady=(10, 0))
        self.pixel_ref_radio1 = tk.Radiobutton(root, text="Width", variable=self.pixel_ref_width, value=True)
        self.pixel_ref_radio1.grid(row=8, column=self.UI_COL, pady=(0, 0))
        self.pixel_ref_radio2 = tk.Radiobutton(root, text="Height", variable=self.pixel_ref_width, value=False)
        self.pixel_ref_radio2.grid(row=9, column=self.UI_COL, pady=(0, 10))
        self.update_slider_label()

        # Button to process all images in a folder
        self.process_folder_button = tk.Button(root, text="Process all Images in Folder...", command=self.process_folder)
        self.process_folder_button.grid(row=10, column=self.UI_COL, pady=10)

        # Button to save the processed image (and the low-res image)
        self.save_button = tk.Button(root, text="Save Pixelated Image", command=self.save_image, state=tk.DISABLED)
        self.save_button.grid(row=self.SIZE_ROW, column=self.UI_COL, pady=10)


    def select_image(self):
        # Ask user to select an image file
        file_path = self.get_file()
        if file_path:
            self.selected_file = file_path
            self.process_button.config(state=tk.NORMAL)
            self.enable_pixel_slider()  # Enable the pixel size slider
            img = cv2.imread(str(self.selected_file))
            self.display_image(img, self.img_label, self.img_size_label)
            self.update_pixel_slider_range(img)  # Update slider range based on image dimensions

    def get_file(self) -> Path:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        file = Path(filedialog.askopenfilename(title="Select an image file"))
        root.destroy()  # Destroy the hidden window after selection
        return file

    def get_folder(self) -> Path:
        root = tk.Tk()
        root.withdraw()
        folder = Path(filedialog.askdirectory(title="Select a folder"))
        root.destroy()
        return folder

    def enable_pixel_slider(self):
        self.pixel_slider.config(state=tk.NORMAL)

    def update_pixel_slider_range(self, img):
        # Determine the maximum allowable pixel sizing based on image dimensions
        min_dimension = min(img.shape[:2])
        max_pixel_size = min_dimension // 10
        self.pixel_slider.config(to=max_pixel_size)
        self.pixel_sizing = min(self.pixel_sizing, max_pixel_size)  # Ensure current value is within new range
        self.pixel_slider.set(self.pixel_sizing)

    def update_slider_label(self):
        if self.by_pixel_size.get():
            self.slider_hint.config(text="How many pixels will merge together.\nBigger=More pixelated")
        else:
            self.slider_hint.config(text="The size of the new image in pixels.\nBigger=Less pixelated")
        self.show_hide_pixel_ref_dimension()

    def update_pixel_size(self, value):
        self.pixel_sizing = int(value)

    def show_hide_pixel_ref_dimension(self):
        if self.by_pixel_size.get():
            self.pixel_ref_label.grid_forget()
            self.pixel_ref_radio1.grid_forget()
            self.pixel_ref_radio2.grid_forget()
        else:
            self.pixel_ref_label.grid(row=7, column=self.UI_COL, pady=(10, 0))
            self.pixel_ref_radio1.grid(row=8, column=self.UI_COL, pady=(0, 0))
            self.pixel_ref_radio2.grid(row=9, column=self.UI_COL, pady=(0, 10))

    def process_image(self, display=True):
        if self.selected_file is None:
            return

        # Read the selected image
        img = cv2.imread(str(self.selected_file))

        # Perform image processing (e.g., pixelate_by_pixel_size the image)
        if self.by_pixel_size.get():
            self.processed_img, self.low_res_img = pixelate_by_pixel_size(img, self.pixel_sizing)
        else:
            self.processed_img, self.low_res_img = pixelate_to_size(img, self.pixel_sizing, self.pixel_ref_width.get(), not self.pixel_ref_width.get())

        if display:
            # Display the original image
            self.display_image(img, self.img_label, self.img_size_label)

            # Display the processed image
            self.display_image(self.processed_img, self.processed_label, self.processed_size_label)
            self.append_label(self.processed_size_label, f" (True size: {self.low_res_img.shape[1]}x{self.low_res_img.shape[0]})")

        # Enable the save button
        self.save_button.config(state=tk.NORMAL)

    def process_folder(self):
        # Ask user to select a folder containing images
        folder = self.get_folder()
        if folder:
            # Process each image in the folder
            for file_path in folder.glob("*"):
                if file_path.is_file() and file_path.suffix in IMAGE_FORMATS:
                    self.selected_file = file_path
                    self.process_image(display=False)
                    self.save_image(save_folder=folder)
                    self.selected_file = None

    def append_label(self, label, text):
        label.config(text=label.cget("text") + text)

    def rewrite_label(self, label, text):
        label.config(text=text)

    def display_image(self, img, label, size_label, max_size=MAX_IMG_DISP_SIZE):
        # Resize image to fit within max_size (maintaining aspect ratio)
        height, width = img.shape[:2]
        if max_size:
            if height > max_size or width > max_size:
                scaling_factor = max_size / max(height, width)
                img = cv2.resize(img, None, fx=scaling_factor, fy=scaling_factor, interpolation=cv2.INTER_AREA)
        # Convert image from BGR to RGB (for displaying with Tkinter)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        # Create PIL Image object
        pil_img = Image.fromarray(img_rgb)
        # Convert PIL Image to Tkinter PhotoImage
        tk_img = ImageTk.PhotoImage(image=pil_img)

        # Display image in label
        label.configure(image=tk_img)
        label.image = tk_img  # Keep a reference to prevent garbage collection
        # Add text to label with image dimensions (below the image)
        size_label.configure(text=f"{width}x{height} pixels")

    def save_image(self, save_folder=None):
        # Ask user to select a folder to save the processed image
        if save_folder is None:
            save_folder = self.get_folder()
        if save_folder:
            # Save the processed image
            save_path = save_folder / f"{self.selected_file.stem}_pixelated_{self.pixel_sizing}{self.selected_file.suffix}"
            cv2.imwrite(str(save_path), self.processed_img)

            # Save the low-res image
            low_res_path = save_folder / f"{self.selected_file.stem}_low_res_{self.pixel_sizing}{self.selected_file.suffix}"
            cv2.imwrite(str(low_res_path), self.low_res_img)

            print(f"Images saved to {save_folder}")
            print(save_path.name, "and", low_res_path.name)

def main():
    # Create the main window
    root = tk.Tk()
    app = ImageProcessingApp(root)
    root.resizable(width=False, height=False)
    root.mainloop()

def pixelate_by_pixel_size(input:np.ndarray, pixel_size:int = 16):
    # Inspired from: https://stackoverflow.com/a/55509210/15783454

    # Get input size
    height, width = input.shape[:2]
    # print(f"Input size: {width}x{height} pixels")

    # Desired "pixelated" size
    w, h = (math.ceil(width / pixel_size), math.ceil(height / pixel_size))
    # print(f"Target size: {w}x{h} pixels")

    # Resize input to "pixelated" size
    pixel_perfect = cv2.resize(input, (w, h), interpolation=cv2.INTER_LINEAR)
    # print(f"Pixelated output size: {w * pixel_size}x{h * pixel_size} pixels")
    # Initialize output image
    output = cv2.resize(pixel_perfect, (w * pixel_size, h * pixel_size), interpolation=cv2.INTER_NEAREST)
    return output, pixel_perfect

def pixelate_to_size(input:np.ndarray, size:int = 16, keep_width:bool = True, keep_height:bool = False):
    assert not (keep_width and keep_height) and (keep_width or keep_height), "Only one of width or height can and must be True"

    height, width = input.shape[:2]

    if keep_width:
        w = size
        h = round(size * height / width)
    elif keep_height:
        h = size
        w = round(size * width / height)

    pixel_perfect = cv2.resize(input, (w, h), interpolation=cv2.INTER_LINEAR)
    output = cv2.resize(pixel_perfect, (width, height), interpolation=cv2.INTER_NEAREST)
    return output, pixel_perfect


if __name__ == "__main__":
    main()


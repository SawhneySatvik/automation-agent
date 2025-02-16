from fastapi import HTTPException
from PIL import Image
import os

def process_image(filename, targetfile, resize_width=None, resize_height=None, quality=80):
    print(f"Processing image: {filename}, {targetfile}, {resize_width}, {resize_height}, {quality}")
    
    if not os.path.exists(filename) or not targetfile or not (resize_width or resize_height or quality):
        raise HTTPException(status_code=400, detail=f"Invalid input parameters: input_path: {filename}, output_path: {targetfile} and one of (resize_width : {resize_width}, resize_height: {resize_height}, quality: {quality})")
    
    """
    Compress or resize an image and save it to output_path. credit_card.png
    
    Parameters:
        input_path (str): Path to the original image.
        output_path (str): Path to save the processed image.
        resize_width (int, optional): New width (maintains aspect ratio if height is None).
        resize_height (int, optional): New height (maintains aspect ratio if width is None).
        quality (int, optional): Compression quality (1-100) for JPEG/WebP (default: 80).
    """
    try:
        # Open image
        img = Image.open(filename)

        # Resize if needed
        if resize_width or resize_height:
            img = img.resize((resize_width, resize_height), Image.LANCZOS)

        # Save image with compression
        img.save(targetfile, quality=quality, optimize=True)
        print(f"✅ Image saved to {targetfile}")
        return targetfile
    
    except Exception as e:
        print(f"❌ Error processing image: {e}")
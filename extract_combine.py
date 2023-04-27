import os
import cv2
import sys
import shutil
from tqdm import tqdm
# Usage: python extract_combine.py videoName
# Example: python extract_combine.py rick_roll
videoName = sys.argv[1]
vidcap = cv2.VideoCapture(f'{videoName}.mp4')
success,image = vidcap.read()
count = 0
os.makedirs('frames')

output_file = f"videos/{videoName}.mjpeg"
while success:
  cv2.imwrite("frames/frame%d.jpg" % count, image)     # save frame as JPEG file      
  success,image = vidcap.read()
  count += 1
# print(count)

# Open output file in binary mode

with open(output_file, "wb") as f:
    # Loop over input files
    for i in tqdm(range(count)):
        # Open input file in binary mode and read image data
        with open(f'frames/frame{i}.jpg', "rb") as img:
            data = img.read()
        # Get length of image data and pack it into header
        length = len(data)
        if length > 99999:
            length = 99999
            print('Overload!')
        # data = data[:length]
        # Write header and image data to output file
        # print(length)
        f.write((str(length).zfill(5)).encode())
        f.write(data[:length])
shutil.rmtree('frames')
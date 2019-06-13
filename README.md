BBox-Label-Tool
===============

A simple tool for labeling object multiple class bounding boxes in images, implemented with Python Tkinter.


**Screenshot:**
![Label Tool](./screenshot.png)

Data Organization
-----------------
LabelTool  
|  
|--main.py   *# source code for the tool*  
|  
|--InputImages/   *# directory containing the images to be labeled*  
|  
|--OutputImages/   *# directory for the image processing results*  
|  
|--OutputLabels/   *# directory for the labeling results*  

Environment
----------
- python 3.6
- python PIL (Pillow)

Run
-------
$ python main.py

Usage
-----
1. Input a folder and click `Load`. The images in the folder will begin to load.
2. Check the Classification field, to see if it matches the box you're about to draw.
3. To create a new bounding box, left-click to select the first vertex. Moving the mouse to draw a rectangle, and left-click again to select the second vertex.
  - To cancel the bounding box while drawing, just press `<Esc>`.
  - To delete an existing bounding box, select it from the listbox, and click `Delete`.
  - To delete all existing bounding boxes in the image, simply click `ClearAll`.
4. After finishing one image, click `Next` to advance. Likewise, click `Prev` to reverse.
  - Be sure to click `Next` after finishing a image, or the result won't be saved. 

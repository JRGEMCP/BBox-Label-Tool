from tkinter import *
from PIL import Image, ImageTk
import os
import glob
import math

# colors for the bboxes
COLORS = ['red', 'blue', 'yellow', 'pink', 'cyan', 'green', 'black']


IMG_SCALE_FACTOR = 1
IMG_DISPLAY_WIDTH = math.floor(2880 / IMG_SCALE_FACTOR)
IMG_DISPLAY_HEIGHT = math.floor(1880 / IMG_SCALE_FACTOR)
IMG_DEFAULT_CLASS = "Dog"

cwd = os.path.dirname(os.path.realpath(__file__))

raw_input_image_path = cwd+"/InputImages"
output_image_path = cwd+"/OutputImages"
output_label_path = cwd+"/OutputLabels"
supported_image_format = "png"  # JPEG also available


def scale_up_coords(input1, input2):
    return input1*IMG_SCALE_FACTOR, input2*IMG_SCALE_FACTOR


def scale_down_coords(input):
    index = 0
    scaled_coords = {}
    unscaled_coords = {}
    for i in input:
        scaled_coords[index] = math.floor(i/IMG_SCALE_FACTOR)
        unscaled_coords[index] = i
        index = index + 1
    return scaled_coords, unscaled_coords


def parse_label_line(line):
    classification = line.split('[', 1)[0].strip(" ")
    raw_coords = (line.split('[', 1)[1]).split(']', 1)[0].split()
    cords = [int(t.replace(",", "").strip()) for t in raw_coords]
    scaled_cords, unscaled_cords = scale_down_coords(cords)
    return classification, scaled_cords, unscaled_cords


# while in the system memory, store label properly
# (self.curClassification, [x1, y1, x2, y2])
def transform_raw_label(line):
    classification, scaled_cords, unscaled_cords = parse_label_line(line)
    return classification, [unscaled_cords[0], unscaled_cords[1], unscaled_cords[2], unscaled_cords[3]]


def scale_raw_image_and_save(image_path):
    image_file_name = image_path.split(os.sep)[-1]
    result_image = output_image_path + os.sep + image_file_name
    img = Image.open(image_path)
    resized = img.resize((IMG_DISPLAY_WIDTH, IMG_DISPLAY_HEIGHT), Image.ANTIALIAS)
    resized.save(result_image)
    return result_image


class LabelTool:
    def __init__(self, master, custom_image_path, custom_labels_path, supported_image_format="JPEG"):
        # set up the main frame
        self.parent = master
        self.parent.title("LabelTool")
        self.frame = Frame(self.parent)
        self.frame.pack(fill=BOTH, expand=1)
        self.parent.resizable(width=FALSE, height=FALSE)

        # initialize global state
        self.imageDir = ''
        self.imageList = []
        self.labelsDir = ''
        self.cur = 0
        self.total = 0
        self.imagename = ''
        self.curClassification = IMG_DEFAULT_CLASS
        self.labelfilename = ''
        self.tkimg = None

        # initialize mouse state
        self.STATE = {}
        self.STATE['click'] = 0
        self.STATE['x'], self.STATE['y'] = 0, 0

        # reference to bbox
        self.bboxIdList = []
        self.bboxId_Temp = None
        self.bboxList = []
        self.bboxClassificationIDList = []
        self.hl = None
        self.vl = None

        # ----------------- GUI stuff ---------------------
        # dir entry & load
        self.label = Label(self.frame, text = "Images Dir:")
        self.label.grid(row = 0, column = 0, sticky = E)
        self.entry = Entry(self.frame)
        self.entry.grid(row = 0, column = 1, sticky = W+E)
        self.ldBtn = Button(self.frame, text = "Load", command=self.loadDir)
        self.ldBtn.grid(row = 0, column = 2, sticky = W+E)

        # main panel for labeling
        self.mainPanel = Canvas(self.frame, cursor='tcross')
        self.mainPanel.bind("<Button-1>", self.mouseClick)
        self.mainPanel.bind("<Motion>", self.mouseMove)
        self.parent.bind("<Escape>", self.cancelBBox)  # press <Espace> to cancel current bbox
        self.mainPanel.grid(row=1, column=1, rowspan=4, sticky=W+N)

        # showing selected classification for bounding box
        self.label = Label(self.frame, text="Classification:")
        self.label.grid(row=1, column=2, sticky=W+N)
        self.classificationEntry = Entry(self.frame)
        self.classificationEntry.grid(row=2, column=2, sticky=W+E)

        # showing bbox info & delete bbox
        self.lb1 = Label(self.frame, text = 'Bounding boxes:')
        self.lb1.grid(row = 3, column = 2,  sticky = W+N)
        self.listbox = Listbox(self.frame, width = 22, height = 12)
        self.listbox.grid(row = 4, column = 2, sticky = N)
        self.btnDel = Button(self.frame, text = 'Delete', command=self.delBBox)
        self.btnDel.grid(row = 5, column = 2, sticky = W+E+N)
        self.btnClear = Button(self.frame, text = 'ClearAll', command=self.clearBBox)
        self.btnClear.grid(row = 6, column = 2, sticky = W+E+N)
        self.btnSave = Button(self.frame, text = 'Save Label', command=self.saveImage)
        self.btnSave.grid(row = 8, column = 2, sticky = W+E+N)

        # control panel for image navigation
        self.ctrPanel = Frame(self.frame)
        self.ctrPanel.grid(row = 7, column = 1, columnspan = 2, sticky = W+E)
        self.prevBtn = Button(self.ctrPanel, text='<< Prev', width = 10, command = self.prevImage)
        self.prevBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.nextBtn = Button(self.ctrPanel, text='Next >>', width = 10, command = self.nextImage)
        self.nextBtn.pack(side = LEFT, padx = 5, pady = 3)
        self.progLabel = Label(self.ctrPanel, text = "Progress:     /    ")
        self.progLabel.pack(side = LEFT, padx = 5)
        self.labelPath = Label(self.frame, text="Cur Label:")
        self.labelPath.grid(row=8, column=0, sticky=E)
        self.entryPath = Entry(self.frame)
        self.entryPath.grid(row=8, column=1, sticky=W + E)

        # display mouse position
        self.disp = Label(self.ctrPanel, text='')
        self.disp.pack(side = RIGHT)

        self.frame.columnconfigure(1, weight = 1)
        self.frame.rowconfigure(4, weight = 1)

        self.imageDir = custom_image_path
        self.entry.insert(0, self.imageDir)
        self.classificationEntry.insert(0, self.curClassification)
        self.labelsDir = custom_labels_path
        self.custom_image_format = supported_image_format

    def loadDir(self):

        s = self.entry.get()
        self.parent.focus()

        self.imageList = glob.glob(os.path.join(self.imageDir, '*.'+self.custom_image_format))
        print("Searching for images inside: " + os.path.join(self.imageDir, '*.'+self.custom_image_format))
        if len(self.imageList) == 0:
            print('No .' + self.custom_image_format + ' images found in the specified dir!')
            return

        # default to the 1st image in the collection
        self.cur = 1
        self.total = len(self.imageList)

        if not os.path.exists(self.labelsDir):
            os.mkdir(self.labelsDir)

        if not os.path.exists(output_image_path):
            os.mkdir(output_image_path)

        self.loadImage()
        print('{images:d} images loaded from {folder:s}'.format(images=self.total, folder=s))

    def loadImage(self):
        # load image
        imagepath = self.imageList[self.cur - 1]
        new_image_path = scale_raw_image_and_save(imagepath)
        self.tkimg = ImageTk.PhotoImage(Image.open(new_image_path).resize((IMG_DISPLAY_WIDTH, IMG_DISPLAY_HEIGHT)))
        self.mainPanel.config(width=max(self.tkimg.width(), 400), height=max(self.tkimg.height(), 400))
        self.mainPanel.create_image(0, 0, image=self.tkimg, anchor=NW)
        self.progLabel.config(text="{a:04d}/{total:04d}".format(a=self.cur, total=self.total))

        # load labels
        self.clearBBox()
        self.imagename = imagepath.rsplit('/', 1)[-1]
        labelname = self.imagename + '.txt'
        self.labelfilename = os.path.join(self.labelsDir, labelname)
        self.entryPath.delete(0, 'end')
        self.entryPath.insert(0, self.labelfilename)

        if os.path.exists(self.labelfilename):
            with open(self.labelfilename) as f:
                for line in f:
                    classification, scaled_tmp, unscaled_tmp = parse_label_line(line)
                    self.add_a_bound_box_and_text(classification, scaled_tmp[0], scaled_tmp[1], scaled_tmp[2], scaled_tmp[3])

    def saveImage(self):
        if self.bboxList.__len__ != 0:
            with open(self.labelfilename, 'w') as f:
                for class_and_bbox in self.bboxList:
                    f.write(' '.join(map(str, class_and_bbox)) + '\n')
            print('Image No. {curlurl:d} saved'.format(curlurl=self.cur))

    def mouseClick(self, event):
        if self.STATE['click'] == 0:
            self.STATE['x'], self.STATE['y'] = event.x, event.y
        else:
            x1, x2 = min(self.STATE['x'], event.x), max(self.STATE['x'], event.x)
            y1, y2 = min(self.STATE['y'], event.y), max(self.STATE['y'], event.y)
            self.mainPanel.delete(self.bboxId_Temp)
            self.bboxId_Temp = None
            self.add_a_bound_box_and_text(self.classificationEntry.get().strip(" "), x1, y1, x2, y2)
        self.STATE['click'] = 1 - self.STATE['click']

    def mouseMove(self, event):
        scaled_x, scaled_y = scale_up_coords(event.x, event.y)
        self.disp.config(text='x: %d, y: %d' % (scaled_x, scaled_y))
        if self.tkimg:
            if self.hl:
                self.mainPanel.delete(self.hl)
            self.hl = self.mainPanel.create_line(0, event.y, self.tkimg.width(), event.y, width = 2)
            if self.vl:
                self.mainPanel.delete(self.vl)
            self.vl = self.mainPanel.create_line(event.x, 0, event.x, self.tkimg.height(), width = 2)
        if 1 == self.STATE['click']:
            if self.bboxId_Temp:
                self.mainPanel.delete(self.bboxId_Temp)
            self.bboxId_Temp = self.mainPanel.create_rectangle(self.STATE['x'], self.STATE['y'], \
                                                               event.x, event.y, \
                                                               width = 2, \
                                                               outline = COLORS[len(self.bboxList) % len(COLORS)])

    def cancelBBox(self, event):
        if 1 == self.STATE['click']:
            if self.bboxId_Temp:
                self.mainPanel.delete(self.bboxId_Temp)
                self.bboxId_Temp = None
                self.STATE['click'] = 0

    def delBBox(self):
        sel = self.listbox.curselection()
        if len(sel) != 1:
            return
        idx = int(sel[0])
        self.delete_a_bound_box_and_text(idx)

    def clearBBox(self):
        for idx in range(len(self.bboxIdList)):
            self.mainPanel.delete(self.bboxIdList[idx])
            self.mainPanel.delete(self.bboxList[idx])
            self.mainPanel.delete(self.bboxClassificationIDList[idx])
        self.listbox.delete(0, 'end')
        self.bboxIdList = []
        self.bboxList = []
        self.bboxClassificationIDList = []

    def prevImage(self, event = None):
        self.saveImage()
        if self.cur > 1:
            self.cur -= 1
            self.loadImage()

    def nextImage(self, event = None):
        self.saveImage()
        if self.cur < self.total:
            self.cur += 1
            self.loadImage()

    def add_a_bound_box_and_text(self, classification, x1, y1, x2, y2):
        self.bboxList.append((classification, [x1, y1, x2, y2]))
        tmpId = self.mainPanel.create_rectangle(x1, y1, x2, y2, width=2, outline=COLORS[(len(self.bboxList) - 1) % len(COLORS)])
        self.bboxIdList.append(tmpId)
        self.listbox.insert(END, '({x1:d}, {y1:d}) -> ({x2:d}, {y2:d})'.format(x1=x1, y1=y1, x2=x2, y2=y2))

        textId = self.mainPanel.create_text(x1, y1 + 5, anchor=NE,
                                            text=classification.strip(" "),
                                            fill=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])
        self.bboxClassificationIDList.append(textId)
        self.listbox.itemconfig(len(self.bboxIdList) - 1, fg=COLORS[(len(self.bboxIdList) - 1) % len(COLORS)])

    def delete_a_bound_box_and_text(self, idx):
        self.mainPanel.delete(self.bboxIdList[idx])
        self.bboxIdList.pop(idx)
        self.mainPanel.delete(self.bboxList[idx])
        self.bboxList.pop(idx)
        self.mainPanel.delete(self.bboxClassificationIDList[idx])
        self.bboxClassificationIDList.pop(idx)
        self.listbox.delete(idx)


if __name__ == '__main__':
    root = Tk()
    tool = LabelTool(root, raw_input_image_path, output_label_path, supported_image_format)
    root.resizable(width=True, height=True)
    root.mainloop()

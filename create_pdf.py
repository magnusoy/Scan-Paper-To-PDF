# import the necessary libraries
from transform import four_point_transform
from skimage.filters import threshold_local
from fpdf import FPDF
import os
import argparse
import cv2
import imutils

parser = argparse.ArgumentParser(
    description='Scan images and create a PDF containing them.')
parser.add_argument('directory', type=str,
                    help='Assign directory where images are located.')
parser.add_argument('filename', type=str,
                    help='Name your pdf-file')
args = parser.parse_args()

# if user forget to add .pdf at the end
if not args.filename.endswith(".pdf"):
    filename = args.filename + ".pdf"

# creating list objects
imagelist = list()
scannedImageList = list()
# create pdf object for merging images to one pdf
pdf = FPDF()
# uses current directory if user dont add any as arg
if args.directory == '':
    dir_path = os.path.dirname(os.path.realpath(__file__))
else:
    dir_path = args.directory
# iterate in given directory looking for images
for file in os.listdir(dir_path):
    if file.endswith(".jpg") or file.endswith(".png"):
        imagelist.append(os.path.join(dir_path, file))

if len(imagelist) == 0:
    print("Can't find any images in given directory: " + dir_path)
    quit()

page = 0
for orgimage in imagelist:
    # load the image and compute the ratio of the old height
    # to the new height, clone it, and resize it
    image = cv2.imread(orgimage)
    ratio = image.shape[0] / 500.0
    orig = image.copy()
    image = imutils.resize(image, height=500)

    # convert the image to grayscale, blur it, and find edges
    # in the image
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.GaussianBlur(gray, (5, 5), 0)
    edged = cv2.Canny(gray, 75, 200)

    # find the contours in the edged image, keeping only the
    # largest ones, and initialize the screen contour
    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST,
                            cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if imutils.is_cv2() else cnts[1]
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

    # loop over the contours
    for c in cnts:
        # approximate the contour
        peri = cv2.arcLength(c, True)
        approx = cv2.approxPolyDP(c, 0.02 * peri, True)

        # if our approximated contour has four points, then we
        # can assume that we have found our screen
        if len(approx) == 4:
            screenCnt = approx
            break

    # apply the four point transform to obtain a top-down
    # view of the original image
    warped = four_point_transform(orig, screenCnt.reshape(4, 2) * ratio)

    # convert the warped image to grayscale, then threshold it
    # to give it that 'black and white' paper effect
    warped = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
    T = threshold_local(warped, 11, offset=10, method="gaussian")
    warped = (warped > T).astype("uint8") * 255
    scanned_filename = os.path.join(dir_path, "scanned_" + str(page) + ".jpg")
    cv2.imwrite(scanned_filename, warped)
    page += 1

# iterate directory finding scanned images
for file in os.listdir(dir_path):
    if file.startswith("scanned_"):
        temp_filename = os.path.join(dir_path, file)
        scannedImageList.append(temp_filename)

# creating PDF-pages with scanned images
for image in scannedImageList:
    pdf.add_page()
    pdf.image(image, w=200, h=260)

# saves PDF containing scanned images
pdf.output(os.path.join(dir_path, filename), "F")

if filename in os.listdir(dir_path):
    delete_file = input(
        "PDF-file successfully created, do you want to delete images? (y/n)")
    if delete_file == "y":
        # delete original files
        for image in imagelist:
            os.remove(image)
        # delete scanned files
        for image in scannedImageList:
            os.remove(image)
        print("Images are now deleted")
    elif delete_file == "n" or delete_file == "":
        print("Images are not deleted")
else:
    print("Error, PDF-file was not successfully created!")

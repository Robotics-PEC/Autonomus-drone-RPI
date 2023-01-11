import cv2
import numpy as np 
import glob
from tqdm import tqdm
import PIL.ExifTags
import PIL.Image

#============================================
# Camera calibration
#============================================

#Define size of chessboard target. 

chessboard_size = (7,5)

#Define arrays to save detected points
obj_points = [] #3D points in real world space 
img_points = [] #3D points in image plane

#Prepare grid and points to display

objp = np.zeros((np.prod(chessboard_size),3),dtype=np.float32)


objp[:,:2] = np.mgrid[0:chessboard_size[0], 0:chessboard_size[1]].T.reshape(-1,2)

#read images

calibration_paths = glob.glob('images/*')

#Iterate over images to find intrinsic matrix
for image_path in tqdm(calibration_paths):

	#Load image
	image = cv2.imread(image_path)
	gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
	print("Image loaded, Analizying...")
	#find chessboard corners
	ret,corners = cv2.findChessboardCorners(gray, chessboard_size, None)

	if ret == True:
		print("Chessboard detected!")
		print(image_path)
		#define criteria for subpixel accuracy
		criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
		#refine corner location (to subpixel accuracy) based on criteria.
		cv2.cornerSubPix(gray, corners, (5,5), (-1,-1), criteria)
		obj_points.append(objp)
		img_points.append(corners)

#Calibrate camera
ret, K, dist, rvecs, tvecs = cv2.calibrateCamera(obj_points, img_points,gray.shape[::-1], None, None)

#Save parameters into numpy file
np.save("./camera_params/ret", ret)
np.save("./camera_params/K", K)
np.save("./camera_params/dist", dist)
np.save("./camera_params/rvecs", rvecs)
np.save("./camera_params/tvecs", tvecs)

#Get exif data in order to get focal length. 
exif_img = PIL.Image.open(calibration_paths[0])

exif_data = {
	PIL.ExifTags.TAGS[k]:v
	for k, v in exif_img._getexif().items()
	if k in PIL.ExifTags.TAGS}

#Get focal length in tuple form
# focal_length_exif = exif_data['FocalLength']

# #Get focal length in decimal form
# focal_length = focal_length_exif[0]/focal_length_exif[1]

# #Save focal length
# np.save("./camera_params/FocalLength", focal_length)

#Calculate projection error. 
mean_error = 0
for i in range(len(obj_points)):
	img_points2, _ = cv2.projectPoints(obj_points[i],rvecs[i],tvecs[i], K, dist)
	error = cv2.norm(img_points[i], img_points2, cv2.NORM_L2)/len(img_points2)
	mean_error += error

total_error = mean_error/len(obj_points)
print (total_error)
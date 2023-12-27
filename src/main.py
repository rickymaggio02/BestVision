import os
import numpy as np
import cv2
import matplotlib.pyplot as plt
from vo_pipeline import *

# Setup
if config['dataset'] == 'kitti':
    # Set kitti_path to the folder containing "05" and "poses"
    kitti_path = 'kitti'  # replace with your path
    assert os.path.exists(kitti_path), "KITTI path does not exist"
    ground_truth = np.loadtxt(f'{kitti_path}/poses/05.txt')[:, -9:-7]
    last_frame = 4540
    K = np.array([[718.856, 0, 607.1928],
                  [0, 718.856, 185.2157],
                  [0, 0, 1]])
    
    bootstrap_frames = [0, 2]
    img0 = cv2.imread(f'{kitti_path}/05/image_0/{bootstrap_frames[0]:06d}.png', cv2.IMREAD_GRAYSCALE)
    img1 = cv2.imread(f'{kitti_path}/05/image_0/{bootstrap_frames[1]:06d}.png', cv2.IMREAD_GRAYSCALE)

elif config['dataset'] == 'malaga':
    # Set malaga_path to the folder containing Malaga dataset
    malaga_path = 'path_to_malaga_dataset'  # replace with your path
    assert os.path.exists(malaga_path), "Malaga path does not exist"
    left_images = [img for img in os.listdir(f'{malaga_path}/malaga-urban-dataset-extract-07_rectified_800x600_Images') if img.endswith('.png')]
    left_images.sort()
    last_frame = len(left_images)
    K = np.array([[621.18428, 0, 404.0076],
                  [0, 621.18428, 309.05989],
                  [0, 0, 1]])
    
    bootstrap_frames = [0, 2]
    img0 = cv2.imread(f'{malaga_path}/malaga-urban-dataset-extract-07_rectified_800x600_Images/{left_images[bootstrap_frames[0]]}', cv2.IMREAD_GRAYSCALE)
    img1 = cv2.imread(f'{malaga_path}/malaga-urban-dataset-extract-07_rectified_800x600_Images/{left_images[bootstrap_frames[1]]}', cv2.IMREAD_GRAYSCALE)

elif config['dataset'] == 'parking':
    # Set parking_path to the folder containing parking dataset
    parking_path = 'parking'  # replace with your path
    assert os.path.exists(parking_path), "Parking path does not exist"
    last_frame = 598
    K = np.loadtxt(f'{parking_path}/K.txt')
    ground_truth = np.loadtxt(f'{parking_path}/poses.txt')[:, -9:-7]
    
    bootstrap_frames = [0, 2]
    img0 = cv2.imread(f'{parking_path}/images/img_{bootstrap_frames[0]:05d}.png', cv2.IMREAD_GRAYSCALE)
    img1 = cv2.imread(f'{parking_path}/images/img_{bootstrap_frames[1]:05d}.png', cv2.IMREAD_GRAYSCALE)

else:
    raise ValueError("Invalid dataset selection")



# instantiate the VOInitializer
VOInit = VOInitializer(K)

### 1 - Initialization
# detect, describe and match features
kps_1, kps_2 = VOInit.getKeypointMatches(img0, img1)

# estimate pose
img1_img2_pose_tranform = VOInit.getPoseEstimate(kps_1, kps_2)

# triangulate landmarks
state = VOInit.get_2D_3D_landmarks_association(kps_1, kps_2, img1_img2_pose_tranform)
X = np.array(list(state.values()))

# plot the initialization images
plt.figure(figsize=(10, 10))
plt.imshow(img0, cmap='gray')
plt.scatter(kps_1[:, 0], kps_1[:, 1], c='r', s=20)
plt.xlabel('x (pixesl)')
plt.ylabel('y (pixels)')
plt.title('Image 1')
plt.show()

plt.figure(figsize=(10, 10))
plt.imshow(img0, cmap='gray')
plt.scatter(kps_2[:, 0], kps_2[:, 1], c='r', s=20)
plt.xlabel('x (pixesl)')
plt.ylabel('y (pixels)')
plt.title('Image 2')
plt.show()

# 3D plot of the initialization 3D landmarks (X)
fig = plt.figure(figsize=(10, 10))
ax = fig.add_subplot(111, projection='3d')
ax.scatter(X[:, 0], X[:, 1], X[:, 2], c='r', s=20)
ax.set_xlabel('x (m)')
ax.set_ylabel('y (m)')
ax.set_zlabel('z (m)')
ax.set_title('3D landmarks (X)')
plt.show()

# plot a filtered version of the 3D landmarks (X) (some bugs, comes form Ricardo)
# T_hom = np.vstack((np.hstack((img1_img2_pose_tranform, np.zeros((1,3)))), np.array([0,0,0,1])))
# t_inv = np.linalg.inv(T_hom)
# axis = t_inv @ np.vstack((np.hstack((np.eye(3), np.zeros((3,1)))), np.ones((4,1)).T))

# filter = np.linalg.norm(X, axis = 0) < 4
# print("filter len ", filter.shape)
# X_filtered = X[:, filter]
# plt.scatter(X_filtered[0,:], X_filtered[2,:], color='blue', marker='o', label='Points')
# plt.scatter(P[0,:], P[2,:], color='red', marker='o', label='Points')
# plt.plot([axis[0,3],axis[0,0]],[axis[2,3], axis[2,0]], 'r-')
# plt.plot([axis[0,3],axis[0,2]],[axis[2,3], axis[2,2]], 'g-')
# plt.xlabel('X-axis')
# plt.ylabel('Z-axis')
# plt.ylim((0,10))
# plt.xlim((-5,5))
# plt.title('2D Points Visualization')
# plt.legend() # Show legend
# plt.show() # Show the plot

# # plot all and filtered 2D keypoints (img 1)
# plt.imshow(img1)
# points = kps_1[filter, :]
# print("size filtered points ", points.shape)
# plt.scatter(kps_1[:,0], kps_1[:,1], color='blue', marker='o', label='All keypoints')
# plt.scatter(points[:,0], points[:,1], color='red', marker='o', label='Filtered keypoints')
# plt.plot()
# plt.show()

# # plot all and filtered 2D keypoints (img 2)
# plt.imshow(img1)
# points2 = kps_2[filter,:]
# plt.scatter(kps_2[:,0], kps_2[:,1], color='blue', marker='o', label='All keypoints')
# plt.scatter(points2[:,0], points2[:,1], color='red', marker='o', label='Filtered keypoints')
# plt.plot()
# plt.show()


### - Continuous Operation

#instantiate BestVision:
vision = BestVision(K)
vision.update_state(kps_2, X.T)


# loading the next image
if config['dataset'] == 'kitti':
    img2 = cv2.imread(f'{kitti_path}/05/image_0/{5:06d}.png', cv2.IMREAD_GRAYSCALE)

elif config['dataset'] == 'malaga':
    img2 = cv2.imread(f'{malaga_path}/malaga-urban-dataset-extract-07_rectified_800x600_Images/{left_images[bootstrap_frames[2]]}', cv2.IMREAD_GRAYSCALE)

elif config['dataset'] == 'parking':
    img2 = cv2.imread(f'{parking_path}/images/img_{bootstrap_frames[2]:05d}.png', cv2.IMREAD_GRAYSCALE)

else:
    raise ValueError("Invalid dataset selection")

# instantiate Landmark association
associate = KeypointsToLandmarksAssociator(K)
state_2 = associate.associateKeypoints(img1,img2, vision.state)




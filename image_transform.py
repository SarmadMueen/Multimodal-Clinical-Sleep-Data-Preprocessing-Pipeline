import numpy as np
from skimage import transform

# Example coordinattes start from upper left- upper right-lower right- lower left

area_of_interest = [(226, 160),
                    (387, 160),
                    (402, 507),
                    (193, 507)]


area_of_projection =   [(226, 160),
                    (387, 160),
                    (402, 507),
                    (193, 507)]





def project_planes(image, src, dst):
    x_src = [val[0] for val in src] + [src[0][0]]
    y_src = [val[1] for val in src] + [src[0][1]]
    x_dst = [val[0] for val in dst] + [dst[0][0]]
    y_dst = [val[1] for val in dst] + [dst[0][1]]
    
    fig, ax = plt.subplots(1,2, figsize=(13,6))
    
    new_image = image.copy() 
    projection = np.zeros_like(new_image)
    ax[0].imshow(new_image);
    ax[0].plot(x_src, y_src, 'r--')
    ax[0].set_title('Area of Interest')
    ax[1].imshow(projection)
    ax[1].plot(x_dst, y_dst, 'r--')
    ax[1].set_title('Area of Projection')

def project_transform(image, src, dst):
    tform = transform.estimate_transform('projective', np.array(src), np.array(dst))
    transformed = transform.warp(image, tform.inverse, output_shape=(image.shape[0], image.shape[1]))
    
    # Convert the transformed image to uint8 and scale it to the range [0, 255]
    transformed = (transformed * 255).astype(np.uint8)
    
    # Calculate the bounding box of the destination area
    min_x = min(dst, key=lambda x: x[0])[0]
    max_x = max(dst, key=lambda x: x[0])[0]
    min_y = min(dst, key=lambda x: x[1])[1]
    max_y = max(dst, key=lambda x: x[1])[1]
    
    # Crop the transformed image to the destination area
    cropped_transformed = transformed[int(min_y):int(max_y), int(min_x):int(max_x)]
    
    return cropped_transformed


import numpy as np
import image_ops

img = np.zeros((100, 100, 3), dtype=np.uint8)
img[:] = (200, 50, 50)

print("size:       ", image_ops.image_size(img))
print("mean color: ", image_ops.mean_color(img))

region = (25, 25, 50, 50)  # x, y, w, h
out = image_ops.draw_rect(img, region, (0, 255, 0))
print("after draw, mean color:", image_ops.mean_color(out))

cropped = image_ops.crop(img, region)
print("cropped size:", image_ops.image_size(cropped))

channels = image_ops.split_channels(img)
print("channels:   ", len(channels))
merged = image_ops.merge_channels(channels)
print("merged size:", image_ops.image_size(merged))

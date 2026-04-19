import time
from collections import deque
import numpy as np
import flood_fill


def flood_fill_python(image, y, x, fill_value, tolerance):
    out = image.copy()
    seed = int(image[y, x])
    visited = np.zeros(image.shape, dtype=bool)
    queue = deque([(y, x)])
    while queue:
        cy, cx = queue.popleft()
        if cy < 0 or cy >= image.shape[0] or cx < 0 or cx >= image.shape[1]:
            continue
        if visited[cy, cx]:
            continue
        if abs(int(image[cy, cx]) - seed) > tolerance:
            continue
        visited[cy, cx] = True
        out[cy, cx] = fill_value
        queue.extend([(cy + 1, cx), (cy - 1, cx), (cy, cx + 1), (cy, cx - 1)])
    return out

img = np.full((1024, 1024), 50, dtype=np.uint8)
img[200:800, 200:800] = 180
img[400:600, 400:600] = 60
seed_y, seed_x = 300, 300 
fill_value = 255
tolerance = 10

t0 = time.perf_counter()
py_out = flood_fill_python(img, seed_y, seed_x, fill_value, tolerance)
t1 = time.perf_counter()
cpp_out = flood_fill.flood_fill(img, seed_y, seed_x, fill_value, tolerance)
t2 = time.perf_counter()

py_time  = t1 - t0
cpp_time = t2 - t1

filled_pixels = int((cpp_out == fill_value).sum())
print(f"Image: {img.shape[1]}x{img.shape[0]}  seed=({seed_y},{seed_x})  tolerance={tolerance}  filled={filled_pixels:,} pixels\n")
print(f"flood_fill")
print(f"  Python : {py_time:.3f}s")
print(f"  C++    : {cpp_time:.4f}s")
print(f"  Speedup: {py_time / cpp_time:.0f}x")

assert np.array_equal(py_out, cpp_out), "results differ!"
print("\nBoth implementations produce identical output.")

import time
import numpy as np
import mandelbrot as mb
from PIL import Image


def mandelbrot_python(x_min, x_max, y_min, y_max, width, height, max_iter):
    result = []
    dx = (x_max - x_min) / width
    dy = (y_max - y_min) / height
    for row in range(height):
        c_im = y_min + row * dy
        for col in range(width):
            c_re = x_min + col * dx
            z_re, z_im = 0.0, 0.0
            for i in range(max_iter):
                if z_re * z_re + z_im * z_im > 4.0:
                    break
                z_re, z_im = z_re * z_re - z_im * z_im + c_re, 2.0 * z_re * z_im + c_im
            result.append(i)
    return result


X_MIN, X_MAX = -2.5, 1.0
Y_MIN, Y_MAX = -1.25, 1.25
WIDTH, HEIGHT = 800, 600
MAX_ITER = 100

print(f"Mandelbrot  {WIDTH}x{HEIGHT}  max_iter={MAX_ITER}\n")

t0 = time.perf_counter()
py_result = mandelbrot_python(X_MIN, X_MAX, Y_MIN, Y_MAX, WIDTH, HEIGHT, MAX_ITER)
t1 = time.perf_counter()
cpp_result = mb.mandelbrot(X_MIN, X_MAX, Y_MIN, Y_MAX, WIDTH, HEIGHT, MAX_ITER)
t2 = time.perf_counter()

py_time  = t1 - t0
cpp_time = t2 - t1
print(f"  Python : {py_time:.2f}s")
print(f"  C++    : {cpp_time:.4f}s")
print(f"  Speedup: {py_time / cpp_time:.0f}x")

img = np.array(cpp_result).reshape(HEIGHT, WIDTH).astype(np.float32)
img = np.log1p(img) / np.log1p(MAX_ITER)
img = (img * 255).astype(np.uint8)

Image.fromarray(img).save("mandelbrot.png")
print("\nSaved mandelbrot.png")


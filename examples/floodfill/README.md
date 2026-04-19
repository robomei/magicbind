# performance comparison: flood fill

This example demonstrates when moving code to C++ actually makes sense.

Many image operations (brightness, blur, grayscale) can be expressed as numpy array operations that run in optimized C internally. Rewriting those in C++ would give little to no benefit.

Flood fill is different. Each pixel to visit is determined by the result of the previous step, so there is no way to process pixels in parallel or express the algorithm as a batch array operation. numpy has no built-in for it, and any Python implementation requires an explicit loop, one Python iteration per pixel. That is where C++ wins.

Both the Python and C++ versions here use the same BFS algorithm. The only difference is that the C++ version runs the loop in compiled code instead of the Python interpreter.

Requires OpenCV (`apt install libopencv-dev` or `brew install opencv`).

```bash
uv run magicbind add cpp/flood_fill.h --pkg opencv4 --system-compiler
uv run python main.py
```

Example output:

```
Image: 1024x1024  seed=(300,300)  tolerance=10  filled=320,000 pixels

flood_fill
  Python : 1.378s
  C++    : 0.016s
  Speedup: 84x

Both implementations produce identical output.
```

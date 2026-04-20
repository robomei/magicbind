# performance comparison: flood fill

This example shows when C++ actually helps. Many image operations can be written as numpy array ops that run in optimized C internally. Rewriting those in C++ gives little benefit.

Flood fill for example is different: each pixel to visit depends on the previous step, so the algorithm can't be vectorized. Any Python implementation needs an explicit loop, one iteration per pixel. That's where C++ wins.

Both versions here use the same BFS algorithm, running in the Python interpreter vs. compiled code.

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

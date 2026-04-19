# performance comparison: mandelbrot

Renders the Mandelbrot set by iterating each pixel until escape or max iterations.
Input is just a handful of parameters, so there is no data transfer overhead — the speedup is purely computation.

Both sides implement the same algorithm. The Python version uses a triple nested loop;
the C++ version runs the same logic in compiled code.

```bash
uv run magicbind add cpp/mandelbrot.h
uv run python main.py
```

If Pillow is installed (`uv add pillow`), the result is also saved as `mandelbrot.png`.

Example output:

```
Mandelbrot  800x600  max_iter=100

  Python : 1.58s
  C++    : 0.044s
  Speedup: 36x
```

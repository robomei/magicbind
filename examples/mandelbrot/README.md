# performance comparison: mandelbrot

Renders the Mandelbrot set by iterating each pixel until escape or max iterations. Both sides implement the same algorithm. The Python version uses a triple nested loop;
the C++ version runs the same logic in compiled code.

```bash
uv run magicbind add cpp/mandelbrot.h
uv run python main.py
```

Example output:

```
Mandelbrot  800x600  max_iter=100

  Python : 1.58s
  C++    : 0.044s
  Speedup: 36x
```

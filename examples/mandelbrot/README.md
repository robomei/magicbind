# performance comparison: mandelbrot

Renders the Mandelbrot set by iterating each pixel until escape or max iterations. Both versions implement the same algorithm, one in Python and one in compiled C++.

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

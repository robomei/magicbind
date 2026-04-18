# magicbind

The easy way to speed up Python bottlenecks with C++. No CMake, no build system, no boilerplate. Just point magicbind at your header and it takes care of the rest.

```bash
magicbind add mylib.h
```

magicbind parses the header, generates [nanobind](https://github.com/wjakob/nanobind) glue code, compiles it with a bundled Zig compiler, and installs the extension into your Python environment.

## Install

```bash
uv add magicbind
```

A C++ compiler is bundled via the [ziglang](https://pypi.org/project/ziglang/) package, so you don't need one installed.

## Basic usage

Given a header:

```cpp
// math_utils.h
#include <vector>
#include <optional>

double sum(const std::vector<double>& values);
std::optional<double> mean(const std::vector<double>& values);
double clamp(double value, double lo, double hi);
```

If there is a `math_utils.cpp` next to the header, magicbind picks it up automatically. You can also pass source files explicitly. If everything is defined in the header, no source file is needed.

```bash
magicbind add math_utils.h                    # auto-detects math_utils.cpp
magicbind add math_utils.h --source other.cpp # explicit
magicbind add math_utils.h --source a.cpp --source b.cpp
```

Then use it from Python:

```python
import math_utils

math_utils.sum([1, 2, 3])       # 6.0
math_utils.mean([])             # None
math_utils.clamp(10, 0, 5)      # 5.0
```

STL types are converted automatically: `std::vector` becomes a list, `std::optional` becomes `None` or a value, `std::pair` becomes a tuple.

## System libraries

To use a library installed on your system, pass `--pkg` with its pkg-config name:

```bash
magicbind add image_ops.h --pkg opencv4 --system-compiler
```

`--system-compiler` is required when linking against system C++ libraries. The default Zig compiler is great for self-contained code, but system libraries like OpenCV were compiled with a different C++ runtime, so you need the system's g++ or clang++ to match.

You can also specify include and link paths manually:

```bash
magicbind add mylib.h \
  --include /opt/mylib/include \
  --lib /opt/mylib/lib \
  --link mylib
```

## Rebuilding

When you change the header or source, run:

```bash
magicbind build          # rebuilds all modules
magicbind build mylib    # rebuilds one module
```

This replays the original `add` command with the same flags and compiler, without you having to remember them.

## OpenCV

magicbind ships built-in type casters for common OpenCV types. Write normal C++ functions:

```cpp
// image_ops.h
#include <opencv2/core.hpp>
#include <string>

cv::Mat blur(const cv::Mat& src, int kernel_size = 5);
cv::Mat to_grayscale(const cv::Mat& src);
cv::Size image_size(const cv::Mat& src);
cv::Mat crop(const cv::Mat& src, cv::Rect roi);
cv::Scalar mean_color(const cv::Mat& src);
```

And call them from Python with numpy arrays, no manual conversion needed:

```python
import numpy as np
import image_ops

img = np.zeros((480, 640, 3), dtype=np.uint8)

blurred       = image_ops.blur(img, 11)          # numpy array
gray          = image_ops.to_grayscale(img)       # numpy array
w, h          = image_ops.image_size(img)         # tuple
cropped       = image_ops.crop(img, (10, 10, 100, 100))  # rect as tuple
b, g, r, _   = image_ops.mean_color(img)         # scalar as tuple
```

Supported types: `cv::Mat` ↔ `numpy.ndarray`, `cv::Point` / `cv::Size` / `cv::Rect` / `cv::Scalar` ↔ tuple, and their typed variants (`cv::Point2f`, `cv::Rect2d`, etc.).

## How it works

magicbind uses libclang to parse the header into an intermediate representation, generates a nanobind binding file, and compiles everything in a single `zig c++` (or system compiler) invocation. Build artifacts go into `.magicbind/build/` and the compiled extension is installed directly into site-packages.

## Templates

Template functions and classes are not bound directly. Expose concrete overloads in your header:

```cpp
template <typename T>
T clamp(T value, T lo, T hi);

// Expose concrete overloads:
inline int    clamp(int v,    int lo,    int hi)    { return ::clamp(v, lo, hi); }
inline float  clamp(float v,  float lo,  float hi)  { return ::clamp(v, lo, hi); }
inline double clamp(double v, double lo, double hi) { return ::clamp(v, lo, hi); }
```

All three are available in Python as `mylib.clamp`. The right overload is picked automatically based on the argument types.

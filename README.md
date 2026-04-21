# magicbind

[![CI](https://github.com/robomei/magicbind/actions/workflows/ci.yml/badge.svg)](https://github.com/robomei/magicbind/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/magicbind)](https://pypi.org/project/magicbind/)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/magicbind?cacheSeconds=300)](https://pypi.org/project/magicbind/)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

The easy way to speed up Python bottlenecks with C++. No CMake, no build system, no boilerplate. Just point magicbind at your header and it takes care of the rest.

```bash
uv run magicbind add mylib.h
```

magicbind parses the header, generates [nanobind](https://github.com/wjakob/nanobind) glue code, compiles it, and installs the extension into your Python environment.

## Install

```bash
uv add magicbind
```

magicbind uses your system compiler (`g++`, `clang++`, or MSVC) if one is available. If not, it falls back to a bundled Zig compiler via the [ziglang](https://pypi.org/project/ziglang/) package.

## Basic usage

Given a header:

```cpp
// math_utils.h
#include <vector>

inline double sum(const std::vector<double>& values) 
{
    double s = 0;
    for (auto x : values) s += x;
    return s;
}
```

```bash
uv run magicbind add math_utils.h
```

Then use it from Python:

```python
import math_utils

math_utils.sum([1, 2, 3])  # 6.0
```

If the implementation is in a `.cpp` file instead, magicbind auto-detects it. You can also pass sources explicitly:

```bash
uv run magicbind add math_utils.h --source math_utils.cpp
```

## System libraries (optional)

To use a library installed on your system, pass `--pkg` with its pkg-config name:

```bash
uv run magicbind add image_ops.h --pkg opencv4
```

On Linux and macOS you can use `--pkg` to resolve flags automatically via pkg-config. On Windows, pkg-config is not available; use `--include`, `--lib`, and `--link` to specify paths manually:

```bash
uv run magicbind add mylib.h \
  --include C:\mylib\include \
  --lib C:\mylib\lib \
  --link mylib
```

On Windows, magicbind automatically configures the MSVC build environment via `vswhere.exe`. Visual Studio or the standalone [Build Tools](https://aka.ms/vs/stable/vs_BuildTools.exe) must be installed (select the "Desktop development with C++" workload).

## Rebuilding

When you change the header or source, run:

```bash
uv run magicbind build          # rebuilds all modules
uv run magicbind build mylib    # rebuilds one module
```

This replays the original `add` command with the same flags and compiler, without you having to remember them.

## OpenCV

magicbind ships built-in type casters for common OpenCV types:

```cpp
// image_ops.h
#include <opencv2/core.hpp>

cv::Mat blur(const cv::Mat& src, int kernel_size = 5);
cv::Size image_size(const cv::Mat& src);
```

```python
import numpy as np
import image_ops

img = np.zeros((480, 640, 3), dtype=np.uint8)
blurred = image_ops.blur(img, 11)   # numpy array
w, h = image_ops.image_size(img)    # tuple
```

Supported types: `cv::Mat` ↔ `numpy.ndarray`, `cv::Point` / `cv::Size` / `cv::Rect` / `cv::Scalar` ↔ tuple, and their typed variants (`cv::Point2f`, `cv::Rect2d`, etc.).

## Jupyter

Write C++ directly in a notebook cell:

```python
%load_ext magicbind
```

```cpp
%%magicbind math_utils
#include <vector>

double sum(const std::vector<double>& v)
{
    double s = 0;
    for (auto x : v) s += x;
    return s;
}
```

```python
math_utils.sum([1.0, 2.0, 3.0])  # 6.0
```

The module is compiled and imported automatically. Re-running the cell recompiles and reloads. Requires magicbind in your environment.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/robomei/magicbind/blob/main/examples/notebook/magicbind_colab.ipynb)

## How it works

magicbind uses libclang to parse the header into an intermediate representation, generates a nanobind binding file, and compiles it with your system compiler (`g++`, `clang++` or MSVC), falling back to a bundled Zig compiler if none is found. Build artifacts go into `.magicbind/build/` and the compiled extension is installed directly into site-packages.

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

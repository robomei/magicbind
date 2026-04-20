# opencv example

OpenCV integration: `cv::Mat`, `cv::Size`, `cv::Rect`, `cv::Scalar`, `std::vector<cv::Mat>`.

Requires OpenCV installed on your system (`apt install libopencv-dev` or `brew install opencv`).

```bash
uv run magicbind add cpp/image_ops.h --pkg opencv4 --system-compiler
uv run python main.py
```

The `--system-compiler` flag is required because OpenCV is compiled with the system
C++ runtime (libstdc++), which is incompatible with Zig's bundled libc++.

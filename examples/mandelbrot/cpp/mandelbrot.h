#pragma once
#include <vector>

// Renders the Mandelbrot set into a flat row-major array of iteration counts.
// Each value is the number of iterations before escape (0..max_iter).
std::vector<int> mandelbrot(
    double x_min, double x_max,
    double y_min, double y_max,
    int width, int height,
    int max_iter
);

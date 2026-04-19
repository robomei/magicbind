#include "mandelbrot.h"

std::vector<int> mandelbrot(
    double x_min, double x_max,
    double y_min, double y_max,
    int width, int height,
    int max_iter
) {
    std::vector<int> result(width * height);
    double dx = (x_max - x_min) / width;
    double dy = (y_max - y_min) / height;

    for (int row = 0; row < height; ++row) {
        double c_im = y_min + row * dy;
        for (int col = 0; col < width; ++col) {
            double c_re = x_min + col * dx;
            double z_re = 0.0, z_im = 0.0;
            int iter = 0;
            while (z_re * z_re + z_im * z_im <= 4.0 && iter < max_iter) {
                double tmp = z_re * z_re - z_im * z_im + c_re;
                z_im = 2.0 * z_re * z_im + c_im;
                z_re = tmp;
                ++iter;
            }
            result[row * width + col] = iter;
        }
    }
    return result;
}

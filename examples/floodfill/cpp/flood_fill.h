#pragma once
#include <opencv2/core.hpp>

// Flood fill on a grayscale image starting from (y, x).
// Fills all connected pixels within `tolerance` of the seed value with `fill_value`.
cv::Mat flood_fill(const cv::Mat& image, int y, int x, uint8_t fill_value, int tolerance);

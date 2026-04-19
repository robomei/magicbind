#pragma once
#include <opencv2/core.hpp>
#include <vector>

// Returns image dimensions as (width, height)
cv::Size image_size(const cv::Mat& image);

// Crops the image to the given rectangle
cv::Mat crop(const cv::Mat& image, cv::Rect region);

// Mean color of the image as (B, G, R, A)
cv::Scalar mean_color(const cv::Mat& image);

// Draws a filled rectangle with the given color
cv::Mat draw_rect(const cv::Mat& image, cv::Rect region, cv::Scalar color);

// Splits the image into per-channel grayscale images
std::vector<cv::Mat> split_channels(const cv::Mat& image);

// Merges single-channel images into one multi-channel image
cv::Mat merge_channels(const std::vector<cv::Mat>& channels);

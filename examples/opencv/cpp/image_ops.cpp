#include "image_ops.h"
#include <opencv2/imgproc.hpp>

cv::Size image_size(const cv::Mat& image) {
    return image.size();
}

cv::Mat crop(const cv::Mat& image, cv::Rect region) {
    return image(region).clone();
}

cv::Scalar mean_color(const cv::Mat& image) {
    return cv::mean(image);
}

cv::Mat draw_rect(const cv::Mat& image, cv::Rect region, cv::Scalar color) {
    cv::Mat out = image.clone();
    cv::rectangle(out, region, color, cv::FILLED);
    return out;
}

std::vector<cv::Mat> split_channels(const cv::Mat& image) {
    std::vector<cv::Mat> channels;
    cv::split(image, channels);
    return channels;
}

cv::Mat merge_channels(const std::vector<cv::Mat>& channels) {
    cv::Mat out;
    cv::merge(channels, out);
    return out;
}

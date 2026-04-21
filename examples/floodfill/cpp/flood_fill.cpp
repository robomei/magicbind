#include "flood_fill.h"
#include <queue>
#include <cstdlib>

cv::Mat flood_fill(const cv::Mat& image, int y, int x, uint8_t fill_value, int tolerance)
{
    cv::Mat out = image.clone();
    int seed = image.at<uint8_t>(y, x);
    cv::Mat visited = cv::Mat::zeros(image.rows, image.cols, CV_8UC1);

    std::queue<std::pair<int,int>> q;
    q.push({y, x});

    const int dy[] = {1, -1, 0, 0};
    const int dx[] = {0,  0, 1,-1};

    while (!q.empty())
    {
        auto [cy, cx] = q.front(); q.pop();
        if (cy < 0 || cy >= image.rows || cx < 0 || cx >= image.cols) continue;
        if (visited.at<uint8_t>(cy, cx)) continue;
        if (std::abs(static_cast<int>(image.at<uint8_t>(cy, cx)) - seed) > tolerance) continue;

        visited.at<uint8_t>(cy, cx) = 1;
        out.at<uint8_t>(cy, cx) = fill_value;

        for (int d = 0; d < 4; ++d)
            q.push({cy + dy[d], cx + dx[d]});
    }
    return out;
}

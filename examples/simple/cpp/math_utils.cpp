#include "math_utils.h"
#include <algorithm>
#include <numeric>
#include <sstream>

double sum(const std::vector<double>& values) {
    return std::accumulate(values.begin(), values.end(), 0.0);
}

std::optional<double> mean(const std::vector<double>& values) {
    if (values.empty()) return std::nullopt;
    return sum(values) / static_cast<double>(values.size());
}

double clamp(double value, double lo, double hi) {
    return std::clamp(value, lo, hi);
}

std::pair<double, double> minmax(const std::vector<double>& values) {
    auto [mn, mx] = std::minmax_element(values.begin(), values.end());
    return {*mn, *mx};
}

std::string describe(const std::vector<double>& values) {
    if (values.empty()) return "empty";
    std::ostringstream os;
    os << "n=" << values.size() << " sum=" << sum(values) << " mean=" << *mean(values);
    return os.str();
}

std::vector<std::vector<double>> chunk(const std::vector<double>& values, int size) {
    std::vector<std::vector<double>> result;
    for (int i = 0; i < static_cast<int>(values.size()); i += size)
        result.push_back({values.begin() + i,
                          values.begin() + std::min(i + size, static_cast<int>(values.size()))});
    return result;
}

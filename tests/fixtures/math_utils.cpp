#include "math_utils.h"
#include <algorithm>
#include <numeric>
#include <sstream>
#include <stdexcept>

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

std::vector<std::vector<double>> chunk(const std::vector<double>& values, int size) {
    std::vector<std::vector<double>> result;
    for (int i = 0; i < static_cast<int>(values.size()); i += size)
        result.push_back({values.begin() + i, values.begin() + std::min(i + size, static_cast<int>(values.size()))});
    return result;
}

std::string describe(const std::vector<double>& values) {
    if (values.empty()) return "empty";
    std::ostringstream os;
    os << "n=" << values.size() << " sum=" << sum(values) << " mean=" << *mean(values);
    return os.str();
}

std::map<std::string, double> to_map(const std::vector<std::string>& keys, const std::vector<double>& values) {
    std::map<std::string, double> result;
    for (size_t i = 0; i < keys.size() && i < values.size(); ++i)
        result[keys[i]] = values[i];
    return result;
}

double map_sum(const std::map<std::string, double>& m) {
    double s = 0;
    for (const auto& [k, v] : m) s += v;
    return s;
}

int set_size(const std::set<int>& s) {
    return static_cast<int>(s.size());
}

std::set<int> unique_ints(const std::vector<int>& values) {
    return {values.begin(), values.end()};
}

std::array<double, 3> first_three(const std::vector<double>& values) {
    return {values[0], values[1], values[2]};
}

std::variant<int, double, std::string> classify(double value) {
    if (value == static_cast<int>(value)) return static_cast<int>(value);
    if (value < 1000.0) return value;
    return std::string("large");
}

std::complex<double> complex_mul(std::complex<double> a, std::complex<double> b) {
    return a * b;
}

std::unordered_map<std::string, int> count_chars(const std::string& s) {
    std::unordered_map<std::string, int> result;
    for (char c : s)
        result[std::string(1, c)]++;
    return result;
}

std::string file_extension(const std::filesystem::path& p) {
    return p.extension().string();
}

int string_length(std::string_view s) {
    return static_cast<int>(s.size());
}

double safe_divide(double a, double b) {
    if (b == 0.0) throw std::invalid_argument("division by zero");
    return a / b;
}

double get_element(const std::vector<double>& values, int index) {
    return values.at(index);  // throws std::out_of_range
}

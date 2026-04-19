#pragma once
#include <vector>
#include <optional>
#include <string>
#include <map>
#include <unordered_map>
#include <set>
#include <variant>
#include <array>
#include <complex>
#include <unordered_map>
#include <string_view>
#include <filesystem>

double sum(const std::vector<double>& values);
std::optional<double> mean(const std::vector<double>& values);
double clamp(double value, double lo, double hi);
std::pair<double, double> minmax(const std::vector<double>& values);
std::string describe(const std::vector<double>& values);
std::vector<std::vector<double>> chunk(const std::vector<double>& values, int size);
std::map<std::string, double> to_map(const std::vector<std::string>& keys, const std::vector<double>& values);
double map_sum(const std::map<std::string, double>& m);
std::set<int> unique_ints(const std::vector<int>& values);
int set_size(const std::set<int>& s);
std::array<double, 3> first_three(const std::vector<double>& values);
std::variant<int, double, std::string> classify(double value);
std::complex<double> complex_mul(std::complex<double> a, std::complex<double> b);
std::unordered_map<std::string, int> count_chars(const std::string& s);
std::string file_extension(const std::filesystem::path& p);
int string_length(std::string_view s);
double safe_divide(double a, double b);
double get_element(const std::vector<double>& values, int index);

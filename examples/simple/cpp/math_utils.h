#pragma once
#include <vector>
#include <optional>
#include <string>

double sum(const std::vector<double>& values);
std::optional<double> mean(const std::vector<double>& values);
double clamp(double value, double lo, double hi);
std::pair<double, double> minmax(const std::vector<double>& values);
std::string describe(const std::vector<double>& values);
std::vector<std::vector<double>> chunk(const std::vector<double>& values, int size);

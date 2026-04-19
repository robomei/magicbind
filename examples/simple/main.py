import math_utils

data = [3.0, 1.0, 4.0, 1.0, 5.0, 9.0, 2.0, 6.0]

print(math_utils.describe(data))
print("sum:   ", math_utils.sum(data))
print("mean:  ", math_utils.mean(data))
print("minmax:", math_utils.minmax(data))
print("clamp: ", math_utils.clamp(15.0, 0.0, 10.0))
print("chunks:", math_utils.chunk(data, 3))

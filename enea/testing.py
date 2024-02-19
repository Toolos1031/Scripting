e = "1"
dir = {
    "a" : 1,
    "b" : 2,
    "c" : 3,
    "d" : 4,
    e : 5
    }
print(dir)
print(min(dir))

min_dir = min(dir)

min_values = [key for key, value in dir.items() if value == min(dir.values())]
print(min_values[0])
year = 2025
age = int(input("Введіть свій вік "))
birth = year - age
print(birth)
for i in range(age+1):
    print(f"У {birth+i} мені було {i}")
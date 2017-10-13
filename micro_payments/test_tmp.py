

print(data)


address = hex(data & (D160 - 1))
amount = data / D160

print(address, amount)

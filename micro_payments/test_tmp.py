D160 = 2**160

amount = 54391 * 10**18

address = int('0x8ad98b6f7cf894fd1c47eb7e291713742bca0d83', 0)

data = D160 * amount + address

print(data)


address = hex(data & (D160 - 1))
amount = data / D160

print(address, amount)

first_byte = 0
last_bytes = 45678
data_bytes = (first_byte).to_bytes(5, byteorder='little')
data_int = int.from_bytes(data_bytes, byteorder='big') + last_bytes
data_bytes = (data_int).to_bytes(5, byteorder='big')

print(len(data_bytes))
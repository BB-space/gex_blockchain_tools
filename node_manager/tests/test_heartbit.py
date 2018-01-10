class TestHeartbit:

    heartbits = [0,0]
    last_reward = 0
    size = 256
    total_size = size * 2
    days_in_payment = 32
    absent_days = 2

    def __init__(self):
        pass

    def heartbit(self, index):
            if index >= self.total_size and index % self.size == 0:
                self.heartbits[int(index % self.total_size / self.size)] = 0
            self.heartbits[int(index % self.total_size / self.size)] = self.heartbits[int(index % self.total_size / self.size)] \
                                                                    | (1 << (index % self.total_size % self.size))
            if index - self.last_reward >= self.days_in_payment:
                self.last_reward = index
                res = 0
                for j in range(0, self.days_in_payment):
                    #print(bin(self.heartbits[int(index % self.total_size / self.size)]))
                    #print(bin(1 << (index % self.total_size % self.size)))
                    #print(bin(self.heartbits[int(index % self.total_size / self.size)] & (1 << (index % self.total_size % self.size))))
                    print(self.getBit(self.heartbits[int(index % self.total_size / self.size)], (index % self.total_size % self.size)))
                    print(res)
                    if self.heartbits[int(index % self.total_size / self.size)] & (1 * 2 ** (index % self.total_size % self.size)) != 0:
                        res = res + 1
                    if j - res > self.absent_days:
                        res = -1
                        break
                    index = index - 1
                print(res)


    def getBit(self, number, pos):
        return number & 1 * 2 ** pos != 0


    def print(self):
        print(self.heartbits[0])
        print(self.heartbits[1])


test = TestHeartbit()
for i in range(0, 33):
    test.heartbit(i)
#test.print()

'''   
size = 256
arr = [[0] * size, [0] * size]
for i in range(3, size + 3):
    if i >= size*2 and i % size == 0:
        for j in range(0, size):
            arr[int(i % (size * 2) / size)] [j] = 0
    arr[int(i % (size*2) / size)][(i % (size*2)) % size] = 1
print(i)
print(arr[0])
print(arr[1])

i = size + 2 # size + 2
print(i)
res = 0
for j in range(0, 32):
    if arr[int(i % (size * 2) / size)][(i % (size * 2)) % size] == 1:
        res = res+1
    if j-res>2:
        res = -1
        break
    i = i - 1
print(res)
'''
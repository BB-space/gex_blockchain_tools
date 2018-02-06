import binascii

from node_manager.tests.basic import Basic
import socket
import time

class TestNode(Basic):

    def __init__(self):
        super().__init__()

    def test_deposit(self, ip, port, nonce, publicKey):
        type = 0x1
        data = type.to_bytes(1, byteorder='big') + port.to_bytes(4, byteorder='big') + \
               nonce.to_bytes(4, byteorder='big') + socket.inet_aton(ip) + bytearray.fromhex(publicKey)

        #print(data)
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))
        self.getGasUsed(self.token.transact({'from': self.web3.eth.accounts[0]}).transfer(
            self.data['node_manager_address'], 100000000000000000000, data), "node create")

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))


test = TestNode()
hex_str = "f6c5ff277e7a050dcb8083e4952b238fd514a8692f3a25a8c60cd1aa15faaa31c3e40672cc1232e2c95204e106ffc61ea76f53ebb92ae0c05f1a27c8cc3c5fdf"
#test.test_deposit("10.255.255.255", 6000, 12345, hex_str)
time.sleep(300)
#ip, port, status, publicKey, lastRewardDate, leavingDate, startDate = test.contract.call().getNode(0)
#print(test.web3.fromAscii(publicKey)[2:])

'''
print(test.contract.call().getNodeIPs())
id = test.contract.call().getActiveNodeIDs()
print(test.contract.call().getActiveNodeIPs(id))
print(test.contract.call().getNodeIPs())
'''

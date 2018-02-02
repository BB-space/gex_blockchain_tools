from node_manager.tests.basic import Basic


class TestNode(Basic):

    def __init__(self):
        super().__init__()

    def test_deposit(self, ip, port, nonce):
        type = 0x1
        data = type.to_bytes(1, byteorder='big') + port.to_bytes(4, byteorder='big') + \
               nonce.to_bytes(4, byteorder='big') + ip.encode()

        # print(data)

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))
        self.getGasUsed(self.token.transact({'from': self.web3.eth.accounts[0]}).transfer(
            self.data['node_manager_address'], 100000000000000000000, data), "node create")

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))


test = TestNode()
test.test_deposit("10.255.255.255", 6000, 12345)
'''
print(test.contract.call().getNodeIPs())
print(test.contract.call().getNode(2))
id = test.contract.call().getActiveNodeIDs()
print(test.contract.call().getActiveNodeIPs(id))
print(test.contract.call().getNodeIPs())
'''

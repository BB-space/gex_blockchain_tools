from node_manager.tests.basic import Basic


class TestMchain(Basic):

    def __init__(self):
        super().__init__()

    def test_mchain_creation(self, storage_bytes, lifetime, max_nodes, nonce):
        type = 0x10
        data = type.to_bytes(1, byteorder='big') + storage_bytes.to_bytes(32, byteorder='big') + \
               lifetime.to_bytes(32, byteorder='big') + max_nodes.to_bytes(32, byteorder='big') + \
               nonce.to_bytes(4, byteorder='big')

        # print(data)
        # print(self.contract.call().fallbackCreateMchainDataConvert(data))

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))

        self.getGasUsed(self.token.transact({
            'from': self.web3.eth.accounts[0]}).transfer(self.data['node_manager_address'], 100, data), "basic mchain")

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))

    def test_withdraw_mchain(self):
        # self.test_mchain_creation(98764, 1, 12345, 4444)
        # self.test_mchain_creation(98764, 1, 12345, 4444)
        print(test.contract.call().getMchainList())
        print(test.contract.call().getMchain(0))
        print(test.contract.call().getMchain(1))

        self.getGasUsed(self.contract.transact({
            'from': self.web3.eth.accounts[0]}).withdrawFromMchain(0), "withdraw from mchain")

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))

        print(test.contract.call().getMchainList())


test = TestMchain()
'''
print(test.contract.call().getMchainList())
print(test.contract.call().getMchain(0))
print(test.contract.call().getMchain(1))

test.test_withdraw_mchain()
print(test.contract.call().getMchain(0))
print(test.contract.call().getMchain(1))

test.test_mchain_creation(98764, 6000, 12345, 4444) 
test.test_mchain_creation(98764, 6000, 12345, 4444)
test.test_mchain_creation(11111, 55, 2, 5555)
test.test_mchain_creation(222, 155, 24, 53555)
'''
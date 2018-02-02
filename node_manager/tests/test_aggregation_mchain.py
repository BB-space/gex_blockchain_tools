from node_manager.tests.basic import Basic


class TestAggregationMchain(Basic):

    def __init__(self):
        super().__init__()

    def test_aggregation_mchain_creation(self, storage_bytes, lifetime, max_nodes, nonce):
        type = 0x11
        data = type.to_bytes(1, byteorder='big') + storage_bytes.to_bytes(32, byteorder='big') + \
               lifetime.to_bytes(32, byteorder='big') + max_nodes.to_bytes(
            32, byteorder='big') + nonce.to_bytes(4, byteorder='big')

        # print(data)
        # print(self.contract.call().fallbackCreateMchainDataConvert(data))

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))

        self.getGasUsed(self.token.transact({
            'from': self.web3.eth.accounts[0]}).transfer(self.data['node_manager_address'], 100, data),
                        "aggregation mchain")

        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))

    def test_withdraw_mchains(self):
        # self.test_mchain_creation(98764, 1, 12345, 4444)
        print(test.contract.call().getMchains())
        self.getGasUsed(self.contract.transact({
            'from': self.web3.eth.accounts[0]}).withdrawFromMchains(), "withdraw from mchain")
        print(str(self.token.call().balanceOf(self.web3.eth.accounts[0])) + " " + str(
            self.token.call().balanceOf(self.data['node_manager_address'])))
        print(test.contract.call().getMchains())

    def test_add_mchain(self, aggregation_index, basic_index, nonce):
        self.getGasUsed(self.contract.transact({
            'from': self.web3.eth.accounts[0]}).addToAggregationMchain(aggregation_index, basic_index, nonce),
                        "add basic mchain")


test = TestAggregationMchain()
'''
test.test_aggregation_mchain_creation(98764, 6000, 12345, 4444)
test.test_aggregation_mchain_creation(11111, 55, 2, 5555)
test.test_aggregation_mchain_creation(222, 155, 24, 53555)
test.test_add_mchain(1, 1, 53555)
print(test.contract.call().getMchainListFromAggregationMchain(1))
print(test.contract.call().getMchains())
time.sleep(5)
test.test_withdraw_mchains()
'''
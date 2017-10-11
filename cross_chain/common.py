from enum import Enum

# 'gex_to_eth' means that token is transferring from GEX notwork to Ethereum network.
# The same way 'eth_to_gex' corresponds to transfer from Ethereum to GEX.
TransferType = Enum('TransferType', 'gex_to_eth eth_to_gex')

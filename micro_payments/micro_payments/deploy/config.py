FILE_PATH = '../micro_payments/data/data.json'
CHAIN_NAME = 'privtest'
SENDERS = 11
D160 = 2 ** 160
private_keys = []
addresses = []
challenge_period = 1
channel_lifetime = 1
supply = 10000000
token_name = 'Galactic Exchange Token'
token_decimals = 18
token_symbol = 'GEX'
supply *= 10 ** token_decimals
txn_wait = 250
event_wait = txn_wait
signer_key_path = "/tmp/ethereum_dev_mode/keystore/UTC--2017-10-13T07-47-42.456207242Z" \
                  "--f43b2675fc72ce6e48f7063dcf0ee74ad04d40ff"
signer_pass_path = '/tmp/ethereum_dev_mode/keystore/f43b2675fc72ce6e48f7063dcf0ee74ad04d40ff'

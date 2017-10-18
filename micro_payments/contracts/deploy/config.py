FILE_PATH = 'data.json'
CHAIN_NAME = 'privtest'
SENDERS = 3
D160 = 2 ** 160
private_keys = []
addresses = []
challenge_period = 1
channel_lifetime = 1
supply = 10000000
sender_addresses = ['0xe2e429949e97f2e31cd82facd0a7ae38f65e2f38',
                    '0xd1bf222ef7289ae043b723939d86c8a91f3aac3f',
                    '0xE0902284c85A9A03dAA3B5ab032e238cc05CFF9a',
                    '0x0052D7B657553E7f47239d8c4431Fef001A7f99c']
token_name = 'MyToken'
token_decimals = 18
token_symbol = 'TKN'
supply *= 10 ** token_decimals
token_assign = int(supply / (len(sender_addresses) + SENDERS))
txn_wait = 250
event_wait = txn_wait
signer_key_path = "/tmp/ethereum_dev_mode/keystore/UTC--2017-10-13T07-47-42.456207242Z--f43b2675fc72ce6e48f7063dcf0ee74ad04d40ff"
signer_pass_path = '/tmp/ethereum_dev_mode/keystore/f43b2675fc72ce6e48f7063dcf0ee74ad04d40ff'

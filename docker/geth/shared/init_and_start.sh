#!/bin/sh

set -e
set -x

geth --datadir /eth_datadir init /shared/genesis.json
#geth --datadir /eth_datadir  --rpc --rpccorsdomain="*" --rpcapi "admin,debug,miner,shh,txpool,personal,eth,net,web3" --rpcaddr "0.0.0.0" --ws  --wsorigins="*" --wsaddr="0.0.0.0" --wsapi "personal,eth,net,web3" js "/shared/pending_mining.js"
geth --etherbase '0x6870EA70c8582A3C3c778ae719b502e4644fD9dE' --datadir /eth_datadir  --rpc --rpccorsdomain="*" --rpcapi "admin,debug,miner,shh,txpool,personal,eth,net,web3" --rpcaddr "0.0.0.0" --ws  --wsorigins="*" --wsaddr="0.0.0.0" --wsapi "personal,eth,net,web3" --mine

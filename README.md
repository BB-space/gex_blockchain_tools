# gex_blockchain_tools
Base repository with contracts implementation and deployment. 


## Contracts

#### NodeManager

Managment of nodes, mchains, and aggregation mchains. 

Main functions: 

- addToAggregationMchain

- initWithdrawDeposit

- completeWithdrawDeposit

- withdrawFromMchain

- withdrawFromAggregationMchain

- createNode (via GexToken transfer)

- createMchain (via GexToken transfer)

- createAggregationMchain (via GexToken transfer)

#### GexToken

ERC223 token implementation. 

#### GexBot

// TODO

## Deployment

ABI and contract addresses are stored in data.json file.  

#### Truffle

```
sh build.sh 
```

To configure network connections use truffle.js

#### Populus

```
python node_manager/deploy/deploy.py
```

To configure network connections use node_manager/deploy/project.json

To change deployment configuration use node_manager/deploy/config.py

## Contribution

#### Requirements
- web3
- populus

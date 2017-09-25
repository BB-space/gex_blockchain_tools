pragma solidity ^0.4.0;


import './GEXToken.sol';


contract EthContract {

    uint constant QUORUM_MINIMUM = 10;

    GEXToken token;

    struct NodeInfo {
    address addr;
    string ip;
    string pubKey;
    }

    struct BurnRequest {
    address addr;
    uint amount;
    NodeInfo[] nodes;
    uint counter;
    string publicDestructionKey;
    }

    mapping (address => uint) balances;

    mapping (bytes32 => BurnRequest) requests;

    event TokenBurned(bytes32 id);

    function EthContract(GEXToken gexToken){
        token = gexToken;
    }

    function burnRequest(string publicDestructionKey, uint amount)  {
        bytes32 id = keccak256(msg.sender, amount, publicDestructionKey, block.timestamp);
        BurnRequest storage br;
        br.addr = msg.sender;
        br.amount = amount;
        br.publicDestructionKey = publicDestructionKey;
        requests[id] = br;
    }

    function verifySign(string signedKey) private returns (bool){
        //todo
        return true;
    }

    function burn(bytes32 id, string signedKey) payable returns (bool){
        require(requests[id].addr != address(0x0));
        if (requests[id].counter < QUORUM_MINIMUM) {
            if (verifySign(signedKey)) {
                requests[id].counter++;
                if (requests[id].counter == QUORUM_MINIMUM) {
                    balances[requests[id].addr] -= requests[id].amount;
                    TokenBurned(id);
                }
                return true;
            }
        }
        return false;
    }
}

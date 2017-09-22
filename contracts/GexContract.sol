pragma solidity ^0.4.0;


contract GexContract {

    uint constant QUORUM_MINIMUM = 10;

    struct NodeInfo {
    address addr;
    string ip;
    string pubKey;
    }

    struct MintRequest {
    address addr;
    uint amount;
    NodeInfo[] nodes;
    uint counter;
    }

    mapping (bytes32 => MintRequest) requests;

    mapping (address => uint) balances;

    event SearchNodes(bytes32 id);

    event NodesRegistrationFinished(bytes32 id);

    function GexContract(){}

    function mintRequest(uint amount){
        bytes32 id = keccak256(msg.sender, amount, block.timestamp);
        MintRequest storage mr;
        mr.addr = msg.sender;
        mr.amount = amount;
        requests[id] = mr;
        SearchNodes(id);
    }

    function register(bytes32 id, string pubKey, string ip) returns (bool){
        require(requests[id].addr != address(0x0));
        if (requests[id].nodes.length < QUORUM_MINIMUM) {
            if (checkNode(id, pubKey)) {
                requests[id].nodes.push(NodeInfo({
                addr : msg.sender,
                ip : ip,
                pubKey : pubKey
                }));
                if (requests[id].nodes.length == QUORUM_MINIMUM) {
                    NodesRegistrationFinished(id);
                }
                return true;
            }
        }
        return false;
    }

    function checkNode(bytes32 id, string pubKey) private returns (bool){
        return true;
    }

    function mint(bytes32 id){
        require(requests[id].addr != address(0x0));
        if (requests[id].counter < QUORUM_MINIMUM) {
            requests[id].counter++;
            if (requests[id].counter == QUORUM_MINIMUM) {
                //requests[id].addr.transfer(requests[id].amount);
                // import "./SafeMath.sol";
                //safeAdd(balances[requests[id].addr], requests[id].amount);
                balances[requests[id].addr] += requests[id].amount;
            }
        }
    }
}

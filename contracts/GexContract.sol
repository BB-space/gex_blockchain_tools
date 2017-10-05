pragma solidity ^0.4.9;


//import './GEXToken.sol';


contract GexContract {

    uint constant QUORUM_MINIMUM = 10;

    //GEXToken gexToken;

    address token;

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

    function GexContract(address _token){
        //gexToken = GEXToken(_token);
        token = _token;
    }

    function balanceOf(address _owner) constant returns (uint256 balance) {
        return balances[_owner];
    }

    // todo visa versa
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
        //todo
        return true;
    }

    function mint(bytes32 id){
        require(requests[id].addr != address(0x0));
        if (requests[id].counter < QUORUM_MINIMUM) {
            requests[id].counter++;
            if (requests[id].counter == QUORUM_MINIMUM) {
                //requests[id].addr.transfer(requests[id].amount);
                //safeAdd(balances[requests[id].addr], requests[id].amount);
                //balances[requests[id].addr] += requests[id].amount;

                //gexToken.mint(requests[id].addr, requests[id].amount);
                token.call(bytes4(sha3("mint(address _to,uint256 _amount)")), requests[id].addr, requests[id].amount);
                //if (!token.mint(_beneficiary, tokens)) revert();
            }
        }
    }
}

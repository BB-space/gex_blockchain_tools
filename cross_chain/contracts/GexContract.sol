pragma solidity ^0.4.13;


//import './GEXToken.sol';


contract GexContract {

    uint constant QUORUM_MINIMUM = 10;

    //GEXToken gexToken;

    address token;

    // pubKey is a string ?
    //struct Node {
    //address addr;
    //string ip;
    //}

    struct MintRequest {
    address to;
    uint amount;
    bytes32[] validators;
    uint mintCounter;
    uint registerCounter;
    }


    //mapping (string => Node) nodes;
    mapping (bytes32 => bytes32) nodes;

    mapping (bytes32 => MintRequest) requests;

    mapping (address => uint) balances;

    event SearchNodes(bytes32 event_id);

    event NodesRegistrationFinished(bytes32 event_id);

    function GexContract(address _token){
        //gexToken = GEXToken(_token);
        token = _token;
    }

    // todo remove
    function add(bytes32 event_id)  {
        MintRequest mr;
        mr.amount = 110;
        mr.validators.push(event_id);
        mr.validators.push(event_id);
        mr.validators.push(event_id);
        requests[event_id] = mr;
    }

    //public
    function getValidators(bytes32 event_id) constant returns (bytes32[]) {
        // uint len = requests[event_id].validators.length;
        //bytes32[] memory v = new bytes32[](len);

        // for (uint i = 0; i < len; i++) {
        //Person storage person = people[indexes[i]];
        // v[i] = requests[event_id].validators[i];
        //}

        // return v;
        return requests[event_id].validators;
    }

    function getAmount(bytes32 event_id) constant returns (uint) {
        return requests[event_id].amount;
    }

    function getNodeIp(bytes32 validator) constant returns (bytes32) {
        return nodes[validator];
    }

    // todo visa versa
    function mintRequest(uint amount){
        bytes32 event_id = keccak256(msg.sender, amount, block.timestamp);
        MintRequest storage mr;
        mr.to = msg.sender;
        mr.amount = amount;
        requests[event_id] = mr;
        SearchNodes(event_id);
    }

    function register(bytes32 event_id, bytes32 pubKey, bytes32 ip) returns (bool){
        require(requests[event_id].to != address(0x0));
        //if (requests[event_id].registerCounter + 1 < QUORUM_MINIMUM) {
        if (requests[event_id].validators.length < QUORUM_MINIMUM) {
            if (checkNode(event_id, pubKey)) {
                if (nodes[pubKey] == "") {
                    nodes[pubKey] = ip;
                }
                requests[event_id].validators.push(pubKey);
                //requests[event_id].validators[requests[event_id].registerCounter] = pubKey;
                requests[event_id].registerCounter++;
                //Node({
                //addr : msg.sender,
                //ip : ip,
                //pubKey : pubKey
                //}));
                if (requests[event_id].validators.length == QUORUM_MINIMUM) {
                    NodesRegistrationFinished(event_id);
                }
                return true;
            }
        }
        return false;
    }

    function checkNode(bytes32 event_id, bytes32 pubKey) private returns (bool){
        //todo
        return true;
    }

    function mint(bytes32 event_id){
        require(requests[event_id].to != address(0x0));
        if (requests[event_id].mintCounter < QUORUM_MINIMUM) {
            requests[event_id].mintCounter++;
            if (requests[event_id].mintCounter == QUORUM_MINIMUM) {
                //requests[id].addr.transfer(requests[id].amount);
                //safeAdd(balances[requests[id].addr], requests[id].amount);
                //balances[requests[id].addr] += requests[id].amount;

                //gexToken.mint(requests[id].addr, requests[id].amount);
                token.call(bytes4(sha3("mint(address _to,uint256 _amount)")), requests[event_id].to, requests[event_id].amount);
                //if (!token.mint(_beneficiary, tokens)) revert();
            }
        }
    }
}

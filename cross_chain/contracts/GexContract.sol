pragma solidity ^0.4.13;


contract GexContract {

    uint constant QUORUM_MINIMUM = 10;

    address tokenContract;

    struct MintRequest {
    address to;
    uint amount;
    address[] validators;
    uint mintCounter;
    }

    mapping (bytes32 => MintRequest) requests;

    event SearchNodes(bytes32 event_id);

    event NodesRegistrationFinished(bytes32 event_id);

    function GexContract(address _tokenContract){
        tokenContract = _tokenContract;
    }

    function getValidators(bytes32 event_id) constant returns (address[]) {
        return requests[event_id].validators;
    }

    function getAmount(bytes32 event_id) constant returns (uint) {
        return requests[event_id].amount;
    }

    // todo visa versa
    function mintRequest(uint amount){
        bytes32 event_id = keccak256(msg.sender, amount, block.timestamp);
        MintRequest storage mr; // todo do we need storage?
        mr.to = msg.sender;
        mr.amount = amount;
        requests[event_id] = mr;
        SearchNodes(event_id);
    }

    function register(bytes32 event_id) returns (bool){
        if (requests[event_id].validators.length < QUORUM_MINIMUM) {
            if (checkNode(msg.sender)) {
                requests[event_id].validators.push(msg.sender);
                if (requests[event_id].validators.length == QUORUM_MINIMUM) {
                    NodesRegistrationFinished(event_id);
                }
                return true;
            }
        }
        return false;
    }

    function checkNode(address nodeAddress) private returns (bool){
        //todo check that node is registered and move to library
        return true;
    }

    function mint(bytes32 event_id){
        require(requests[event_id].to != address(0x0));
        if (requests[event_id].mintCounter < QUORUM_MINIMUM) {
            requests[event_id].mintCounter++;
            if (requests[event_id].mintCounter == QUORUM_MINIMUM) {
                tokenContract.call(bytes4(sha3("mint(address _to,uint256 _amount)")),
                requests[event_id].to, requests[event_id].amount);
                // todo if (!token.mint(_beneficiary, tokens)) revert();
            }
        }
    }
}

pragma solidity ^0.4.15;


//todo ann require with type everywhere or return 2 types structure
contract EthContract {

    uint constant QUORUM_MINIMUM = 10;

    address tokenContract;

    struct Request {
    address addr;
    uint amount;
    address[] validators;
    uint counter;
    bytes32 publicDestructionKey;
    bool isBurnRequest;
    }

    // todo delete(requests[event_id])
    mapping (bytes32 => Request) requests;

    event TokenBurned(bytes32 event_id);

    function EthContract(address _token){
        tokenContract = _token;
    }

    function isEventPresent(bytes32 _event_id) constant returns (bool) {
        return requests[_event_id].amount != 0;
    }

    function mintRequest(bytes32 _event_id, uint _amount){
        Request request;
        // todo do we need storage or memory?
        request.addr = msg.sender;
        request.amount = _amount;
        request.isBurnRequest = true;
        requests[_event_id] = request;
    }

    function mint(bytes32 _event_id){
        require(!requests[_event_id].isBurnRequest);
        if (requests[_event_id].counter < QUORUM_MINIMUM) {
            requests[_event_id].counter++;
            if (requests[_event_id].counter == QUORUM_MINIMUM) {
                tokenContract.call(bytes4(sha3("mint(address _to,uint256 _amount)")),
                requests[_event_id].addr, requests[_event_id].amount);
                // todo if (!token.mint(_beneficiary, tokens)) revert();
            }
        }
    }

    function burnRequest(bytes32 _event_id, bytes32 _publicDestructionKey, uint _amount)  {
        Request request;
        // todo do we need storage or memory?
        request.addr = msg.sender;
        request.amount = _amount;
        request.publicDestructionKey = _publicDestructionKey;
        request.isBurnRequest = false;
        requests[_event_id] = request;
    }

    function verifySign(string _signedKey) private returns (bool){
        //todo
        return true;
    }

    function burn(bytes32 _event_id, string _signedKey) returns (bool){
        require(requests[_event_id].isBurnRequest);
        if (requests[_event_id].counter < QUORUM_MINIMUM) {
            if (verifySign(_signedKey)) {
                requests[_event_id].counter++;
                if (requests[_event_id].counter == QUORUM_MINIMUM) {
                    tokenContract.call(bytes4(sha3("burn(address _from,uint _amount)")),
                    requests[_event_id].addr, requests[_event_id].amount);
                    TokenBurned(_event_id);
                }
                return true;
            }
        }
        return false;
    }
}

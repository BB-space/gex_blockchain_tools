pragma solidity ^0.4.15;


//todo ann require with type everywhere or return 2 types structure
contract GexContract {

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

    event SearchNodes(bytes32 event_id);

    event NodesRegistrationFinished(bytes32 event_id);

    event TokenBurned(bytes32 event_id);

    function GexContract(address _tokenContract){
        tokenContract = _tokenContract;
    }

    function getValidators(bytes32 _event_id) constant returns (address[]) {
        return requests[_event_id].validators;
    }

    function getAmount(bytes32 _event_id) constant returns (uint) {
        return requests[_event_id].amount;
    }

    function isEventPresent(bytes32 _event_id) constant returns (bool) {
        return requests[_event_id].amount != 0;
    }

    function mintRequest(bytes32 _event_id, uint _amount){
        //bytes32 event_id = keccak256(msg.sender, amount, block.timestamp);
        Request request;
        // todo do we need storage or memory?
        request.addr = msg.sender;
        request.amount = _amount;
        request.isBurnRequest = false;
        requests[_event_id] = request;
        SearchNodes(_event_id);
    }

    function burnRequest(bytes32 _event_id, bytes32 _publicDestructionKey, uint _amount)  {
        Request request;
        // todo do we need storage or memory?
        request.addr = msg.sender;
        request.amount = _amount;
        request.publicDestructionKey = _publicDestructionKey;
        request.isBurnRequest = true;
        requests[_event_id] = request;
        SearchNodes(_event_id);
    }


    function register(bytes32 _event_id) returns (bool){
        // Here we check amount to make sure that the given event is present in mapping.
        // 'amount' filed must be set for the transfer.
        require(requests[_event_id].amount != 0);
        if (requests[_event_id].validators.length < QUORUM_MINIMUM) {
            if (checkNode(msg.sender)) {
                requests[_event_id].validators.push(msg.sender);
                if (requests[_event_id].validators.length == QUORUM_MINIMUM) {
                    NodesRegistrationFinished(_event_id);
                }
                return true;
            }
        }
        return false;
    }

    function checkNode(address _validator) private returns (bool){
        //todo check that node is registered and move to library
        return true;
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

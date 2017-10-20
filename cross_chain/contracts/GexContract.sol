pragma solidity ^0.4.15;


contract GexContract {

    uint8 constant QUORUM_MINIMUM = 10;

    address public token_address;

    struct Request {
    address addr;
    uint amount;
    // todo
    address[] validators;
    address[] checks;
    //
    uint counter;
    bool registration_finished;
    uint block_number;
    }

    mapping (bytes32 => Request) requests;

    event SearchNodes(bytes32 event_id);

    event NodesRegistrationFinished(bytes32 event_id);

    event TokenBurned(bytes32 event_id);

    event EventIDGenerated(
    bytes32 _event_id,
    uint _block_number,
    address _addr,
    uint _amount);

    function GexContract(address _tokenContract){
        token_address = _tokenContract;
    }

    function mintRequest(
    uint _block_number,
    address _addr,
    uint _amount)
    public
    {
        //bytes32 event_id = keccak256(msg.sender, amount, block.timestamp);
        bytes32 event_id = sha3(_block_number, _addr, _amount);
        requests[event_id].addr = _addr;
        requests[event_id].amount = _amount;
        requests[event_id].block_number = _block_number;
        EventIDGenerated(event_id, _block_number, _addr, _amount);
        SearchNodes(event_id);
    }

    function burn(
    bytes32 _event_id,
    uint _block_number,
    address _addr,
    uint _amount)
    public
    {
        // todo check return value
        require(_amount > 0);
        bytes32 event_id = sha3(_block_number, _addr, _amount);
        // todo
        require(event_id == _event_id);
        requests[event_id].addr = _addr;
        requests[event_id].amount = _amount;
        requests[event_id].block_number = _block_number;
        token_address.call(bytes4(sha3("burn(address _from,uint _amount)")),
        requests[_event_id].addr, requests[_event_id].amount);
        TokenBurned(_event_id);
    }

    function register(bytes32 _event_id) public {
        require(requests[_event_id].amount != 0);
        require(!requests[_event_id].registration_finished);
        if (checkNode(msg.sender)) {
            requests[_event_id].validators.push(msg.sender);
            if (requests[_event_id].validators.length == QUORUM_MINIMUM) {
                NodesRegistrationFinished(_event_id);
                requests[_event_id].registration_finished = true;
            }

        }
    }

    function checkNode(address _validator) private returns (bool){
        //todo check that node is registered and move to library
        return _validator != 0;
    }

    function mint(bytes32 _event_id) public {
        require(requests[_event_id].registration_finished);
        if (requests[_event_id].counter < QUORUM_MINIMUM) {
            // todo rewrite
            for (uint i = 0; i < requests[_event_id].validators.length; i++) {
                if (requests[_event_id].validators[i] == msg.sender) {
                    for (uint j = 0; j < requests[_event_id].checks.length; j++) {
                        if (requests[_event_id].checks[j] == msg.sender) {
                            return;
                        }
                    }
                    requests[_event_id].counter++;
                    if (requests[_event_id].counter == QUORUM_MINIMUM) {
                        token_address.call(bytes4(sha3("mint(address _to,uint256 _amount)")),
                        requests[_event_id].addr, requests[_event_id].amount);
                        delete requests[_event_id];
                        // todo if (!token.mint(_beneficiary, tokens)) revert();
                    }
                    break;
                }
            }
        }
    }
}

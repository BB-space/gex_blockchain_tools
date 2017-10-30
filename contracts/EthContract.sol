pragma solidity ^0.4.15;


contract EthContract {

    uint8 constant QUORUM_MINIMUM = 2; // TODO make 10

    address public token_address;

    struct Request {
    address addr_to;
    address addr_from;
    uint256 amount;
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

    event TokenMinted(bytes32 event_id);

    event GasCost(
    string _function_name,
    uint _gaslimit,
    uint _gas_remaining);


    function EthContract(address _tokenContract){
        token_address = _tokenContract;
    }

    function generateEventID(
    uint _block_number,
    address _addr_from,
    address _addr_to,
    uint256 _amount)
    returns (bytes32){
        //bytes32 event_id = keccak256(msg.sender, amount, block.timestamp);
        return sha3(_block_number, _addr_from, _addr_to, _amount);
    }

    // 84172 gas
    function mintRequest(
    uint _block_number,
    address _addr_from,
    address _addr_to,
    uint256 _amount)
    public
    {
        GasCost('mintRequest start', block.gaslimit, msg.gas);
        bytes32 event_id = generateEventID(_block_number, _addr_from, _addr_to, _amount);
        requests[event_id].block_number = _block_number;
        requests[event_id].addr_from = _addr_from;
        requests[event_id].addr_to = _addr_to;
        requests[event_id].amount = _amount;
        SearchNodes(event_id);
        GasCost('mintRequest end', block.gaslimit, msg.gas);
    }

    // 113719 gas
    function burn(
    bytes32 _event_id,
    uint _block_number,
    address _addr_from,
    address _addr_to,
    uint256 _amount)
    public
    {
        GasCost('burn start', block.gaslimit, msg.gas);
        // todo check return value
        require(_amount > 0);
        bytes32 event_id = generateEventID(_block_number, _addr_from, _addr_to, _amount);
        // todo
        require(event_id == _event_id);
        requests[event_id].addr_from = _addr_from;
        requests[event_id].addr_to = _addr_to;
        requests[event_id].amount = _amount;
        requests[event_id].block_number = _block_number;
        token_address.call(bytes4(sha3("burn(address,uint256)")), _addr_from, _amount);
        TokenBurned(_event_id);
        GasCost('burn end', block.gaslimit, msg.gas);
    }

    // 65717 gas
    function register(bytes32 _event_id) public {
        GasCost('register start', block.gaslimit, msg.gas);
        require(requests[_event_id].amount != 0);
        require(!requests[_event_id].registration_finished);
        if (checkNode(msg.sender)) {
            requests[_event_id].validators.push(msg.sender);
            if (requests[_event_id].validators.length == QUORUM_MINIMUM) {
                NodesRegistrationFinished(_event_id);
                requests[_event_id].registration_finished = true;
            }

        }
        GasCost('register end', block.gaslimit, msg.gas);
    }

    function checkNode(address _validator) private returns (bool){
        //todo check that node is registered and move to library
        return _validator != 0;
    }

    // mint for 1 node 117209 gas
    function mint(bytes32 _event_id) public {
        GasCost('mint start', block.gaslimit, msg.gas);
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
                        token_address.call(bytes4(sha3("mint(address,uint256)")),
                        requests[_event_id].addr_to, requests[_event_id].amount);
                        TokenMinted(_event_id);
                        delete requests[_event_id];
                        // todo if (!token.mint(_beneficiary, tokens)) revert();
                    }
                    break;
                }
            }
        }
        GasCost('mint end', block.gaslimit, msg.gas);
    }
}

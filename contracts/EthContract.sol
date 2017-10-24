pragma solidity ^0.4.15;


contract EthContract {

    uint8 constant QUORUM_MINIMUM = 2; // TODO make 10

    address public token_address;

    struct Request {
    address addr_to;
    address addr_from;
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

    event TokenMinted(bytes32 event_id);

    event Test3();

    event Test4(bytes32 event_id, uint counter);

    event Test5();

    event Test6();

    function EthContract(address _tokenContract){
        token_address = _tokenContract;
    }

    function mintRequest(
    uint _block_number,
    address _addr_from,
    address _addr_to,
    uint _amount)
    public
    {
        //bytes32 event_id = keccak256(msg.sender, amount, block.timestamp);
        bytes32 event_id = sha3(_block_number, _addr_from, _addr_to, _amount);
        requests[event_id].block_number = _block_number;
        requests[event_id].addr_from = _addr_from;
        requests[event_id].addr_to = _addr_to;
        requests[event_id].amount = _amount;
        SearchNodes(event_id);
    }

    function burn(
    bytes32 _event_id,
    uint _block_number,
    address _addr_from,
    address _addr_to,
    uint _amount)
    public
    {
        // todo check return value
        require(_amount > 0);
        bytes32 event_id = sha3(_block_number, _addr_from, _addr_to, _amount);
        // todo
        require(event_id == _event_id);
        requests[event_id].addr_from = _addr_from;
        requests[event_id].addr_to = _addr_to;
        requests[event_id].amount = _amount;
        requests[event_id].block_number = _block_number;
        token_address.call(bytes4(sha3("burn(address,uint)")), requests[_event_id].addr_from, requests[_event_id].amount);
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

    function f() public {
        token_address.call(bytes4(sha3("t()")));
    }

    function mintTest(address addr) public {
        token_address.call(bytes4(sha3("mint(address,uint)")), addr, 10);
    }

    function mint(bytes32 _event_id) public {
        require(requests[_event_id].registration_finished);
        if (requests[_event_id].counter < QUORUM_MINIMUM) {
            Test3();
            // todo rewrite
            for (uint i = 0; i < requests[_event_id].validators.length; i++) {
                if (requests[_event_id].validators[i] == msg.sender) {
                    for (uint j = 0; j < requests[_event_id].checks.length; j++) {
                        if (requests[_event_id].checks[j] == msg.sender) {
                            return;
                        }
                    }
                    requests[_event_id].counter++;
                    Test4(_event_id, requests[_event_id].counter);
                    if (requests[_event_id].counter == QUORUM_MINIMUM) {
                        Test5();
                        token_address.call(bytes4(sha3("mint(address,uint)")),
                        requests[_event_id].addr_to, requests[_event_id].amount);
                        Test6();
                        TokenMinted(_event_id);
                        delete requests[_event_id];
                        // todo if (!token.mint(_beneficiary, tokens)) revert();
                    }
                    break;
                }
            }
        }
    }
}

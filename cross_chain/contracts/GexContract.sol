pragma solidity ^0.4.15;


contract GexContract {

    uint constant QUORUM_MINIMUM = 10;

    address tokenContract;

    struct MintRequest {
    address to;
    uint amount;
    address[] validators;
    uint mintCounter;
    }

    struct BurnRequest {
    address from;
    uint amount;
    address[] validators;
    uint burnCounter;
    bytes32 publicDestructionKey;
    }

    // todo delete(requests[event_id])
    mapping (bytes32 => MintRequest) mintRequests;

    mapping (bytes32 => BurnRequest) burnRequests;

    event SearchNodes(bytes32 event_id);

    event NodesRegistrationFinished(bytes32 event_id);

    event TokenBurned(bytes32 event_id);

    function GexContract(address _tokenContract){
        tokenContract = _tokenContract;
    }

    function getValidators(bytes32 _event_id) constant returns (address[]) {
        return mintRequests[_event_id].validators;
    }

    function getAmount(bytes32 _event_id) constant returns (uint) {
        return mintRequests[_event_id].amount;
    }

    function mintRequest(bytes32 _event_id, uint _amount){
        //bytes32 event_id = keccak256(msg.sender, amount, block.timestamp);
        MintRequest mr;
        // todo do we need storage or memory?
        mr.to = msg.sender;
        mr.amount = _amount;
        mintRequests[_event_id] = mr;
        SearchNodes(_event_id);
    }

    function burnRequest(bytes32 _event_id, bytes32 _publicDestructionKey, uint _amount)  {
        BurnRequest br;
        // todo do we need storage or memory?
        br.from = msg.sender;
        br.amount = _amount;
        br.publicDestructionKey = _publicDestructionKey;
        burnRequests[_event_id] = br;
        SearchNodes(_event_id);
    }


    function register(bytes32 _event_id) returns (bool){
        if (mintRequests[_event_id] != '') {
            if (mintRequests[_event_id].validators.length < QUORUM_MINIMUM) {
                if (checkNode(msg.sender)) {
                    mintRequests[_event_id].validators.push(msg.sender);
                    if (mintRequests[_event_id].validators.length == QUORUM_MINIMUM) {
                        NodesRegistrationFinished(_event_id);
                    }
                    return true;
                }
            }
        }
        else if (burnRequests[_event_id] != '') {
            if (burnRequests[_event_id].validators.length < QUORUM_MINIMUM) {
                if (checkNode(msg.sender)) {
                    burnRequests[_event_id].validators.push(msg.sender);
                    if (burnRequests[_event_id].validators.length == QUORUM_MINIMUM) {
                        NodesRegistrationFinished(_event_id);
                    }
                    return true;
                }
            }
        }
        return false;
    }

    function checkNode(address _validator) private returns (bool){
        //todo check that node is registered and move to library
        return true;
    }

    function mint(bytes32 _event_id){
        if (mintRequests[_event_id].mintCounter < QUORUM_MINIMUM) {
            mintRequests[_event_id].mintCounter++;
            if (mintRequests[_event_id].mintCounter == QUORUM_MINIMUM) {
                tokenContract.call(bytes4(sha3("mint(address _to,uint256 _amount)")),
                mintRequests[_event_id].to, mintRequests[_event_id].amount);
                // todo if (!token.mint(_beneficiary, tokens)) revert();
            }
        }
    }

    function verifySign(string _signedKey) private returns (bool){
        //todo
        return true;
    }

    function burn(bytes32 _event_id, string _signedKey) returns (bool){
        if (burnRequests[_event_id].burnCounter < QUORUM_MINIMUM) {
            if (verifySign(_signedKey)) {
                burnRequests[_event_id].burnCounter++;
                if (burnRequests[_event_id].burnCounter == QUORUM_MINIMUM) {
                    tokenContract.call(bytes4(sha3("burn(address _from,uint _amount)")),
                    burnRequests[_event_id].from, burnRequests[_event_id].amount);
                    TokenBurned(_event_id);
                }
                return true;
            }
        }
        return false;
    }
}

pragma solidity ^0.4.15;


contract EthContract {

    uint constant QUORUM_MINIMUM = 10;

    address tokenContract;

    struct MintRequest {
    address to;
    uint amount;
    uint mintCounter;
    }

    struct BurnRequest {
    address from;
    uint amount;
    uint burnCounter;
    bytes32 publicDestructionKey;
    }

    // todo delete(requests[event_id])
    mapping (bytes32 => MintRequest) mintRequests;

    mapping (bytes32 => BurnRequest) burnRequests;

    event TokenBurned(bytes32 event_id);

    function EthContract(address _token){
        tokenContract = _token;
    }

    function mintRequest(bytes32 _event_id, uint _amount){
        MintRequest mr;
        // todo do we need storage or memory?
        mr.to = msg.sender;
        mr.amount = _amount;
        mintRequests[_event_id] = mr;
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

    function burnRequest(bytes32 _event_id, bytes32 _publicDestructionKey, uint _amount)  {
        BurnRequest br;
        // todo do we need storage or memory?
        br.from = msg.sender;
        br.amount = _amount;
        br.publicDestructionKey = _publicDestructionKey;
        burnRequests[_event_id] = br;
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

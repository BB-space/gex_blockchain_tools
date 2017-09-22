pragma solidity ^0.4.0;


contract EthContract {

    mapping (address => uint) balances;

    event TokenBurned();

    function EthContract(){}

    function burnRequest(string publicDestructionKey) payable {
        balances[msg.sender] += msg.value;
    }

    function burn(){
        TokenBurned();
    }
}

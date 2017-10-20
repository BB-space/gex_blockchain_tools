pragma solidity ^0.4.0;


contract Test {
    function Test(){}

    function sha(uint block_number, address addr, uint amount) returns (bytes32 result){
        return sha3(block_number, addr, amount);
    }

    function compute_sha(bytes input) returns (bytes32 result) {
        return sha3(input);
    }

    function sha_args(bytes input, bytes extra) returns (bytes32 result) {
        return sha3(input, extra);
    }

}

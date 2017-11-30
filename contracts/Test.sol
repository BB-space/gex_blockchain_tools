pragma solidity ^0.4.0;


contract Test {
    uint l = 0;
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

    function checkk(uint i) returns (uint) {
        require(i == 1);
        return 2;
    }

    function getl() returns (uint) {
        return l;
    }

    function check(uint i) {
        require(i == 1);
        l=i;
    }
}
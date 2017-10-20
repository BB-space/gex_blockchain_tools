pragma solidity ^0.4.0;


contract Test {
    function Test(){}

    event GetSha(bytes32 event_id);


    function sha(bytes message){
        GetSha(sha3(message));
    }

    function compute_sha(bytes input) returns (bytes32 result) {
        return sha3(input);
    }

    function sha_args(bytes input, bytes extra) returns (bytes32 result) {
        return sha3(input, extra);
    }

}

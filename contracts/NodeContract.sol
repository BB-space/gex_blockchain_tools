pragma solidity ^0.4.15;


contract NodeContract {
    mapping (address => NodeInfo) nodes;

    struct NodeInfo {
    address publicChainAddr;
    bytes32 ip;
    uint256 reputation;
    bytes32 publicKey;
    }

    function NodeContract(){
    }

    function addNode(address _publicChainAddr, bytes32 _ip, uint256 _reputation, bytes32 _publicKey){
        nodes[msg.sender] = NodeInfo(_publicChainAddr, _ip, _reputation, _publicKey);
    }

    function getPublicChainAddr(address nodeAddr) constant returns (address) {
        return nodes[nodeAddr].publicChainAddr;
    }

    function getIp(address nodeAddr) constant returns (bytes32) {
        return nodes[nodeAddr].ip;
    }

    function getReputation(address nodeAddr) constant returns (uint256) {
        return nodes[nodeAddr].reputation;
    }

    function getPublicKey(address nodeAddr) constant returns (bytes32) {
        return nodes[nodeAddr].publicKey;
    }

}

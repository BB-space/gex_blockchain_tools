pragma solidity ^0.4.15;


contract NodeManager {

    address public tokenAddress;

    uint public constant depositValue = 100 * 10 ** 18; // todo rewrite coins
    uint constant leavingPeriod = 5260000; // 2 month. 3 month will be 7890000
    uint constant paymentPeriod = 2764800; // 32*60*60*24

    uint startEpoch;
    uint256 annualMint;
    uint256 dailyMint;

    enum NodeStatus {Active, Leaving, Left} // todo another names

    struct Node {
        uint256 deposit;
        bytes32 ip; // todo uint128 ?
        uint16 port; // todo The port number is an unsigned 16-bit integer, so 65535. https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers
        uint depositDate;
        uint leavingDate;
        uint lastRewardDate;
        uint256[2] heartbits;
        NodeStatus status;
    }

    struct BasicChannel {
        address owner;
        uint256 storageBytes;
        uint lifetime;
        uint startTime;
        uint maxNodes;
    }

    struct AggregationChannel {
        address owner;
        uint256 storageBytes;
        uint lifetime;
        uint startTime;
        uint maxNodes;
        mapping (uint256 => bool) basicChannels;
        uint nextAggregatedBasicChannelIndex;
    }

    mapping (uint256 => Node) nodes;

    mapping (uint256 => BasicChannel) basicChannel;

    mapping (uint256 => AggregationChannel) aggregationChannel;

    mapping (address => mapping (uint256 => bool)) nodeIndexes;

    uint256 nextNodeIndex;

    uint256 nextBasicChannelIndex;

    uint256 nextAggregationChannelIndex;

    event NodeCreated(
        uint256 nodeId,
        bytes32 ip,
        uint16 port,
        uint nonce
    );

    event BasicChannelCreated(
        uint256 channelID,
        address owner,
        uint256 storageBytes,
        uint lifetime,
        uint maxNodes,
        uint nonce
    );

    event AggregationChannelCreated(
        uint256 channelID,
        address owner,
        uint256 storageBytes,
        uint lifetime,
        uint maxNodes,
        uint nonce
    );

    event BasicChannelAdded(
        uint256 aggregationChannelID,
        uint256 basicChannelID,
        uint nonce
    );

    //owner
    function NodeManager(address token, uint256 mintValue) {
        tokenAddress = token;
        startEpoch = block.timestamp;
        annualMint = mintValue;
        dailyMint = annualMint / 365; // todo rewrite
    }

    /*
    // user should run approve before call deposit method
    function deposit(bytes32 ip, uint16 port, uint nonce) public {
        require (ip != 0x0); // todo another checks
        require (port > 0);
        nodes[nextNodeIndex].ip = ip;
        nodes[nextNodeIndex].port = port;
        nodes[nextNodeIndex].deposit = depositValue;
        nodes[nextNodeIndex].status = NodeStatus.Active;
        nodes[nextNodeIndex].lastRewardDate = block.timestamp;
        nodes[nextNodeIndex].depositDate = block.timestamp;
        nodeIndexes[msg.sender][nextNodeIndex] = true;
        NodeCreated(nextNodeIndex, ip, port, nonce);
        nextNodeIndex = nextNodeIndex + 1;
        // todo test
        tokenAddress.call(bytes4(sha3("transferFrom(address, address, uint256)")), msg.sender, this, depositValue);
    }

*/
    // use should call transfer to make a deposit.
    function tokenFallback(address sender, uint256 value, bytes data) public {
        require(msg.sender == tokenAddress);
        require(value == depositValue);
        require (ip != 0x0); // todo another checks
        require (port > 0);
        // todo get ip, port, nonce from the data filed
        nodes[nextNodeIndex].ip = ip;
        nodes[nextNodeIndex].port = port;
        nodes[nextNodeIndex].deposit = depositValue;
        nodes[nextNodeIndex].status = NodeStatus.Active;
        nodes[nextNodeIndex].lastRewardDate = block.timestamp;
        nodes[nextNodeIndex].depositDate = block.timestamp;
        nodeIndexes[msg.sender][nextNodeIndex] = true;
        NodeCreated(nextNodeIndex, ip, port, nonce);
        nextNodeIndex = nextNodeIndex + 1;
    }



    // add nonce
    function createBasicChannel(
        address owner,
        uint256 storageBytes,
        uint lifetime, uint maxNodes, uint nonce
    )
    public
    {
        basicChannel[nextBasicChannelIndex].owner = owner;
        basicChannel[nextBasicChannelIndex].storageBytes = storageBytes;
        basicChannel[nextBasicChannelIndex].lifetime = lifetime;
        basicChannel[nextBasicChannelIndex].maxNodes = maxNodes;
        basicChannel[nextBasicChannelIndex].startTime = block.timestamp;
        BasicChannelCreated(nextBasicChannelIndex, owner, storageBytes, lifetime, maxNodes, nonce);
        nextBasicChannelIndex = nextBasicChannelIndex + 1;
    }

    // add nonce
    function createAggregationChannel(
        address owner,
        uint256 storageBytes,
        uint lifetime,
        uint maxNodes,
        uint nonce
    )
    public
    {
        aggregationChannel[nextAggregationChannelIndex].owner = owner;
        aggregationChannel[nextAggregationChannelIndex].storageBytes = storageBytes;
        aggregationChannel[nextAggregationChannelIndex].lifetime = lifetime;
        aggregationChannel[nextAggregationChannelIndex].maxNodes = maxNodes;
        aggregationChannel[nextAggregationChannelIndex].startTime = block.timestamp;
        AggregationChannelCreated(nextAggregationChannelIndex, owner, storageBytes, lifetime, maxNodes, nonce);
        nextAggregationChannelIndex = nextAggregationChannelIndex + 1;
    }

    function addToAggregationChannel(uint256 aggregationChannelID, uint256 basicChannelID, uint nonce){
        // basic channel should be present
        require(aggregationChannel[basicChannelID].owner != address(0));
        // aggregation channel should be present
        require(aggregationChannel[aggregationChannelID].owner != address(0));
        // aggregation channel must be alive
        require((aggregationChannel[aggregationChannelID].startTime +
              aggregationChannel[aggregationChannelID].lifetime) > block.timestamp);
        // basic channel must be alive
        require((basicChannel[basicChannelID].startTime + basicChannel[basicChannelID].lifetime) > block.timestamp);
        // basic channel must expire before aggregation channel
        require((basicChannel[basicChannelID].startTime + basicChannel[basicChannelID].lifetime) <
               (aggregationChannel[aggregationChannelID].startTime + aggregationChannel[aggregationChannelID].lifetime));
        // check that basic channel is not present in the aggregation channel already
        require(!aggregationChannel[aggregationChannelID].basicChannels[basicChannelID]);
        aggregationChannel[aggregationChannelID].basicChannels[basicChannelID] = true;
        aggregationChannel[aggregationChannelID].nextAggregatedBasicChannelIndex += 1;
        BasicChannelAdded(aggregationChannelID, basicChannelID, nonce);
    }

    function initWithdrawDeposit(uint256 nodeNumber) public {
        require(nodeIndexes[msg.sender][nodeNumber]);
        require(nodes[nodeNumber].status == NodeStatus.Active);
        nodes[nodeNumber].status = NodeStatus.Leaving;
        nodes[nodeNumber].leavingDate = block.timestamp;
    }

    function completeWithdrawDeposit(uint256 nodeNumber) public {
        require(nodeIndexes[msg.sender][nodeNumber]);
        require(nodes[nodeNumber].status == NodeStatus.Leaving);
        require(block.timestamp - nodes[nodeNumber].leavingDate >= leavingPeriod);
        nodes[nodeNumber].deposit = 0;
        nodes[nodeNumber].status = NodeStatus.Left;
        tokenAddress.call(bytes4(sha3("transfer(address, uint256)")), msg.sender, depositValue);
    }

    function getNodeIPs() public returns (bytes32[]) {
        bytes32[] arr;
        uint j = 0;
        for (uint i = 0; i < nextNodeIndex; i++) {
            if(nodes[i].status == NodeStatus.Active){
                arr[j] = nodes[i].ip;
                j++;
            }
        }
        return arr;
    }

    function getActiveNodesCount() internal returns (uint) {
        uint activeNodes = 0;
        for (uint i = 0; i < nextNodeIndex; i++) {
            if(nodes[i].status == NodeStatus.Active){
                activeNodes++;
            }
        }
        return activeNodes;
    }

    function heartbit(uint256 nodeNumber) public {
        require(nodeIndexes[msg.sender][nodeNumber]);
        uint index = (block.timestamp - startEpoch) / 86400 - 1;  // 24*60*60
        if (index >= 256 * 2 && index % 256 == 0) {
            nodes[nodeNumber].heartbits[int(index % (256 * 2) / 256)] = 0;
        }
        nodes[nodeNumber].heartbits[int(index % (256 * 2) / 256)] =
            nodes[nextNodeIndex].heartbits[int(index % (256 * 2) / 256)] | (1 << (index % (256 * 2) % 256)); // bitwise_or
        // reward
        if (block.timestamp - nodes[nextNodeIndex].lastRewardDate >= paymentPeriod){
            // todo check the last 32 days
            nodes[nextNodeIndex].lastRewardDate = block.timestamp;
            tokenAddress.call(bytes4(sha3("transfer(address, uint256)")),
                msg.sender, dailyMint / getActiveNodesCount());
        }
    }

       // todo uint256
    function getBit(bytes1 a, uint8 n) returns (bool) {
        return a & shiftLeft(0x01, n) != 0;
    }

    function shiftLeft(bytes1 a, uint8 n) returns (bytes1) {
        var shifted = uint8(a) * 2 ** n;
        return bytes1(shifted);
    }
}
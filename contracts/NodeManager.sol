pragma solidity ^0.4.15;

/// @title Node Manager contract
contract NodeManager {

    enum NodeStatus {Active, Leaving, Left}

    uint constant secondsToDay = 86400; // utility variable for time conversion
    // 60 days in seconds. Time period after which user can withdraw node deposit and leave the system
    uint constant leavingPeriod = 5260000;
    // min term in which node can be rewarded for it's contribution
    uint constant paymentDays = 32;
    // paymentDays days in seconds
    uint constant paymentPeriod = paymentDays * secondsToDay;
    // permitted number of days node may not send the heartbit during the paymentPeriod
    uint constant absentDays = 2;
    uint constant heartbitUnit = 256;
    uint constant heartbitTotal = heartbitUnit * 2;

    address tokenAddress; // address of the token contract
    uint256 annualMint; // total reword for nodes per year
    uint256 dailyMint; // daily reword for nodes
    uint depositValue; // size of a deposit to add node to the system

    struct Node {
        uint256 deposit; // todo do we need this variable at all?
        bytes15 ip; // todo use another type
        uint16 port; // todo The port number is an unsigned 16-bit integer, so 65535. https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers
        uint depositDate; // todo do we need this variable at all?
        uint leavingDate; // date when node was moved to the Leaving state
        uint lastRewardDate; // date when node was rewarded last time
        uint256[2] heartbits; // bitmap of heartbit signals for last 512 days
        NodeStatus status;
    }

    struct BasicChannel {
        address owner; // channel owner
        uint256 storageBytes; // number of bytes this channel can store
        uint lifetime;  // number seconds this channel will be considered as alive
        uint startDate; // date of channel creation
        uint maxNodes; // max number of nodes associated with this channel
        uint256 deposit; // value of tokens associated with this channel
    }

    struct AggregationChannel {
        address owner; // channel owner
        uint256 storageBytes; // number of bytes this channel can store
        uint lifetime;  // number seconds this channel will be considered as alive
        uint startDate; // date of channel creation
        uint maxNodes; // max number of nodes associated with this channel
        uint256 deposit; // value of tokens associated with this channel
        mapping (uint256 => bool) basicChannels; // basic channels aggregated by this channel
        uint nextAggregatedBasicChannelIndex; // index to store next basic channel
    }

    // mapping of node index to a node instance
    mapping (uint256 => Node) nodes;
    // mapping of a basic channel index to a basic channel instance
    mapping (uint256 => BasicChannel) basicChannel;
    // mapping of an aggregation channel index to a aggregation channel instance
    mapping (uint256 => AggregationChannel) aggregationChannel;
    // mapping of owner address to node indexes associated with it
    mapping (address => mapping (uint256 => bool)) nodeIndexes; // todo set struct here. list?? do the same as with channels
    // mapping of owner address to basic channel indexes associated with it
    mapping (address => uint256[]) basicChannelIndexes;
    // mapping of owner address to aggregation channel indexes associated with it
    mapping (address => uint256[]) aggregationChannelIndexes;
    // index to store next node
    uint256 nextNodeIndex;
    // index to store next basic channel
    uint256 nextBasicChannelIndex;
    // index to store next aggregation channel
    uint256 nextAggregationChannelIndex;

    event NodeCreated(
        uint256 nodeId,
        bytes15 ip,
        uint16 port,
        uint16 nonce
    );

    // todo add deposit
    event BasicChannelCreated(
        uint256 channelID,
        address owner,
        uint256 storageBytes,
        uint lifetime,
        uint maxNodes,
        uint16 nonce
    );

     // todo add deposit
    event AggregationChannelCreated(
        uint256 channelID,
        address owner,
        uint256 storageBytes,
        uint lifetime,
        uint maxNodes,
        uint16 nonce
    );

    event BasicChannelAdded(
        uint256 aggregationChannelID,
        uint256 basicChannelID,
        uint16 nonce
    );


    // todo owner
    function NodeManager(address token, uint256 mintValue) {
        tokenAddress = token;
        annualMint = mintValue;
        dailyMint = annualMint / 365; // todo rewrite
        // todo check
        nextNodeIndex = 1;
        nextBasicChannelIndex = 1;
        nextAggregationChannelIndex = 1;
        depositValue = 100; // todo change 100 * 10 ** 18
    }

    function getTime() public returns (uint) {
        return block.timestamp;
    }

    // use should call transfer to make a deposit
    function tokenFallback(address sender, uint256 value, bytes data) public {
        require(msg.sender == tokenAddress);
        require(value == depositValue);
        uint16 port;
        uint16 nonce;
        bytes15 ip;
        (port, nonce, ip) = fallbackDataConvert(data);
        // todo add unique ip check
        require (ip != 0x0); // todo another checks
        require (port > 0);
        nodes[nextNodeIndex].ip = ip;
        nodes[nextNodeIndex].port = port;
        nodes[nextNodeIndex].deposit = depositValue;
        nodes[nextNodeIndex].status = NodeStatus.Active;
        nodes[nextNodeIndex].lastRewardDate = block.timestamp;
        nodes[nextNodeIndex].depositDate = block.timestamp;
        nodeIndexes[msg.sender][nextNodeIndex] = true;
        NodeCreated(nextNodeIndex, ip, port, nonce); // todo return owner
        nextNodeIndex = nextNodeIndex + 1;
    }


    function fallbackDataConvert(
        bytes b)
        //internal
        constant
        returns (uint16, uint16, bytes15)
    {
        bytes15 ip;
        bytes4 port;
        bytes4 nonce;
        assembly {
            port := mload(add(b, 0x20))
            nonce := mload(add(b, 0x24))
            ip := mload(add(b, 0x28))
        }
        return (uint16(port),uint16(nonce),ip);
    }

    // todo add to tokenFallback
    function createBasicChannel(
        uint256 storageBytes,
        uint lifetime,
        uint maxNodes,
        uint16 nonce,
        uint256 deposit
    )
    public
    {
        basicChannel[nextBasicChannelIndex].owner = msg.sender;
        basicChannel[nextBasicChannelIndex].storageBytes = storageBytes;
        basicChannel[nextBasicChannelIndex].lifetime = lifetime;
        basicChannel[nextBasicChannelIndex].maxNodes = maxNodes;
        basicChannel[nextBasicChannelIndex].startDate = block.timestamp;
        basicChannel[nextBasicChannelIndex].deposit = deposit;
        basicChannelIndexes[msg.sender].push(nextBasicChannelIndex);
        BasicChannelCreated(nextBasicChannelIndex, msg.sender, storageBytes, lifetime, maxNodes, nonce);
        nextBasicChannelIndex = nextBasicChannelIndex + 1;
    }

    // todo add to tokenFallback
    function createAggregationChannel(
        uint256 storageBytes,
        uint lifetime,
        uint maxNodes,
        uint16 nonce,
        uint256 deposit
    )
    public
    {
        aggregationChannel[nextAggregationChannelIndex].owner = msg.sender;
        aggregationChannel[nextAggregationChannelIndex].storageBytes = storageBytes;
        aggregationChannel[nextAggregationChannelIndex].lifetime = lifetime;
        aggregationChannel[nextAggregationChannelIndex].maxNodes = maxNodes;
        aggregationChannel[nextAggregationChannelIndex].startDate = block.timestamp;
        aggregationChannel[nextAggregationChannelIndex].deposit = deposit;
        aggregationChannelIndexes[msg.sender].push(nextAggregationChannelIndex);
        AggregationChannelCreated(nextAggregationChannelIndex, msg.sender, storageBytes, lifetime, maxNodes, nonce);
        nextAggregationChannelIndex = nextAggregationChannelIndex + 1;
    }

    function addToAggregationChannel(uint256 aggregationChannelID, uint256 basicChannelID, uint16 nonce){
        // basic channel should be present
        require(aggregationChannel[basicChannelID].owner != address(0));
        // aggregation channel should be present
        require(aggregationChannel[aggregationChannelID].owner != address(0));
        // aggregation channel must be alive
        require((aggregationChannel[aggregationChannelID].startDate +
              aggregationChannel[aggregationChannelID].lifetime) > block.timestamp);
        // basic channel must be alive
        require((basicChannel[basicChannelID].startDate + basicChannel[basicChannelID].lifetime) > block.timestamp);
        // basic channel must expire before aggregation channel
        require((basicChannel[basicChannelID].startDate + basicChannel[basicChannelID].lifetime) <
               (aggregationChannel[aggregationChannelID].startDate + aggregationChannel[aggregationChannelID].lifetime));
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

    function withdrawFromChannels() public {
        uint withdrawValue = 0;
        if (aggregationChannelIndexes[msg.sender].length > 0) {
        }
        if (basicChannelIndexes[msg.sender].length > 0) {
        }
        if(withdrawValue > 0) {
            tokenAddress.call(bytes4(sha3("transfer(address, uint256)")), msg.sender, withdrawValue);
        }
    }

    function getNodeIPs() public returns (bytes16[]) {
        bytes16[] arr;
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
        uint index = block.timestamp / secondsToDay - 1;
        if (index >= heartbitTotal && index % heartbitUnit == 0) {
            nodes[nodeNumber].heartbits[index % heartbitTotal / heartbitUnit] = 0;
        }
        nodes[nodeNumber].heartbits[index % heartbitTotal / heartbitUnit] =
            nodes[nextNodeIndex].heartbits[index % heartbitTotal / heartbitUnit] | (1 << (index % heartbitTotal % heartbitUnit));
        // reward
        if (block.timestamp - nodes[nextNodeIndex].lastRewardDate >= paymentPeriod){
            nodes[nextNodeIndex].lastRewardDate = block.timestamp;
            uint dayToPayFor = 0;
            for(uint i = 0; i < paymentDays; i++){
                if (nodes[nodeNumber].heartbits[index % heartbitTotal / heartbitUnit] & (1 * 2 ** (index % heartbitTotal % heartbitUnit)) != 0){
                    dayToPayFor = dayToPayFor + 1;
                    if(i - dayToPayFor > absentDays){
                        return;
                    }
                    index = index - 1;
                }
            }
            tokenAddress.call(bytes4(sha3("transfer(address, uint256)")), msg.sender, dayToPayFor * (dailyMint / getActiveNodesCount()));
        }
    }

    // todo
    /*
    function() {
    throw;
    }*/
}
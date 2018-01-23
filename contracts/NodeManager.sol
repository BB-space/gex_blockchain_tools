pragma solidity ^0.4.15;

/// Token interface declaration
interface GeToken {
    function transfer(address _to, uint _value) public returns (bool);
    function mint(address _to, uint _amount) returns (bool);
}

/// @title Node Manager contract
contract NodeManager {

    enum NodeStatus {Active, Leaving, Left}

    enum TransactionOperation {CreateNode, CreateBasicChannel, CreateAggregationChannel}

    uint32 constant SECONDS_TO_DAY = 86400; // utility variable for time conversion
    // 60 days in seconds. Time period after which user can withdraw node deposit and leave the system
    uint32 constant LEAVING_PERIOD = 5260000;
    // min term in which node can be rewarded for it's contribution
    uint8 constant PAYMENT_DAYS = 32;
    // paymentDays days in seconds
    uint32 constant PAYMENT_PERIOD = PAYMENT_DAYS * SECONDS_TO_DAY;
    // permitted number of days node may not send the heartbit during the paymentPeriod
    uint8 constant ABSENT_DAYS = 2;
    // 30 days. Max lifetime of any channel
    uint32 constant CHANNEL_MAX_LIFETIME = 2630000;
    uint16 constant HEARTBIT_UNIT = 256;
    uint16 constant HEARTBIT_TOTAL = HEARTBIT_UNIT * 2;
    uint constant depositValue = 100000000000000000000; //  size of a deposit to add node to the system 100 * 10 ** 18

    address tokenAddress; // address of the token contract
    uint annualMint; // total reword for nodes per year
    uint dailyMint; // daily reword for nodes


    struct Node {
        bytes15 ip;
        uint16 port;
        uint leavingDate; // date when node was moved to the Leaving state
        uint lastRewardDate; // date when node was rewarded last time
        uint[2] heartbits; // bitmap of heartbit signals for last 512 days
        NodeStatus status;
    }

    struct BasicChannel {
        address owner; // channel owner
        uint storageBytes; // number of bytes this channel can store
        uint lifetime;  // number of seconds this channel will be considered as alive
        uint startDate; // date of channel creation
        uint maxNodes; // max number of nodes associated with this channel
        uint deposit; // value of tokens associated with this channel
    }

    struct AggregationChannel {
        address owner; // channel owner
        uint storageBytes; // number of bytes this channel can store
        uint lifetime;  // number of seconds this channel will be considered as alive
        uint startDate; // date of channel creation
        uint maxNodes; // max number of nodes associated with this channel
        uint deposit; // value of tokens associated with this channel
        mapping (uint => bool) basicChannels; // basic channels aggregated by this channel
        uint nextAggregatedBasicChannelIndex; // index to store next basic channel
    }

    struct DoublyLinkedList {
        uint index;
        uint prev;
        uint next;
    }

    // mapping of node index to a node instance
    mapping (uint => Node) nodes;
    // mapping of a basic channel index to a basic channel instance
    mapping (uint => BasicChannel) basicChannel;
    // mapping of an aggregation channel index to a aggregation channel instance
    mapping (uint => AggregationChannel) aggregationChannel;
    // mapping of owner address to node indexes associated with it
    mapping (address => mapping (uint => bool)) nodeIndexes; // todo Note: we do not delete nodes
    // mapping of owner address to basic channel indexes associated with it
    mapping (address => DoublyLinkedList[]) basicChannelIndexes;
    // mapping of owner address to aggregation channel indexes associated with it
    mapping (address => DoublyLinkedList[]) aggregationChannelIndexes;
    // index to store next node
    uint nextNodeIndex;
    // index to store next basic channel
    uint nextBasicChannelIndex;
    // index to store next aggregation channel
    uint nextAggregationChannelIndex;

    /*
     *  Events
     */

    event Test1();
    event Test2();

    event NodeCreated(
        uint nodeID,
        address owner,
        bytes15 ip,
        uint16 port,
        uint16 nonce
    );

    event BasicChannelCreated(
        uint channelID,
        address owner,
        uint storageBytes,
        uint lifetime,
        uint maxNodes,
        uint deposit,
        uint16 nonce
    );

    event AggregationChannelCreated(
        uint channelID,
        address owner,
        uint storageBytes,
        uint lifetime,
        uint maxNodes,
        uint deposit,
        uint16 nonce
    );

    event BasicChannelAdded(
        uint aggregationChannelID,
        uint basicChannelID,
        uint16 nonce
    );

    /*
     *  Constructor
     */

    /// @dev Constructor for creating the Node Manager contract
    /// @param _token The address of the token contract
    /// @param _annualMint Amount of tokens rewarded to nodes per year. Should be specified with decimals
    function NodeManager(address _token, uint _annualMint) {
        // todo implement: annualMint should be reduced by a half each N years
        tokenAddress = _token;
        annualMint = _annualMint;
        dailyMint = annualMint / getDaysInCurrentYear(); // todo getDaysInCurrentYear() is very expensive
        nextNodeIndex = 1;
        nextBasicChannelIndex = 1;
        nextAggregationChannelIndex = 1;
    }

    /*
     *  Public functions
     */

    /// @dev Function for adding an existed basic channel to an existed aggregation channel
    /// @param aggregationChannelID Aggregation channel index
    /// @param basicChannelID Basic channel index
    /// @param nonce Unique identifier of a current operation
    function addToAggregationChannel(
        uint aggregationChannelID,
        uint basicChannelID,
        uint16 nonce
    )
    public
    {
        // todo should msg.sender be a owner of basic or aggregation channel ?
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
               (aggregationChannel[aggregationChannelID].startDate +
               aggregationChannel[aggregationChannelID].lifetime));
        // check that basic channel is not present in the aggregation channel already
        require(!aggregationChannel[aggregationChannelID].basicChannels[basicChannelID]);
        aggregationChannel[aggregationChannelID].basicChannels[basicChannelID] = true;
        aggregationChannel[aggregationChannelID].nextAggregatedBasicChannelIndex += 1;
        BasicChannelAdded(aggregationChannelID, basicChannelID, nonce);
    }

    /// @dev Function marks node as Leaving. After that node cannot participate in any new channels
    /// @param nodeNumber Node index
    function initWithdrawDeposit(uint nodeNumber) public {
        require(nodeIndexes[msg.sender][nodeNumber]);
        require(nodes[nodeNumber].status == NodeStatus.Active);
        nodes[nodeNumber].status = NodeStatus.Leaving;
        nodes[nodeNumber].leavingDate = block.timestamp;
    }

    /// @dev Function that withdraw node deposit to a node owner and marks node as Leaving.
    ///      At this time all channels associated with this node are finished, because a lifetime
    ///      of a channel is 30 days, when leaving period is 60
    /// @param nodeNumber Node index
    function completeWithdrawDeposit(uint nodeNumber) public {
        require(nodeIndexes[msg.sender][nodeNumber]);
        require(nodes[nodeNumber].status == NodeStatus.Leaving);
        require(block.timestamp - nodes[nodeNumber].leavingDate >= LEAVING_PERIOD);
        nodes[nodeNumber].status = NodeStatus.Left;
        GeToken(tokenAddress).transfer(msg.sender, depositValue);
        //tokenAddress.call(bytes4(sha3("transfer(address, uint)")), msg.sender, depositValue);
    }

    /// @dev Function withdraws deposit from all finished channels of msg.sender and deletes this channels
    function withdrawFromChannels() public {
        uint withdrawValue = 0;
        uint i;
        if(aggregationChannelIndexes[msg.sender].length > 0){
            i = aggregationChannelIndexes[msg.sender][0].next;
            while(i != 0) {
                if(aggregationChannel[aggregationChannelIndexes[msg.sender][i].index].startDate +
                    aggregationChannel[aggregationChannelIndexes[msg.sender][i].index].lifetime < block.timestamp){
                    withdrawValue = withdrawValue +
                        aggregationChannel[aggregationChannelIndexes[msg.sender][i].index].deposit;
                    aggregationChannelIndexes[msg.sender][aggregationChannelIndexes[msg.sender][i].prev].next =
                        aggregationChannelIndexes[msg.sender][i].next;
                    delete aggregationChannel[aggregationChannelIndexes[msg.sender][i].index];
                    delete aggregationChannelIndexes[msg.sender][i];
                    //todo length-- ?
                }
                i = aggregationChannelIndexes[msg.sender][i].next;
            }
        }
        if(basicChannelIndexes[msg.sender].length > 0){
            i = basicChannelIndexes[msg.sender][0].next;
            while(i != 0) {
                if(basicChannel[basicChannelIndexes[msg.sender][i].index].startDate +
                    basicChannel[basicChannelIndexes[msg.sender][i].index].lifetime < block.timestamp){
                    withdrawValue = withdrawValue +
                        basicChannel[basicChannelIndexes[msg.sender][i].index].deposit;
                    basicChannelIndexes[msg.sender][basicChannelIndexes[msg.sender][i].prev].next =
                        basicChannelIndexes[msg.sender][i].next;
                    delete basicChannel[basicChannelIndexes[msg.sender][i].index];
                    delete basicChannelIndexes[msg.sender][i];
                    //todo length-- ?
                }
                i = basicChannelIndexes[msg.sender][i].next;
            }
        }
        if(withdrawValue > 0) {
            GeToken(tokenAddress).transfer(msg.sender, withdrawValue);
            //tokenAddress.call(bytes4(sha3("transfer(address, uint)")), msg.sender, withdrawValue);
        }
    }

    /// @dev Function returns an ip list of all Active nodes
    /// @return ip list
    function getNodeIPs()
        public
        view
        returns (bytes16[])
    {
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

    /// @dev Function returns an basic channel indexes for msg.sender
    /// @return basic channel indexes list
    function getBasicChannels()
        public
        constant
        returns (uint[] memory arr)
    {
        arr = new uint[](basicChannelIndexes[msg.sender].length);
        uint i;
        uint j = 0;
        if(basicChannelIndexes[msg.sender].length > 0){
            i = basicChannelIndexes[msg.sender][0].next;
            while(i != 0) {
                arr[j] = basicChannelIndexes[msg.sender][i].index;
                i = basicChannelIndexes[msg.sender][i].next;
                j=j+1;
            }
        }
    }

    /*
    uint n = 7;
    //mapping(uint => uint[]) a;
    function getArray() constant returns (uint[] memory arr) {

        //uint[] a;

        a[0].push(1);
        a[0].push(2);

        arr = new uint[](a[0].length);
        //uint[2] arr;
        //arr.length = 2;
        for(uint i=0;i<a[0].length;i++){
            arr[i] = i;
        }
        //return arr;
    }*/

    function get(uint i) public
        view
        returns (uint,uint,uint)
    {
        return (basicChannelIndexes[msg.sender][i].prev, basicChannelIndexes[msg.sender][i].index, basicChannelIndexes[msg.sender][i].next);
    }
    /// @dev Function stores node heartbits and rewards node
    ///      Heartbits is a bitmap which stores information about presence of a node in the system for last 512 days
    ///      Each bit represents one day
    /// @param nodeNumber Node index
    // todo see warning
    function heartbit(uint nodeNumber) public {
        require(nodeIndexes[msg.sender][nodeNumber]);
        uint index = block.timestamp / SECONDS_TO_DAY - 1;
        if (index >= HEARTBIT_TOTAL && index % HEARTBIT_UNIT == 0) {
            nodes[nodeNumber].heartbits[index % HEARTBIT_TOTAL / HEARTBIT_UNIT] = 0;
        }
        // since HEARTBIT_TOTAL = HEARTBIT_UNIT * 2
        // we can use % HEARTBIT_UNIT instead of % HEARTBIT_TOTAL % HEARTBIT_UNIT
        nodes[nodeNumber].heartbits[index % HEARTBIT_TOTAL / HEARTBIT_UNIT] =
            nodes[nextNodeIndex].heartbits[index % HEARTBIT_TOTAL / HEARTBIT_UNIT] | (1 << (index % HEARTBIT_UNIT));
        // if the last reward was more than 32 days ago - check node heartbit for this period and reward
        if (block.timestamp - nodes[nextNodeIndex].lastRewardDate >= PAYMENT_PERIOD){
            nodes[nextNodeIndex].lastRewardDate = block.timestamp;
            uint8 daysToPayFor = 0;
            for(uint8 i = 0; i < PAYMENT_DAYS; i++){
                if (nodes[nodeNumber].heartbits[index % HEARTBIT_TOTAL / HEARTBIT_UNIT] &
                (1 * 2 ** (index % HEARTBIT_UNIT)) != 0) {
                    daysToPayFor = daysToPayFor + 1;
                     // if node was absent more than 2 days - don't pay for whole payment period
                    if(i - daysToPayFor > ABSENT_DAYS){
                        return;
                    }
                    index = index - 1;
                }
            }
            // this transaction will work only if this contract is an owner of token contract
            GeToken(tokenAddress).mint(msg.sender, daysToPayFor * (dailyMint / getActiveNodesCount()));
            //tokenAddress.call(bytes4(sha3("transfer(address, uint)")), msg.sender, dayToPayFor * (dailyMint / getActiveNodesCount()));
        }
    }

     /*
     *  Private functions
     */

    /// @dev Function counts Active nodes
    /// @return number of Active nodes
    function getActiveNodesCount()
        internal
        view
        returns (uint)
    {
        uint activeNodes = 0;
        for (uint i = 0; i < nextNodeIndex; i++) {
            if(nodes[i].status == NodeStatus.Active){
                activeNodes++;
            }
        }
        return activeNodes;
    }

    /// @dev Function that is called when a user or another contract wants to transfer funds.
    ///      Fallback is called when user is making deposit to create node, basic or aggregation channel
    /// @param _from Transaction initiator, analogue of msg.sender
    /// @param _value Number of tokens to transfer.
    /// @param _data Data containig a function signature and/or parameters
    // todo make internal
    function tokenFallback(address _from, uint _value, bytes _data) public {
        require(msg.sender == tokenAddress);
        TransactionOperation operationType = fallbackOperationTypeConvert(_data);
        if(operationType == TransactionOperation.CreateNode) {
            // create node
            createNode(_from, _value, _data);
        } else if (operationType == TransactionOperation.CreateBasicChannel) {
            // create basic channel
            createBasicChannel(_from, _value, _data);
        } else {
            // create aggregation channel
            createAggregationChannel(_from, _value, _data);
        }
    }

    /// @dev Function for creating a node
    /// @param _from Transaction initiator, analogue of msg.sender
    /// @param _value Number of tokens to transfer.
    /// @param _data Data containig a function signature and/or parameters:
    ///      port Node port for the communication inside the system
    ///      nonce Unique identifier of a current operation
    ///      ip IPv4 address of the node
    function createNode(address _from, uint _value, bytes _data) internal {
        require(_value == depositValue);
        uint16 port;
        uint16 nonce;
        bytes15 ip;
        (port, nonce, ip) = fallbackCreateNodeDataConvert(_data);
        require (ip != 0x0); // todo add ip validation
        //  Port number is an unsigned 16-bit integer, so 65535 will the max value
        require (port > 0); // todo discuss port range https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers
        nodes[nextNodeIndex].ip = ip;
        nodes[nextNodeIndex].port = port;
        nodes[nextNodeIndex].status = NodeStatus.Active;
        nodes[nextNodeIndex].lastRewardDate = block.timestamp;
        nodeIndexes[_from][nextNodeIndex] = true;
        NodeCreated(nextNodeIndex, _from, ip, port, nonce);
        nextNodeIndex = nextNodeIndex + 1;
    }

    /// @dev Function for creating a basic channel
    /// @param _from Transaction initiator, analogue of msg.sender
    /// @param _value Number of tokens to transfer.
    /// @param _data Data containig a function signature and/or parameters:
    ///      storageBytes Number of bytes this channel can store
    ///      lifetime Number of seconds this channel will be considered as alive
    ///      maxNodes Max number of nodes associated with this channel
    ///      nonce Unique identifier of a current operation
    function createBasicChannel(address _from, uint _value, bytes _data) internal {
        uint storageBytes;
        uint lifetime;
        uint maxNodes;
        uint16 nonce;
        (storageBytes, lifetime, maxNodes, nonce) = fallbackCreateChannelDataConvert(_data);
        // channel can live max 30 days
        require(lifetime <= CHANNEL_MAX_LIFETIME);
        basicChannel[nextBasicChannelIndex].owner = _from;
        basicChannel[nextBasicChannelIndex].storageBytes = storageBytes;
        basicChannel[nextBasicChannelIndex].lifetime = lifetime;
        basicChannel[nextBasicChannelIndex].maxNodes = maxNodes;
        basicChannel[nextBasicChannelIndex].startDate = block.timestamp;
        basicChannel[nextBasicChannelIndex].deposit = _value;
        if(basicChannelIndexes[_from].length == 0){
            // element at the 0 position is linked to the first element
            basicChannelIndexes[_from].push(DoublyLinkedList(0, 0, 1));
            basicChannelIndexes[_from].push(DoublyLinkedList(nextBasicChannelIndex, 0, 0));
        } else {
            //todo fix length
            basicChannelIndexes[_from][basicChannelIndexes[_from].length-1].next =
                basicChannelIndexes[_from].length;
            basicChannelIndexes[_from].push(
                DoublyLinkedList(nextBasicChannelIndex,basicChannelIndexes[_from].length - 2, 0));

        }
        BasicChannelCreated(nextBasicChannelIndex, _from, storageBytes, lifetime, maxNodes, _value, nonce);
        nextBasicChannelIndex = nextBasicChannelIndex + 1;
    }

    /// @dev Function for creating a aggregation channel
    /// @param _from Transaction initiator, analogue of msg.sender
    /// @param _value Number of tokens to transfer.
    /// @param _data Data containig a function signature and/or parameters:
    ///      storageBytes Number of bytes this channel can store
    ///      lifetime Number of seconds this channel will be considered as alive
    ///      maxNodes Max number of nodes associated with this channel
    ///      nonce Unique identifier of a current operation
    function createAggregationChannel(address _from, uint _value, bytes _data) internal {
        uint storageBytes;
        uint lifetime;
        uint maxNodes;
        uint16 nonce;
        (storageBytes, lifetime, maxNodes, nonce) = fallbackCreateChannelDataConvert(_data);
        // channel can live max 30 days
        require(lifetime <= CHANNEL_MAX_LIFETIME);
        aggregationChannel[nextAggregationChannelIndex].owner = _from;
        aggregationChannel[nextAggregationChannelIndex].storageBytes = storageBytes;
        aggregationChannel[nextAggregationChannelIndex].lifetime = lifetime;
        aggregationChannel[nextAggregationChannelIndex].maxNodes = maxNodes;
        aggregationChannel[nextAggregationChannelIndex].startDate = block.timestamp;
        aggregationChannel[nextAggregationChannelIndex].deposit = _value;
         if(aggregationChannelIndexes[_from].length == 0){
            // element at the 0 position is linked to the first element
            aggregationChannelIndexes[_from].push(DoublyLinkedList(0, 0, 1));
            aggregationChannelIndexes[_from].push(DoublyLinkedList(nextAggregationChannelIndex, 0, 0));
        } else {
            aggregationChannelIndexes[_from][aggregationChannelIndexes[_from].length - 1].next =
                aggregationChannelIndexes[_from].length;
            aggregationChannelIndexes[_from].push(
                DoublyLinkedList(nextAggregationChannelIndex,aggregationChannelIndexes[_from].length - 2, 0));

        }
        AggregationChannelCreated(nextAggregationChannelIndex, _from, storageBytes,
                                    lifetime, maxNodes, _value, nonce);
        nextAggregationChannelIndex = nextAggregationChannelIndex + 1;
    }


    /// @dev Function for parsing first 2 data bytes to determine the type of the transaction operation
    /// @param data Data containig a function signature and/or parameters
    /// @return type of the transaction operation
     function fallbackOperationTypeConvert(bytes data)
        internal
        pure
        returns (TransactionOperation)
    {
         bytes1 operationType;
         assembly {
            operationType := mload(add(data, 0x20))
        }
        //require(operationType != 0x0 || operationType < 0x4);
        if(operationType == 0x1) {
            return TransactionOperation.CreateNode;
        } else if(operationType == 0x10) {
            return TransactionOperation.CreateBasicChannel;
        } else {
            return TransactionOperation.CreateAggregationChannel;
        }

    }

    /// @dev Function for parsing data bytes to a set of parameters for node creation
    /// @param data Data containig a function signature and/or parameters
    /// @return parsed fallback parameters:
    ///      port Node port for the communication inside the system
    ///      nonce Unique identifier of a current operation
    ///      ip IPv4 address of the node
    function fallbackCreateNodeDataConvert(bytes data)
        internal
        pure
        returns (uint16, uint16, bytes15)
    {
        bytes4 port;
        bytes4 nonce;
        bytes15 ip;
        assembly {
            port := mload(add(data, 0x21))
            nonce := mload(add(data, 0x25))
            ip := mload(add(data, 0x29))
        }
        return (uint16(port), uint16(nonce), ip);
    }

    /// @dev Function for parsing data bytes to a set of parameters for channel creation
    /// @param data Data containig a function signature and/or parameters
    /// @return parsed fallback parameters:
    ///      storageBytes Number of bytes this channel can store
    ///      lifetime Number of seconds this channel will be considered as alive
    ///      maxNodes Max number of nodes associated with this channel
    ///      nonce Unique identifier of a current operation
    function fallbackCreateChannelDataConvert(bytes data)
        internal
        pure
        returns (uint, uint, uint, uint16)
    {
        bytes32 storageBytes;
        bytes32 lifetime;
        bytes32 maxNodes;
        bytes4 nonce;
        assembly {
            storageBytes := mload(add(data, 33))
            lifetime := mload(add(data, 65))
            maxNodes := mload(add(data, 97))
            nonce := mload(add(data, 129))
        }
        return (uint(storageBytes), uint(lifetime), uint(maxNodes), uint16(nonce));
    }

        /*
    function() {
    throw;
    }*/

     /*
     *  Find a leap year
     *  Taken from https://github.com/pipermerriam/ethereum-datetime
     */

    uint constant YEAR_IN_SECONDS = 31536000;
    uint constant LEAP_YEAR_IN_SECONDS = 31622400;
    uint16 constant ORIGIN_YEAR = 1970;

     function getDaysInCurrentYear()
     internal
     view
     returns (uint16)
     {
        if (isLeapYear(getYear(block.timestamp))) {
            return 366;
        }
        return 365;
    }

     function isLeapYear(uint16 year)
     internal
     pure
     returns (bool)
     {
        if (year % 4 != 0) {
                return false;
        }
        if (year % 100 != 0) {
                return true;
        }
        if (year % 400 != 0) {
                return false;
        }
        return true;
    }

     function getYear(uint timestamp)
     internal
     pure
     returns (uint16)
     {
        uint secondsAccountedFor = 0;
        uint16 year;
        uint numLeapYears;

        year = uint16(ORIGIN_YEAR + timestamp / YEAR_IN_SECONDS);
        numLeapYears = leapYearsBefore(year) - leapYearsBefore(ORIGIN_YEAR);

        secondsAccountedFor += LEAP_YEAR_IN_SECONDS * numLeapYears;
        secondsAccountedFor += YEAR_IN_SECONDS * (year - ORIGIN_YEAR - numLeapYears);

        while (secondsAccountedFor > timestamp) {
                if (isLeapYear(uint16(year - 1))) {
                        secondsAccountedFor -= LEAP_YEAR_IN_SECONDS;
                }
                else {
                        secondsAccountedFor -= YEAR_IN_SECONDS;
                }
                year -= 1;
        }
        return year;
    }

     function leapYearsBefore(uint year)
     internal
     pure
     returns (uint)
     {
            year -= 1;
            return year / 4 - year / 100 + year / 400;
     }

}
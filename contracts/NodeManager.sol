pragma solidity ^0.4.15;

interface GeToken {
    function transfer(address _to, uint _value) public returns (bool);
    function mint(address _to, uint _amount) returns (bool); // todo onlyOwner
}


/// @title Node Manager contract
contract NodeManager {

    enum NodeStatus {Active, Leaving, Left}

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

    // mapping of node index to a node instance
    mapping (uint => Node) nodes;
    // mapping of a basic channel index to a basic channel instance
    mapping (uint => BasicChannel) basicChannel;
    // mapping of an aggregation channel index to a aggregation channel instance
    mapping (uint => AggregationChannel) aggregationChannel;
    // mapping of owner address to node indexes associated with it
    mapping (address => mapping (uint => bool)) nodeIndexes; // todo set struct here. list?? do the same as with channels
    // mapping of owner address to basic channel indexes associated with it
    mapping (address => uint[]) basicChannelIndexes;
    // mapping of owner address to aggregation channel indexes associated with it
    mapping (address => uint[]) aggregationChannelIndexes;
    // index to store next node
    uint nextNodeIndex;
    // index to store next basic channel
    uint nextBasicChannelIndex;
    // index to store next aggregation channel
    uint nextAggregationChannelIndex;

    /*
     *  Events
     */

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

    /// @dev Function that is called when a user or another contract wants to transfer funds.
    ///      Fallback is called when user is making transfer to register node in the system
    /// @param _from Transaction initiator, analogue of msg.sender
    /// @param _value Number of tokens to transfer.
    /// @param _data Data containig a function signature and/or parameters
    function tokenFallback(address _from, uint _value, bytes _data) public {
        require(msg.sender == tokenAddress);
        require(_value == depositValue);
        uint16 port;
        uint16 nonce;
        bytes15 ip;
        (port, nonce, ip) = fallbackDataConvert(_data);
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
    /// @param storageBytes Number of bytes this channel can store
    /// @param lifetime Number of seconds this channel will be considered as alive
    /// @param maxNodes Max number of nodes associated with this channel
    /// @param nonce Unique identifier of a current operation
    /// @param deposit Value of tokens associated with this channel
    // todo add to tokenFallback
    function createBasicChannel(
        uint storageBytes,
        uint lifetime,
        uint maxNodes,
        uint16 nonce,
        uint deposit
    )
    public
    {
        // channel can live max 30 days
        require(lifetime <= CHANNEL_MAX_LIFETIME);
        basicChannel[nextBasicChannelIndex].owner = msg.sender;
        basicChannel[nextBasicChannelIndex].storageBytes = storageBytes;
        basicChannel[nextBasicChannelIndex].lifetime = lifetime;
        basicChannel[nextBasicChannelIndex].maxNodes = maxNodes;
        basicChannel[nextBasicChannelIndex].startDate = block.timestamp;
        basicChannel[nextBasicChannelIndex].deposit = deposit;
        basicChannelIndexes[msg.sender].push(nextBasicChannelIndex);
        BasicChannelCreated(nextBasicChannelIndex, msg.sender, storageBytes, lifetime, maxNodes, deposit, nonce);
        nextBasicChannelIndex = nextBasicChannelIndex + 1;
    }

    /// @dev Function for creating a aggregation channel
    /// @param storageBytes Number of bytes this channel can store
    /// @param lifetime Number of seconds this channel will be considered as alive
    /// @param maxNodes Max number of nodes associated with this channel
    /// @param nonce Unique identifier of a current operation
    /// @param deposit Value of tokens associated with this channel
    // todo add to tokenFallback
    function createAggregationChannel(
        uint storageBytes,
        uint lifetime,
        uint maxNodes,
        uint16 nonce,
        uint deposit
    )
    public
    {
        // channel can live max 30 days
        require(lifetime <= CHANNEL_MAX_LIFETIME);
        aggregationChannel[nextAggregationChannelIndex].owner = msg.sender;
        aggregationChannel[nextAggregationChannelIndex].storageBytes = storageBytes;
        aggregationChannel[nextAggregationChannelIndex].lifetime = lifetime;
        aggregationChannel[nextAggregationChannelIndex].maxNodes = maxNodes;
        aggregationChannel[nextAggregationChannelIndex].startDate = block.timestamp;
        aggregationChannel[nextAggregationChannelIndex].deposit = deposit;
        aggregationChannelIndexes[msg.sender].push(nextAggregationChannelIndex);
        AggregationChannelCreated(nextAggregationChannelIndex, msg.sender, storageBytes,
                                    lifetime, maxNodes, deposit, nonce);
        nextAggregationChannelIndex = nextAggregationChannelIndex + 1;
    }

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
        if (aggregationChannelIndexes[msg.sender].length > 0) {
            // todo
        }
        if (basicChannelIndexes[msg.sender].length > 0) {
            // todo
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
            uint dayToPayFor = 0;
            for(uint i = 0; i < PAYMENT_DAYS; i++){
                if (nodes[nodeNumber].heartbits[index % HEARTBIT_TOTAL / HEARTBIT_UNIT] &
                (1 * 2 ** (index % HEARTBIT_UNIT)) != 0) {
                    dayToPayFor = dayToPayFor + 1;
                     // if node was absent more than 2 days - don't pay for whole payment period
                    if(i - dayToPayFor > ABSENT_DAYS){
                        return;
                    }
                    index = index - 1;
                }
            }
            // todo this contract should be the owner
            GeToken(tokenAddress).mint(msg.sender, dayToPayFor * (dailyMint / getActiveNodesCount()));
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

    /// @dev Function for parsing data bytes to a set of parameters
    /// @param data Data containig a function signature and/or parameters
    /// @return parsed fallback parameters
    function fallbackDataConvert(bytes data)
        //todo make internal
        pure
        returns (uint16, uint16, bytes15)
    {
        bytes15 ip;
        bytes4 port;
        bytes4 nonce;
        assembly {
            port := mload(add(data, 0x20))
            nonce := mload(add(data, 0x24))
            ip := mload(add(data, 0x28))
        }
        return (uint16(port),uint16(nonce),ip);
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
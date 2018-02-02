pragma solidity ^0.4.15;

/// Token interface declaration
interface GeToken {
    function transfer(address _to, uint _value) public returns (bool);
    function mint(address _to, uint _amount) public returns (bool);
}

/// @title Node Manager contract
contract NodeManager {

    enum NodeStatus {Active, Leaving, Left}

    enum TransactionOperation {CreateNode, CreateMchain, CreateAggregationMchain}

    uint32 constant SECONDS_TO_DAY = 86400; // utility variable for time conversion
    // 60 days in seconds. Time period after which user can withdraw node deposit and leave the system
    uint32 constant LEAVING_PERIOD = 5260000;
    // min term in which node can be rewarded for it's contribution
    uint8 constant PAYMENT_DAYS = 32;
    // paymentDays days in seconds
    uint32 constant PAYMENT_PERIOD = PAYMENT_DAYS * SECONDS_TO_DAY;
    // permitted number of days node may not send the heartbit during the paymentPeriod
    uint8 constant ABSENT_DAYS = 2;
    // 30 days. Max lifetime of any mchain
    uint32 constant MCHAIN_MAX_LIFETIME = 2630000;
    uint16 constant HEARTBIT_UNIT = 256;
    uint16 constant HEARTBIT_TOTAL = HEARTBIT_UNIT * 2;
    uint public constant DEPOSIT_VALUE = 100000000000000000000; //  size of a deposit to add node to the system 100 * 10 ** 18

    address tokenAddress; // address of the token contract
    uint annualMint; // total reword for nodes per year
    uint dailyMint; // daily reword for nodes

// todo get key startdate
    struct Node {
        bytes15 ip; // todo save as number and provide function for ip check
        uint16 port;
        bytes key; // todo size ?
        uint registrationDate;
        uint leavingDate; // date when node was moved to the Leaving state
        uint lastRewardDate; // date when node was rewarded last time
        uint[2] heartbits; // bitmap of heartbit signals for last 512 days
        NodeStatus status;
    }

    struct Mchain {
        address owner; // mchain owner
        uint storageBytes; // number of bytes this mchain can store
        uint lifetime;  // number of seconds this mchain will be considered as alive
        uint startDate; // date of mchain creation
        uint maxNodes; // max number of nodes associated with this mchain
        uint deposit; // value of tokens associated with this mchain
    }

    struct AggregationMchain {
        address owner; // mchain owner
        uint storageBytes; // number of bytes this mchain can store
        uint lifetime;  // number of seconds this mchain will be considered as alive
        uint startDate; // date of mchain creation
        uint maxNodes; // max number of nodes associated with this mchain
        uint deposit; // value of tokens associated with this mchain
        mapping (uint => bool) mchainsPresence; // mchains aggregated by this mchain
        uint[] mchains;
        uint nextAggregatedMchainIndex; // index to store next mchain
    }

    // mapping of node index to a node instance
    mapping (uint => Node) nodes;
    // mapping of a mchain index to a mchain instance
    mapping (uint => Mchain) mchain;
    // mapping of an aggregation mchain index to a aggregation mchain instance
    mapping (uint => AggregationMchain) aggregationMchain;
    // mapping of owner address to node indexes associated with it
    mapping (address => mapping (uint => bool)) nodeIndexes; // todo Note: we do not delete nodes
    // mapping of owner address to mchain indexes associated with it
    mapping (address => uint[]) mchainIndexes;
    // mapping of owner address to aggregation mchain indexes associated with it
    mapping (address => uint[]) aggregationMchainIndexes;
    // index to store next node
    uint nextNodeIndex;
    // index to store next mchain
    uint nextMchainIndex;
    // index to store next aggregation mchain
    uint nextAggregationMchainIndex;

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

    event MchainCreated(
        uint mchainID,
        address owner,
        uint storageBytes,
        uint lifetime,
        uint maxNodes,
        uint deposit,
        uint16 nonce,
        bytes32 name
    );

    event AggregationMchainCreated(
        uint mchainID,
        address owner,
        uint storageBytes,
        uint lifetime,
        uint maxNodes,
        uint deposit,
        uint16 nonce,
        bytes32 name
    );

    event MchainAdded(
        uint aggregationMchainID,
        uint mchainID,
        uint16 nonce
    );

    // todo remove
    event NumberEvent(uint num);

    function setNumber(uint num) public {
        NumberEvent(num);
    }

    function getNumber() public returns(uint)  {
        return 5;
    }

    event BytesEvent(bytes data);

    function testBytes(bytes data) public {
        BytesEvent(data);
    }

    //

    /*
     *  Constructor
     */

    /// @dev Constructor for creating the Node Manager contract
    /// @param _token The address of the token contract
    /// @param _annualMint Amount of tokens rewarded to nodes per year. Should be specified with decimals
    function NodeManager(address _token, uint _annualMint) public {
        // todo implement: annualMint should be reduced by a half each N years
        tokenAddress = _token;
        annualMint = _annualMint;
        //dailyMint = annualMint / 365;
        dailyMint = annualMint / getDaysInCurrentYear(); // todo getDaysInCurrentYear() is very expensive
        //nextNodeIndex = 1;
        //nextMchainIndex = 1;
        //nextAggregationMchainIndex = 1;
    }

    /*
     *  Public functions
     */

    /// @dev Function for adding an existed mchain to an existed aggregation mchain
    /// @param aggregationMchainID Aggregation mchain index
    /// @param mchainID Basic mchain index
    /// @param nonce Unique identifier of a current operation
    function addToAggregationMchain(
        uint aggregationMchainID,
        uint mchainID,
        uint16 nonce
    )
    public
    {
        // msg.sender should be an owner of the aggregation mchain
        require(aggregationMchain[aggregationMchainID].owner == msg.sender);
        // mchain should be present
        require(aggregationMchain[mchainID].owner != address(0));
        // aggregation mchain must be alive
        require((aggregationMchain[aggregationMchainID].startDate +
        aggregationMchain[aggregationMchainID].lifetime) > block.timestamp);
        // mchain must be alive
        require((mchain[mchainID].startDate + mchain[mchainID].lifetime) > block.timestamp);
        // mchain must expire before aggregation mchain
        require((mchain[mchainID].startDate + mchain[mchainID].lifetime) <
               (aggregationMchain[aggregationMchainID].startDate + aggregationMchain[aggregationMchainID].lifetime));
        // check that mchain is not present in the aggregation mchain already
        require(!aggregationMchain[aggregationMchainID].mchainsPresence[mchainID]);
        aggregationMchain[aggregationMchainID].mchainsPresence[mchainID] = true;
        aggregationMchain[aggregationMchainID].mchains.push(mchainID);
        aggregationMchain[aggregationMchainID].nextAggregatedMchainIndex += 1;
        MchainAdded(aggregationMchainID, mchainID, nonce);
    }

    /// @dev Function marks node as Leaving. After that node cannot participate in any new mchains
    /// @param nodeNumber Node index
    function initWithdrawDeposit(uint nodeNumber) public {
        require(nodeIndexes[msg.sender][nodeNumber]);
        require(nodes[nodeNumber].status == NodeStatus.Active);
        nodes[nodeNumber].status = NodeStatus.Leaving;
        nodes[nodeNumber].leavingDate = block.timestamp;
    }

    /// @dev Function that withdraw node deposit to a node owner and marks node as Leaving.
    ///      At this time all mchains associated with this node are finished, because a lifetime
    ///      of a mchain is 30 days, when leaving period is 60
    /// @param nodeNumber Node index
    function completeWithdrawDeposit(uint nodeNumber) public {
        require(nodeIndexes[msg.sender][nodeNumber]);
        require(nodes[nodeNumber].status == NodeStatus.Leaving);
        require(block.timestamp - nodes[nodeNumber].leavingDate >= LEAVING_PERIOD);
        nodes[nodeNumber].status = NodeStatus.Left;
        GeToken(tokenAddress).transfer(msg.sender, DEPOSIT_VALUE);
        //tokenAddress.call(bytes4(sha3("transfer(address, uint)")), msg.sender, depositValue);
    }

    /// @dev Function withdraws deposit from a mchain with given index for msg.sender and deletes this mchain
    /// @param index Index of mchain in the mchains list
    function withdrawFromMchain(uint index) public {
        require(mchainIndexes[msg.sender].length > index);
        require(mchain[mchainIndexes[msg.sender][index]].startDate +
            mchain[mchainIndexes[msg.sender][index]].lifetime < block.timestamp);
        // add mchain deposit value to the total
        uint withdraw = mchain[mchainIndexes[msg.sender][index]].deposit;
        // delete mchain from the mchain list
        delete mchain[mchainIndexes[msg.sender][index]];
        // last element will be moved or deleted
        // if the element is not last
        if(index != mchainIndexes[msg.sender].length - 1) {
            // move the last element to the place on the current element
            mchainIndexes[msg.sender][index] = mchainIndexes[msg.sender][mchainIndexes[msg.sender].length - 1];
        }
        // delete mchain from the mchain indexes list for msg.sender
        delete mchainIndexes[msg.sender][mchainIndexes[msg.sender].length - 1];
        mchainIndexes[msg.sender].length--;
        GeToken(tokenAddress).transfer(msg.sender, withdraw);
    }

    /// @dev Function withdraws deposit from a aggregation mchain with given index for msg.sender
    ///      and deletes this aggregation mchain
    /// @param index Index of aggregation mchain in the aggregationMchain list
    function withdrawFromAggregationMchain(uint index) public {
        require(aggregationMchainIndexes[msg.sender].length > index);
        require(aggregationMchain[aggregationMchainIndexes[msg.sender][index]].startDate +
            aggregationMchain[aggregationMchainIndexes[msg.sender][index]].lifetime < block.timestamp);
        // add aggregation mchain deposit value to the total
        uint withdraw = aggregationMchain[aggregationMchainIndexes[msg.sender][index]].deposit;
        // delete aggregation mchain from the aggregation mchain list
        delete aggregationMchain[aggregationMchainIndexes[msg.sender][index]];
        // last element will be moved or deleted
        // if the element is not last
        if(index != aggregationMchainIndexes[msg.sender].length - 1) {
            // move the last element to the place on the current element
            aggregationMchainIndexes[msg.sender][index] =
                aggregationMchainIndexes[msg.sender][aggregationMchainIndexes[msg.sender].length - 1];
        }
        // delete aggregation mchain from the aggregation mchain indexes list for msg.sender
        delete aggregationMchainIndexes[msg.sender][aggregationMchainIndexes[msg.sender].length - 1];
        aggregationMchainIndexes[msg.sender].length--;
        GeToken(tokenAddress).transfer(msg.sender, withdraw);
    }

    /// @dev Function withdraws deposit from all finished mchains of msg.sender and deletes this mchains
    function withdrawFromMchains() public {
        uint withdrawTotal = 0;
        uint i = 0;
        while(i < aggregationMchainIndexes[msg.sender].length){
            if(aggregationMchain[aggregationMchainIndexes[msg.sender][i]].startDate +
            aggregationMchain[aggregationMchainIndexes[msg.sender][i]].lifetime < block.timestamp) {
            // add mchain deposit value to the total
            withdrawTotal = withdrawTotal + aggregationMchain[aggregationMchainIndexes[msg.sender][i]].deposit;
            // delete mchain from the aggregation mchain list
            delete aggregationMchain[aggregationMchainIndexes[msg.sender][i]];
            // last element will be moved or deleted
            // if the element is not last
            if(i != aggregationMchainIndexes[msg.sender].length - 1) {
                // move the last element to the place on the current element
                aggregationMchainIndexes[msg.sender][i] =
                aggregationMchainIndexes[msg.sender][aggregationMchainIndexes[msg.sender].length - 1];
            }
            // delete mchain from the aggregation mchain indexes list for msg.sender
            delete aggregationMchainIndexes[msg.sender][aggregationMchainIndexes[msg.sender].length - 1];
            aggregationMchainIndexes[msg.sender].length--;
            } else {
                 i++;
            }
        }
        i = 0;
        while(i<mchainIndexes[msg.sender].length){
            if(mchain[mchainIndexes[msg.sender][i]].startDate +
            mchain[mchainIndexes[msg.sender][i]].lifetime < block.timestamp) {
            // add mchain deposit value to the total
            withdrawTotal = withdrawTotal + mchain[mchainIndexes[msg.sender][i]].deposit;
            // delete mchain from the mchain list
            delete mchain[mchainIndexes[msg.sender][i]];
            // last element will be moved or deleted
            // if the element is not last
            if(i != mchainIndexes[msg.sender].length - 1) {
                // move the last element to the place on the current element
                mchainIndexes[msg.sender][i] = mchainIndexes[msg.sender][mchainIndexes[msg.sender].length - 1];
            }
            // delete mchain from the mchain indexes list for msg.sender
            delete mchainIndexes[msg.sender][mchainIndexes[msg.sender].length - 1];
            mchainIndexes[msg.sender].length--;
            } else {
                 i++;
            }
        }
        if(withdrawTotal > 0) {
            GeToken(tokenAddress).transfer(msg.sender, withdrawTotal);
            //tokenAddress.call(bytes4(sha3("transfer(address, uint)")), msg.sender, withdrawValue);
        }
    }

    // todo result array may be huge and contain a lot of 0 because of non active nodes. Use DoublyLinkedList?
    /// @dev Function returns an ip list of all Active nodes
    /// @return ip list
    function getActiveNodeIPs()
        public
        view
        returns (bytes15[] memory arr)
    {
        arr = new bytes15[](nextNodeIndex); // -1);
        uint j = 0;
        for (uint i = 1; i < nextNodeIndex; i++) {
            if(nodes[i].status == NodeStatus.Active){
                arr[j] = nodes[i].ip;
                j++;
            }
        }
    }

    function getActiveNodeIPs(uint[] id)
        public
        view
        returns (bytes15[] memory arr)
    {
        arr = new bytes15[](nextNodeIndex); // -1);
        uint j = 0;
        for (uint i = 0; i < id.length; i++) {
            if(nodes[id[i]].status == NodeStatus.Active){
                arr[j] = nodes[id[i]].ip;
                j++;
            }
        }
    }

    function getActiveNodeIDs()
        public
        view
        returns (uint[] memory arr)
    {
        arr = new uint[](nextNodeIndex); // -1);
        uint j = 0;
        for (uint i = 1; i < nextNodeIndex; i++) {
            if(nodes[i].status == NodeStatus.Active){
                arr[j] = i;
                j++;
            }
        }
    }
    /// @dev Function returns an node info by index
    /// @return node info
    ///     ip IP address of node
    ///     port TCP PORT of node
    ///     status Node status
    ///     key Node account public key
    ///     lastRewardDate Date when node was rewarded last time
    ///     leavingDate Date when node was moved to the Leaving state
    function getNode(uint index)
        public
        view
        returns (bytes15, uint16, NodeStatus, bytes, uint, uint)
    {
        // todo add check
        return (nodes[index].ip, nodes[index].port, nodes[index].status, nodes[index].key,
            nodes[index].lastRewardDate, nodes[index].leavingDate);
    }

    /// @dev Function returns an mchain info by index
    /// @return mchain info
    ///      storageBytes Number of bytes this mchain can store
    ///      lifetime Number of seconds this mchain will be considered as alive
    ///      startDate Number of seconds of mchain creation
    ///      maxNodes Max number of nodes associated with this mchain
    ///      deposit Value of tokens associated with this mchain
    function getMchain(uint index)
        public
        view
        returns (address, uint, uint, uint, uint, uint)
    {
        // todo add check
        return (mchain[index].owner, mchain[index].storageBytes, mchain[index].lifetime,
            mchain[index].startDate, mchain[index].maxNodes, mchain[index].deposit);
    }

    /// @dev Function returns an aggregation mchain info by index
    /// @return basis mchain info
    ///      storageBytes Number of bytes this mchain can store
    ///      lifetime Number of seconds this mchain will be considered as alive
    ///      startDate Number of seconds of mchain creation
    ///      maxNodes Max number of nodes associated with this mchain
    ///      deposit Value of tokens associated with this mchain
    function getAggregationMchain(uint index)
        public
        view
        returns (address, uint, uint, uint, uint, uint)
    {
        // todo add check
        return (aggregationMchain[index].owner, aggregationMchain[index].storageBytes,
            aggregationMchain[index].lifetime, aggregationMchain[index].startDate,
            aggregationMchain[index].maxNodes, aggregationMchain[index].deposit);
    }


    /// @dev Function returns mchain indexes array associated with the aggregation mchain
    /// @return mchain indexes list
    function getMchainListFromAggregationMchain(uint index)
        public
        view
        returns (uint[])
    {
        // todo add check
        return aggregationMchain[index].mchains;
    }


    /// @dev Function returns mchain indexes array associated with  msg.sender
    /// @return mchain indexes list
    function getMchainList()
        public
        view
        returns (uint[])
    {
        // todo add check
        return mchainIndexes[msg.sender];
    }

    /// @dev Function returns aggregation mchain indexes array associated with msg.sender
    /// @return aggregation mchain indexes list
    function getAggregationMchainList()
        public
        view
        returns (uint[])
    {
        // todo add check
        return aggregationMchainIndexes[msg.sender];
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
            nodes[nodeNumber].heartbits[index % HEARTBIT_TOTAL / HEARTBIT_UNIT] | (1 << (index % HEARTBIT_UNIT));
        // if the last reward was more than 32 days ago - check node heartbit for this period and reward
        if (block.timestamp - nodes[nodeNumber].lastRewardDate >= PAYMENT_PERIOD){
            nodes[nodeNumber].lastRewardDate = block.timestamp;
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
    ///      Fallback is called when user is making deposit to create node, mchain or aggregation mchain
    /// @param _from Transaction initiator, analogue of msg.sender
    /// @param _value Number of tokens to transfer.
    /// @param _data Data containig a function signature and/or parameters
    // todo make internal here and for other callback functions
    function tokenFallback(address _from, uint _value, bytes _data) public {
        require(msg.sender == tokenAddress);
        TransactionOperation operationType = fallbackOperationTypeConvert(_data);
        if(operationType == TransactionOperation.CreateNode) {
            // create node
            createNode(_from, _value, _data);
        } else if (operationType == TransactionOperation.CreateMchain) {
            // create mchain
            createMchain(_from, _value, _data);
        } else {
            // create aggregation mchain
            createAggregationMchain(_from, _value, _data);
        }
    }

    /// @dev Function for creating a node
    /// @param _from Transaction initiator, analogue of msg.sender
    /// @param _value Number of tokens to transfer.
    /// @param _data Data containig a function signature and/or parameters:
    ///      port Node port for the communication inside the system
    ///      nonce Unique identifier of a current operation
    ///      ip IPv4 address of the node
    function createNode(address _from, uint _value, bytes _data) //internal
    {
        require(_value == DEPOSIT_VALUE);
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

    /// @dev Function for creating a mchain
    /// @param _from Transaction initiator, analogue of msg.sender
    /// @param _value Number of tokens to transfer.
    /// @param _data Data containig a function signature and/or parameters:
    ///      storageBytes Number of bytes this mchain can store
    ///      lifetime Number of seconds this mchain will be considered as alive
    ///      maxNodes Max number of nodes associated with this mchain
    ///      nonce Unique identifier of a current operation
    ///      name mchain name
    function createMchain(address _from, uint _value, bytes _data) internal {
        uint storageBytes;
        uint lifetime;
        uint maxNodes;
        uint16 nonce;
        bytes32 name;
        (storageBytes, lifetime, maxNodes, nonce, name) = fallbackCreateMchainDataConvert(_data);
        // mchain can live max 30 days
        require(lifetime <= MCHAIN_MAX_LIFETIME);
        mchain[nextMchainIndex].owner = _from;
        mchain[nextMchainIndex].storageBytes = storageBytes;
        mchain[nextMchainIndex].lifetime = lifetime;
        mchain[nextMchainIndex].maxNodes = maxNodes;
        mchain[nextMchainIndex].startDate = block.timestamp;
        mchain[nextMchainIndex].deposit = _value;
        mchainIndexes[_from].push(nextMchainIndex);
        MchainCreated(nextMchainIndex, _from, storageBytes, lifetime, maxNodes, _value, nonce, name);
        nextMchainIndex = nextMchainIndex + 1;
    }

    /// @dev Function for creating a aggregation mchain
    /// @param _from Transaction initiator, analogue of msg.sender
    /// @param _value Number of tokens to transfer.
    /// @param _data Data containig a function signature and/or parameters:
    ///      storageBytes Number of bytes this mchain can store
    ///      lifetime Number of seconds this mchain will be considered as alive
    ///      maxNodes Max number of nodes associated with this mchain
    ///      nonce Unique identifier of a current operation
    ///      name mchain name
    function createAggregationMchain(address _from, uint _value, bytes _data) internal {
        uint storageBytes;
        uint lifetime;
        uint maxNodes;
        uint16 nonce;
        bytes32 name;
        (storageBytes, lifetime, maxNodes, nonce, name) = fallbackCreateMchainDataConvert(_data);
        // mchain can live max 30 days
        require(lifetime <= MCHAIN_MAX_LIFETIME);
        aggregationMchain[nextAggregationMchainIndex].owner = _from;
        aggregationMchain[nextAggregationMchainIndex].storageBytes = storageBytes;
        aggregationMchain[nextAggregationMchainIndex].lifetime = lifetime;
        aggregationMchain[nextAggregationMchainIndex].maxNodes = maxNodes;
        aggregationMchain[nextAggregationMchainIndex].startDate = block.timestamp;
        aggregationMchain[nextAggregationMchainIndex].deposit = _value;
        aggregationMchainIndexes[_from].push(nextAggregationMchainIndex);
        AggregationMchainCreated(nextAggregationMchainIndex, _from, storageBytes,
                                    lifetime, maxNodes, _value, nonce, name);
        nextAggregationMchainIndex = nextAggregationMchainIndex + 1;
    }

    /// @dev Function for parsing first 2 data bytes to determine the type of the transaction operation
    /// @param data Data containig a function signature and/or parameters
    /// @return type of the transaction operation
     function fallbackOperationTypeConvert(bytes data)
        //internal
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
            return TransactionOperation.CreateMchain;
        } else {
            return TransactionOperation.CreateAggregationMchain;
        }

    }

    /// @dev Function for parsing data bytes to a set of parameters for node creation
    /// @param data Data containig a function signature and/or parameters
    /// @return parsed fallback parameters:
    ///      port Node port for the communication inside the system
    ///      nonce Unique identifier of a current operation
    ///      ip IPv4 address of the node
    function fallbackCreateNodeDataConvert(bytes data)
        //internal
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

    /// @dev Function for parsing data bytes to a set of parameters for mchain creation
    /// @param data Data containig a function signature and/or parameters
    /// @return parsed fallback parameters:
    ///      storageBytes Number of bytes this mchain can store
    ///      lifetime Number of seconds this mchain will be considered as alive
    ///      maxNodes Max number of nodes associated with this mchain
    ///      nonce Unique identifier of a current operation
    ///      name mchain name
    function fallbackCreateMchainDataConvert(bytes data)
        internal
        pure
        returns (uint, uint, uint, uint16, bytes32)
    {
        bytes32 storageBytes;
        bytes32 lifetime;
        bytes32 maxNodes;
        bytes4 nonce;
        bytes32 name;
        assembly {
            storageBytes := mload(add(data, 33))
            lifetime := mload(add(data, 65))
            maxNodes := mload(add(data, 97))
            nonce := mload(add(data, 129))
            name := mload(add(data, 133))
        }
        return (uint(storageBytes), uint(lifetime), uint(maxNodes), uint16(nonce), name);
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
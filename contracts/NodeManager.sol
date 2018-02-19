pragma solidity ^0.4.17;

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
    //  size of a deposit to add node to the system 100 * 10 ** 18
    uint public constant DEPOSIT_VALUE = 100000000000000000000;

    address tokenAddress; // address of the token contract
    uint annualMint; // total reword for nodes per year
    uint dailyMint; // daily reword for nodes

    struct Node {
        bytes4 ip;
        uint16 port;
        bytes publicKey; // ECDSA public key
        uint startDate; // date when node was registered
        uint leavingDate; // date when node was moved to the Leaving state
        uint lastRewardDate; // date when node was rewarded last time
        uint[2] heartbits; // bitmap of heartbit signals for last 512 days
        NodeStatus status;
    }

    struct Mchain {
        address owner; // mchain owner
        uint indexInOwnerList; // index in the mchainIndexes array
        uint storageBytes; // number of bytes this mchain can store
        uint cpu;
        uint transactionThroughput;
        uint lifetime;  // number of seconds this mchain will be considered as alive
        uint startDate; // date of mchain creation
        uint maxNodes; // max number of nodes associated with this mchain
        uint deposit; // value of tokens associated with this mchain
        string name; // mchain name
    }

    struct AggregationMchain {
        address owner; // mchain owner
        uint storageBytes; // number of bytes this mchain can store
        uint lifetime;  // number of seconds this mchain will be considered as alive
        uint startDate; // date of mchain creation
        uint maxNodes; // max number of nodes associated with this mchain
        uint deposit; // value of tokens associated with this mchain
        bytes32 name; // mchain name
        mapping (uint => bool) mchainsPresence; // mchains aggregated by this mchain
        uint[] mchains; // list of mchains associated with this aggregation mchain
        uint nextAggregatedMchainIndex; // index to store next mchain
    }

    // mapping of node index to a node instance
    mapping (uint => Node) nodes;
    // mapping of a mchain index to a mchain instance
    mapping (bytes32 => Mchain) mchain;
    // mapping of an aggregation mchain index to a aggregation mchain instance
    mapping (uint => AggregationMchain) aggregationMchain;
    // mapping of owner address to node indexes associated with it
    mapping (address => mapping (uint => bool)) nodeIndexes; // todo Note: we do not delete nodes
    // mapping of owner address to mchain indexes associated with it
    mapping (address => bytes32[]) mchainIndexes;
    // mapping of owner address to aggregation mchain indexes associated with it
    mapping (address => uint[]) aggregationMchainIndexes;
    uint nextNodeIndex; // index to store next node
    uint nextAggregationMchainIndex; // index to store next aggregation mchain

    /*
     *  Events
     */

    // todo remove
    event Test1(bytes32 a, bytes32 b);
    event Test2();
    //

    event NodeCreated(
        uint nodeID,
        address owner,
        bytes4 ip,
        uint16 port,
        uint16 nonce
    );

    event MchainCreated(
        string mchainID,
        address owner,
        uint storageBytes,
        uint lifetime,
        uint maxNodes,
        uint deposit,
        uint16 nonce
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

    event WithdrawFromMchain(
        address owner,
        uint deposit,
        string mchainID
    );

    event WithdrawFromAggregationMchain(
        address owner,
        uint deposit,
        uint mchainID
    );

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
    }

    /*
     *  Public functions
     */

    // /// @dev Function for adding an existed mchain to an existed aggregation mchain
    // /// @param aggregationMchainID Aggregation mchain index
    // /// @param mchainID Basic mchain index
    // /// @param nonce Unique identifier of a current operation
    // function addToAggregationMchain(
    //     uint aggregationMchainID,
    //     uint mchainID,
    //     uint16 nonce
    // )
    // public
    // {
    //     // msg.sender should be an owner of the aggregation mchain
    //     require(aggregationMchain[aggregationMchainID].owner == msg.sender);
    //     // mchain should be present
    //     require(aggregationMchain[mchainID].owner != address(0));
    //     // aggregation mchain must be alive
    //     require((aggregationMchain[aggregationMchainID].startDate +
    //     aggregationMchain[aggregationMchainID].lifetime) > block.timestamp);
    //     // mchain must be alive
    //     require((mchain[mchainID].startDate + mchain[mchainID].lifetime) > block.timestamp);
    //     // mchain must expire before aggregation mchain
    //     require((mchain[mchainID].startDate + mchain[mchainID].lifetime) <
    //           (aggregationMchain[aggregationMchainID].startDate + aggregationMchain[aggregationMchainID].lifetime));
    //     // check that mchain is not present in the aggregation mchain already
    //     require(!aggregationMchain[aggregationMchainID].mchainsPresence[mchainID]);
    //     aggregationMchain[aggregationMchainID].mchainsPresence[mchainID] = true;
    //     aggregationMchain[aggregationMchainID].mchains.push(mchainID);
    //     aggregationMchain[aggregationMchainID].nextAggregatedMchainIndex += 1;
    //     MchainAdded(aggregationMchainID, mchainID, nonce);
    // }

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

    /// @dev Function withdraws deposit from a mchain with given id and deletes this mchain
    /// @param mchainId Id of mchain
    function withdrawFromMchain(string mchainId) public {
        bytes32 id = keccak256(mchainId);
        require(mchain[id].startDate + mchain[id].lifetime < block.timestamp);
        uint withdraw = mchain[id].deposit;
        deleteMchain(id);
        GeToken(tokenAddress).transfer(msg.sender, withdraw);
        WithdrawFromMchain(msg.sender, withdraw, mchainId);
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
        // todo uncomment and move to the end on the function
        // WithdrawFromAggregationMchain(msg.sender, withdraw, aggregationMchainIndexes[msg.sender][index]);
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

    /* todo result array may be huge and contain a lot of 0 because of non active nodes. Use DoublyLinkedList? The same
       for the methods below
    */
    /// @dev Function returns an ip list of all Active nodes
    /// @return ip list
    function getActiveNodeIPs()
        public
        view
        returns (bytes4[] memory arr)
    {
        arr = new bytes4[](nextNodeIndex);
        uint j = 0;
        for (uint i = 1; i < nextNodeIndex; i++) {
            if(nodes[i].status == NodeStatus.Active){
                arr[j] = nodes[i].ip;
                j++;
            }
        }
    }

    /// @dev Function returns an ip list of all Active nodes with given indexes
    /// @return ip list
    function getActiveNodeIPs(uint[] id)
        public
        view
        returns (bytes4[] memory arr)
    {
        arr = new bytes4[](nextNodeIndex);
        uint j = 0;
        for (uint i = 0; i < id.length; i++) {
            if(nodes[id[i]].status == NodeStatus.Active){
                arr[j] = nodes[id[i]].ip;
                j++;
            }
        }
    }

    //// @dev Function returns an start dates list of all Active nodes with given indexes
    /// @return start dates  list
    function getActiveNodeStartDates(uint[] id)
        public
        view
        returns (uint[] memory arr)
    {
        arr = new uint[](nextNodeIndex);
        uint j = 0;
        for (uint i = 0; i < id.length; i++) {
            if(nodes[id[i]].status == NodeStatus.Active){
                arr[j] = nodes[id[i]].startDate;
                j++;
            }
        }
    }

    /// @dev Function returns an indexes list of all Active nodes
    /// @return indexes list
    function getActiveNodeIDs()
        public
        view
        returns (uint[] memory arr)
    {
        arr = new uint[](nextNodeIndex);
        uint j = 0;
        for (uint i = 1; i < nextNodeIndex; i++) {
            if(nodes[i].status == NodeStatus.Active){
                arr[j] = i;
                j++;
            }
        }
    }

    //// Next methods don't have any checks - they will return empty values if not present

    /// @dev Function returns an node info by index
    /// @return node info
    ///     ip IP address of node
    ///     port TCP PORT of node
    ///     status Node status
    ///     key Node account public key
    ///     lastRewardDate Date when node was rewarded last time
    ///     leavingDate Date when node was moved to the Leaving state
    ///     startDate Date when node was registered
    function getNode(uint index)
        public
        view
        returns (bytes4, uint16, NodeStatus, bytes, uint, uint, uint)
    {
        return (nodes[index].ip, nodes[index].port, nodes[index].status, nodes[index].publicKey,
            nodes[index].lastRewardDate, nodes[index].leavingDate, nodes[index].startDate);
    }

    /// @dev Function returns an mchain info by index
    /// @return mchain info
    ///      owner Mchain owner address
    ///      name Mchain name
    ///      storageBytes Number of bytes this mchain can store
    ///      lifetime Number of seconds this mchain will be considered as alive
    ///      startDate Number of seconds of mchain creation
    ///      maxNodes Max number of nodes associated with this mchain
    ///      deposit Value of tokens associated with this mchain
    function getMchain(string mchainId)
        public
        view
        returns (address, string, uint, uint, uint, uint, uint, uint, uint)
    {
        bytes32 id = keccak256(mchainId);
        return (mchain[id].owner,
                mchain[id].name,
                mchain[id].storageBytes,
                mchain[id].cpu,
                mchain[id].transactionThroughput,
                mchain[id].lifetime,
                mchain[id].startDate,
                mchain[id].maxNodes,
                mchain[id].deposit);
    }

    /// @dev Function returns an aggregation mchain info by index
    /// @return basis mchain info
    ///      owner Mchain owner address
    ///      name Mchain name
    ///      storageBytes Number of bytes this mchain can store
    ///      lifetime Number of seconds this mchain will be considered as alive
    ///      startDate Number of seconds of mchain creation
    ///      maxNodes Max number of nodes associated with this mchain
    ///      deposit Value of tokens associated with this mchain
    function getAggregationMchain(uint index)
        public
        view
        returns (address, bytes32, uint, uint, uint, uint, uint)
    {
        return (aggregationMchain[index].owner, aggregationMchain[index].name, aggregationMchain[index].storageBytes,
            aggregationMchain[index].lifetime, aggregationMchain[index].startDate, aggregationMchain[index].maxNodes,
            aggregationMchain[index].deposit);
    }


    /// @dev Function returns mchain indexes array associated with the aggregation mchain
    /// @return mchain indexes list
    function getMchainListFromAggregationMchain(uint index)
        public
        view
        returns (uint[])
    {
        return aggregationMchain[index].mchains;
    }


    // /// @dev Function returns mchain ids associated with  msg.sender
    // /// @return mchain ids list
    // function getMchainList()
    //     public
    //     view
    //     returns (string[] ids)
    // {
    //     ids = new string[](mchainIndexes[msg.sender].length);
    //     for (uint i = 0; i < ids.length; ++i) {
    //         ids[i] = mchain[mchainIndexes[msg.sender][i]].name;
    //     }
    // }

    function getMchainListSize() public view returns (uint size) {
        return mchainIndexes[msg.sender].length;
    }

    function getMchainByIndex(uint index) public view
            returns (address, string, uint, uint, uint, uint, uint, uint, uint) {
        require(index < mchainIndexes[msg.sender].length);
        bytes32 id = mchainIndexes[msg.sender][index];
        return (mchain[id].owner,
                mchain[id].name,
                mchain[id].storageBytes,
                mchain[id].cpu,
                mchain[id].transactionThroughput,
                mchain[id].lifetime,
                mchain[id].startDate,
                mchain[id].maxNodes,
                mchain[id].deposit);
    }

    function getMchainIdByIndex(uint index) public view returns (string) {
        require(index < mchainIndexes[msg.sender].length);
        return mchain[mchainIndexes[msg.sender][index]].name;
    }

    /// @dev Function returns aggregation mchain indexes array associated with msg.sender
    /// @return aggregation mchain indexes list
    function getAggregationMchainList()
        public
        view
        returns (uint[])
    {
        return aggregationMchainIndexes[msg.sender];
    }

    /// @dev Function checks if provided mchainId exists
    /// @param mchainId id for check
    /// @return true if mchainId is not used
    function isMchainIdAvailable(string mchainId) public view returns(bool) {
        return mchain[keccak256(mchainId)].owner == address(0);
    }

    // /// @dev Function stores node heartbits and rewards node
    // ///      Heartbits is a bitmap which stores information about presence of a node in the system for last 512 days
    // ///      Each bit represents one day
    // /// @param nodeNumber Node index
    // // todo THIS FUNCTION WAS NOT TESTED AT ALL. see warning and see test_heartbit.py
    // function heartbit(uint nodeNumber) private { // todo make public
    //     require(nodeIndexes[msg.sender][nodeNumber]);
    //     uint index = block.timestamp / SECONDS_TO_DAY - 1;
    //     if (index >= HEARTBIT_TOTAL && index % HEARTBIT_UNIT == 0) {
    //         nodes[nodeNumber].heartbits[index % HEARTBIT_TOTAL / HEARTBIT_UNIT] = 0;
    //     }
    //     // since HEARTBIT_TOTAL = HEARTBIT_UNIT * 2
    //     // we can use % HEARTBIT_UNIT instead of % HEARTBIT_TOTAL % HEARTBIT_UNIT
    //     nodes[nodeNumber].heartbits[index % HEARTBIT_TOTAL / HEARTBIT_UNIT] =
    //         nodes[nodeNumber].heartbits[index % HEARTBIT_TOTAL / HEARTBIT_UNIT] | (1 << (index % HEARTBIT_UNIT));
    //     // if the last reward was more than 32 days ago - check node heartbit for this period and reward
    //     if (block.timestamp - nodes[nodeNumber].lastRewardDate >= PAYMENT_PERIOD){
    //         nodes[nodeNumber].lastRewardDate = block.timestamp;
    //         uint8 daysToPayFor = 0;
    //         for(uint8 i = 0; i < PAYMENT_DAYS; i++){
    //             if (nodes[nodeNumber].heartbits[index % HEARTBIT_TOTAL / HEARTBIT_UNIT] &
    //             (1 * 2 ** (index % HEARTBIT_UNIT)) != 0) {
    //                 daysToPayFor = daysToPayFor + 1;
    //                  // if node was absent more than 2 days - don't pay for whole payment period
    //                 if(i - daysToPayFor > ABSENT_DAYS){
    //                     return;
    //                 }
    //                 index = index - 1;
    //             }
    //         }
    //         // this transaction will work only if this contract is an owner of token contract
    //         GeToken(tokenAddress).mint(msg.sender, daysToPayFor * (dailyMint / getActiveNodesCount()));
    //         //tokenAddress.call(bytes4(sha3("transfer(address, uint)")), msg.sender,
    //         // dayToPayFor * (dailyMint / getActiveNodesCount()));
    //     }
    // }

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
    /// @param _data Data containing a function signature and/or parameters
    function tokenFallback(address _from, uint _value, bytes _data) public {
        require(msg.sender == tokenAddress);
        TransactionOperation operationType = fallbackOperationTypeConvert(_data);
        if(operationType == TransactionOperation.CreateNode) {
            // create node
            createNode(_from, _value, _data);
        } else if (operationType == TransactionOperation.CreateMchain) {
            // create mchain
            createMchain(_from, _value, _data);
        }
        // } else {
        //     // create aggregation mchain
        //     createAggregationMchain(_from, _value, _data);
        // }
    }

    /// @dev Function for creating a node
    /// @param _from Transaction initiator, analogue of msg.sender
    /// @param _value Number of tokens to transfer.
    /// @param _data Data containing a function signature and/or parameters:
    ///      port Node port for the communication inside the system
    ///      nonce Unique identifier of a current operation
    ///      ip IPv4 address of the node
    function createNode(address _from, uint _value, bytes _data) internal {
        require(_value == DEPOSIT_VALUE);
        uint16 nonce;
        (nodes[nextNodeIndex].port, nonce, nodes[nextNodeIndex].ip, nodes[nextNodeIndex].publicKey) =
                fallbackCreateNodeDataConvert(_data);
        require (nodes[nextNodeIndex].ip != 0x0); // todo add ip validation
        //  Port number is an unsigned 16-bit integer, so 65535 will the max value
        // todo discuss port range https://en.wikipedia.org/wiki/List_of_TCP_and_UDP_port_numbers
        require (nodes[nextNodeIndex].port > 0);
        nodes[nextNodeIndex].status = NodeStatus.Active;
        nodes[nextNodeIndex].lastRewardDate = block.timestamp;
        nodes[nextNodeIndex].startDate = block.timestamp;
        nodeIndexes[_from][nextNodeIndex] = true;
        NodeCreated(nextNodeIndex, _from, nodes[nextNodeIndex].ip, nodes[nextNodeIndex].port, nonce);
        nextNodeIndex = nextNodeIndex + 1;
    }

    /// @dev Function for creating a mchain
    /// @param _from Transaction initiator, analogue of msg.sender
    /// @param _value Number of tokens to transfer.
    /// @param _data Data containing a function signature and/or parameters:
    ///      storageBytes Number of bytes this mchain can store
    ///      lifetime Number of seconds this mchain will be considered as alive
    ///      maxNodes Max number of nodes associated with this mchain
    ///      nonce Unique identifier of a current operation
    ///      name mchain name
    function createMchain(address _from, uint _value, bytes _data) internal {
        uint16 nonce;
        Mchain memory newMchain;
        (newMchain, nonce) = fallbackCreateMchainDataConvert(_data);
        // mchain can live max 30 days
        require(newMchain.lifetime <= MCHAIN_MAX_LIFETIME);

        // name must be unique
        bytes32 id = keccak256(newMchain.name);
        require(mchain[id].owner == address(0));

        newMchain.owner = _from;
        newMchain.startDate = block.timestamp;
        newMchain.deposit = _value;

        mchain[id] = newMchain;
        mchain[id].indexInOwnerList = mchainIndexes[_from].length;
        mchainIndexes[_from].push(id);
        MchainCreated(newMchain.name, _from, newMchain.storageBytes, newMchain.lifetime,
            newMchain.maxNodes, _value, nonce);
    }

    /// @dev Function for deleting a mchain
    /// @param mchainId Id of mchain
    function deleteMchain(bytes32 mchainId) internal {
        require(mchain[mchainId].owner == msg.sender);

        uint index = mchain[mchainId].indexInOwnerList;

        // if the element is not last
        if(index != mchainIndexes[msg.sender].length - 1) {
            // move the last element to the place on the current element
            mchainIndexes[msg.sender][index] = mchainIndexes[msg.sender][mchainIndexes[msg.sender].length - 1];
            mchain[mchainIndexes[msg.sender][index]].indexInOwnerList = index;
        }
        // delete mchain from the mchain indexes list for msg.sender
        delete mchainIndexes[msg.sender][mchainIndexes[msg.sender].length - 1];
        mchainIndexes[msg.sender].length--;

        // delete mchain from the mchain list
        delete mchain[mchainId];
    }

    // /// @dev Function for creating a aggregation mchain
    // /// @param _from Transaction initiator, analogue of msg.sender
    // /// @param _value Number of tokens to transfer.
    // /// @param _data Data containing a function signature and/or parameters:
    // ///      storageBytes Number of bytes this mchain can store
    // ///      lifetime Number of seconds this mchain will be considered as alive
    // ///      maxNodes Max number of nodes associated with this mchain
    // ///      nonce Unique identifier of a current operation
    // ///      name mchain name
    // function createAggregationMchain(address _from, uint _value, bytes _data) internal {
    //     uint16 nonce;
    //     (aggregationMchain[nextAggregationMchainIndex].storageBytes,
    //             aggregationMchain[nextAggregationMchainIndex].lifetime,
    //             aggregationMchain[nextAggregationMchainIndex].maxNodes, nonce,
    //             aggregationMchain[nextAggregationMchainIndex].name) =
    //             fallbackCreateMchainDataConvert(_data);
    //     // mchain can live max 30 days
    //     require(aggregationMchain[nextAggregationMchainIndex].lifetime <= MCHAIN_MAX_LIFETIME);
    //     aggregationMchain[nextAggregationMchainIndex].owner = _from;
    //     aggregationMchain[nextAggregationMchainIndex].startDate = block.timestamp;
    //     aggregationMchain[nextAggregationMchainIndex].deposit = _value;
    //     aggregationMchainIndexes[_from].push(nextAggregationMchainIndex);
    //     AggregationMchainCreated(nextAggregationMchainIndex, _from,
    //             aggregationMchain[nextAggregationMchainIndex].storageBytes,
    //             aggregationMchain[nextAggregationMchainIndex].lifetime,
    //             aggregationMchain[nextAggregationMchainIndex].maxNodes, _value, nonce,
    //             aggregationMchain[nextAggregationMchainIndex].name);
    //     nextAggregationMchainIndex = nextAggregationMchainIndex + 1;
    // }

    /// @dev Function for parsing first 2 data bytes to determine the type of the transaction operation
    /// @param data Data containing a function signature and/or parameters
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
        require(operationType == 0x1 || operationType == 0x10 || operationType == 0x11);
        if(operationType == 0x1) {
            return TransactionOperation.CreateNode;
        } else if(operationType == 0x10) {
            return TransactionOperation.CreateMchain;
        } else {
            return TransactionOperation.CreateAggregationMchain;
        }

    }

    /// @dev Function for parsing data bytes to a set of parameters for node creation
    /// @param data Data containing a function signature and/or parameters
    /// @return parsed fallback parameters:
    ///      port Node port for the communication inside the system
    ///      nonce Unique identifier of a current operation
    ///      ip IPv4 address of the node
    function fallbackCreateNodeDataConvert(bytes data)
        internal
        pure
        returns (uint16, uint16, bytes4, bytes)
    {
        bytes4 port;
        bytes4 nonce;
        bytes4 ip;
        bytes memory publicKey = new bytes(64);
        bytes32 a;
        bytes32 b;
        assembly {
            port := mload(add(data, 33)) // 0x21
            nonce := mload(add(data, 37)) // 0x25
            ip := mload(add(data, 41)) // 0x29
            // todo this is hotfix to get public key with length 64 bytes
            a := mload(add(data, 45)) // 0x33
            b := mload(add(data, 77))
        }
        uint8 k = 0;
        for (uint8 i = 0; i < 32; i++) publicKey[k++] = a[i];
        for (i = 0; i < 32; i++) publicKey[k++] = b[i];
        return (uint16(port), uint16(nonce), ip, publicKey);
    }

    /// @dev Function for parsing data bytes to a set of parameters for mchain creation
    /// @param data Data containing a function signature and/or parameters
    /// @return parsed fallback parameters:
    ///      storageBytes Number of bytes this mchain can store
    ///      lifetime Number of seconds this mchain will be considered as alive
    ///      maxNodes Max number of nodes associated with this mchain
    ///      nonce Unique identifier of a current operation
    ///      name mchain name
    function fallbackCreateMchainDataConvert(bytes data)
        internal
        pure
        returns (Mchain _mchain, uint16 nonce)
    {
        require(data.length > 163);

        uint cursor = 1 + 32;
        _mchain.storageBytes = uint(readBytes32(data, cursor));
        cursor += 32;
        _mchain.cpu = uint(readBytes32(data, cursor));
        cursor += 32;
        _mchain.transactionThroughput = uint(readBytes32(data, cursor));
        cursor += 32;
        _mchain.lifetime = uint(readBytes32(data, cursor));
        cursor += 32;
        _mchain.maxNodes = uint(readBytes32(data, cursor));
        cursor += 32;
        nonce = uint16(readBytes2(data, cursor));
        cursor += 2;

        uint index = cursor - 32;
        _mchain.name = new string(data.length - index);
        for (uint i = 0; i < bytes(_mchain.name).length; ++i) {
            bytes(_mchain.name)[i] = data[index + i];
        }
    }

    function readBytes32(bytes data, uint cursor) internal pure returns (bytes32 result) {
        assembly {
            result := mload(add(data, cursor))
        }
    }

    function readBytes2(bytes data, uint cursor) internal pure returns (bytes2 result) {
        assembly {
            result := mload(add(data, cursor))
        }
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
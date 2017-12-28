pragma solidity ^0.4.15;


contract NodeRegistration {

    address public token_address;

    uint start_epoch;

    struct Node {
        uint256 deposit;
        bytes32 ip;
        uint port;
        uint deposit_date;
        uint leaving_date;
        uint last_reward_date;
        uint256[2] heartbits;
        uint status;
    }

    struct BasicChannel {
        address owner;
        uint256 storage_bytes;
        uint lifetime;
        uint starttime;
        uint max_nodes;
    }

    struct AggregationChannel {
        address owner;
        uint256 storage_bytes;
        uint lifetime;
        uint starttime;
        uint max_nodes;
        mapping (uint256 => bool) basic_channels;
        uint next_aggregated_basic_channel_index;
    }

    mapping (uint256 => Node) nodes;

    mapping (uint256 => BasicChannel) basic_channel;

    mapping (uint256 => AggregationChannel) aggregation_channel;

    mapping (address => uint256) node_indexes;

    uint256 next_node_index;

    uint256 next_basic_channel_index;

    uint256 next_aggregation_channel_index;

    event NodeCreated(uint256 node_id, bytes32 ip, uint port, uint nonce);

    event BasicChannelCreated(uint256 channel_id, address owner, uint256 storage_bytes, uint lifetime, uint max_nodes);

    event AggregationChannelCreated(uint256 channel_id, address owner, uint256 storage_bytes, uint lifetime, uint max_nodes);

    event BasicChannelAdded(uint256 aggregation_channel_id, uint256 basic_channel_id);

    function NodeRegistration(address _tokenContract){
        token_address = _tokenContract;
        start_epoch = block.timestamp;
    }

    function deposit(bytes32 ip, uint port, uint nonce) public {
        token_address.call(bytes4(sha3("transferFrom(address, address, uint256)")), msg.sender, this, 100);
        nodes[next_node_index].deposit = 100;
        nodes[next_node_index].ip = ip;
        nodes[next_node_index].port = port;
        nodes[next_node_index].status = 1; // todo
        nodes[next_node_index].last_reward_date = block.timestamp;
        nodes[next_node_index].deposit_date = block.timestamp;
        NodeCreated(next_node_index, ip, port, nonce);
        next_node_index = next_node_index + 1;
    }

    function heartbit() public {
        uint index = (block.timestamp - start_epoch) / 86400 - 1;  // 24*60*60
        if (index >= 256 && index % 256 == 0) {
            nodes[node_indexes[msg.sender]].heartbits[index % 2] = 0;
        }
        nodes[node_indexes[msg.sender]].heartbits[index % 2] = nodes[next_node_index].heartbits[index % 2] | (1 << (index % 256)); // bitwise_or
        // reward
        if (block.timestamp - nodes[next_node_index].last_reward_date >= 2764800){// 32*60*60*24
            nodes[next_node_index].last_reward_date = block.timestamp;
        // todo send reward
        // Token(self.token_address).transfer(msg.sender, as_num256(what))
        }
    }

    function createBasicChannel(address owner, uint256 storage_bytes, uint lifetime, uint max_nodes) public {
        basic_channel[next_basic_channel_index].owner = owner;
        basic_channel[next_basic_channel_index].storage_bytes = storage_bytes;
        basic_channel[next_basic_channel_index].lifetime = lifetime;
        basic_channel[next_basic_channel_index].max_nodes = max_nodes;
        basic_channel[next_basic_channel_index].starttime = block.timestamp;
        BasicChannelCreated(next_basic_channel_index, owner, storage_bytes, lifetime, max_nodes);
        next_basic_channel_index = next_basic_channel_index + 1;
    }

    function createAggregationChannel(address owner, uint256 storage_bytes, uint lifetime, uint max_nodes) public {
        aggregation_channel[next_aggregation_channel_index].owner = owner;
        aggregation_channel[next_aggregation_channel_index].storage_bytes = storage_bytes;
        aggregation_channel[next_aggregation_channel_index].lifetime = lifetime;
        aggregation_channel[next_aggregation_channel_index].max_nodes = max_nodes;
        aggregation_channel[next_aggregation_channel_index].starttime = block.timestamp;
        AggregationChannelCreated(next_aggregation_channel_index, owner, storage_bytes, lifetime, max_nodes);
        next_aggregation_channel_index = next_aggregation_channel_index + 1;
    }

    function addToAggregationChannel(uint256 aggregation_channel_id, uint256 basic_channel_id){
        // basic channel should be present
        require(aggregation_channel[basic_channel_id].owner != address(0));
        // aggregation channel should be present
        require(aggregation_channel[aggregation_channel_id].owner != address(0));
        // aggregation channel must be alive
        require((aggregation_channel[aggregation_channel_id].starttime + aggregation_channel[aggregation_channel_id].lifetime) > block.timestamp);
        // basic channel must be alive
        require((basic_channel[basic_channel_id].starttime + basic_channel[basic_channel_id].lifetime) > block.timestamp);
        // basic channel must expire before aggregation channel
        require((basic_channel[basic_channel_id].starttime + basic_channel[basic_channel_id].lifetime) <
               (aggregation_channel[aggregation_channel_id].starttime + aggregation_channel[aggregation_channel_id].lifetime));
        // check that basic channel is not present in the aggregation channel already
        require(!aggregation_channel[aggregation_channel_id].basic_channels[basic_channel_id]);
        aggregation_channel[aggregation_channel_id].basic_channels[basic_channel_id] = true;
        aggregation_channel[aggregation_channel_id].next_aggregated_basic_channel_index += 1;
        BasicChannelAdded(aggregation_channel_id, basic_channel_id);
    }

    function initWithdrawDeposit(uint256 node_number) public {
        require(node_indexes[msg.sender] == node_number);
        require(nodes[node_number].status == 1);
        nodes[node_number].status = 2;
        nodes[node_number].leaving_date = block.timestamp;
    }

    // todo remove node number
    function completeWithdrawDeposit(uint256 node_number) public {
        require(node_indexes[msg.sender] == node_number);
        require(nodes[node_number].status == 2);
        require(block.timestamp - nodes[node_number].leaving_date >= 5260000);  // 2 month. 3 month will be 7890000
        nodes[node_number].deposit = 0;
        nodes[node_number].status = 3;
        // todo check that channels are closed
        // remove from list
        // Token(self.token_address).transferFrom(self, msg.sender, as_num256(self.nodes[node_number].deposit))
        token_address.call(bytes4(sha3("transfer(address, uint256)")), msg.sender, 100);
    }

    function getNodeIPs() public returns (bytes32[]) {
        bytes32[] arr;
        uint j =0;
        for (uint i = 0; i < next_node_index; i++) {
            if(nodes[i].status == 1){
                arr[j] = nodes[i].ip;
                j++;
            }
        }
        return arr;
    }
}

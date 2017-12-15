class Token():
    def transferFrom(_from: address, _to: address, _value: num(num256)) -> bool: pass

    def transfer(_to: address, _amount: num(num256)) -> bool: pass


NodeCreated: __log__({node_id: num256, node_ip: bytes32, port: num, nonce: num})
BasicChannelCreated: __log__(
    {channel_id: num256, owner: address, storage_bytes: num256, lifetime: timedelta, max_nodes: num})
AggregationChannelCreated: __log__(
    {channel_id: num256, owner: address, storage_bytes: num256, lifetime: timedelta, max_nodes: num})
BasicChannelAdded: __log__({aggregation_channel_id: num256, basic_channel_id: num256})
NewNumber: __log__({name: num})

#   Node status:
#   0 - NOT SET
#   1 - ACTIVE
#   2 - LEAVING
#   3 - DEAD

nodes: public({
                  deposit: num,  # type ? num decimal(wei) wei_value currency_value
                  node_ip: bytes32,
                  port: num,
                  status: num,
                  deposit_date: timestamp,
                  leaving_date: timestamp,
                  last_reward_date: timestamp,
                  heartbits: num256[2]
              }[num256])

next_node_index: public(num256)
next_basic_channel_index: public(num256)
next_aggregation_channel_index: public(num256)
# Mapping of node's signature address to their index number
node_indexes: public(num256[address])

token_address: public(address)
start_epoch: timestamp

basic_channel: public({
                          owner: address,
                          storage_bytes: num256,
                          lifetime: timedelta,
                          starttime: timestamp,
                          max_nodes: num
                      }[num])

# todo add max number of basic channels
aggregation_channel: public({
                                owner: address,
                                storage_bytes: num256,
                                lifetime: timedelta,
                                starttime: timestamp,
                                max_nodes: num,
                                basic_channels: bool[num256],
                                next_aggregated_basic_channel_index: num
                            }[num])

new_number: public(num)


@public
def __init__(_token_address: address):
    # starts with 1 because 0 is an empty value
    self.token_address = _token_address
    self.next_node_index = as_num256(1)
    self.next_basic_channel_index = as_num256(1)
    self.next_aggregation_channel_index = as_num256(1)
    self.new_number = 1
    self.start_epoch = 1513296000  # 15 December 2017 00:00:00


@public
@payable
def deposit(node_ip: bytes32, port: num, nonce: num):
    # in client call 'token_contract.transact({'from': <from_address>}).approve(<this_contract_address>, amount)' first
    # todo send in wei
    Token(self.token_address).transferFrom(msg.sender, self, as_num256(100))
    # todo save nonce
    self.nodes[self.next_node_index].deposit = 100
    self.nodes[self.next_node_index].node_ip = node_ip
    self.nodes[self.next_node_index].port = port
    self.nodes[self.next_node_index].status = 1
    self.nodes[self.next_node_index].deposit_date = block.timestamp
    self.nodes[self.next_node_index].last_reward_date = block.timestamp
    self.node_indexes[msg.sender] = self.next_node_index
    log.NodeCreated(self.next_node_index, node_ip, port, nonce)
    self.next_node_index = num256_add(self.next_node_index, as_num256(1))


@public
def heartbit():
    day = (block.timestamp - self.start_epoch) / 86400  # 24*60*60
    j = day - 1
    if j % 2 == 1:
        if j >= 256 and j % 256 == 0:
            self.nodes[self.node_indexes[msg.sender]].heartbits[1] = as_num256(0)
        self.nodes[self.node_indexes[msg.sender]].heartbits[1] = bitwise_or(
            self.nodes[self.next_node_index].heartbits[1], shift(as_num256(1), j % 256))
    else:
        if j >= 256 and j % 256 == 0:
            self.nodes[self.node_indexes[msg.sender]].heartbits[0] = as_num256(0)
        self.nodes[self.node_indexes[msg.sender]].heartbits[0] = bitwise_or(
            self.nodes[self.next_node_index].heartbits[0], shift(as_num256(1), j % 256))
        # reward
    if block.timestamp - self.nodes[self.next_node_index].last_reward_date >= 2764800:  # 32*60*60*24
        self.nodes[self.next_node_index].last_reward_date = block.timestamp
        # todo send reward


@public
def createBasicChannel(owner: address, storage_bytes: num256, lifetime: timedelta, max_nodes: num):
    self.basic_channel[self.next_basic_channel_index] = {
        owner: owner,
        storage_bytes: storage_bytes,
        lifetime: lifetime,
        max_nodes: max_nodes,
        starttime: block.timestamp
    }
    log.BasicChannelCreated(self.next_basic_channel_index, owner, storage_bytes, lifetime, max_nodes)
    self.next_basic_channel_index = num256_add(self.next_basic_channel_index, as_num256(1))


@public
def createAggregationChannel(owner: address, storage_bytes: num256, lifetime: timedelta, max_nodes: num):
    self.aggregation_channel[self.next_aggregation_channel_index].owner = owner
    self.aggregation_channel[self.next_aggregation_channel_index].storage_bytes = storage_bytes
    self.aggregation_channel[self.next_aggregation_channel_index].lifetime = lifetime
    self.aggregation_channel[self.next_aggregation_channel_index].starttime = block.timestamp
    self.aggregation_channel[self.next_aggregation_channel_index].max_nodes = max_nodes
    self.aggregation_channel[self.next_aggregation_channel_index].next_aggregated_basic_channel_index = 1
    log.AggregationChannelCreated(self.next_aggregation_channel_index, owner, storage_bytes, lifetime, max_nodes)
    self.next_aggregation_channel_index = num256_add(self.next_aggregation_channel_index, as_num256(1))


@public
def addToAggregationChannel(aggregation_channel_id: num256, basic_channel_id: num256):
    # basic channel should be present
    assert not not self.aggregation_channel[basic_channel_id].owner
    # aggregation channel should be present
    assert not not self.aggregation_channel[aggregation_channel_id].owner
    # aggregation channel must be alive
    assert (self.aggregation_channel[aggregation_channel_id].starttime + self.aggregation_channel[
        aggregation_channel_id].lifetime) > block.timestamp
    # basic channel must be alive
    assert (self.basic_channel[basic_channel_id].starttime + self.basic_channel[
        basic_channel_id].lifetime) > block.timestamp
    # basic channel must expire before aggregation channel
    assert (self.basic_channel[basic_channel_id].starttime + self.basic_channel[basic_channel_id].lifetime) < \
           (self.aggregation_channel[aggregation_channel_id].starttime + self.aggregation_channel[
               aggregation_channel_id].lifetime)
    # check that basic channel is not present in the aggregation channel already
    assert not self.aggregation_channel[aggregation_channel_id].basic_channels[basic_channel_id]
    self.aggregation_channel[aggregation_channel_id].basic_channels[basic_channel_id] = true
    self.aggregation_channel[aggregation_channel_id].next_aggregated_basic_channel_index += 1
    log.BasicChannelAdded(aggregation_channel_id, basic_channel_id)


# todo remove
@public
def garbageCollectBasticChannel(channel_id: num256):
    assert not not self.basic_channel[channel_id].owner
    assert (self.basic_channel[channel_id].starttime + self.basic_channel[channel_id].lifetime) < block.timestamp
    self.basic_channel[channel_id] = {
        owner: None,
        storage_bytes: as_num256(0),
        lifetime: 0,
        max_nodes: 0,
        starttime: 0
    }


# todo remove
@public
def garbageCollectAggregationChannel(channel_id: num256):
    assert not not self.aggregation_channel[channel_id].owner
    # because basic channel can be added to an aggregation channel only if its lifetime is less then an aggregation channel lifetime
    # there is no need to check basic channels lifetime
    assert (self.aggregation_channel[channel_id].starttime + self.aggregation_channel[
        channel_id].lifetime) < block.timestamp
    self.aggregation_channel[self.next_aggregation_channel_index].owner = None
    self.aggregation_channel[self.next_aggregation_channel_index].storage_bytes = as_num256(0)
    self.aggregation_channel[self.next_aggregation_channel_index].lifetime = 0
    self.aggregation_channel[self.next_aggregation_channel_index].starttime = 0
    self.aggregation_channel[self.next_aggregation_channel_index].max_nodes = 0
    self.aggregation_channel[self.next_aggregation_channel_index].next_aggregated_basic_channel_index = 0
    # todo delete basic_channels


@public
def initWithdrawDeposit(node_number: num256):
    assert self.node_indexes[msg.sender] == node_number
    assert self.nodes[node_number].status == 1
    self.nodes[node_number].status = 2
    self.nodes[node_number].leaving_date = block.timestamp


# todo remove node number
@public
def completeWithdrawDeposit(node_number: num256):
    assert self.node_indexes[msg.sender] == node_number
    assert self.nodes[node_number].status == 2
    assert block.timestamp - self.nodes[node_number].leaving_date >= 5260000  # 2 month. 3 month will be 7890000
    # todo check that channels are closed
    # remove from list
    # Token(self.token_address).transferFrom(self, msg.sender, as_num256(self.nodes[node_number].deposit))
    Token(self.token_address).transfer(msg.sender, as_num256(self.nodes[node_number].deposit))
    self.nodes[node_number].deposit = 0
    self.nodes[node_number].status = 3


@public
@constant
def getNodeStatus(node_number: num) -> num:
    assert self.nodes[as_num256(node_number)].status != 0
    return self.nodes[as_num256(node_number)].status


@public
def setNumber(n: num):
    self.new_number = n
    log.NewNumber(self.new_number)


@public
@constant
def getNumber() -> num:
    return self.new_number


@public
@constant
def getTokenAddress() -> address:
    return self.token_address

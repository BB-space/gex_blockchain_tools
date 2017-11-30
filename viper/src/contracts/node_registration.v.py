class Token():
    def transferFrom(_from: address, _to: address, _value: num(num256)) -> bool: pass


BasicChannelCreated: __log__(
    {channel_id: num256, owner: address, storage_bytes: num256, lifetime: timedelta, number_of_nodes: num})
AggregationChannelCreated: __log__(
    {channel_id: num256, owner: address, storage_bytes: num256, lifetime: timedelta, number_of_nodes: num})

#   Node status:
#   0 - ACTIVE
#   1 - LEAVING
#   2 - DEAD


# Information about nodes
nodes: public({
                  deposit: num,  # type ? num decimal(wei) wei_value currency_value
                  node_ip: bytes <= 100,
                  user_port: num,
                  cluster_port: num,
                  status: num,
                  deposit_date: timestamp
              }[num])

# Number of nodes
next_node_index: public(num)
# Chennel indexes
next_basic_channel_index: public(num256)
next_aggregation_channel_index: public(num256)

# Mapping of node's signature address to their index number
node_indexes: public(num[address])

token_address: public(address)

basic_channel: public({
                          owner: address,
                          storage_bytes: num256,
                          lifetime: timedelta,
                          starttime: timestamp,
                          number_of_nodes: num
                      }[num])

aggregation_channel: public({
                                owner: address,
                                storage_bytes: num256,
                                lifetime: timedelta,
                                starttime: timestamp,
                                number_of_nodes: num,
                                basic_channels: num256[num],
                                next_aggregated_basic_channel_index: num
                            }[num])


@public
def _init_(token: address):
    # starts with 1 because 0 is an empty value
    self.token_address = token
    self.next_node_index = as_num256(1)
    self.next_basic_channel_index = as_num256(1)
    self.next_aggregation_channel_index = as_num256(1)


@public
@payable
def deposit(owner: address, amount: num, node_ip: bytes <= 100, user_port: num, cluster_port: num):
    assert amount >= 100
    # in client call 'token_contract.transact({'from': <from_address>}).approve(<this_contract_address>, amount)' first
    Token(self.token_address).transferFrom(msg.sender, self, as_num256(amount))
    self.nodes[self.next_node_index] = {
        deposit: amount,
        node_ip: node_ip,
        user_port: user_port,
        cluster_port: cluster_port,
        status: 0,
        deposit_date: block.timestamp
    }
    self.next_node_index += 1
    # user can make another person a deposit owner
    # one nobe can have only one node
    self.node_indexes[owner] = self.next_node_index
    # todo save address to immutable list


@public
def createBasicChannel(owner: address, storage_bytes: num256, lifetime: timedelta, number_of_nodes: num):
    self.basic_channel[self.next_basic_channel_index] = {
        owner: owner,
        storage_bytes: storage_bytes,
        lifetime: lifetime,
        number_of_nodes: number_of_nodes,
        starttime: block.timestamp
    }
    # todo add some unique property
    log.BasicChannelCreated(self.next_basic_channel_index, owner, storage_bytes, lifetime, number_of_nodes)
    self.next_basic_channel_index = num256_add(self.next_basic_channel_index, as_num256(1))


@public
def createAggregationChannel(owner: address, storage_bytes: num256, lifetime: timedelta, number_of_nodes: num):
    # self.aggregation_channel[self.next_aggregation_channel_index] = {
    #    owner: owner,
    #    storage_bytes: storage_bytes,
    #    lifetime: lifetime,
    #    number_of_nodes: number_of_nodes,
    #    starttime: block.timestamp,
    #    basic_channels: None,  # null
    #    next_aggregated_basic_channel_index: 0
    # }
    self.aggregation_channel[self.next_aggregation_channel_index].owner = owner
    self.aggregation_channel[self.next_aggregation_channel_index].storage_bytes = storage_bytes
    self.aggregation_channel[self.next_aggregation_channel_index].lifetime = lifetime
    self.aggregation_channel[self.next_aggregation_channel_index].starttime = block.timestamp
    self.aggregation_channel[self.next_aggregation_channel_index].number_of_nodes = number_of_nodes
    self.aggregation_channel[self.next_aggregation_channel_index].next_aggregated_basic_channel_index = 1
    # todo add some unique property
    # todo add basic_chennels list
    log.AggregationChannelCreated(self.next_aggregation_channel_index, owner, storage_bytes, lifetime, number_of_nodes)
    self.next_aggregation_channel_index = num256_add(self.next_aggregation_channel_index, as_num256(1))


@public
def addToAggregationChannel(new_basic_channel: num256, aggregation_channel_id: num256):
    # todo for array
    # check this assert
    assert not not self.aggregation_channel[aggregation_channel_id].owner
    self.aggregation_channel[aggregation_channel_id].basic_channels[
        self.aggregation_channel[aggregation_channel_id].next_aggregated_basic_channel_index] = \
        new_basic_channel
    self.aggregation_channel[aggregation_channel_id].next_aggregated_basic_channel_index += 1


@public
def garbageCollectBasticChannel(channel_id: num256):
    self.basic_channel[channel_id] = {
        owner: None,
        storage_bytes: as_num256(0),
        lifetime: 0,
        number_of_nodes: 0,
        starttime: 0
    }


@public
def garbageCollectAggregationChannel(channel_id: num256):
    # check that all other channels are closed
    self.aggregation_channel[self.next_aggregation_channel_index].owner = None
    self.aggregation_channel[self.next_aggregation_channel_index].storage_bytes = as_num256(0)
    self.aggregation_channel[self.next_aggregation_channel_index].lifetime = 0
    self.aggregation_channel[self.next_aggregation_channel_index].starttime = 0
    self.aggregation_channel[self.next_aggregation_channel_index].number_of_nodes = 0
    self.aggregation_channel[self.next_aggregation_channel_index].next_aggregated_basic_channel_index = 0
    # basic_channels


# Withdraw node deposit, and remove the node from the node list.
@public
def initWithdrawDeposit(node_number: num):
    assert self.node_indexes[msg.sender] == node_number
    assert self.nodes[node_number].status == 0
    # todo add node status check to other methods
    self.nodes[node_number].status = 1
    # only owner can withdraw? if somebody make another person an owner. who will withdraw?


@public
def completeWithdrawDeposit(node_number: num):
    assert self.nodes[node_number].status == 1
    # tdo check that channels are closed
    # send money
    # remove from list
    self.nodes[node_number].status = 2


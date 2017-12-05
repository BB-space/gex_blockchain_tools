class Token():
    def transferFrom(_from: address, _to: address, _value: num(num256)) -> bool: pass

NodeCreated: __log__({node_id: num256, node_ip: bytes32, user_port: num, cluster_port: num})
BasicChannelCreated: __log__(
    {channel_id: num256, owner: address, storage_bytes: num256, lifetime: timedelta, number_of_nodes: num})
AggregationChannelCreated: __log__(
    {channel_id: num256, owner: address, storage_bytes: num256, lifetime: timedelta, number_of_nodes: num})
NewNumber: __log__({name: num})

#   Node status:
#   0 - NOT SET
#   1 - ACTIVE
#   2 - LEAVING
#   3 - DEAD

# Information about nodes
nodes: public({
                  deposit: num,  # type ? num decimal(wei) wei_value currency_value
                  node_ip: bytes32,
                  user_port: num,
                  cluster_port: num,
                  status: num,
                  deposit_date: timestamp
              }[num256])

next_node_index: public(num256)
next_basic_channel_index: public(num256)
next_aggregation_channel_index: public(num256)
# Mapping of node's signature address to their index number
node_indexes: public(num256[address])

token_address: public(address)

new_number: public(num)

@public
def _init_():
    #token: address
    # starts with 1 because 0 is an empty value
    self.token_address = msg.sender
    self.next_node_index = as_num256(1)
    self.next_basic_channel_index = as_num256(1)
    self.next_aggregation_channel_index = as_num256(1)
    self.new_number = 1

@public
@payable
def deposit(owner: address, amount: num, node_ip: bytes32, user_port: num, cluster_port: num):
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
    log.NodeCreated(self.next_node_index, node_ip, user_port, cluster_port)
    # user can make another person a deposit owner
    # one node can have only one node
    self.node_indexes[owner] = self.next_node_index
    self.next_node_index = num256_add(self.next_node_index, as_num256(1))
    # todo save address to immutable list

@public
def setNumber(n: num):
    self.new_number = n
    log.NewNumber(self.new_number)


@public
@constant
def getNumber() -> num:
    return self.new_number
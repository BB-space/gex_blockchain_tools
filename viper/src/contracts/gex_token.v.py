# Events of the token.
Transfer: __log__({_from: indexed(address), _to: indexed(address), _value: num256})
Approval: __log__({_owner: indexed(address), _spender: indexed(address), _value: num256})
Mint: __log__({ _to: indexed(address), _amount: num})
Burn: __log__({ _from: indexed(address), _amount: num})

# Variables of the token.
name: bytes32
symbol: bytes32
totalSupply: num
cap: num
decimals: num
balances: num[address]
allowed: num[address][address]
# todo
owners: address[2]

@public
def __init__(_name: bytes32, _symbol: bytes32, _decimals: num, _cap: num, _initialSupply: num):
    self.name = _name
    self.symbol = _symbol
    self.decimals = _decimals
    self.totalSupply = _initialSupply * 10 ** _decimals
    self.cap = _cap * 10 ** _decimals
    self.balances[msg.sender] = self.totalSupply
    self.owners[0] = msg.sender

@public
def set_owner(i: num, new_owner: address):
    assert msg.sender in self.owners
    self.owners[i] = new_owner

@public
def is_owner() -> bool:
    return msg.sender in self.owners

@public
def mint(_to: address, _amount: num):
    assert self.is_owner(msg.sender)
    assert self.totalSupply + _amount <= self.cap
    self.totalSupply = self.totalSupply + _amount
    self.balances[_to] = self.balances[_to] + _amount
    log.Mint(_to, _amount)

@public
def burn(_from: address, _amount: num):
    assert self.is_owner(msg.sender)
    assert self.balances[_from] >= _amount
    self.balances[_from] = self.balances[_from] - _amount
    self.totalSupply = self.totalSupply - _amount
    log.Burn(_from, _amount)


@public
@constant
def symbol() -> bytes32:
    return self.symbol


@public
@constant
def name() -> bytes32:
    return self.name

@public
@constant
def cap() -> num:
    return self.cap

# What is the balance of a particular account?
@public
@constant
def balanceOf(_owner: address) -> num256:
    return as_num256(self.balances[_owner])


# Return total supply of token.
@public
@constant
def totalSupply() -> num256:
    return as_num256(self.totalSupply)


# Send `_value` tokens to `_to` from your account
@public
def transfer(_to: address, _amount: num(num256)) -> bool:
    assert self.balances[msg.sender] >= _amount
    assert self.balances[_to] + _amount >= self.balances[_to]

    self.balances[msg.sender] -= _amount  # Subtract from the sender
    self.balances[_to] += _amount  # Add the same to the recipient
    log.Transfer(msg.sender, _to, as_num256(_amount))  # log transfer event.

    return True


# Transfer allowed tokens from a specific account to another.
@public
def transferFrom(_from: address, _to: address, _value: num(num256)) -> bool:
    assert _value <= self.allowed[_from][msg.sender]
    assert _value <= self.balances[_from]

    self.balances[_from] -= _value  # decrease balance of from address.
    self.allowed[_from][msg.sender] -= _value  # decrease allowance.
    self.balances[_to] += _value  # incease balance of to address.
    log.Transfer(_from, _to, as_num256(_value))  # log transfer event.

    return True


# Allow _spender to withdraw from your account, multiple times, up to the _value amount.
# If this function is called again it overwrites the current allowance with _value.
#
# NOTE: To prevent attack vectors like the one described here and discussed here,
#       clients SHOULD make sure to create user interfaces in such a way that they
#       set the allowance first to 0 before setting it to another value for the
#       same spender. THOUGH The contract itself shouldn't enforce it, to allow
#       backwards compatilibilty with contracts deployed before.
#
@public
def approve(_spender: address, _amount: num(num256)) -> bool:
    self.allowed[msg.sender][_spender] = _amount
    log.Approval(msg.sender, _spender, as_num256(_amount))

    return True


# Get the allowance an address has to spend anothers' token.
@public
def allowance(_owner: address, _spender: address) -> num256:
    return as_num256(self.allowed[_owner][_spender])
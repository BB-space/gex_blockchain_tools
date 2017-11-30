class Token():
    def transferFrom(_from: address, _to: address, _value: num(num256)) -> bool: pass
    def balanceOf(_owner: address) -> num256: pass

Before: __log__({_owner: indexed(address)})
After: __log__()

@public
def bar(arg1: address, _from: address, _to: address, _value: num):
    log.Before(msg.sender)
    Token(arg1).transferFrom(_from, _to, as_num256(_value))
    #Token(arg1).balanceOf(_from)
    log.After()

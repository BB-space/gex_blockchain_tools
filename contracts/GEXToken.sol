pragma solidity ^0.4.0;


import './token/StandardToken.sol';
import './Ownable.sol';

contract GEXToken is StandardToken, Ownable {
    event Mint(address indexed to, uint256 amount);

    event Burn(address indexed from, uint256 amount);

    function GEXToken(){}

    function mint(address _to, uint256 _amount) onlyOwner returns (bool) {
        totalSupply = totalSupply.add(_amount);
        balances[_to] = balances[_to].add(_amount);
        Mint(_to, _amount);
        return true;
    }

    function burn(address _from, uint _amount)  onlyOwner returns (bool) {
        require(balances[_from] >= _amount);
        balances[_from] = balances[_from].sub(_amount);
        totalSupply = totalSupply.sub(_amount);
        Burn(_from, _amount);
        return true;
    }
}

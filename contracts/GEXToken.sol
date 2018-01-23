pragma solidity ^0.4.15;


import './token_223/StandardToken.sol';
import './Ownable.sol';


contract GEXToken is StandardToken, Ownable {

    string public constant name = "Galactic Exchange Token";

    string public constant symbol = "GEX";

    uint public constant decimals = 18;

    uint public constant cap = 100000 * 10 ** decimals; // the maximum amount of tokens that can ever be created

    event Mint(address indexed to, uint256 amount);

    event Burn(address indexed from, uint256 amount);

    function GEXToken(){
        balances[msg.sender] = 1000 * 10 ** decimals;
        // TODO remove after testing
    }

    function mint(address _to, uint256 _amount)
        onlyOwner
        public
        returns (bool)
    {
        require(totalSupply + _amount <= cap);
        totalSupply = totalSupply + _amount;
        balances[_to] = balances[_to] + _amount;
        Mint(_to, _amount);
        return true;
    }

    function burn(address _from, uint256 _amount)
        onlyOwner
        public
        returns (bool)
    {
        require(balances[_from] >= _amount);
        balances[_from] = balances[_from] - _amount;
        totalSupply = totalSupply - _amount;
        Burn(_from, _amount);
        return true;
    }
}

pragma solidity ^0.4.0;


import './token_20/StandardToken.sol'; // TODO rewrite for token_223
import './Ownable.sol';


contract GEXToken is StandardToken, Ownable {

    string public constant name = "Galactic Exchange Token";

    string public constant symbol = "GEX";

    uint8 public constant decimals = 18;

    uint public constant cap = 100000 * decimals; // the maximum amount of tokens that can ever be created

    event Mint(address indexed to, uint256 amount);

    event Burn(address indexed from, uint256 amount);

    function GEXToken(){
    }

    function mint(address _to, uint256 _amount) onlyOwner returns (bool) {
        require(totalSupply.add(_amount) <= cap);
        totalSupply = totalSupply.add(_amount);
        balances[_to] = balances[_to].add(_amount);
        Mint(_to, _amount);
        return true;
    }

    function burn(address _from, uint _amount) onlyOwner returns (bool) {
        require(balances[_from] >= _amount);
        balances[_from] = balances[_from].sub(_amount);
        totalSupply = totalSupply.sub(_amount);
        Burn(_from, _amount);
        return true;
    }
}

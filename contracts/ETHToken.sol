pragma solidity ^0.4.15;


import './token_223/StandardToken.sol';
import './Ownable.sol';
import './SafeMath.sol';


contract ETHToken is StandardToken, Ownable {

    using SafeMath for uint;

    string public constant name = "Galactic Exchange Token";

    string public constant symbol = "GEX";

    uint public constant decimals = 18;

    uint public constant cap = 100000 * 10 ** decimals; // the maximum amount of tokens that can ever be created

    event Mint(address indexed to, uint amount);

    event Burn(address indexed from, uint amount);

    event MintStart(address indexed to, uint amount);

    event BurnStart(address indexed from, uint amount);

    event Test(address addr);


    function ETHToken(){
        balances[msg.sender] = 1000 * 10 ** decimals;
        // TODO remove after testing
    }

    function getOwner() public returns (address){
        return owner;
    }

    function t(){
        Test(msg.sender);
    }

    function mint(address _to, uint _amount) onlyOwner returns (bool) {
        MintStart(_to, _amount);
        require(totalSupply.add(_amount) <= cap);
        totalSupply = totalSupply.add(_amount);
        balances[_to] = balances[_to].add(_amount);
        Mint(_to, _amount);
        return true;
    }

    function burn(address _from, uint _amount) onlyOwner returns (bool) {
        BurnStart(_from, _amount);
        require(balances[_from] >= _amount);
        balances[_from] = balances[_from].sub(_amount);
        totalSupply = totalSupply.sub(_amount);
        Burn(_from, _amount);
        return true;
    }
}

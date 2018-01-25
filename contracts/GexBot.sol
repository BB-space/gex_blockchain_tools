pragma solidity ^0.4.16;

interface Token1 {
    function transfer2(
        address _to,
        uint256 _value
    )
        public
        returns (bool success);
    function balanceOf(address _owner) public constant returns (uint balance);
}

contract GexBot {

    struct Cell {
        bool active;
        uint88 amountEth;
        uint88 amountGex;
        uint88 loanEth;
        uint88 loanGex;
        int88 sendEth;
        int88 sendGex;
    }

    uint88 private gexInitialReserve;
    uint88 private ethInitialReserve;
    uint40 private numberOfAddresses;
    uint88 public currentGex;
    uint88 public currentEth;
    uint88 private previousGex;
    uint88 private previousEth;
    uint40 public previousTime;
    uint24 constant private DAY = 85800;
    address private gexAddress;
    address public owner;

    mapping (address => Cell) public applications;
    mapping (uint40 => address) private addresses;

    event Fee(uint88 value);
    event ExchangedRateOfDay(
        uint88 exchangeRateUp,
        uint88 exchangeRateDown
    );
    event Message(
        string inf,
        address sender,
        uint88 value
    );

    function GexBot(address _address) public {
        gexAddress = _address;
        owner = msg.sender;
        previousEth = 1000000000000000000000; //like initial reserve
        previousGex = 1000000000000000000000; //like initial reserve
        previousTime = uint40(block.timestamp);
    }

    //Manager function
    function transferOwnership(address newOwner) public {
        require(owner == msg.sender);
        require(newOwner != address(0));
        owner = newOwner;
    }

    function destroy() public {
        require(msg.sender == owner);
        uint256 balance = Token1(gexAddress).balanceOf(address(this));
        require(Token1(gexAddress).transfer2(owner, balance));
        selfdestruct(owner);
    }

    //converting functions
    function stringToUint(bytes _data) private pure returns (uint) {
        uint answer;
        uint step = 1;
        for (uint i = _data.length; i > 0; i--) {
            if ((uint(_data[i - 1]) >= 48 && uint(_data[i - 1]) <= 57)) {
                answer += (uint(_data[i - 1]) - 48) * step;
                step *= 10;
            } else return 0;
        }
        return answer;
    }

    function bytesToUint(bytes _data) public pure returns (uint x) {
        require(_data.length <= 32);
        uint step = 1;
        for (uint i = _data.length; i > 0; i--) {
            x += (uint(_data[i - 1]) % 16 + (uint(_data[i - 1]) / 16) * 16) * step;
            step *= 256;
        }
    }

    //Fallback function
    function () public payable { depositEth(""); }

    //Fallback function ERC-223
    function tokenFallback(
        address _sender,
        uint256 _value,
        bytes _data
    )
        public
    {
        require(msg.sender == gexAddress);
        require(_value > 0);
        if (_data.length == 0) {
            depositGex(_sender, uint88(_value), 0);
        } else {
            bytes26 flag;
            bytes26 addReserveKey = bytes26("addgalacticexchangereserve");
            assembly {
                flag := mload(add(_data, 0x20))
            }
            if (_sender == owner && flag == addReserveKey) {
                gexInitialReserve += uint88(_value);
            } else {
                depositGex(_sender, uint88(_value), uint88(bytesToUint(_data)));
            }
        }
    }

    //Public functions
    function depositEth(bytes _data) public payable {
        require(previousTime + DAY > block.timestamp);
        uint88 _fee = uint88(bytesToUint(_data));
        if (_data.length != 0) {
            bytes26 flag;
            bytes26 addReserveKey = bytes26("addgalacticexchangereserve");
            assembly {
                flag := mload(add(_data, 0x20))
            }
            if (flag == addReserveKey && msg.sender == owner) {
                ethInitialReserve += uint88(msg.value);
                return;
            }
        }
        uint88 amountEth = uint88(msg.value);
        require(amountEth >= _fee);
        int88 debt = -applications[msg.sender].sendEth;
        if (debt > 0) {
            if (amountEth >= uint88(debt)) {
                amountEth -= uint88(debt);
                applications[msg.sender].sendEth = 0;
            } else {
                applications[msg.sender].sendEth += int88(amountEth);
                amountEth = 0;
            }
            Message(
                "Debt paid in eth",
                msg.sender,
                uint88(msg.value - amountEth)
            );
        }
        if (amountEth > 0) {
            uint40 index = numberOfAddresses;
            if (!applications[msg.sender].active) {
                applications[msg.sender].active = true;
                addresses[index] = msg.sender;
                numberOfAddresses++;
            }
            //amountEth -= fee(amountEth, true);
            if (lazyFee(amountEth, _fee, true)) {
                amountEth -= _fee;
            } else {
                amountEth -= fee(amountEth,true);
            }
            applications[msg.sender].amountEth += amountEth;
            currentEth += uint88(amountEth);
            uint88 amount = uint88((uint256((amountEth * 80) / 100) *
                uint256(previousGex + currentGex)) /
                uint256(previousEth + currentEth));
            applications[msg.sender].loanGex += amount;
            transferGex(
                msg.sender,
                amount,
                "Order is accepted and loan is sent in gex"
            );
        } else {
            Message("Order is not accepted", msg.sender, 0);
        }
    }

    function returnGex() public {
        require(applications[msg.sender].sendGex > 0);
        uint88 amount = uint88(applications[msg.sender].sendGex);
        applications[msg.sender].sendGex = 0;
        transferGex(msg.sender, amount, "Send gex successfully");
    }

    function returnEth() public {
        require(applications[msg.sender].sendEth > 0);
        uint88 amount = uint88(applications[msg.sender].sendEth);
        applications[msg.sender].sendEth = 0;
        transferEth(msg.sender, amount, "Send eth successfully");
    }

    function timeToChange() public {
        require(previousTime + DAY < block.timestamp);
        require(msg.sender == owner);
        uint88 totalEth = currentEth;
        uint88 totalGex = currentGex;
        if (numberOfAddresses > 0) {
            uint40 index = numberOfAddresses;
            address account;
            Cell storage cell = applications[addresses[0]];
            uint40 max = 0;
            if (index > 10) {
                max = index - 10;
            }
            for (int40 step = int40(index) - 1; step >= int40(max); step--) {
                account = addresses[uint40(step)];
                cell = applications[account];
                if (totalGex > 0) {
                    applications[account].sendEth +=
                        int88(((int256(cell.amountGex) * int256(totalEth)) /
                        int256(totalGex)) - int256(cell.loanEth));
                }
                applications[account].amountGex = 0;
                applications[account].loanEth = 0;
                if (totalEth > 0) {
                    applications[account].sendGex +=
                        int88(((int256(cell.amountEth) * int256(totalGex)) /
                        int256(totalEth)) - int256(cell.loanGex));
                }
                applications[account].amountEth = 0;
                applications[account].loanGex = 0;
                applications[account].active = false;
                delete(addresses[uint40(step)]);
            }
            numberOfAddresses -= index - max;
        }
        if (numberOfAddresses == 0) {
            previousTime = uint40(block.timestamp);
            previousEth = totalEth;
            previousGex = totalGex;
            ExchangedRateOfDay(totalEth, totalGex);
            currentGex = 0;
            currentEth = 0;
        }
        transferEth(
            msg.sender,
            uint88(msg.gas * tx.gasprice),
            "Spent money was sent back"
        );
    }

    //Private functions
    function depositGex(address _sender, uint88 _amount, uint88 _fee) private {
        require(previousTime + DAY > block.timestamp);
        require(_amount >= _fee);
        uint88 amountGex = _amount;
        int88 debt = -applications[_sender].sendGex;
        if (debt > 0) {
            if (_amount >= uint88(debt)) {
                amountGex -= uint88(debt);
                applications[_sender].sendGex = 0;
            } else {
                amountGex = 0;
                applications[_sender].sendGex += int88(_amount);
            }
            Message("Debt paid in gex", _sender, _amount - amountGex);
        }
        if (amountGex > 0) {
            uint40 index = numberOfAddresses;
            if (!applications[_sender].active) {
                applications[_sender].active = true;
                addresses[index] = _sender;
                numberOfAddresses++;
            }
            //amountGex -= fee(amountGex, false);
            if (lazyFee(amountGex, _fee, false)) {
                amountGex -= _fee;
            } else {
                amountGex -= fee(amountGex, false);
            }
            applications[_sender].amountGex += uint88(amountGex);
            currentGex += uint88(amountGex);
            uint88 amount = uint88((uint256((amountGex * 80) / 100) *
                uint256(previousEth + currentEth)) /
                uint256(previousGex + currentGex));
            applications[_sender].loanEth += uint88(amount);
            transferEth(
                _sender,
                amount,
                "Order is accepted and loan is sent in eth"
            );
        } else {
            Message("Order is not accepted", _sender, 0);
        }
    }

    function lazyFee(
        uint88 _amount,
        uint88 _fee,
        bool _ethCur
    )
        private
        view
        returns (bool)
    {
        uint88 amountToOrder = _amount - _fee;
        uint88 reserve;
        uint88 up;
        uint88 down;
        uint88 initialReserve;
        uint88 stateReserve;
        if (_ethCur) {
            up = previousGex + currentGex;
            down = previousEth + currentEth;
            initialReserve = gexInitialReserve;
            stateReserve = uint88(Token1(gexAddress).balanceOf(address(this)));
        } else {
            up = previousEth + currentEth;
            down = previousGex + currentGex;
            initialReserve = ethInitialReserve;
            stateReserve = uint88(this.balance);
        }
        reserve = stateReserve -
            uint88((uint256(amountToOrder * 80) / 100 *
            uint256(up)) / uint256(down + amountToOrder));
        uint88 formula = uint88((uint256(initialReserve) *
            uint256(initialReserve - reserve) * uint256(amountToOrder)) /
            (4 * uint256(reserve) * uint256(reserve)));
        return _amount >= amountToOrder + formula;
    }

    function fee(       //up to 30 000 gas
        uint88 _amount,
        bool _ethCur
    )
        private
        returns (uint88)
    {
        uint88 amountToOrder = _amount;
        uint88 amountToOrderPrevious;
        uint88 reserve;
        uint88 up;
        uint88 down;
        uint88 initialReserve;
        uint88 stateReserve;
        if (_ethCur) {
            up = previousGex + currentGex;
            down = previousEth + currentEth;
            initialReserve = gexInitialReserve;
            stateReserve = uint88(Token1(gexAddress).balanceOf(address(this)));
        } else {
            up = previousEth + currentEth;
            down = previousGex + currentGex;
            initialReserve = ethInitialReserve;
            stateReserve = uint88(this.balance);
        }
        for (uint8 step = 0; step < 20; step++) {
            amountToOrderPrevious = amountToOrder;
            reserve = stateReserve -
                uint88((uint256(amountToOrderPrevious * 80) / 100 *
                uint256(up)) / uint256(down + amountToOrderPrevious));
            if (reserve >= initialReserve) {
                amountToOrder = _amount;
            } else {
                amountToOrder = uint88((uint256(_amount) * 4 *
                    uint256(reserve) * uint256(reserve)) /
                    (uint256(initialReserve) *
                    uint256(initialReserve - reserve) +
                    4 * uint256(reserve) * uint256(reserve)));
            }
            if (amountToOrderPrevious == amountToOrder) {
                break;
            }
        }
        reserve = stateReserve -
                uint88((uint256(amountToOrder * 80) / 100 *
                uint256(up)) / uint256(down + amountToOrder));
        if (reserve >= initialReserve) {
            amountToOrder = 0;
        } else {
            amountToOrder = uint88((uint256(initialReserve) *
                uint256(initialReserve - reserve) *
                uint256(amountToOrder)) /
                (4 * uint256(reserve) * uint256(reserve)));
        }
        Fee(amountToOrder);
        return amountToOrder;
    }

    function transferGex(       //up to 42 000 gas
        address _sender,
        uint88 _amount,
        string _message
    )
        private
    {
        Message(_message, _sender, _amount);
        require(Token1(gexAddress).transfer2(_sender, _amount));
    }

    function transferEth(       //up to 35 000 gas
        address _sender,
        uint88 _amount,
        string _message
    )
        private
    {
        Message(_message, _sender, _amount);
        _sender.transfer(_amount);
    }
}
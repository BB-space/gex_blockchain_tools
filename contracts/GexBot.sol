pragma solidity ^0.4.13;

interface Token1 {
    function transfer(address _to, uint256 _value) public returns(bool success);
    function balanceOf(address _owner) public returns(uint balance);
}

contract GexBot{
    uint256 public GexInitialReserve;
    uint256 public EthInitialReserve;
    uint256 public currentDay;
    uint256 public numberOfTransactions;

    Token1 public token;

    struct Order {
    uint256 amount;
    uint256 lended;
    uint256 day;
    }

    struct Debt {
    uint256 amountGex;
    uint256 amountEth;
    }

    mapping (address => uint256[]) public transactionGex;
    mapping (address => uint256[]) public transactionEth;
    mapping (uint256 => Order) public orderByTransaction;
    mapping (address => Debt) public arrears;
    mapping (uint256 => uint256[2]) public exchangeRate;               //exchange_rate = total_eth / total_gex   1 GEX = ETH / exchange_rate

    address public GexAddress;

    address public owner;

    modifier onlyOwner {
        require(msg.sender == owner);
        _;
    }

    event OrderDone(uint256 transaction);
    event OrderUndone(address sender);
    event lendDone(uint256 transaction);
    event lendUndone(uint256 transaction);
    event debtsPaymentEthDone(address sender, uint256 value);
    event debtsPaymentGexDone(address sender, uint256 value);
    event transferGexDone(address sender, uint256 value);
    event transferGexUndone(address sender, uint256 value);
    event transferEthDone(address sender, uint256 value);
    event transferEthUndone(address sender, uint256 value);
    event debtGex(address sender, uint256 value);
    event debtEth(address sender, uint256 value);
    event Fee(uint256 value);
    event exchangedRateOfDay(uint256 day, uint256 exchangeRateUp, uint256 exchangeRateDown);

    function GexBot(address _address) payable {
        owner = msg.sender;

        GexAddress = _address;
        token = Token1(GexAddress);
        EthInitialReserve = msg.value;
        GexInitialReserve = 0;
        currentDay = 1;
    }

    function tokenFallback(address _sender, uint256 _value, bytes _data) public {
        require(msg.sender == GexAddress);

        if (_data.length == 0) {
            putGex(_sender, _value);
        } else {
            bytes1 flag;
            assembly {
            flag := mload(add(_data, 0x20))
            }
            if (_sender == owner && flag == bytes1(18)) {
                GexInitialReserve += _value;
            } else if (flag == bytes1(13)){
                debtsPaymentGEX(_sender, _value);
            } else {
                putGex(_sender, _value);
            }
        }
    }

    function putEth() public payable {
        uint256 amountEth = msg.value;
        uint256 day = currentDay;
        uint256 nOT = numberOfTransactions;
        uint256 debt = arrears[msg.sender].amountEth;
        if (debt > 0) {
            if (amountEth >= debt) {
                amountEth -= debt;
                arrears[msg.sender].amountEth = 0;
            } else {
                arrears[msg.sender].amountEth -= amountEth;
                amountEth = 0;
            }
            debtsPaymentEthDone(msg.sender, msg.value - amountEth);
        }
        if (amountEth != 0) {
            amountEth -= feeETHtoGEX(amountEth);
            orderByTransaction[nOT] = Order({
            amount: amountEth,
            lended: 0,
            day: day
            });

            transactionEth[msg.sender].push(nOT);


            OrderDone(nOT);
            exchangeRate[currentDay % 100][0] += amountEth;
            uint256[2] storage rate1 = exchangeRate[(currentDay - 1) % 100];
            uint256[2] storage rate = exchangeRate[currentDay % 100];
            if (rate1[0] + rate[0] > 0 && rate1[1] + rate[1] > 0) {
                orderByTransaction[nOT].lended += transferGEX(msg.sender, (((amountEth * 80) / 100) * (rate1[1] + rate[1])) / (rate1[0] + rate[0]));
                lendDone(nOT);
            } else {
                lendUndone(nOT);
            }

            numberOfTransactions++;
        } else {
            OrderUndone(msg.sender);
        }
    }

    function feeETHtoGEX(uint256 _amount) public returns(uint256 amount) {
        uint256 amountToOrder = _amount;
        uint256 amountToOrderPrevious;
        uint256 reserve;
        uint256[2] storage rate1 = exchangeRate[(currentDay - 1) % 100];
        uint256[2] storage rate = exchangeRate[currentDay % 100];
        uint256 GIR = GexInitialReserve;
        uint256 GR = uint256(token.balanceOf(address(this)));
        do {
            amountToOrderPrevious = amountToOrder;
            reserve = GR - ((amountToOrderPrevious * 80) / 100 * (rate1[1] + rate[1])) / (rate1[0] + rate[0] + amountToOrderPrevious);
            if (reserve >= GIR) {
                amountToOrder = _amount;
            } else {
                amountToOrder = (_amount * 4 * reserve * reserve) / (GIR * (GIR - reserve) + 4 * reserve * reserve);
            }
        } while (amountToOrderPrevious != amountToOrder);
        reserve = GR - ((amountToOrder * 80) / 100 * (rate1[1] + rate[1])) / (rate1[0] + rate[0] + amountToOrder);
        if (reserve >= GIR) {
            amount = 0;
        } else {
            amount = (GIR * (GIR - reserve) * amountToOrder) / (4 * reserve * reserve);
        }
        Fee(amount);
    }

    function debtsPaymentETH() public payable {
        uint256 amount = msg.value;
        uint256 debt = arrears[msg.sender].amountEth;
        if (debt > 0) {
            if (amount >= debt) {
                amount -= debt;
                arrears[msg.sender].amountEth = 0;
            } else {
                arrears[msg.sender].amountEth -= amount;
                amount = 0;
            }
            debtsPaymentEthDone(msg.sender, msg.value - amount);
        }
    }

    function putGex(address _sender, uint256 _amount) private {
        require(msg.sender == GexAddress);
        uint256 amountGex = _amount;
        uint256 day = currentDay;
        uint256 nOT = numberOfTransactions;
        uint256 debt = arrears[_sender].amountGex;
        if (debt > 0) {
            if (_amount >= debt) {
                amountGex -= debt;
                arrears[_sender].amountGex = 0;
            } else {
                amountGex = 0;
                arrears[_sender].amountGex -= _amount;
            }
            debtsPaymentGexDone(_sender, _amount - amountGex);
        }
        if (amountGex != 0) {
            amountGex -= feeGEXtoETH(amountGex);
            orderByTransaction[nOT] = Order({
            amount: amountGex,
            lended: 0,
            day: day
            });

            transactionGex[_sender].push(nOT);


            OrderDone(nOT);
            exchangeRate[currentDay % 100][1] += amountGex;
            uint256[2] storage rate1 = exchangeRate[(currentDay - 1) % 100];
            uint256[2] storage rate = exchangeRate[currentDay % 100];
            if ((rate1[0] + rate[0]) > 0 && (rate1[1] + rate[1]) > 0) {
                orderByTransaction[nOT].lended += transferETH(_sender, (((amountGex * 80) / 100) * (rate1[0] + rate[0])) / (rate1[1] + rate[1]));
                lendDone(nOT);
            } else {
                lendUndone(nOT);
            }

            numberOfTransactions++;
        } else {
            OrderUndone(_sender);
        }
    }

    function feeGEXtoETH(uint256 _amount) public returns(uint256 amount) {
        uint256 amountToOrder = _amount;
        uint256 amountToOrderPrevious;
        uint256 reserve;
        uint256[2] storage rate1 = exchangeRate[(currentDay - 1) % 100];
        uint256[2] storage rate = exchangeRate[currentDay % 100];
        uint256 EIR = EthInitialReserve;
        uint256 ER = uint256(this.balance);
        do {
            amountToOrderPrevious = amountToOrder;
            reserve = ER - ((amountToOrderPrevious * 80) / 100 * (rate1[0] + rate[0])) / (rate1[1] + rate[1] + amountToOrderPrevious);
            if (reserve >= EIR) {
                amountToOrder = _amount;
            } else {
                amountToOrder = (_amount * 4 * reserve * reserve) / (EIR * (EIR - reserve) + 4 * reserve * reserve);
            }
        } while (amountToOrderPrevious != amountToOrder);
        reserve = ER - ((amountToOrder * 80) / 100 * (rate1[0] + rate[0])) / (rate1[1] + rate[1] + amountToOrder);
        if (reserve >= EIR) {
            amount = 0;
        } else {
            amount = (EIR * (EIR - reserve) * amountToOrder) / (4 * reserve * reserve);
        }
        Fee(amount);
    }

    function debtsPaymentGEX(address _sender, uint256 _amount) public {
        uint256 amount = _amount;
        uint256 debt = arrears[_sender].amountGex;
        if (debt > 0) {
            if (amount >= debt) {
                amount -= debt;
                arrears[_sender].amountGex = 0;
            } else {
                arrears[_sender].amountGex -= amount;
                amount = 0;
            }
            debtsPaymentGexDone(_sender, _amount - amount);
        }
    }

    function returnGEX() public {
        uint256 amountGex = 0;
        uint256 lendedGex = 0;
        uint256 index = 0;
        uint256 state = 0;
        uint256 day = currentDay;
        uint256[] storage tE = transactionEth[msg.sender];
        Order storage order = orderByTransaction[tE[index]];
        do{
            order = orderByTransaction[tE[index]];
            if (order.day < day) {
                if (day - order.day < 100) {
                    amountGex += (order.amount * exchangeRate[order.day % 100][1]) / exchangeRate[order.day % 100][0];
                    lendedGex += order.lended;
                }
            }
            index++;
        } while (index < tE.length && order.day < day);

        if (order.day < day) {
            state = index;
        } else {
            state = index - 1;
        }

        if (amountGex < lendedGex) {
            arrears[msg.sender].amountGex += lendedGex - amountGex;
            debtGex(msg.sender, lendedGex - amountGex);
        } else if (amountGex > lendedGex) {
            transferGEX(msg.sender, amountGex - lendedGex);
        }
        if (state > 0) {
            for (index = state; index < tE.length; index++) {
                transactionEth[msg.sender][index - state] = tE[index];
            }
            for (index = tE.length - state; index < tE.length; index++) {
                delete(transactionEth[msg.sender][index]);
            }
            transactionEth[msg.sender].length -= state;
        }
    }

    function returnETH() public {
        uint256 amountEth = 0;
        uint256 lendedEth = 0;
        uint256 index = 0;
        uint256 state = 0;
        uint256 day = currentDay;
        uint256[] storage tG = transactionGex[msg.sender];
        Order storage order = orderByTransaction[tG[index]];
        do {
            order = orderByTransaction[tG[index]];
            if (order.day < day) {
                if (day - order.day < 100) {
                    amountEth += (order.amount * exchangeRate[order.day % 100][0]) / exchangeRate[order.day % 100][1];
                    lendedEth += order.lended;
                }
            }
            index++;
        } while (index < tG.length && order.day < day);

        if (order.day < day) {
            state = index;
        } else {
            state = index - 1;
        }

        if (amountEth < lendedEth) {
            arrears[msg.sender].amountEth += lendedEth - amountEth;
            debtEth(msg.sender, lendedEth - amountEth);
        } else if (amountEth > lendedEth) {
            transferETH(msg.sender, amountEth - lendedEth);
        }

        if (state > 0) {
            for (index = state; index < tG.length; index++) {
                transactionGex[msg.sender][index - state] = tG[index];
            }
            for (index = tG.length - state; index < tG.length; index++) {
                delete(transactionGex[msg.sender][index]);
            }
            transactionGex[msg.sender].length -= state;
        }
    }

    function transferGEX(address _sender, uint256 _amount) private returns(uint256 amount) {
        amount = _amount;
        transferGexDone(_sender, _amount);
        require(token.transfer(_sender, _amount));
    }

    function transferETH(address _sender, uint256 _amount) private returns(uint256 amount) {
        amount = _amount;
        transferEthDone(_sender, _amount);
        _sender.transfer(amount);
    }

    function timeToChange() public onlyOwner {
        uint256 day = currentDay;
        uint256[2] storage rate= exchangeRate[day % 100];
        /*if (rate[0] == 0 && rate[1] == 0) {
            exchangeRate[day % 100][0] = exchangeRate[(day - 1) % 100][0];
            exchangeRate[day % 100][1] = exchangeRate[(day - 1) % 100][1];
        }*/
        exchangedRateOfDay(day, rate[0], rate[1]);
        currentDay++;
    }
}
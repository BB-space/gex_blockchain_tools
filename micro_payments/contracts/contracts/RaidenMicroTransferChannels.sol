pragma solidity ^0.4.15;

import "../../contracts/token_223/Token.sol";
import "../../contracts/lib/ECVerify.sol";
import "../../contracts/NodeContract.sol";

/// @title Raiden MicroTransfer Channels Contract.
contract RaidenMicroTransferChannels {

    /*
     *  Data structures
     */
    enum ClosingStatus {Cheating, Good, Overspend}

    address public owner;
    address public token_address;
    uint8 public challenge_period;
    uint8 public channel_lifetime;
    string constant prefix = "\x19Ethereum Signed Message:\n";
    uint constant D160 = 0x10000000000000000000000000000000000000000;

    Token token;

    mapping (bytes32 => Channel) channels;
    mapping (bytes32 => ClosingRequest) closing_requests;


    struct Channel {
        uint192 deposit; // amount of the coins (tokens) in the channel
        uint32 open_block_number; // number of the block when the channel was opened
        uint32 collateral; // the amount of coins to be paid out to the person who proved that the sender is cheating
        uint32 channel_fee; // fee the sender pays to the nodes that maintain the channel
        address[] maintaining_nodes; // nodes that maintain the channel, currently 3 is required
        address topic_holder_node; // the node that hosts the payment kafka topic
        bytes32 random_n;
    }

    struct ClosingRequest {
        uint32 settle_block_number; // the block when the channel can be settled
        ClosingStatus closing_status; // the closing status of the channel
        uint256[] closing_balances_data; // the data, which will be used to settle the channel
    }

    /*
     *  Modifiers
     */

    modifier isToken() {
        require(msg.sender == token_address);
        _;
    }

    /*
     *  Events
     */

    event ChannelCreated(
        address indexed _sender,
        uint192 _deposit,
        uint32 _channel_fee,
        bytes32 _random_n);

    event ChannelToppedUp (
        address indexed _sender,
        uint32 indexed _open_block_number,
        uint192 _added_deposit,
        uint192 _deposit);

    event ChannelCloseRequested(
        address indexed _sender,
        uint256[] _payment_data,
        uint32 indexed _open_block_number);

    event ChannelSettled(
        address indexed _sender,
        uint256[] _payment_data,
        uint32 indexed _open_block_number);

    event MaintainerRegistered(
        address indexed _sender,
        uint32 indexed _open_block_number,
        address indexed _maintainer);

    event ChannelTopicCreated(
        address indexed _sender,
        uint32 indexed _open_block_number,
        address indexed _topic_holder);

    event CollateralPayed(
        address indexed _sender,
        uint32 indexed _open_block_number,
        uint32 _collateral);

    event GasCost(
        string _function_name,
        uint _gaslimit,
        uint _gas_remaining);

    /*
     *  Constructor
     */

    /// @dev Constructor for creating the Raiden microtransfer channels contract.
    /// @param _token The address of the token_223 used by the channels.
    /// @param _challenge_period A fixed number of blocks representing the challenge period after a sender requests the closing of the channel without the receivers's signature.
    function RaidenMicroTransferChannels(address _token, uint8 _challenge_period, uint8 _channel_lifetime) {
        require(_token != 0x0);
        require(_challenge_period > 0);
        require(_channel_lifetime > 0);

        owner = msg.sender;
        token_address = _token;
        token = Token(_token);

        challenge_period = _challenge_period;
        channel_lifetime = _channel_lifetime;
    }

    /*
     *  Public helper functions (constant)
     */

    /// @dev Returns the unique channel identifier used in the contract.
    /// @param _sender The address that sends tokens.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @return Unique channel identifier.
    function getKey(
        address _sender,
        uint32 _open_block_number)
        public
        constant
        returns (bytes32 data)
    {
        return sha3(_sender, _open_block_number);
    }

    /// @dev Returns a hash of the balance message needed to be signed by the sender.
    /// @param _open_block_number The block number at which a channel between the sender and receivers was created.
    /// @param _payment_data The array of uint256 incoded (balance, address) pairs
    /// @return Hash of the balance message.
    function getBalanceMessage(
        address _sender,
        uint32 _open_block_number,
        uint256[] _payment_data)
        public
        constant
        returns (string)
    {
        string memory str = concat("Key: ", bytes32ToString(getKey(_sender, _open_block_number)));
        str = concat(str, ", Data: ");
        for (i = 0; i < data.length; i++){
            str = concat(str, uintToString(uint256(data[i])));
        }
        return str;
    }

    // 56014 gas cost
    /// @dev Returns the sender address extracted from the balance proof.
    /// @param _sender The address that sends tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receivers was created.
    /// @param _payment_data The array of uint256 incoded (balance, address) pairs
    /// @param _balance_msg_sig The balance message signed by the sender or one of the receivers.
    /// @return Address of the balance proof signer.
    function verifyBalanceProof(  // TODO Check that the order of elements in array does not change! (shouldn't)
        address _sender,
        uint32 _open_block_number,
        uint256[] _payment_data,
        bytes _balance_msg_sig)
        public
        constant
        returns (address)
    {
        //GasCost('close verifyBalanceProof getBalanceMessage start', block.gaslimit, msg.gas);
        // Create message which should be signed by sender
        string memory message = getBalanceMessage(_sender, _open_block_number, _payment_data);
        //GasCost('close verifyBalanceProof getBalanceMessage end', block.gaslimit, msg.gas);

        //GasCost('close verifyBalanceProof length start', block.gaslimit, msg.gas);
        // 2446 gas cost
        uint256 message_length = bytes(message).length;
        //GasCost('close verifyBalanceProof length end', block.gaslimit, msg.gas);

        //GasCost('close verifyBalanceProof uintToString start', block.gaslimit, msg.gas);
        string memory message_length_string = uintToString(message_length);
        //GasCost('close verifyBalanceProof uintToString end', block.gaslimit, msg.gas);

        //GasCost('close verifyBalanceProof concat start', block.gaslimit, msg.gas);
        // Prefix the message
        string memory prefixed_message = concat(prefix, message_length_string);
        //GasCost('close verifyBalanceProof concat end', block.gaslimit, msg.gas);

        prefixed_message = concat(prefixed_message, message);


        // Hash the prefixed message string
        bytes32 prefixed_message_hash = sha3(prefixed_message);

        // Derive address from signature
        address signer = ECVerify.ecverify(prefixed_message_hash, _balance_msg_sig);
        return signer;
    }

    /*
     *  External functions
     */

    /// @dev Calls createChannel, compatibility with ERC 223; msg.sender is token_223 contract.
    /// @param _sender The address that sends the tokens.
    /// @param _deposit The amount of tokens that the sender escrows.
    /// @param _data flag_byte + uint32 open_block_number / uint32 channel_fee
    function tokenFallback(
        address _sender,
        uint256 _deposit,
        bytes _data)
        external
    {
        // Make sure we trust the token
        require(msg.sender == token_address);
        //GasCost('tokenFallback start0', block.gaslimit, msg.gas);
        uint length = _data.length;

        // data - flag_byte (1 byte) + open_block_number (4 bytes) or flag_byte (1 byte) + channel_fee (4 bytes)
        require(length == 5);
        bytes1 flag_byte;
        uint32 number;

        (flag_byte, number) = fallbackDataConvert(data);

        if (flag_byte == x00){
            createChannelPrivate(_sender, number, uint192(_deposit));
        } else if (flag_byte == x01) {
            topUpPrivate(_sender, number, uint192(_deposit));
        } else {
            revert();
        }

    }

    /// @dev Function called when any of the parties wants to close the channel and settle; any receiver needs a balance proof to immediately settle, sender triggers a challenge period.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _payment_data The array of uint256 incoded (balance, address) pairs
    /// @param _balance_msg_sig The balance message signed by the sender.
    function close(
        address _sender,
        uint32 _open_block_number,
        uint256[] _payment_data,
        bytes _balance_msg_sig)
        external
    {
        bytes32 key = getKey(_sender, _open_block_number);

        require(closing_requests[key].settle_block_number == 0);  // can only call this method once per channel
        require(uint32(block.number) - _open_block_number >= channel_lifetime);
        require(_balance_msg_sig.length == 65);

        //GasCost('close verifyBalanceProof start', block.gaslimit, msg.gas);
        address sender = verifyBalanceProof(_sender, _open_block_number, _payment_data, _balance_msg_sig);
        require(sender == _sender);
        //GasCost('close verifyBalanceProof end', block.gaslimit, msg.gas);

        initChallengePeriod(_receiver, _open_block_number, _payment_data, ClosingStatus.Good);
    }

    // very expensive, but the collateral should cover the expenses
    function report_cheating( // TODO test this
        address _sender,
        uint32 _open_block_number,
        uint256[] _right_payment_data,
        bytes _right_balance_msg_sig,
        uint256[] _wrong_payment_data,
        bytes _wrong_balance_msg_sig)
        external
    {
        require(msg.sender != _sender); // user cannot report himself
        bytes32 memory key = getKey(_sender, _open_block_number);

        // check that both transactions were signed by the _sender
        address sender = verifyBalanceProof(_sender, _open_block_number, _right_payment_data, _right_balance_msg_sig);
        require(sender == _sender);
        sender = verifyBalanceProof(_sender, _open_block_number, _wrong_payment_data, _wrong_balance_msg_sig);
        require(sender == _sender);

        address[] memory wrong_receivers;
        uint[] memory wrong_balances;
        (wrong_receivers, wrong_balances) = decodePaymentData(_wrong_payment_data);

        address[] memory right_receivers;
        uint[] memory right_balances;
        (right_receivers, right_balances) = decodePaymentData(_right_payment_data);

        uint memory balances_sum = 0;

        for (uint i = 0; i < wrong_balances.length; i++){
            balances_sum += wrong_balances[i];
        }

        if (balances_sum > channels[key].deposit){
            payCollateral(_sender, _open_block_number);
            initChallengePeriod(_sender, _open_block_number, _right_payment_data, ClosingStatus.Overspend);

        } else {
            uint8 array_length = min(right_balances.length, wrong_balances.length);
            int[] memory balance_diff = new int[](array_length);
            bool memory finished = false;

            for (uint i = 0; i < array_length; i++){
                if (right_receivers[i] == wrong_receivers[i]){
                    balance_diff.append(int(right_balances[i] - wrong_balances[i]));
                } else {
                    // TODO wrong receivers order, what should we do?
                }
            }

            //case 1
            if (!finished && wrong_balances.length > right_balances.length){
                for (uint i = 0; i < array_length; i++){
                    if (balances_sum[i] > 0){
                        payCollateral(_sender, _open_block_number);
                        initChallengePeriod(_sender, _open_block_number, _right_payment_data, ClosingStatus.Cheating);
                        finished = true;
                        break;
                    }
                }
            }
            //case 2
            if (!finished && wrong_balances.length == right_balances.length){
                bool memory pos = false;
                bool memory neg = false;
                for (uint i = 0; i < array_length; i++){
                    if (balances_sum[i] > 0){
                        pos = true;
                    } else if (balances_sum[i] < 0){
                        neg = true;
                    }
                    if (pos && neg){
                        payCollateral(_sender, _open_block_number);
                        initChallengePeriod(_sender, _open_block_number, _right_payment_data, ClosingStatus.Cheating);
                        break;
                    }
                }
            }
            //case 3
            if (!finished && wrong_balances.length < right_balances.length){
                for (uint i = 0; i < array_length; i++){
                    if (balances_sum[i] < 0){
                        payCollateral(_sender, _open_block_number);
                        initChallengePeriod(_sender, _open_block_number, _right_payment_data, ClosingStatus.Cheating);
                        break;
                    }
                }
            }
        }
    }

    function decodePaymentData(
        uint256[] _payment_data)
        public
        constant
        returns(address[], uint[])
    {
        // TODO test this
        address[] memory receivers;
        uint[] memory balances;

        for (uint i=0; i<_payment_data.length; i++) {
            receivers.append(address( _payment_data[i] & (D160-1)));
            balances.append(_payment_data[i] / D160);
        }

        return(receivers, balances);
    }

    /// @dev Function for getting information about a channel.
    /// @param _sender The address that sends tokens.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @return Channel information (unique_identifier, deposit, settle_block_number, closing_balance).
    function getChannelInfo(
        address _sender,
        uint32 _open_block_number)
        external
        constant
        returns (bytes32, uint192, uint32, uint32, uint32, uint256[])
    {
        bytes32 key = getKey(_sender, _open_block_number);
        require(channels[key].open_block_number != 0);

        return (key, channels[key].deposit, channels[key].collateral, channels[key].channel_fee, closing_requests[key].settle_block_number, closing_requests[key].closing_balances_data);
    }

    /// @dev Function called by the sender after the challenge period has ended, in case the receiver has not closed the channel.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    function settle(    // TODO change this !
        address _sender,
        uint32 _open_block_number,
        uint256[] _payment_data)
        external
    {
        bytes32 key = getKey(_sender, _open_block_number);

        require(closing_requests[key].settle_block_number != 0);
	    require(block.number > closing_requests[key].settle_block_number);

        settleChannel(_sender, _open_block_number, _payment_data);
    }

    function registerMaintainer(
        address _sender,
        uint32 _open_block_number)
        external
    {
        bytes32 key = getKey(_sender, _open_block_number);
        require(channels[key].open_block_number != 0);
        require(channels[key].maintaining_nodes.length < 3);

        //todo check for eligibility using the random_n in the channel

        channels[key].maintaining_nodes.append(msg.sender);
        if (channels[key].maintaining_nodes.length == 1){
            channels[key].topic_holder_node = msg.sender;
            ChannelTopicCreated(_sender, _open_block_number, msg.sender);
        }

        MaintainerRegistered(_sender, _open_block_number, msg.sender);
    }

    /*
     *  Private functions
     */

    /// @dev Creates a new channel between a sender and a receivers, only callable by the token_223 contract.
    /// @param _sender The address that receives tokens.
    /// @param _deposit The amount of tokens that the sender escrows.
    function createChannelPrivate(
        address _sender,
        uint32 _channel_fee,
        uint192 _deposit)
        private
    {
        //GasCost('createChannel start', block.gaslimit, msg.gas);
        uint32 open_block_number = uint32(block.number);

        // Create unique identifier from sender and current block number
        bytes32 key = getKey(_sender, open_block_number);

        require(channels[key].deposit == 0);
        require(channels[key].open_block_number == 0);
        require(closing_requests[key].settle_block_number == 0);

        uint192 memory deposit = ((_deposit - _channel_fee) / 100) * 85;
        uint32 memory collateral = (_deposit - _channel_fee) - deposit;

        if (deposit + collateral + _channel_fee == _deposit){   // temporary structure, will probably delete this after some tests
            ChannelCreated(0, 0, 0, 0);
        } else {
            bytes32 memory random_n = bytes32(0);
            Channel channel;

            channel.deposit = deposit;
            channel.open_block_number = open_block_number;
            channel.collateral = collateral;
            channel.channel_fee = _channel_fee;
            channel.random_n = random_n;

            channels[key] = channel;
            //GasCost('createChannel end', block.gaslimit, msg.gas);

            ChannelCreated(_sender, deposit, _channel_fee, random_n);
        }
    }

    /// @dev Funds channel with an additional deposit of tokens, only callable by the token_223 contract.
    /// @param _sender The address that sends tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _added_deposit The added token deposit with which the current deposit is increased.
    function topUpPrivate(
        address _sender,
        uint32 _open_block_number,
        uint192 _added_deposit)
        private
    {
        //GasCost('topUp start', block.gaslimit, msg.gas);
        require(_added_deposit != 0);
        require(_open_block_number != 0);

        bytes32 key = getKey(_sender, _open_block_number);

        require(channels[key].deposit != 0);
        require(closing_requests[key].settle_block_number == 0);

        uint192 memory deposit = (_added_deposit  / 100) * 85;
        uint32 memory collateral = _added_deposit - deposit;

        channels[key].deposit += deposit;
        channels[key].collateral += collateral;
        ChannelToppedUp(_sender, _open_block_number, deposit, channels[key].deposit);
        //GasCost('topUp end', block.gaslimit, msg.gas);
    }


    /// @dev Sender starts the challenge period; this can only happend once.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _balance The amount of tokens owed by the sender to the receiver.
    function initChallengePeriod(
        address _sender,
        uint32 _open_block_number,
        uint256[] _payment_data,
        ClosingStatus _closing_status)
        private
    {
        //GasCost('initChallengePeriod end', block.gaslimit, msg.gas);
        bytes32 key = getKey(_sender, _open_block_number);

        require(closing_requests[key].settle_block_number == 0);
        require(_balance <= channels[key].deposit);

        // Mark channel as closed
        closing_requests[key].settle_block_number = uint32(block.number) + challenge_period;
        closing_requests[key].closing_balance = _balance;
        ChannelCloseRequested(msg.sender, _receiver, _open_block_number, _balance);
        //GasCost('initChallengePeriod end', block.gaslimit, msg.gas);
    }

    /// @dev Closes the channel and settles by transfering the balance to the receiver and the rest of the deposit back to the sender.
    /// @param _sender The address that sends tokens.
    /// @param _receiver The address that receives tokens.
    /// @param _open_block_number The block number at which a channel between the sender and receiver was created.
    /// @param _balance The amount of tokens owed by the sender to the receiver.
    function settleChannel(  // TODO change this
        address _sender,
        uint32 _open_block_number,
        uint256[] _payment_data)
        private
    {
        //GasCost('settleChannel start', block.gaslimit, msg.gas);
        bytes32 key = getKey(_sender, _open_block_number);
        Channel channel = channels[key];

        require(channel.open_block_number != 0);
        require(_balance <= channel.deposit);

        // send minimum of _balance and deposit to receiver
        uint send_to_receiver = min(_balance, channel.deposit);
        if(send_to_receiver > 0) {
            //GasCost('settleChannel', block.gaslimit, msg.gas);
            require(token.transfer(_receiver, send_to_receiver));
        }

        // send maximum of deposit - balance and 0 to sender
        uint send_to_sender = max(channel.deposit - _balance, 0);
        if(send_to_sender > 0) {
            //GasCost('settleChannel', block.gaslimit, msg.gas);
            require(token.transfer(_sender, send_to_sender));
        }

        assert(channel.deposit >= _balance);

        // remove closed channel structures
        delete channels[key];
        delete closing_requests[key];

        ChannelSettled(_sender, _receiver, _open_block_number, _balance);
        //GasCost('settleChannel end', block.gaslimit, msg.gas);
    }

    function payCollateral(
        address _sender,
        uint32 _open_block_number)
        private
    {
        bytes32 key = getKey(_sender, _open_block_number);
        require(token.transfer(msg.sender, channels[key].collateral));
        channels[key].collateral = 0;
    }

    /*
     *  Internal functions
     */

    /// @dev Internal function for getting the maximum between two numbers.
    /// @param a First number to compare.
    /// @param b Second number to compare.
    /// @return The maximum between the two provided numbers.
    function max(uint192 a, uint192 b)
        internal
        constant
        returns (uint)
    {
        if (a > b) return a;
        else return b;
    }

    /// @dev Internal function for getting the minimum between two numbers.
    /// @param a First number to compare.
    /// @param b Second number to compare.
    /// @return The minimum between the two provided numbers.
    function min(uint192 a, uint192 b)
        internal
        constant
        returns (uint)
    {
        if (a < b) return a;
        else return b;
    }

    // 2662 gas cost
    /// @dev Internal function for getting the block number or channel fee from tokenFallback data bytes.
    /// @param b Bytes received.
    /// @return Block number.
    function fallbackDataConvert(
        bytes b)
        internal
        constant
        returns (uint32)
    {
        bytes1 flag_byte;
        bytes4 number;
        assembly {
            flag_byte := mload(add(b, 0x20))
            number := mload(add(b, 0x21))
        }
        return (flag_byte, uint32(number));
    }

    function memcpy(
        uint dest,
        uint src,
        uint len)
        private
    {
        // Copy word-length chunks while possible
        for(; len >= 32; len -= 32) {
            assembly {
                mstore(dest, mload(src))
            }
            dest += 32;
            src += 32;
        }

        // Copy remaining bytes
        uint mask = 256 ** (32 - len) - 1;
        assembly {
            let srcpart := and(mload(src), not(mask))
            let destpart := and(mload(dest), mask)
            mstore(dest, or(destpart, srcpart))
        }
    }

    // 3813 gas cost
    function concat(
        string _self,
        string _other)
        internal
        constant
        returns (string)
    {
        uint self_len = bytes(_self).length;
        uint other_len = bytes(_other).length;
        uint self_ptr;
        uint other_ptr;

        assembly {
            self_ptr := add(_self, 0x20)
            other_ptr := add(_other, 0x20)
        }

        var ret = new string(self_len + other_len);
        uint retptr;
        assembly { retptr := add(ret, 32) }
        memcpy(retptr, self_ptr, self_len);
        memcpy(retptr + self_len, other_ptr, other_len);
        return ret;
    }

    // 9613 gas
    function uintToString(
        uint v)
        internal
        constant
        returns (string)
    {
        bytes32 ret;
        if (v == 0) {
            ret = '0';
        }
        else {
             while (v > 0) {
                ret = bytes32(uint(ret) / (2 ** 8));
                ret |= bytes32(((v % 10) + 48) * 2 ** (8 * 31));
                v /= 10;
            }
        }

        bytes memory bytesString = new bytes(32);
        uint charCount = 0;
        for (uint j=0; j<32; j++) {
            byte char = byte(bytes32(uint(ret) * 2 ** (8 * j)));
            if (char != 0) {
                bytesString[j] = char;
                charCount++;
            }
        }
        bytes memory bytesStringTrimmed = new bytes(charCount);
        for (j = 0; j < charCount; j++) {
            bytesStringTrimmed[j] = bytesString[j];
        }

        return string(bytesStringTrimmed);
    }

    function addressToString(
        address x)
        internal
        constant
        returns (string)
    {
        bytes memory str = new bytes(40);
        for (uint i = 0; i < 20; i++) {
            byte b = byte(uint8(uint(x) / (2**(8*(19 - i)))));
            byte hi = byte(uint8(b) / 16);
            byte lo = byte(uint8(b) - 16 * uint8(hi));
            str[2*i] = char(hi);
            str[2*i+1] = char(lo);
        }
        return string(str);
    }

    function char(byte b)
        internal
        constant
        returns (byte c)
    {
        if (b < 10) return byte(uint8(b) + 0x30);
        else return byte(uint8(b) + 0x57);
    }

    function bytes32ToString(bytes32 x) constant returns (string) {
        bytes memory bytesString = new bytes(32);
        uint charCount = 0;
        for (uint j = 0; j < 32; j++) {
            byte char = byte(bytes32(uint(x) * 2 ** (8 * j)));
            if (char != 0) {
                bytesString[charCount] = char;
                charCount++;
            }
        }
        bytes memory bytesStringTrimmed = new bytes(charCount);
        for (j = 0; j < charCount; j++) {
            bytesStringTrimmed[j] = bytesString[j];
        }
        return string(bytesStringTrimmed);
    }
}

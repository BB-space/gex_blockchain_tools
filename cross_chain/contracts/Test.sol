pragma solidity ^0.4.15;


import "../../contracts/lib/ECVerify.sol";


contract Test {
    function Test(){

    }

    function check(bytes32 _message, bytes sig, address addr) returns (address) {
        bytes32 message = sha3(_message);
        address signer = ECVerify.ecverify(message, sig);
        return signer;
    }

    function verify_new(string message, bytes s) constant returns (address) {
        string memory prefix = "\x19Ethereum Signed Message:\n";
        uint256 message_length =  bytes(message).length;
        string memory message_length_string = uintToString(message_length);
        string memory prefixed_message = concat(prefix, message_length_string);
        prefixed_message = concat(prefixed_message, message);
        bytes32 prefixed_message_hash = sha3(prefixed_message);
        //bytes32 prefixedHash = sha3(prefixed_message, message);

        return ECVerify.ecverify(prefixed_message_hash, s);
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

    function bytes32ToString(
        bytes32 x)
        internal
        constant
        returns (string) {
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

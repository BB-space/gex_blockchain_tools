function toHex(str) {
    var hex = '';
    for (var i = 0; i < str.length; i++) {
        hex += '' + str.charCodeAt(i).toString(16);
    }
    return hex;
}

const Web3 = require('web3');
const web3 = new Web3(new Web3.providers.HttpProvider('http://localhost:8545'));
var fs = require('fs');
var jsonObject = JSON.parse(fs.readFileSync('data.json', 'utf8'));
var Verifier = web3.eth.contract(jsonObject.Verifier_abi).at(jsonObject.Verifier);

const addr = web3.eth.accounts[0];
const msg = 'lalalala';
const hex_msg = '0x' + toHex(msg);
var signature = web3.eth.sign(addr, hex_msg);

console.log("address -----> " + addr);
console.log("msg ---------> " + msg);
console.log("hex(msg) ----> " + hex_msg);
console.log("sig ---------> " + signature);

signature = signature.substr(2);
const r = '0x' + signature.slice(0, 64);
const s = '0x' + signature.slice(64, 128);
const v = '0x' + signature.slice(128, 130);
const v_decimal = web3.toDecimal(v);

console.log("r -----------> " + r);
console.log("s -----------> " + s);
console.log("v -----------> " + v);
console.log("vd ----------> " + v_decimal);

const fixed_msg = "\x19Ethereum Signed Message:\n" + msg.length + msg;
const fixed_msg_sha = web3.sha3(fixed_msg);
data = Verifier.recoverAddr.call(fixed_msg_sha, v_decimal, r, s);
console.log("-----data------");
console.log("input addr ==> " + addr);
console.log("output addr => " + data);
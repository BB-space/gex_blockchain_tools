var abi = [{
    "constant": false,
    "inputs": [{"name": "_value", "type": "int256"}],
    "name": "foo",
    "outputs": [{"name": "", "type": "int256"}],
    "payable": false,
    "type": "function"
}, {
    "anonymous": false,
    "inputs": [{"indexed": true, "name": "_from", "type": "address"}, {
        "indexed": false,
        "name": "_value",
        "type": "int256"
    }],
    "name": "ReturnValue",
    "type": "event"
}]
var MyContract = web3.eth.contract(abi);
var exampleContract = MyContract.at('0x484d58afbe4950b4020db10f4b83b6e71f4604a2');

var exampleEvent = exampleContract.ReturnValue({_from: web3.eth.coinbase});
exampleEvent.watch(function (err, result) {
    if (err) {
        console.log(err)
        return;
    }
    console.log(result.args._value)
    // check that result.args._from is web3.eth.coinbase then
    // display result.args._value in the UI and call
    // exampleEvent.stopWatching()
})
exampleContract.foo.sendTransaction(333, {from: web3.eth.coinbase})

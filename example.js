var abi = [{"constant":false,"inputs":[{"name":"_value","type":"int256"}],"name":"foo","outputs":[{"name":"","type":"int256"}],"payable":false,"type":"function"},{"anonymous":false,"inputs":[{"indexed":true,"name":"_from","type":"address"},{"indexed":false,"name":"_value","type":"int256"}],"name":"ReturnValue","type":"event"}]
var MyContract = web3.eth.contract(abi);
var exampleContract = MyContract.at('0x73e27743c4fd33456b56f4725dcfb17def96f01d');

var exampleEvent = exampleContract.ReturnValue({_from: web3.eth.coinbase});
exampleEvent.watch(function(err, result) {
  if (err) {
    console.log(err)
    return;
  }
  console.log(result.args._value)
  // check that result.args._from is web3.eth.coinbase then
  // display result.args._value in the UI and call    
  // exampleEvent.stopWatching()
})
exampleContract.foo.sendTransaction(2, {from: web3.eth.coinbase})

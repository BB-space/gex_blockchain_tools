var GEXToken = artifacts.require("./GEXToken.sol");
var GexContract = artifacts.require("./GexContract.sol");
var EthContract = artifacts.require("./EthContract.sol");
var ExampleContract = artifacts.require("../contracts/ExampleContract.sol")
module.exports = function (deployer) {
    deployer.deploy(GEXToken).then(function() {
         deployer.deploy(GexContract, GEXToken.address);
         deployer.deploy(EthContract, GEXToken.address);
    });
    //deployer.link(GEXToken, GexContract);
    //deployer.link(GEXToken, EthContract);
    //deployer.deploy(ExampleContract);
};

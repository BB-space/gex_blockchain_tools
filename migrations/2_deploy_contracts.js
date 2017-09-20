var GexContract = artifacts.require("./GexContract.sol");
var EthContract = artifacts.require("./EthContract.sol");

module.exports = function(deployer) {
  deployer.deploy(GexContract);
  //deployer.link(ConvertLib, MetaCoin);
  deployer.deploy(EthContract);
};

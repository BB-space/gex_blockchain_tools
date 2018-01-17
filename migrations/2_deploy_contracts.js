var GEXToken = artifacts.require("./GEXToken.sol");
var NodeManager = artifacts.require("./NodeManager.sol");

module.exports = function (deployer) {
    deployer.deploy(GEXToken).then(function () {
        deployer.deploy(NodeManager, GEXToken.address, 5000000).then(function () {
            GEXToken.at(GEXToken.address).transferOwnership(NodeManager.address);
            var fs = require("fs");
            var jsonObject = {
                token_address: GEXToken.address,
                node_manager_address: NodeManager.address,
                token_abi: GEXToken.abi,
                node_manager_abi: NodeManager.abi
            };
            fs.writeFile("data1.json", JSON.stringify(jsonObject), function (err) {
                if (err) {
                    return console.log(err);
                }
            });
        })
    });
};
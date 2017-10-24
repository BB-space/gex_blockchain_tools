var GEXToken = artifacts.require("./GEXToken.sol");
var GexContract = artifacts.require("./GexContract.sol");
var EthContract = artifacts.require("./EthContract.sol");

/*module.exports = function (deployer) {
    deployer.deploy(GEXToken).then(function () {
        var fs = require("fs");
        var jsonObject = {
            GEXToken: GEXToken.address,
            GEXToken_abi: GEXToken.abi
        };
        fs.writeFile("data.json", JSON.stringify(jsonObject), function (err) {
            if (err) {
                return console.log(err);
            }
        });
    });
};*/

module.exports = function (deployer) {
    deployer.deploy(GEXToken).then(function () {
        deployer.deploy(GexContract, GEXToken.address).then(function () {
            deployer.deploy(EthContract, GEXToken.address).then(function () {
                var fs = require("fs");
                var jsonObject = {
                    GEXToken: GEXToken.address,
                    GexContract: GexContract.address,
                    EthContract: EthContract.address,
                    GEXToken_abi: GEXToken.abi,
                    GexContract_abi: GexContract.abi,
                    EthContract_abi: EthContract.abi
                };
                fs.writeFile("data.json", JSON.stringify(jsonObject), function (err) {
                    if (err) {
                        return console.log(err);
                    }
                });
            });
        });
    });
};

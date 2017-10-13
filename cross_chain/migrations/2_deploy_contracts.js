var GEXToken = artifacts.require("./GEXToken.sol");
var NodeContract = artifacts.require("./NodeContract.sol");
var GexContract = artifacts.require("./GexContract.sol");
var EthContract = artifacts.require("./EthContract.sol");
var Verifier = artifacts.require("./Verifier.sol");

module.exports = function (deployer) {
    deployer.deploy(Verifier).then(function () {
        var fs = require("fs");
        var jsonObject = {
            Verifier: Verifier.address,
            Verifier_abi: Verifier.abi
        };
        fs.writeFile("data.json", JSON.stringify(jsonObject), function (err) {
            if (err) {
                return console.log(err);
            }
        });
    });
};

/*module.exports = function (deployer) {
    deployer.deploy(GEXToken).then(function () {
        deployer.deploy(NodeContract).then(function () {
            deployer.deploy(GexContract, GEXToken.address).then(function () {
                deployer.deploy(EthContract, GEXToken.address).then(function () {
                    var fs = require("fs");
                    var jsonObject = {
                        GEXToken: GEXToken.address,
                        NodeContract: NodeContract.address,
                        GexContract: GexContract.address,
                        EthContract: EthContract.address,
                        GEXToken_abi: GEXToken.abi,
                        NodeContract_abi: NodeContract.abi,
                        GexContract_abi: GexContract.abi,
                        EthContract_abi: EthContract.abi
                    };
                    fs.writeFile("data.json", JSON.stringify(jsonObject), function (err) {
                        if (err) {
                            return console.log(err);
                        }
                    });
                })

            })

        })

    });

};*/

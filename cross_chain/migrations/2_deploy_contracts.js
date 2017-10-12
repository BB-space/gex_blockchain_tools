var GEXToken = artifacts.require("./GEXToken.sol");
var NodeContract = artifacts.require("./NodeContract.sol");
var GexContract = artifacts.require("./GexContract.sol");
var EthContract = artifacts.require("./EthContract.sol");
var Test = artifacts.require("./Test.sol");
var ECVerify = artifacts.require("./ECVerify.sol");
module.exports = function (deployer) {
    deployer.deploy(ECVerify).then(function () {
        deployer.deploy(Test).then(function () {
            var fs = require("fs");
                    var jsonObject = {
                        Test: Test.address,
                        Test_abi: Test.abi
                    };
                    fs.writeFile("data.json", JSON.stringify(jsonObject), function (err) {
                        if (err) {
                            return console.log(err);
                        }
                    });

     })

        deployer.link(ECVerify,Test);
    });
/*
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
    */
};

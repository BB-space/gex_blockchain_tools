let GEXToken = artifacts.require("./GEXToken.sol");
let NodeManager = artifacts.require("./NodeManager.sol");
let GEXBot = artifacts.require("./GexBot.sol");


async function deploy(deployer) {

    await deployer.deploy(GEXToken);
    await deployer.deploy(NodeManager, GEXToken.address, 5000000);
    GEXToken.at(GEXToken.address).transferOwnership(NodeManager.address);

    await deployer.deploy(GEXBot);

    let fs = require("fs");
    let jsonObject = {
        token_address: GEXToken.address,
        token_abi: GEXToken.abi,
        node_manager_address: NodeManager.address,
        node_manager_abi: NodeManager.abi,
        bot_address: GEXBot.address,
        bot_abi: GEXBot.abi
    };

    fs.writeFile("data.json", JSON.stringify(jsonObject), function (err) {
        if (err) {
            return console.log(err);
        }
    });
}


module.exports = deploy;
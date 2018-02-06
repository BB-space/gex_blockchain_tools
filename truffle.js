module.exports = {
  networks: {
    development: {
      host: "localhost", // 51.0.1.99 localhost
      port: 8545, //7545
      //gas: 2900000, //2,5m
      //from: "0x6870EA70c8582A3C3c778ae719b502e4644fD9dE",
      network_id: "*" // Match any network id
    }
  }
};

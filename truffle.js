module.exports = {
  networks: {
    development: {
      host: "localhost", // 51.0.1.99 10.1.0.15
      port: 8545, //8545
        from: "0x2c1ea69632f1702b229e847e626e8dc1436e905c",
      //gas:4712388,
      network_id: "*" // Match any network id
    }
  }
};

// test.js
const { ethers } = require('ethers');
const providerUrl = 'wss://mainnet.infura.io/ws/v3/e33870ee2cd8461db67d69e018b6f8f3';
const provider = new ethers.WebSocketProvider(providerUrl);

provider.on('block', (blockNumber) => {
  console.log('New block:', blockNumber);
});

provider.on('error', (error) => {
  console.error('Error:', error);
});


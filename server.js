const express = require('express');
const { ethers } = require('ethers');
const Bottleneck = require('bottleneck');
const NodeCache = require('node-cache');
const app = express();
const port = 3000;

const providerUrl = 'wss://mainnet.infura.io/ws/v3/e33870ee2cd8461db67d69e018b6f8f3';
const provider = new ethers.WebSocketProvider(providerUrl);

let pendingTransactions = [];

// Create a Bottleneck limiter
const limiter = new Bottleneck({
  minTime: 2000, // Minimum time between each request in ms (adjust as needed)
});

// Create a cache instance
const cache = new NodeCache({ stdTTL: 600, checkperiod: 120 }); // Cache TTL of 10 minutes

provider.on('pending', async (txHash) => {
  try {
    const cachedTx = cache.get(txHash);

    if (cachedTx) {
      // Use cached transaction
      pendingTransactions.push(cachedTx);
    } else {
      // Fetch transaction and cache it
      const tx = await limiter.schedule(() => provider.getTransaction(txHash));
      if (tx) {
        console.log('Fetched transaction:', tx);
        cache.set(txHash, tx);
        pendingTransactions.push(tx);
      }
    }

    if (pendingTransactions.length > 100) {
      pendingTransactions.shift();
    }
  } catch (error) {
    console.error('Error fetching transaction:', error);
  }
});

app.use(express.static('public'));

app.get('/transactions', (req, res) => {
  res.json(pendingTransactions);
});

app.listen(port, () => {
  console.log(`Server listening at http://localhost:${port}`);
});

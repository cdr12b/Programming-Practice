const exchangeFees = {
  coinGecko: 0.0025, // 0.25%
  coinbase: 0.005,   // 0.5%
  kraken: 0.0026,    // 0.26%
  binance: 0.001,     // 0.1%
  kuCoin: 0.001,     // 0.1%
  okx: 0.001,        // 0.1%
  gateIo: 0.002      // 0.2%
};

const axios = require('axios');
const NodeCache = require('node-cache');

// Configure cache with dynamic TTL
const cache = new NodeCache({
  stdTTL: 60, // Default TTL
  checkperiod: 120,
  useClones: false
});

// Exchange-specific configurations
const EXCHANGE_CONFIG = {
  coinGecko: { ttl: 60, retries: 3, healthCheckUrl: 'https://api.coingecko.com/api/v3/ping' },
  coinbase: { ttl: 30, retries: 2, healthCheckUrl: 'https://api.coinbase.com/v2/exchange-rates' },
  kraken: { ttl: 45, retries: 3, healthCheckUrl: 'https://api.kraken.com/0/public/SystemStatus' },
  binance: { ttl: 60, retries: 3, healthCheckUrl: 'https://api.binance.com/api/v3/ping' },
  kuCoin: { ttl: 45, retries: 2, healthCheckUrl: 'https://api.kucoin.com/api/v1/timestamp' },
  okx: { ttl: 60, retries: 3, healthCheckUrl: 'https://www.okx.com/api/v5/system/status' },
  gateIo: { ttl: 60, retries: 3, healthCheckUrl: 'https://api.gateio.ws/api/v4/spot/tickers' }
};

// Helper function for API calls with retries
const fetchWithRetry = async (url, config, retries = 3) => {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await axios.get(url, config);
      return response.data;
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
};

// Enhanced price comparison function
const findArbitrageOpportunities = (prices) => {
  const opportunities = {};
  const MIN_DIFFERENCE_PERCENT = 0.5;

  Object.keys(prices).forEach(coin => {
    const coinPrices = Object.entries(prices)
      .filter(([_, exchange]) => exchange[coin])
      .map(([exchange, data]) => ({ exchange, price: data[coin] }));

    if (coinPrices.length > 1) {
      const min = Math.min(...coinPrices.map(p => p.price));
      const max = Math.max(...coinPrices.map(p => p.price));
      const differencePercent = ((max - min) / min) * 100;

      if (differencePercent > 0 && differencePercent >= MIN_DIFFERENCE_PERCENT) {
        opportunities[coin] = {
          min: coinPrices.find(p => p.price === min),
          max: coinPrices.find(p => p.price === max),
          differencePercent: differencePercent.toFixed(2)
        };
      }
    }
  });

  return opportunities;
};

const calculatePriceComparisons = (brokerPrices) => {
  const comparisons = {};

  Object.keys(brokerPrices).forEach(exchange => {
    if (exchange !== 'arbitrageOpportunities') {
      comparisons[exchange] = {};

      Object.keys(brokerPrices[exchange]).forEach(coin => {
        const price = brokerPrices[exchange][coin];
        const otherPrices = Object.keys(brokerPrices).filter(ex => ex !== exchange).map(ex => brokerPrices[ex][coin]).filter(p => p);

        if (otherPrices.length > 0) {
          const min = Math.min(...otherPrices);
          const max = Math.max(...otherPrices);
          const difference = price - min;

          comparisons[exchange][coin] = {
            difference,
            min: { exchange: Object.keys(brokerPrices).find(ex => brokerPrices[ex][coin] === min), price: min },
            max: { exchange: Object.keys(brokerPrices).find(ex => brokerPrices[ex][coin] === max), price: max }
          };
        }
      });
    }
  });

  return comparisons;
};

// Modified getBrokerPrices with enhanced features
const getBrokerPrices = async () => {
  const cacheKey = 'brokerPrices';
  const cachedPrices = cache.get(cacheKey);

  if (cachedPrices) {
    return cachedPrices;
  }

  try {
    const [coinGeckoPrices, coinbasePrices, krakenPrices, binancePrices, kuCoinPrices, okxPrices, gateIoPrices] = await Promise.all([
      getCoinGeckoPrices(),
      getCoinbasePrices(),
      getKrakenPrices(),
      getBinancePrices(),
      getKuCoinPrices(),
      getOKXPrices(),
      getGateIoPrices(),
    ]);

    const rawPrices = {
      coinGecko: coinGeckoPrices,
      coinbase: coinbasePrices,
      kraken: krakenPrices,
      binance: binancePrices,
      kuCoin: kuCoinPrices,
      okx: okxPrices,
      gateIo: gateIoPrices,
    };

    const normalizedPrices = normalizeBrokerPrices(rawPrices);

    cache.set(cacheKey, normalizedPrices);
    logPriceComparisons(calculatePriceComparisons(normalizedPrices));
    return normalizedPrices;
  } catch (error) {
    throw error;
  }
};

const normalizeBrokerPrices = (rawPrices) => {
  const normalized = {};

  const coinMappings = {
    okx: {
      'BTC-USDT': 'bitcoin',
      'ETH-USDT': 'ethereum',
      'BNB-USDT': 'binancecoin',
      'XRP-USDT': 'ripple',
      'ADA-USDT': 'cardano',
      'SOL-USDT': 'solana',
      'DOT-USDT': 'polkadot',
      'DOGE-USDT': 'dogecoin'
    },
    binance: {
      'BTCUSDT': 'bitcoin',
      'ETHUSDT': 'ethereum',
      'BNBUSDT': 'binancecoin',
      'XRPUSDT': 'ripple',
      'ADAUSDT': 'cardano'
    },
    kuCoin: {
      'BTC-USDT': 'bitcoin',
      'ETH-USDT': 'ethereum',
      'BNB-USDT': 'binancecoin',
      'XRP-USDT': 'ripple',
      'ADA-USDT': 'cardano'
    },
    gateIo: {
      'BTC_USDT': 'bitcoin',
      'ETH_USDT': 'ethereum',
      'BNB_USDT': 'binancecoin',
      'XRP_USDT': 'ripple',
      'ADA_USDT': 'cardano',
      'SOL_USDT': 'solana',
      'DOT_USDT': 'polkadot',
      'DOGE_USDT': 'dogecoin'
    },
    kraken: {
      'XXBT': 'bitcoin',
      'XETH': 'ethereum'
    },
    coinbase: {
      'BTC': 'bitcoin',
      'ETH': 'ethereum'
    },
  };

  Object.entries(rawPrices).forEach(([exchange, prices]) => {
    normalized[exchange] = {};

    Object.entries(prices).forEach(([symbol, price]) => {
      const normalizedSymbol = coinMappings[exchange]?.[symbol] || symbol.toLowerCase();
      normalized[exchange][normalizedSymbol] = price;
    });
  });

  return normalized;
};

const getGateIoPrices = async () => {
  try {
    const response = await fetchWithRetry('https://api.gateio.ws/api/v4/spot/tickers', {}, EXCHANGE_CONFIG.gateIo.retries);
    if (!Array.isArray(response)) {
      throw new Error('Invalid Gate.io API response');
    }
    return response;
  } catch (error) {
    throw error;
  }
};

const getOKXPrices = async () => {
  try {
    const response = await fetchWithRetry('https://www.okx.com/api/v5/market/tickers', {
      params: {
        instType: 'SPOT',
      },
    }, EXCHANGE_CONFIG.okx.retries);
    if (!response?.data) {
      throw new Error('Invalid OKX API response');
    }
    return response;
  } catch (error) {
    throw error;
  }
};

const getBinancePrices = async () => {
  try {
    const response = await fetchWithRetry('https://api.binance.com/api/v3/ticker/price', {
      params: {
        symbols: JSON.stringify(['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'XRPUSDT', 'ADAUSDT']),
      },
    }, EXCHANGE_CONFIG.binance.retries);
    if (!response?.data) {
      throw new Error('Invalid Binance API response');
    }
    return response;
  } catch (error) {
    if (error.response && error.response.status === 451) {
      return {};
    }
    throw error;
  }
};

const getKuCoinPrices = async () => {
  try {
    const response = await fetchWithRetry('https://api.kucoin.com/api/v1/market/allTickers', {}, EXCHANGE_CONFIG.kuCoin.retries);
    if (!response?.data?.ticker) {
      throw new Error('Invalid KuCoin API response');
    }
    return response;
  } catch (error) {
    throw error;
  }
};

/**
 * Fetches price data from CoinGecko API.
 * @returns {Promise<Record<string, number>>} A promise resolving to an object mapping coin IDs to their current prices.
 */
const getCoinGeckoPrices = async () => {
  try {
    const response = await fetchWithRetry('https://api.coingecko.com/api/v3/coins/markets', {
      params: {
        vs_currency: 'usd',
        ids: 'bitcoin,ethereum,binancecoin',
        order: 'market_cap_desc',
        per_page: 10,
        page: 1,
        sparkline: false,
      },
    }, EXCHANGE_CONFIG.coinGecko.retries);

    if (!Array.isArray(response)) {
      throw new Error('Invalid CoinGecko API response');
    }

    return response.reduce((acc, coin) => {
      if (coin?.id && coin?.current_price) {
        acc[coin.id] = coin.current_price;
      }
      return acc;
    }, {});
  } catch (error) {
    throw error;
  }
};

const getCoinbasePrices = async () => {
  try {
    const response = await fetchWithRetry('https://api.coinbase.com/v2/prices/spot?currency=USD', EXCHANGE_CONFIG.coinbase.retries);
    if (!response?.data) {
      throw new Error('Invalid Coinbase API response');
    }
    return response.data;
  } catch (error) {
    throw error;
  }
};

const getKrakenPrices = async () => {
  try {
    const response = await fetchWithRetry('https://api.kraken.com/0/public/Ticker', {
      params: {
        pair: 'XXBTZUSD,XETHZUSD',
      },
    }, EXCHANGE_CONFIG.kraken.retries);

    if (!response?.result) {
      throw new Error('Invalid Kraken API response');
    }

    return response.result;
  } catch (error) {
    throw error;
  }
};

module.exports = {
  getBrokerPrices,
  findArbitrageOpportunities,
  logPriceComparisons,
  exchangeFees
};
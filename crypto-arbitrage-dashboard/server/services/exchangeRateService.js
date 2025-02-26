const axios = require('axios');
const NodeCache = require('node-cache');
const cache = new NodeCache({ stdTTL: 60 }); // Cache data for 60 seconds

const getExchangeRates = async () => {
  const cacheKey = 'exchangeRates';
  const cachedData = cache.get(cacheKey);

  if (cachedData) {
    return cachedData;
  }

  try {
    const response = await axios.get('https://api.frankfurter.app/latest?from=USD');
    const exchangeRates = response.data.rates;

    cache.set(cacheKey, exchangeRates);
    return exchangeRates;
  } catch (error) {
    console.error('Error fetching exchange rates:', error);
    throw error;
  }
};

module.exports = { getExchangeRates };
const express = require('express');
const Decimal = require('decimal.js');
const router = express.Router();
const { getExchangeRates } = require('../services/exchangeRateService');
const { getBrokerPrices, logPriceComparisons, exchangeFees } = require('../services/brokerService');

// Constants for profit calculation
const profitThreshold = new Decimal(1.0001); // Minimum profit threshold (1%)
const tolerance = new Decimal(0.00001); // Tolerance for floating-point comparisons

const calculateArbitrageOpportunities = async () => {
  const [brokerPrices, exchangeRates] = await Promise.all([
    getBrokerPrices(),
    getExchangeRates(),
  ]);

  const opportunities = [];
  const priceComparison = {};
  const fees = exchangeFees;

  // Create a summary object for undefined prices and exchange rates
  const summaryLog = {
    undefinedPrices: new Set(),
    undefinedExchangeRates: new Set()
  };

  // Combine prices from all brokers
  const allPrices = Object.values(brokerPrices).reduce((acc, prices) => {
    return { ...acc, ...prices };
  }, {});

  // Compare prices between brokers
  Object.keys(brokerPrices).forEach((broker1) => {
    Object.keys(brokerPrices).forEach((broker2) => {
      if (broker1 !== broker2) {
        const comparison = {};
        Object.keys(brokerPrices[broker1]).forEach((coin) => {
          const rawPrice1 = brokerPrices[broker1][coin];
          const rawPrice2 = brokerPrices[broker2][coin];

          // Calculate prices with fees
          let price1 = rawPrice1 !== undefined ? rawPrice1 * (1 + fees[broker1]) : undefined;
          let price2 = rawPrice2 !== undefined ? rawPrice2 * (1 + fees[broker2]) : undefined;

          if (price1 === undefined) {
            summaryLog.undefinedPrices.add(coin + broker1);
            price1 = price2;
          } else if (price2 === undefined) {
            summaryLog.undefinedPrices.add(coin + broker2);
            price2 = price1;
          }

          if (isNaN(price1) || isNaN(price2)) {
            console.error(`Invalid price for coin: ${coin}, broker1: ${broker1}, broker2: ${broker2}`);
            return; // Skip this iteration
          }

          const difference = new Decimal(price1).minus(price2).abs();
          const threshold = new Decimal(0.0001); // Define a threshold for logging price differences
          if (difference.greaterThan(threshold)) {
            console.log(`Price difference for ${coin} between ${broker1} and ${broker2}: ${difference.toNumber()}`);
          } else {
            // Skip logging for small differences
          }

          comparison[coin] = {
            difference: difference.toNumber()
          };
        });
        
        if (Object.keys(comparison).length > 0) {
          priceComparison[`${broker1} vs ${broker2}`] = comparison;
        }
      }
    });
  });

  // After creating the priceComparison object, log it correctly
  const validComparisons = {};
  
  Object.entries(priceComparison).forEach(([key, value]) => {
    if (key.includes(' vs ') && Object.keys(value).length > 0) {
      validComparisons[key] = value;
    }
  });
  
  if (Object.keys(validComparisons).length > 0) {
    logPriceComparisons(validComparisons);
  } else {
    console.log('No valid price comparisons found');
  }
  
  // Calculate arbitrage opportunities
  Object.keys(allPrices).forEach((coin1) => {
    Object.keys(allPrices).forEach((coin2) => {
      if (coin1 !== coin2) {
        if (allPrices[coin1] === undefined || allPrices[coin2] === undefined) {
          console.error(`Undefined price for coin: ${coin1} or ${coin2}`);
          return; // Skip this iteration
        }
        if (exchangeRates[coin1] === undefined || exchangeRates[coin2] === undefined) {
          summaryLog.undefinedExchangeRates.add(`Undefined exchange rate for coin: ${coin1} or ${coin2}`);
          return; // Skip this iteration
        }
        const rate = new Decimal(exchangeRates[coin1]).dividedBy(exchangeRates[coin2]);
        const price = new Decimal(allPrices[coin1]).dividedBy(allPrices[coin2]);
        if (price.greaterThan(rate.times(profitThreshold))) {
          opportunities.push({
            from: coin1,
            to: coin2,
            rate: rate.toNumber(),
            price: price.toNumber(),
            profit: price.minus(rate).dividedBy(rate).times(100).toNumber()
          });
        }
      }
    });
  });

  return opportunities;
};

// /usd-arbitrage endpoint
router.get('/usd-arbitrage', async (req, res) => {
  try {
    const opportunities = await calculateArbitrageOpportunities();
    res.json({ opportunities });
  } catch (error) {
    console.error('Error calculating USD arbitrage opportunities:', error);
    res.status(500).json({ error: 'Error calculating USD arbitrage opportunities' });
  }
});

module.exports = router;
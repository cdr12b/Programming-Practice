import React, { useEffect, useState } from 'react';
import axios from 'axios';

const PriceDisplay = () => {
  const [prices, setPrices] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchPrices = async () => {
    try {
      const response = await axios.get('http://localhost:5000/api/prices', {
        params: {
          _: new Date().getTime() // Add a unique timestamp to disable caching
        }
      });
     // console.log('API Response:', response.data); // Log the response data
      setPrices(response.data);
    } catch (error) {
      console.error('Error fetching prices:', error);
      setError('Failed to fetch prices. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPrices();
  }, []);

  if (loading) {
    return <div>Loading prices...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div>
      <h2>Current Prices</h2>
      {prices.length > 0 ? (
        <ul>
          {prices.map((price, index) => (
            <li key={index}>{price.name}: ${price.value}</li>
          ))}
        </ul>
      ) : (
        <div>No prices available.</div>
      )}
    </div>
  );
};

export default PriceDisplay;

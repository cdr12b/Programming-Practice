import React, { useEffect, useState } from 'react';
import axios from 'axios';

const ConversionRates = () => {
  const [conversionRates, setConversionRates] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchConversionRates = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await axios.get('/api/conversion-rates');
        setConversionRates(response.data);
      } catch (error) {
        console.error('Error fetching conversion rates:', error);
        setError('Failed to fetch conversion rates. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchConversionRates();
  }, []);

  if (loading) {
    return <div>Loading conversion rates...</div>;
  }

  if (error) {
    return <div className="error">{error}</div>;
  }

  return (
    <div className="conversion-rates">
      <h2>Conversion Rates</h2>
      <table>
        <thead>
          <tr>
            <th>From</th>
            <th>To</th>
            <th>Rate</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(conversionRates).map(([from, rates]) =>
            Object.entries(rates).map(([to, rate]) => (
              <tr key={`${from}-${to}`}>
                <td>{from}</td>
                <td>{to}</td>
                <td>{typeof rate === 'object' && typeof rate.value === 'number' ? rate.value.toFixed(2) : 'N/A'}</td>
              </tr>
            ))
          )}
        </tbody>
      </table>
    </div>
  );
};

export default ConversionRates;

import React, { useEffect, useState } from 'react';
import axios from 'axios';

const USDAArbitrage = () => {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchOpportunities = async () => {
      try {
        const response = await axios.get('http://localhost:5000/api/usd-arbitrage');
        setOpportunities(response.data);
        setLoading(false);
      } catch (error) {
        console.error('Error fetching arbitrage opportunities:', error);
        setError(error.message);
        setLoading(false);
      }
    };

    fetchOpportunities();
  }, []);

  if (loading) {
    return <div>Loading...</div>;
  }

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div>
      <h1>USD Arbitrage Opportunities</h1>
      {opportunities.length > 0 ? (
        <ul>
          {opportunities.map((opportunity, index) => (
            <li key={index}>
              <strong>Path:</strong> {opportunity.path.join(' → ')} <br />
              <strong>Profit:</strong> {(opportunity.profit * 100).toFixed(2)}%
            </li>
          ))}
        </ul>
      ) : (
        <p>No arbitrage opportunities found.</p>
      )}
    </div>
  );
};

export default USDAArbitrage;
import React, { useEffect, useState } from 'react';
import axios from 'axios';

const ArbitrageOpportunities = () => {
  const [opportunities, setOpportunities] = useState([]);

  useEffect(() => {
    const fetchOpportunities = async () => {
      try {
        const response = await axios.get('/api/arbitrage');
        setOpportunities(response.data);
      } catch (error) {
        console.error('Error fetching arbitrage opportunities:', error);
      }
    };

    fetchOpportunities();
  }, []);

  return (
    <div className="arbitrage-opportunities">
      <h2>Arbitrage Opportunities</h2>
      {/* Arbitrage opportunities display logic will go here */}
    </div>
  );
};

export default ArbitrageOpportunities;

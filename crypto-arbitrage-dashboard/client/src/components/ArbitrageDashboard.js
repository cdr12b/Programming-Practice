import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './ArbitrageDashboard.css';

const ArbitrageDashboard = () => {
  const [opportunities, setOpportunities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchOpportunities = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await axios.get('/api/triangular-arbitrage');
        setOpportunities(response.data);
      } catch (error) {
        console.error('Error fetching arbitrage opportunities:', error);
        setError('Failed to fetch arbitrage opportunities. Please try again later.');
      } finally {
        setLoading(false);
      }
    };

    fetchOpportunities();
  }, []);

  if (loading) {
    return <div className="center">Loading arbitrage opportunities...</div>;
  }

  if (error) {
    return <div className="error center">{error}</div>;
  }

  return (
    <div className="arbitrage-dashboard center">
      <h2>Triangular Arbitrage Opportunities</h2>
      <table>
        <thead>
          <tr>
            <th>Path</th>
            <th>Profit (%)</th>
          </tr>
        </thead>
        <tbody>
          {opportunities.map((opportunity, index) => {
            const profitPercentage = (opportunity.profit * 100).toFixed(2);
            const profitColor = opportunity.profit >= 0 ? 'green' : 'red';
            return (
              <tr key={index}>
                <td>{opportunity.path.join(' -> ')}</td>
                <td style={{ color: profitColor }}>{profitPercentage}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
};

export default ArbitrageDashboard;

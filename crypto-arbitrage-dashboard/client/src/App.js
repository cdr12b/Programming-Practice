import React from 'react';
import './App.css';

import PriceDisplay from './components/PriceDisplay';
import ConversionRates from './components/ConversionRates';
import ArbitrageDashboard from './components/ArbitrageDashboard'; 
import USDAArbitrage from './components/USDAArbitrage';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Crypto Arbitrage Dashboard</h1>
      </header>
      <main>
        <PriceDisplay />
        <ConversionRates />
        <ArbitrageDashboard />
        <USDAArbitrage />
      </main>
    </div>
  );
}

export default App;

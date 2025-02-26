//This code creates a simple Express.js 
//server that listens on port 3000 and responds with "Hello from Web Service!".
const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.send('Hello from Web Service!');
});

app.listen(3000, () => {
  console.log('Web service listening on port 3000');
});
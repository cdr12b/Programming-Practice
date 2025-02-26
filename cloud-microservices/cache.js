//This code creates a Redis client using the redis package and connects to it.
const redis = require('redis');

const client = redis.createClient({
  host: 'localhost',
  port: 6379,
});

client.on('connect', () => {
  console.log('Connected to Redis');
});

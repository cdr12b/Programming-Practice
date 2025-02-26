/*This code creates a PostgreSQL database using
the pg package and creates a table called "users" with two columns: id and name.
*/
const { Pool } = require('pg');

const pool = new Pool({
  user: 'postgres',
  host: 'localhost',
  database: 'mydb',
  password: 'password',
  port: 5432,
});

pool.query('CREATE TABLE IF NOT EXISTS users (id SERIAL PRIMARY KEY, name VARCHAR(255));', (err, res) => {
  if (err) console.error(err);
  else console.log(res);
});
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  profile JSONB NOT NULL   -- holds email, ssn inside the blob
);

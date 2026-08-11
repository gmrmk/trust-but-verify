CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  ssn_encrypted BYTEA NOT NULL,   -- pgcrypto
  email_enc BYTEA NOT NULL
);

const r = require('express').Router();
const rateLimit = require('express-rate-limit');
const loginLimiter = rateLimit({ windowMs: 60000, max: 5 });
r.post('/login', loginLimiter, loginHandler);
module.exports = r;

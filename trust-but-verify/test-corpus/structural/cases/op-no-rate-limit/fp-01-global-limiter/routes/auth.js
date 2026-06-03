const r = require('express').Router();
r.post('/login', loginHandler);
module.exports = r;

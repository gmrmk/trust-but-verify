const r = require('express').Router();
r.post('/login', loginHandler);
r.post('/signup', signupHandler);
module.exports = r;

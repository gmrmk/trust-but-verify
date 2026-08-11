const r = require('express').Router();
r.get('/users/:id', getUser);
r.post('/users', createUser);
r.put('/users/:id', updateUser);
module.exports = r;

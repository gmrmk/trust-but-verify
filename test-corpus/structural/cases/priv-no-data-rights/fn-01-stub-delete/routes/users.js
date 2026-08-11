const r = require('express').Router();
r.get('/users/:id', getUser);
r.delete('/delete-account', (req, res) => res.status(501).send('not implemented'));
module.exports = r;

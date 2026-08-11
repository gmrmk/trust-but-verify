const r = require('express').Router();
r.get('/users/:id', getUser);
r.delete('/account/delete-account', eraseUser);   // GDPR Art. 17
r.get('/account/export', exportUserData);          // GDPR Art. 20
module.exports = r;

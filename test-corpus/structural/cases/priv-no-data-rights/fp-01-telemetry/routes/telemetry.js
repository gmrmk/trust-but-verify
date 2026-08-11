const r = require('express').Router();
r.post('/events', (req, res) => { log(req.headers['user-agent']); res.sendStatus(204); });
module.exports = r;

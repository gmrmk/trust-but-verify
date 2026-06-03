const rateLimit = require('express-rate-limit');
app.use(rateLimit({ windowMs: 60000, max: 20 }));   // applied to all routes
app.use('/auth', require('./routes/auth'));

import express from 'express';
import cors from 'cors';
import aerodromeLayoutRoutes from './routes/aerodromeLayoutRoutes';

const app = express();
const port = process.env.API_PORT || 4000;

app.use(cors());
app.use(express.json());

app.use('/api/aerodrome-layout', aerodromeLayoutRoutes);

app.get('/health', (req, res) => {
  res.json({ status: 'ok', service: 'FTS Node API' });
});

app.listen(port, () => {
  console.log(`FTS Node API running on http://localhost:${port}`);
});

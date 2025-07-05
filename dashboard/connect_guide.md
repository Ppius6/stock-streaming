# Dashboard Connection Guide

This guide explains how to connect various visualization tools to your real-time stock streaming database.

## 🔗 Database Connection Details

```
Host:     localhost (or WSL IP for Windows users)
Port:     5432
Database: stockdb
Username: stocks
Password: [Check your .env file]
```

**For Windows + WSL users:**

- Use your WSL IP address instead of `localhost`
- Find WSL IP: `hostname -I | awk '{print $1}'` in WSL terminal

## Tableau Connection

### Setup Steps

1. Open Tableau Desktop
2. Click "Connect" → "To a Server" → "PostgreSQL"
3. Enter connection details:
   - **Server:** `localhost` (or WSL IP)
   - **Port:** `5432`
   - **Database:** `stockdb`
   - **Username:** `stocks`
   - **Password:** [From your .env file]

### Recommended Data Source Setup

```sql
-- Custom SQL Query for Live Dashboard
SELECT 
    symbol,
    price,
    volume,
    timestamp,
    LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp) as prev_price,
    price - LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp) as price_change,
    ROUND(((price - LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp)) / 
           LAG(price) OVER (PARTITION BY symbol ORDER BY timestamp) * 100), 2) as pct_change
FROM stock_prices 
WHERE timestamp >= NOW() - INTERVAL '4 hours'
ORDER BY timestamp DESC
```

### Dashboard Ideas

- **Line Charts:** Price trends over time by symbol
- **Heat Maps:** Percentage change by stock
- **Bar Charts:** Volume comparison
- **KPI Cards:** Current price, daily change, volume

## PowerBI Connection

### Setup Steps

1. Open PowerBI Desktop
2. Get Data → Database → PostgreSQL Database
3. Enter connection details:
   - **Server:** `localhost:5432` (or `WSL_IP:5432`)
   - **Database:** `stockdb`
4. Advanced Options → SQL Statement:

```sql
SELECT * FROM stock_prices 
WHERE timestamp >= CURRENT_DATE - INTERVAL '7 days'
```

### Data Refresh Settings

- Enable **Auto-refresh** every 5-10 seconds for live data
- Use **DirectQuery** mode for real-time updates
- Set up **Scheduled refresh** for published reports

## DBeaver Connection

### Setup Steps

1. New Database Connection → PostgreSQL
2. Connection Settings:
   - **Host:** `localhost` (or WSL IP)
   - **Port:** `5432`
   - **Database:** `stockdb`
   - **Username:** `stocks`
   - **Password:** [From .env file]
3. Test Connection → Finish

## Troubleshooting

### Connection Refused

```bash
# Check if PostgreSQL is running
docker-compose ps

# Check if port is accessible
telnet localhost 5432

# For WSL users, get correct IP
hostname -I | awk '{print $1}'
```

### Authentication Failed

```bash
# Check your .env file
cat .env

# Test connection from command line
PGPASSWORD=your_password psql -h localhost -U stocks -d stockdb -c "SELECT 1;"
```

### No Data in Tables

```bash
# Check if table exists
docker exec -it postgres psql -U stocks -d stockdb -c "\dt"

# Check recent data
docker exec -it postgres psql -U stocks -d stockdb -c "SELECT COUNT(*) FROM stock_prices;"

# Restart producer/consumer if needed
python producers/stock_producer.py
python consumers/db_consumer.py
```

### Performance Issues

- Add indexes for frequently queried columns
- Use time-based partitioning for large datasets
- Limit query time ranges (last hour/day instead of all data)
- Consider data aggregation for historical analysis

## Support

If you encounter issues:

1. Check the main README.md for setup instructions
2. Verify all Docker containers are running
3. Test database connection from command line first
4. Check logs: `docker-compose logs postgres`

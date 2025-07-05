# Real-Time Stock Streaming & Visualization Platform

A comprehensive real-time stock market data streaming system built with Python, Apache Kafka, PostgreSQL, and Docker. Stream live stock prices from Yahoo Finance, process them through Kafka, store in PostgreSQL, and visualize with modern dashboard tools.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Yahoo Finance │───▶│    Kafka     │───▶│   PostgreSQL    │───▶│  Tableau/PowerBI │
│   (Data Source) │    │ (Streaming)  │    │   (Storage)     │    │ (Visualization)  │
└─────────────────┘    └──────────────┘    └─────────────────┘    └──────────────────┘
         │                       │                     │                      │
    ┌────▼────┐              ┌───▼───┐           ┌─────▼─────┐          ┌─────▼─────┐
    │Producer │              │ Topic │           │   Table   │          │Dashboard  │
    │ Script  │              │Queue  │           │stock_prices│         │ & Alerts │
    └─────────┘              └───────┘           └───────────┘          └───────────┘
```

## Features

- **Real-time Data Streaming**: Live stock prices from Yahoo Finance
- **High-Performance Processing**: Apache Kafka for reliable message streaming
- **Persistent Storage**: PostgreSQL with optimized schema and indexes
- **Multi-Platform Visualization**: Support for Tableau, PowerBI, DBeaver, and custom dashboards
- **Containerized Deployment**: Docker Compose for easy setup and scaling
- **Monitoring Tools**: pgAdmin web interface for database management
- **Cross-Platform**: Works on Windows, macOS, Linux, and WSL

## Supported Stock Symbols

Currently tracking major tech stocks and market leaders:

- **Technology**: NVDA, MSFT, AAPL, GOOGL, GOOG, META, AVGO
- **Semiconductors**: TSM, NVDA, AVGO
- **E-commerce**: AMZN
- **Automotive**: TSLA
- **Finance**: JPM
- **Retail**: WMT

*Easily configurable in `config/stocks.json`*

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.8+
- Git

### Installation

1. **Clone the repository**

   ```bash
   git clone <your-repo-url>
   cd stock-streaming
   ```

2. **Set up environment variables**

   ```bash
   # Copy example environment file
   cp .env.example .env
   
   # Edit .env with your preferred passwords
   nano .env
   ```

3. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Start the infrastructure**

   ```bash
   # Start all services (Kafka, PostgreSQL, pgAdmin)
   docker-compose up -d
   
   # Wait for services to initialize (30-60 seconds)
   docker-compose logs -f
   ```

5. **Start the data pipeline**

   ```bash
   # Terminal 1: Start producer (streams stock prices)
   python producers/stock_producer.py
   
   # Terminal 2: Start consumer (saves to database)
   python consumers/db_consumer.py
   ```

6. **Verify data flow**

   ```bash
   # Check data is being stored
   docker exec -it postgres psql -U stocks -d stockdb -c "SELECT COUNT(*) FROM stock_prices;"
   ```

## 📋 Project Structure

```
stock-streaming/
├── docker-compose.yml          # Infrastructure configuration
├── requirements.txt            # Python dependencies
├── .env                       # Environment variables (not in git)
├── .env.example              # Template for environment setup
├── .gitignore               # Git ignore rules
├── README.md               # This file
├── config/
│   └── stocks.json        # Stock symbols configuration
├── producers/
│   └── stock_producer.py  # Yahoo Finance → Kafka streamer
├── consumers/
│   └── db_consumer.py     # Kafka → PostgreSQL consumer
├── sql/
│   └── init_tables.sql    # Database schema
└── dashboard/
    └── connect_guide.md   # Visualization setup guide
```

## Configuration

### Environment Variables (.env)

```bash
# Database Configuration
POSTGRES_USER=stocks
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=stockdb

# pgAdmin Configuration
PGADMIN_EMAIL=your-email@example.com
PGADMIN_PASSWORD=your_secure_pgadmin_password
```

### Stock Selection (config/stocks.json)

```json
{
  "stocks": [
    "NVDA", "MSFT", "AAPL", "AMZN", "GOOGL",
    "GOOG", "META", "AVGO", "TSM", "TSLA", "JPM", "WMT"
  ],
  "refresh_interval": 10
}
```

## Usage Guide

### Starting the System

```bash
# 1. Start infrastructure
docker-compose up -d

# 2. Wait for initialization
sleep 30

# 3. Check services
docker-compose ps

# 4. Start data pipeline
python producers/stock_producer.py    # Terminal 1
python consumers/db_consumer.py       # Terminal 2
```

### Monitoring Data Flow

```bash
# Check Kafka topics
docker exec kafka kafka-topics --list --bootstrap-server localhost:9092

# Monitor database
docker exec -it postgres psql -U stocks -d stockdb

# View recent data
SELECT symbol, price, timestamp FROM stock_prices ORDER BY timestamp DESC LIMIT 10;
```

### Accessing Services

- **PostgreSQL**: `localhost:5432`
- **pgAdmin**: `http://localhost:5051` (<admin@admin.com> / [your password])
- **Kafka**: `localhost:9092`
- **Zookeeper**: `localhost:2181`

## Visualization & Dashboards

### Connecting External Tools

See `dashboard/connect_guide.md` for detailed instructions on connecting:

- Tableau Desktop/Online
- Microsoft PowerBI
- DBeaver
- Custom Python dashboards

## 🔍 Troubleshooting

### Common Issues

**"NoBrokersAvailable" Error**

```bash
# Kafka not ready - wait longer
docker-compose logs kafka | grep "started"
sleep 60
python producers/stock_producer.py
```

**Database Connection Refused**

```bash
# Check PostgreSQL status
docker-compose logs postgres
docker exec -it postgres psql -U stocks -d stockdb -c "SELECT 1;"
```

**No Data in Database**

```bash
# Verify table exists
docker exec -it postgres psql -U stocks -d stockdb -c "\dt"

# Check producer/consumer logs
python producers/stock_producer.py  # Look for "Sent:" messages
python consumers/db_consumer.py     # Look for "Stored:" messages
```

**WSL + Windows Networking Issues**

```bash
# Get WSL IP for Windows tools
hostname -I | awk '{print $1}'

# Use this IP in DBeaver/Tableau instead of localhost
```

## 🛠️ Development

### Adding New Data Sources

1. Create new producer in `producers/` directory
2. Follow existing producer pattern
3. Send data to appropriate Kafka topic
4. Update consumer to handle new data format

### Extending Database Schema

```sql
-- Add technical indicators
ALTER TABLE stock_prices ADD COLUMN rsi DECIMAL(5,2);
ALTER TABLE stock_prices ADD COLUMN moving_avg_20 DECIMAL(10,2);
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 for Python code
- Add tests for new features
- Update documentation for any changes
- Ensure Docker containers build successfully

## 🙏 Acknowledgments

- **Yahoo Finance** for providing free stock market data
- **Apache Kafka** for robust message streaming
- **PostgreSQL** for reliable data storage
- **Docker** for containerization platform
- **Confluent** for Kafka Docker images

## Support

For questions, issues, or contributions:

- Open an issue on GitHub
- Check the troubleshooting section above
- Review `dashboard/connect_guide.md` for visualization help

---

**⭐ Star this repository if you find it useful!**

Built with ❤️ for real-time financial data enthusiasts.

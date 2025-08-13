# WOL API 📖

A powerful REST API that provides access to Bible verses and study content from the Watchtower Online Library (wol.jw.org). Built with Rust using the Rocket framework and PostgreSQL for high performance and reliability.

[![Rust](https://img.shields.io/badge/rust-%23000000.svg?style=for-the-badge&logo=rust&logoColor=white)](https://www.rust-lang.org/)
[![Docker](https://img.shields.io/badge/docker-%230db7ed.svg?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)

## ✨ Features

- **📜 Verse Retrieval**: Get individual Bible verses with metadata
- **📚 Study Content**: Access study notes, research guide articles, and cross-references
- **🔄 Dynamic Scraping**: Automatically fetches missing content from wol.jw.org
- **📊 Field Filtering**: Customize response data using dot notation (e.g., `verse.study_notes.content.text`)
- **📝 Verse Ranges**: Retrieve multiple consecutive verses in a single request (e.g., Matt 24:19-20)
- **⚡ Caching**: Fast responses (~200ms) with PostgreSQL caching
- **🔄 Force Refresh**: Option to fetch fresh data from source (`fetch=true`)
- **🏥 Health Monitoring**: Built-in health check endpoints

## 🚀 Quick Start

### Prerequisites

- [Docker](https://www.docker.com/get-started) and Docker Compose
- [Git](https://git-scm.com/)

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/advenimus/wol-api.git
   cd wol-api
   ```

2. **Start the services**

   ```bash
   docker-compose up -d --build
   ```

3. **Initialize the database** (first time only)

   ```bash
   # Wait for containers to start, then run:
   docker exec -it wol-api-backend-1 python3 scripts/db_manager_docker.py
   # Choose option 1: "Setup Database"
   ```

4. **Test the API**
   ```bash
   curl "http://localhost:8000/api/v1/study/40/24/14"
   ```

That's it! 🎉 Your WOL API is now running on `http://localhost:8000`

## 📖 API Documentation

### Base URL

- **Local**: `http://localhost:8000`

### Endpoints

#### 1. Basic Verse Retrieval

```
GET /api/v1/verse/{book}/{chapter}/{verse}
```

Returns plain text verse content.

**Example:**

```bash
curl "http://localhost:8000/api/v1/verse/40/24/14"
# Returns: "Therefore, when you catch sight of the disgusting thing..."
```

#### 2. Enhanced Study Endpoint

```
GET /api/v1/study/{book}/{chapter}/{verse}
```

Returns structured JSON with verse text, study notes, and research content.

**Query Parameters:**

- `fields` - Comma-separated list of fields to include
- `limit` - Maximum items for arrays
- `fetch` - Set to `true` to force fresh data from wol.jw.org

**Available Fields:**

- `verse.verse_text` - The Bible verse text
- `verse.book_name` - Book name (e.g., "Matthew")
- `verse.study_notes.content.text` - Study notes for the verse
- `study_content.study_articles` - Research guide articles
- `study_content.outline` - Chapter outline

**Examples:**

```bash
# Get verse with study notes
curl "http://localhost:8000/api/v1/study/40/24/14?fields=verse.verse_text,verse.study_notes.content.text"

# Get research articles (limited to 3)
curl "http://localhost:8000/api/v1/study/40/24/14?fields=study_content.study_articles&limit=3"

# Force fresh data from wol.jw.org
curl "http://localhost:8000/api/v1/study/40/24/14?fetch=true"
```

#### 3. Verse Range Endpoint ⭐ New!

```
GET /api/v1/study/{book}/{chapter}/{verse_range}
```

Returns multiple consecutive verses combined with their study notes.

**Examples:**

```bash
# Get Matthew 24:19-20
curl "http://localhost:8000/api/v1/study/40/24/19-20"

# Single verse (equivalent to 19-19)
curl "http://localhost:8000/api/v1/study/40/24/19-19"

# Longer range
curl "http://localhost:8000/api/v1/study/40/24/18-21"
```

**Response Format:**

```json
{
  "book_num": 40,
  "book_name": "Matthew",
  "chapter": 24,
  "verse_range": "19-20",
  "combined_text": "Woe to the pregnant women and those nursing a baby in those days! Keep praying that your flight may not occur in wintertime nor on the Sabbath day;",
  "study_notes": [
    "in wintertime:Heavy rains, flooding, and cold weather...",
    "on the Sabbath day:In territories like Judea, restrictions..."
  ]
}
```

#### 4. Health Check

```
GET /health
GET /api/v1/health
```

Returns service status and database connectivity information.

## 📝 Bible Book Numbers

Common book numbers for quick reference:

| Book     | Number | Book     | Number | Book    | Number |
| -------- | ------ | -------- | ------ | ------- | ------ |
| Genesis  | 1      | Psalms   | 19     | Matthew | 40     |
| Exodus   | 2      | Proverbs | 20     | Mark    | 41     |
| 1 Samuel | 9      | Isaiah   | 23     | Luke    | 42     |
| 2 Samuel | 10     | Jeremiah | 24     | John    | 43     |
| 1 Kings  | 11     | Daniel   | 27     | Acts    | 44     |
| 2 Kings  | 12     | Malachi  | 39     | Romans  | 45     |

[Complete list available in the codebase]

## 🔧 Configuration

### Environment Variables

- `DATABASE_URL` - PostgreSQL connection string (default: `postgresql://postgres:postgres@db:5432/wol-api`)
- `ROCKET_PORT` - API server port (default: 8000)

### Docker Compose

The included `docker-compose.yml` configures:

- **Backend**: Rust API server on port 8000
- **Database**: PostgreSQL with persistent storage
- **Networking**: Internal Docker network for service communication

## 🗄️ Database Management

Use the interactive database manager for common tasks:

```bash
# Local development
docker exec -it wol-api-backend-1 python3 scripts/db_manager_docker.py

# Production server
docker exec -it wol-api_backend_1 python3 scripts/db_manager_docker.py
```

**Available Options:**

1. **Setup Database** - Creates tables and populates with verse data
2. **Delete Database** - Safely removes all data (with confirmation)
3. **Run Custom Query** - Execute SQL queries with safety checks

## ⚡ Performance

- **Cached Responses**: ~200ms average response time
- **Fresh Scraping**: ~10-15 seconds when using `fetch=true`
- **Concurrent Requests**: Supports high concurrency via Rocket's async architecture
- **Database**: PostgreSQL with connection pooling for optimal performance

## 🛠️ Development

### Local Development

```bash
# Start services
docker-compose up --build

# View logs
docker logs -f wol-api-backend-1

# Execute database operations
docker exec -it wol-api-backend-1 python3 scripts/db_manager_docker.py
```

### Manual Build (without Docker)

```bash
cd backend
cargo build --release
cargo run
```

### Testing

```bash
cd backend
cargo test
```

## 🚀 Deployment

The project uses GitHub Actions for automatic deployment:

1. **Push to main branch** triggers automatic deployment
2. **Production server** updates via rsync and docker-compose
3. **Health checks** verify successful deployment

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## ⚠️ Disclaimer

This API is an independent project and is not affiliated with or endorsed by the Watch Tower Bible and Tract Society of Pennsylvania or any of its associated organizations. The content is sourced from publicly available materials on wol.jw.org for educational and research purposes.

## 🙏 Acknowledgments

- **[@JudeDavis1](https://github.com/JudeDavis1)** - Original concept and expertise
- **Rust Community** - For the amazing ecosystem and tools
- **Rocket Framework** - For the elegant web framework
- **PostgreSQL** - For robust data storage

---

**Made with ❤️ and Rust** 🦀

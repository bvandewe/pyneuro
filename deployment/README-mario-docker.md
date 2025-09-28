# 🍕 Mario's Pizzeria Docker Compose Setup

This Docker Compose configuration provides a complete development environment for Mario's Pizzeria, including all necessary services for a full-stack application with authentication, data persistence, and event streaming.

## 🏗️ Services Overview

### Application Services

- **🍕 Mario Pizzeria App** (`mario-pizzeria-app`)
  - **Port**: 8080 (Main), 5678 (Debug)
  - **URL**: http://localhost:8080
  - **API Docs**: http://localhost:8080/api/docs
  - Full FastAPI application with Neuroglia framework
  - Debug support with remote debugging on port 5678

### Data & Persistence

- **🗄️ MongoDB** (`mongodb`)

  - **Port**: 27017
  - **Connection**: `mongodb://localhost:27017`
  - Primary database for pizzeria data (orders, customers, pizzas)
  - Pre-configured with sample data and optimized indexes

- **📊 MongoDB Express** (`mongo-express`)
  - **Port**: 8081
  - **URL**: http://localhost:8081
  - **Credentials**: admin / admin123
  - Web-based MongoDB admin interface

### Event Streaming & Sourcing

- **🎪 EventStoreDB** (`eventstoredb`)

  - **Port**: 2113 (HTTP), 1113 (WebSocket)
  - **URL**: http://localhost:2113
  - Event sourcing database for domain events
  - Supports projections and event replay

- **🎬 Event Player** (`event-player`)
  - **Port**: 8085
  - **URL**: http://localhost:8085
  - Event visualization and replay tool
  - Integrated with Mario's Pizzeria event streams

### Authentication & Authorization

- **🔐 Keycloak** (`keycloak`)

  - **Port**: 8090
  - **Admin Console**: http://localhost:8090/admin
  - **Admin Credentials**: admin / admin
  - Pre-configured Mario Pizzeria realm with roles and users

- **🐘 PostgreSQL** (`keycloak-db`)
  - **Port**: Internal (5432)
  - Database backend for Keycloak

## 🚀 Quick Start

### Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose v2.0+
- At least 4GB RAM available for containers

### Starting the Environment

1. **Clone and navigate to the project:**

   ```bash
   cd /path/to/pyneuro
   ```

2. **Start all services:**

   ```bash
   docker-compose -f docker-compose.mario.yml up -d
   ```

3. **View logs (optional):**

   ```bash
   # All services
   docker-compose -f docker-compose.mario.yml logs -f

   # Specific service
   docker-compose -f docker-compose.mario.yml logs -f mario-pizzeria-app
   ```

4. **Wait for services to be ready:**

   ```bash
   # Check service health
   docker-compose -f docker-compose.mario.yml ps
   ```

### Accessing Services

Once all services are running, access them at:

| Service                 | URL                            | Credentials             |
| ----------------------- | ------------------------------ | ----------------------- |
| 🍕 Mario's Pizzeria API | http://localhost:8080/api/docs | None (public endpoints) |
| 🗄️ MongoDB Express      | http://localhost:8081          | admin / admin123        |
| 🎪 EventStoreDB         | http://localhost:2113          | None (development mode) |
| 🎬 Event Player         | http://localhost:8085          | None                    |
| 🔐 Keycloak Admin       | http://localhost:8090/admin    | admin / admin           |

## 👤 Pre-configured Users

The Keycloak realm comes with sample users for testing:

### Customers

- **Username**: `mario.rossi` / **Password**: `pizza123`
- **Role**: Customer
- **Email**: mario.rossi@example.com

### Staff

- **Username**: `giuseppe.chef` / **Password**: `chef123`
- **Role**: Chef
- **Email**: giuseppe@mario-pizzeria.com

### Management

- **Username**: `antonio.manager` / **Password**: `manager123`
- **Role**: Manager (includes chef permissions)
- **Email**: antonio@mario-pizzeria.com

## 🗃️ Sample Data

The MongoDB database is automatically initialized with:

### Pizzas (5 varieties)

- Margherita (Classic) - €12.99
- Pepperoni (Classic) - €15.99
- Quattro Stagioni (Premium) - €18.99
- Vegetarian Delight (Vegetarian) - €16.99
- Vegan Supreme (Vegan) - €19.99

### Customers (2 sample customers)

- Mario Rossi (Naples, Italy) - 150 loyalty points
- Luigi Verdi (Rome, Italy) - 75 loyalty points

## 🛠️ Development Workflow

### API Development

1. **Make code changes** in `samples/mario-pizzeria/`
2. **Hot reload** is enabled - changes are automatically reflected
3. **Debug** by attaching to port 5678 in VS Code
4. **Test endpoints** via http://localhost:8080/api/docs

### Database Operations

1. **View data** via MongoDB Express: http://localhost:8081
2. **Run queries** directly in the MongoDB container:

   ```bash
   docker-compose -f docker-compose.mario.yml exec mongodb mongosh mario_pizzeria
   ```

### Event Streaming

1. **Publish events** via the API or Event Player
2. **View events** in EventStoreDB: http://localhost:2113
3. **Monitor event flow** in Event Player: http://localhost:8085

### Authentication Testing

1. **Login** to Keycloak: http://localhost:8090/admin
2. **Manage users** and roles in the Mario Pizzeria realm
3. **Test authentication** with pre-configured users
4. **Get tokens** for API testing

## 🔧 Configuration

### Environment Variables

The application supports these environment variables:

```yaml
# Database connections
CONNECTION_STRINGS: '{"mongo": "mongodb://mongodb:27017", "eventstore": "esdb://eventstoredb:2113?Tls=false"}'

# Event streaming
CLOUD_EVENT_SINK: http://event-player/events/pub
CLOUD_EVENT_SOURCE: https://mario-pizzeria.io
CLOUD_EVENT_TYPE_PREFIX: io.mario-pizzeria

# Authentication
KEYCLOAK_SERVER_URL: http://keycloak:8080
KEYCLOAK_REALM: mario-pizzeria
KEYCLOAK_CLIENT_ID: mario-app

# Application settings
DATA_DIR: /app/data
ENABLE_CORS: "true"
LOG_LEVEL: DEBUG
```

### Custom Configuration

To customize the setup:

1. **Modify environment variables** in `docker-compose.mario.yml`
2. **Update database init script** in `deployment/mongo/init-mario-db.js`
3. **Customize Keycloak realm** in `deployment/keycloak/realm-export.json`
4. **Adjust service ports** if needed to avoid conflicts

## 📊 Monitoring & Debugging

### Container Logs

```bash
# All services
docker-compose -f docker-compose.mario.yml logs -f

# Application only
docker-compose -f docker-compose.mario.yml logs -f mario-pizzeria-app

# Database only
docker-compose -f docker-compose.mario.yml logs -f mongodb
```

### Health Checks

```bash
# Service status
docker-compose -f docker-compose.mario.yml ps

# Application health
curl http://localhost:8080/health

# Database connection
docker-compose -f docker-compose.mario.yml exec mario-pizzeria-app python -c "
import pymongo
client = pymongo.MongoClient('mongodb://mongodb:27017')
print(client.admin.command('ismaster'))
"
```

### Remote Debugging

1. **VS Code**: Attach to `localhost:5678`
2. **PyCharm**: Create remote debug configuration for `localhost:5678`
3. **Set breakpoints** in your Mario Pizzeria code
4. **Trigger API calls** to hit breakpoints

## 🧹 Cleanup

### Stop Services

```bash
docker-compose -f docker-compose.mario.yml down
```

### Clean Up (Remove data volumes)

```bash
docker-compose -f docker-compose.mario.yml down -v
```

### Complete Cleanup (Remove images)

```bash
docker-compose -f docker-compose.mario.yml down -v --rmi all
```

## 🚨 Troubleshooting

### Common Issues

**Port Conflicts**

- Check if ports 8080, 8081, 8085, 8090, 27017, 2113 are free
- Modify ports in docker-compose.mario.yml if needed

**Memory Issues**

- Ensure at least 4GB RAM is available
- Reduce service resource limits if needed

**Database Connection Issues**

- Wait for MongoDB to fully initialize (30-60 seconds)
- Check logs: `docker-compose -f docker-compose.mario.yml logs mongodb`

**Keycloak Setup Issues**

- Keycloak takes 2-3 minutes to fully start
- Check realm import: `docker-compose -f docker-compose.mario.yml logs keycloak`

**Application Startup Issues**

- Ensure all dependencies are up: `docker-compose -f docker-compose.mario.yml up -d --wait`
- Check Python path and imports in logs

### Reset Environment

If you encounter persistent issues:

```bash
# Complete reset
docker-compose -f docker-compose.mario.yml down -v --rmi all
docker system prune -a
docker-compose -f docker-compose.mario.yml up -d --build
```

## 📚 Additional Resources

- [Neuroglia Framework Documentation](../../docs/index.md)
- [Mario's Pizzeria Tutorial](../../docs/guides/mario-pizzeria-tutorial.md)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Keycloak Documentation](https://www.keycloak.org/documentation)
- [MongoDB Documentation](https://docs.mongodb.com/)
- [EventStoreDB Documentation](https://developers.eventstore.com/)

## 🎯 Next Steps

1. **Explore the API** at http://localhost:8080/api/docs
2. **Create orders** using the sample customers and pizzas
3. **Monitor events** in the Event Player
4. **Customize authentication** in Keycloak
5. **Extend the domain model** with new features

Happy coding with Mario's Pizzeria! 🍕

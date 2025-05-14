# VivaCRM v2 Docker Setup

VivaCRM is a customer relationship management system built with Django and modern web technologies.

## Docker Setup

This project is containerized using Docker and Docker Compose for easy development and deployment.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

### Getting Started with Docker

1. Clone the repository:
```bash
git clone https://github.com/vivacrm/vivacrm-v2.git
cd vivacrm-v2
```

2. Create an `.env` file from the example:
```bash
cp .env.example .env
```

3. Update the `.env` file with your configurations.

4. Build and start the containers:
```bash
docker-compose up -d --build
```

5. Create a superuser:
```bash
docker-compose exec web python manage.py createsuperuser
```

6. Access the application at http://localhost:8000

### Docker Compose Services

- `web`: Django application
- `db`: PostgreSQL database
- `redis`: Redis for caching and as Celery broker
- `celery`: Celery worker for background tasks
- `celery-beat`: Celery beat for scheduled tasks
- `nginx`: Nginx web server for serving static files and proxying requests

### Docker Commands

Build and start containers:
```bash
docker-compose up -d
```

Stop containers:
```bash
docker-compose down
```

View logs:
```bash
docker-compose logs -f
```

Run Django management commands:
```bash
docker-compose exec web python manage.py <command>
```

### Production Deployment Considerations

1. **Environment Variables**: 
   - Ensure all sensitive information is stored in environment variables
   - Generate a secure `SECRET_KEY` for production

2. **Database**:
   - Use a production-ready PostgreSQL instance
   - Consider using a managed database service in cloud environments

3. **HTTPS**:
   - Configure SSL/TLS in production
   - Update Nginx configuration to handle HTTPS

4. **Backups**:
   - Set up regular database backups
   - Configure volume backups for user-uploaded media

5. **Monitoring**:
   - Add monitoring for container health
   - Configure logging aggregation

## Customizing Docker Setup

### Scaling Services

You can scale the web and celery workers for better performance:

```bash
docker-compose up -d --scale web=3 --scale celery=2
```

### Changing Database Settings

To use a different database configuration, modify the `db` service in `docker-compose.yml` and update the environment variables accordingly.

### Adding Custom Packages

If you need additional system packages, add them to the `RUN apt-get install` command in the Dockerfile.

## Development with Docker

For local development using Docker:

1. Use the development version of docker-compose:
```bash
docker-compose -f docker-compose.dev.yml up
```

2. This mounts the local directory into the container for live code changes

## License

This project is licensed under the [MIT License](LICENSE).
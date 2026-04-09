# Odoo Setup Guide - Gold Tier

This guide walks you through setting up Odoo Community Edition for the AI Employee accounting integration.

## Prerequisites

- Docker Desktop installed and running
- Docker Compose v2+ (included with Docker Desktop)
- 2GB RAM available for Odoo container
- 5GB disk space for database and filestore

## Quick Start (Docker Compose)

### 1. Start Odoo

```bash
# From project root
cd odoo
docker compose up -d

# Check status
docker compose ps

# View logs
docker compose logs -f odoo
```

### 2. Initial Setup

1. Open browser: http://localhost:8069
2. You'll see the database creation screen
3. Fill in:
   - **Email:** admin@example.com
   - **Password:** admin (change later!)
   - **Database Name:** odoo_db
   - **Phone:** Optional
   - **Language:** English
   - **Country:** Your country
   - **Demo Data:** Check "Load demonstration data" (recommended for testing)

4. Click **Create database**
5. Wait for Odoo to initialize (2-3 minutes)

### 3. Install Accounting Module

1. After login, go to **Apps**
2. Search for "Invoicing" or "Accounting"
3. Click **Install** on "Invoicing" (Community Edition)
4. Wait for installation to complete

### 4. Configure Basic Settings

1. Go to **Settings → Configuration → Invoicing**
2. Enable:
   - Customer Invoices
   - Vendor Bills
   - Payments
3. Save

### 5. Create Test Customer

1. Go to **Customers → Customers**
2. Click **Create**
3. Fill in:
   - Name: Test Customer
   - Email: test@example.com
   - Phone: Optional
4. Click **Save**
5. Note the customer ID from URL (e.g., `id=12`)

### 6. Create Your First Invoice

1. Go to **Customers → Invoices**
2. Click **Create**
3. Fill in:
   - Customer: Select test customer
   - Invoice Date: Today
   - Add a line:
     - Label: Service/Product
     - Quantity: 1
     - Unit Price: 100
4. Click **Confirm**
5. Note the invoice ID

### 7. Update MCP Server Configuration

Edit `mcp-servers/odoo-mcp/index.js`:

```javascript
const CONFIG = {
  ODOO_URL: 'http://localhost:8069',
  ODOO_DB: 'odoo_db',           // Match your database name
  ODOO_EMAIL: 'admin@example.com',
  ODOO_PASSWORD: 'admin',       // Change to your password
};
```

### 8. Install Dependencies & Start MCP

```bash
cd mcp-servers/odoo-mcp
npm install

# Start server
npm start

# Or with PM2
pm2 start mcp-servers/odoo-mcp/index.js --name odoo-mcp
```

## Docker Commands Reference

```bash
# Start Odoo
docker compose up -d

# Stop Odoo
docker compose down

# View logs
docker compose logs -f odoo
docker compose logs -f db

# Restart
docker compose restart

# Reset (WARNING: deletes all data!)
docker compose down -v
docker compose up -d
# Then recreate database from scratch

# Backup database
docker exec odoo_postgres pg_dump -U odoo odoo_db > backup.sql

# Restore database
docker exec -i odoo_postgres psql -U odoo odoo_db < backup.sql
```

## Configuration Files

### docker-compose.yml
Located at `odoo/docker-compose.yml`:
- Port 8069 exposed for web access
- PostgreSQL on internal network
- Volumes persist data across restarts

### Custom Addons (Optional)
Place custom modules in `odoo/odoo-addons/`

### Custom Config (Optional)
Place Odoo config file in `odoo/odoo-config/odoo.conf`

## Production Considerations

For production deployment:

1. **Change default passwords**
   - Admin password in docker-compose.yml
   - Database master password

2. **Use environment variables for secrets**
   ```yaml
   environment:
     - ADMIN_PASSWORD=${ODOO_ADMIN_PASSWORD}
   ```

3. **Add reverse proxy** (nginx/traefik) for HTTPS

4. **Set up automated backups**
   ```bash
   # Cron job for daily backup
   0 2 * * * docker exec odoo_postgres pg_dump -U odoo odoo_db > /backups/odoo_$(date +\%Y\%m\%d).sql
   ```

5. **Monitor disk usage**
   - Database grows over time
   - Set up alerts for > 80% usage

## Troubleshooting

### Odoo Won't Start

```bash
# Check container status
docker compose ps

# Check logs
docker compose logs odoo

# Common issues:
# - Port 8069 already in use: Change port in docker-compose.yml
# - Database not ready: docker compose logs db
```

### Can't Connect from MCP Server

1. Verify Odoo is running: `curl http://localhost:8069`
2. Check database name matches configuration
3. Verify email/password are correct
4. Check MCP server logs for errors

### Database Creation Fails

1. Ensure PostgreSQL container is healthy: `docker compose ps db`
2. Delete and recreate: `docker compose down -v && docker compose up -d`
3. Check disk space

### Authentication Errors in MCP

1. Update credentials in `mcp-servers/odoo-mcp/index.js`
2. Restart MCP server
3. Verify user has accounting permissions

## Odoo JSON-RPC API Reference

Official documentation: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html

Key endpoints:
- `/jsonrpc` - All API calls go here
- Authentication: `common.login`
- Data operations: `object.execute` or `object.execute_kw`

## Next Steps

After Odoo is set up:

1. Configure chart of accounts for your country
2. Set up products/services catalog
3. Add real customers
4. Test invoice creation via MCP
5. Integrate with CEO Briefing generator

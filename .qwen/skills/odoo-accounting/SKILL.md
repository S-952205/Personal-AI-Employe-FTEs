---
name: odoo-accounting
description: Odoo Community accounting operations via JSON-RPC API
version: 1.0.0
---

# Odoo Accounting Operations

Manage business accounting through Odoo Community Edition integration.

## Setup Requirements

### Odoo Installation

1. **Start Odoo via Docker**
   ```bash
   cd odoo
   docker compose up -d
   ```

2. **Create Database**
   - Go to http://localhost:8069
   - Create database with admin user
   - Install Invoicing module

3. **Configure**
   - Set up chart of accounts
   - Add customers
   - Configure payment terms

See full guide: `docs/guides/ODOO_SETUP.md`

## MCP Server Tools

### Invoice Operations

#### `odoo_create_invoice`
Create a new customer invoice.

```json
{
  "customerId": 12,
  "items": [
    {
      "name": "Web Development Services",
      "quantity": 1,
      "price": 1500.00
    },
    {
      "name": "Hosting (Monthly)",
      "quantity": 1,
      "price": 50.00
    }
  ],
  "dueDate": "2026-05-05",  // optional
  "note": "Project Alpha - Milestone 1"  // optional
}
```

#### `odoo_list_invoices`
List invoices with status filter.

```json
{
  "status": "all",  // draft, posted, paid, cancelled, all
  "limit": 20
}
```

#### `odoo_get_invoice`
Get invoice details.

```json
{
  "invoiceId": 1
}
```

#### `odoo_record_payment`
Record payment against invoice.

```json
{
  "invoiceId": 1,
  "amount": 1550.00,
  "date": "2026-04-10",    // optional
  "memo": "Bank transfer"   // optional
}
```

#### `odoo_validate_invoice`
Validate draft invoice (post it).

```json
{
  "invoiceId": 1
}
```

### Customer Management

#### `odoo_list_customers`
List customers.

```json
{
  "limit": 50
}
```

#### `odoo_create_customer`
Create new customer.

```json
{
  "name": "Acme Corp",
  "email": "billing@acme.com",
  "phone": "+1234567890"  // optional
}
```

#### `odoo_customer_balance`
Get customer balance and history.

```json
{
  "customerId": 12
}
```

### Vendor Management

#### `odoo_list_vendors`
List vendors.

```json
{
  "limit": 50
}
```

### Reports

#### `odoo_account_summary`
Get accounting summary.

```json
{
  "dateFrom": "2026-01-01",  // optional
  "dateTo": "2026-04-05"     // optional
}
```

Returns:
- Total invoices
- Total revenue
- Total outstanding
- Total paid

## Starting the MCP Server

```bash
# Install dependencies
cd mcp-servers/odoo-mcp
npm install

# Start server
npm start

# Or with PM2
pm2 start mcp-servers/odoo-mcp/index.js --name odoo-mcp
```

## Configuration

Edit `mcp-servers/odoo-mcp/index.js`:

```javascript
const CONFIG = {
  ODOO_URL: 'http://localhost:8069',
  ODOO_DB: 'odoo_db',
  ODOO_EMAIL: 'admin@example.com',
  ODOO_PASSWORD: 'your_password',
};
```

## HITL Workflow

Accounting operations require approval:

```
1. AI drafts invoice → Creates /Pending_Approval/INVOICE_*.md
2. User reviews and moves to /Approved/
3. Orchestrator executes via MCP
4. Invoice posted in Odoo
```

**Approval Thresholds:**
- Invoices < $500: Auto-approve (optional)
- Invoices >= $500: Always require approval
- Payments: Always require approval

## Common Workflows

### Create Invoice for Client

1. AI receives payment request (email/message)
2. Creates customer in Odoo if new
3. Drafts invoice with line items
4. Creates approval request
5. User approves → Invoice posted

### Record Payment Received

1. AI detects bank transaction
2. Matches to outstanding invoice
3. Creates payment approval request
4. User approves → Payment recorded
5. Invoice marked as paid

### Weekly Accounting Review

1. CEO Briefing includes:
   - Revenue this week
   - Outstanding invoices
   - Recent payments
   - Customer balances
2. Proactive suggestions:
   - "3 invoices overdue, send reminders?"
   - "Customer X has $5000 outstanding balance"

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Connection refused | Check Odoo running: `docker compose ps` |
| Auth failed | Verify email/password in config |
| Customer not found | Check customer exists in Odoo |
| Invoice creation fails | Ensure Invoicing module installed |

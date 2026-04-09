/**
 * Odoo Accounting MCP Server - Gold Tier
 * 
 * Integrates with Odoo Community Edition via JSON-RPC API for:
 * - Creating and managing invoices
 * - Recording payments
 * - Account summaries
 * - Customer/Vendor management
 * 
 * SETUP REQUIRED:
 * 1. Start Odoo via Docker Compose (see odoo/docker-compose.yml)
 * 2. Create database and admin user
 * 3. Update configuration in this file (search for CONFIGURATION)
 * 
 * Odoo JSON-RPC API Docs: https://www.odoo.com/documentation/19.0/developer/reference/external_api.html
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');
const http = require('http');

// ============================================
// CONFIGURATION - UPDATE THESE VALUES
// ============================================

const CONFIG = {
  // Odoo Connection
  ODOO_URL: 'http://localhost:8069',  // Change if running elsewhere
  ODOO_DB: 'odoo_db',                  // Database name (created on first setup)
  ODOO_EMAIL: 'admin@example.com',    // Admin email
  ODOO_PASSWORD: 'admin',             // Admin password
  
  // JSON-RPC Settings
  JSON_RPC_TIMEOUT: 30000,  // 30 seconds
  MAX_RETRIES: 3,
};

// Authentication cache
let authCache = {
  uid: null,
  timestamp: 0,
  ttl: 300000,  // 5 minutes
};

// ============================================
// Odoo JSON-RPC Client
// ============================================

function jsonRpcCall(method, params) {
  return new Promise((resolve, reject) => {
    const url = new URL(CONFIG.ODOO_URL);
    const data = JSON.stringify({
      jsonrpc: '2.0',
      method: method,
      params: params,
      id: Math.floor(Math.random() * 1000000),
    });
    
    const options = {
      hostname: url.hostname,
      port: url.port || 80,
      path: url.pathname,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(data),
      },
      timeout: CONFIG.JSON_RPC_TIMEOUT,
    };
    
    const req = http.request(options, (res) => {
      let body = '';
      res.on('data', (chunk) => body += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(body);
          if (response.error) {
            reject(new Error(`Odoo JSON-RPC Error: ${response.error.message}`));
          } else {
            resolve(response.result);
          }
        } catch (e) {
          reject(new Error(`Failed to parse response: ${e.message}`));
        }
      });
    });
    
    req.on('error', reject);
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('Odoo JSON-RPC request timed out'));
    });
    
    req.write(data);
    req.end();
  });
}

async function authenticate() {
  // Check cache
  if (authCache.uid && Date.now() - authCache.timestamp < authCache.ttl) {
    return authCache.uid;
  }
  
  try {
    const uid = await jsonRpcCall('call', {
      service: 'common',
      method: 'login',
      args: [CONFIG.ODOO_DB, CONFIG.ODOO_EMAIL, CONFIG.ODOO_PASSWORD],
    });
    
    if (!uid) {
      throw new Error('Authentication failed - check credentials');
    }
    
    authCache = { uid, timestamp: Date.now(), ttl: 300000 };
    return uid;
  } catch (error) {
    console.error(`Odoo authentication failed: ${error.message}`);
    throw error;
  }
}

async function odooExecute(model, method, args = [], kwargs = {}) {
  const uid = await authenticate();
  
  return jsonRpcCall('call', {
    service: 'object',
    method: 'execute',
    args: [CONFIG.ODOO_DB, uid, CONFIG.ODOO_PASSWORD, model, method, ...args],
    kwargs: kwargs,
  });
}

async function odooExecuteKw(model, method, args = [], kwargs = {}) {
  const uid = await authenticate();
  
  return jsonRpcCall('call', {
    service: 'object',
    method: 'execute_kw',
    args: [CONFIG.ODOO_DB, uid, CONFIG.ODOO_PASSWORD, model, method, args],
    kwargs: kwargs,
  });
}

// ============================================
// Invoice Operations
// ============================================

async function createInvoice(customerId, items, dueDate = null, note = '') {
  // Calculate total
  const total = items.reduce((sum, item) => sum + (item.price * item.quantity), 0);
  
  // Prepare invoice lines
  const invoiceLines = items.map(item => [0, 0, {
    name: item.name,
    quantity: item.quantity,
    price_unit: item.price,
  }]));
  
  const invoiceData = {
    move_type: 'out_invoice',
    partner_id: customerId,
    invoice_line_ids: invoiceLines,
    invoice_date: new Date().toISOString().split('T')[0],
    ref: note || `INV-${Date.now()}`,
  };
  
  if (dueDate) {
    invoiceData.invoice_date_due = dueDate;
  }
  
  const invoiceId = await odooExecuteKw('account.move', 'create', [], {
    fields: invoiceData,
  });
  
  return {
    success: true,
    invoiceId,
    total,
    message: 'Invoice created',
  };
}

async function listInvoices(status = 'all', limit = 20) {
  const domain = status === 'all' ? [] : [['state', '=', status]];
  
  const invoices = await odooExecuteKw('account.move', 'search_read', [domain], {
    fields: ['name', 'partner_id', 'amount_total', 'amount_residual', 'state', 'invoice_date', 'invoice_date_due'],
    limit: limit,
    order: 'invoice_date desc',
  });
  
  // Format partner_id (it comes as [id, name])
  const formatted = invoices.map(inv => ({
    ...inv,
    customer: Array.isArray(inv.partner_id) ? inv.partner_id[1] : 'Unknown',
    partner_id: inv.partner_id,
  }));
  
  return {
    success: true,
    invoices: formatted,
    count: formatted.length,
    status,
  };
}

async function getInvoice(invoiceId) {
  const invoice = await odooExecuteKw('account.move', 'search_read', [['id', '=', invoiceId]], {
    fields: ['name', 'partner_id', 'amount_total', 'amount_residual', 'state', 'invoice_date', 'invoice_date_due', 'narration'],
    limit: 1,
  });
  
  if (!invoice || invoice.length === 0) {
    throw new Error(`Invoice ${invoiceId} not found`);
  }
  
  const inv = invoice[0];
  return {
    success: true,
    invoice: {
      ...inv,
      customer: Array.isArray(inv.partner_id) ? inv.partner_id[1] : 'Unknown',
    },
  };
}

async function recordPayment(invoiceId, amount, date = null, memo = '') {
  // Create payment
  const paymentData = {
    invoice_ids: [[6, 0, [invoiceId]]],
    amount: amount,
    date: date || new Date().toISOString().split('T')[0],
    payment_type: 'inbound',
    partner_type: 'customer',
    communication: memo || `Payment for invoice ${invoiceId}`,
  };
  
  const paymentId = await odooExecuteKw('account.payment', 'create', [], {
    fields: paymentData,
  });
  
  // Post the payment
  await odooExecuteKw('account.payment', 'action_post', [[paymentId]]);
  
  return {
    success: true,
    paymentId,
    amount,
    message: 'Payment recorded and posted',
  };
}

async function validateInvoice(invoiceId) {
  await odooExecuteKw('account.move', 'action_post', [[invoiceId]]);
  
  return {
    success: true,
    invoiceId,
    message: 'Invoice validated and posted',
  };
}

// ============================================
// Customer/Vendor Operations
// ============================================

async function listCustomers(limit = 50) {
  const customers = await odooExecuteKw('res.partner', 'search_read', [
    [['customer_rank', '>', 0]]
  ], {
    fields: ['name', 'email', 'phone', 'street', 'city', 'country_id', 'customer_rank'],
    limit: limit,
  });
  
  return {
    success: true,
    customers,
    count: customers.length,
  };
}

async function createCustomer(name, email, phone = '') {
  const customerId = await odooExecuteKw('res.partner', 'create', [], {
    fields: {
      name,
      email,
      phone,
      customer_rank: 1,
    },
  });
  
  return {
    success: true,
    customerId,
    message: 'Customer created',
  };
}

async function listVendors(limit = 50) {
  const vendors = await odooExecuteKw('res.partner', 'search_read', [
    [['supplier_rank', '>', 0]]
  ], {
    fields: ['name', 'email', 'phone', 'supplier_rank'],
    limit: limit,
  });
  
  return {
    success: true,
    vendors,
    count: vendors.length,
  };
}

// ============================================
// Accounting Reports
// ============================================

async function getAccountSummary(dateFrom = null, dateTo = null) {
  // Get invoices
  const invoices = await listInvoices('all', 100);
  
  // Calculate totals
  const totalRevenue = invoices.invoices
    .filter(inv => inv.state === 'posted')
    .reduce((sum, inv) => sum + (inv.amount_total || 0), 0);
  
  const totalOutstanding = invoices.invoices
    .filter(inv => inv.state === 'posted')
    .reduce((sum, inv) => sum + (inv.amount_residual || 0), 0);
  
  return {
    success: true,
    summary: {
      totalInvoices: invoices.count,
      totalRevenue,
      totalOutstanding,
      totalPaid: totalRevenue - totalOutstanding,
      period: {
        from: dateFrom || 'All time',
        to: dateTo || 'Now',
      },
      generatedAt: new Date().toISOString(),
    },
  };
}

async function getCustomerBalance(customerId) {
  const invoices = await odooExecuteKw('account.move', 'search_read', [
    [['partner_id', '=', customerId], ['move_type', '=', 'out_invoice']]
  ], {
    fields: ['name', 'amount_total', 'amount_residual', 'state', 'invoice_date'],
  });
  
  const totalOwed = invoices.reduce((sum, inv) => sum + (inv.amount_residual || 0), 0);
  
  return {
    success: true,
    customerId,
    totalOwed,
    invoices: invoices.length,
    details: invoices,
  };
}

// ============================================
// MCP Server Setup
// ============================================

const server = new Server(
  {
    name: 'odoo-accounting-mcp',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Define available tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: 'odoo_create_invoice',
        description: 'Create a new customer invoice. Requires customer ID and line items.',
        inputSchema: {
          type: 'object',
          properties: {
            customerId: { type: 'number', description: 'Odoo customer partner ID' },
            items: {
              type: 'array',
              description: 'Invoice line items',
              items: {
                type: 'object',
                properties: {
                  name: { type: 'string', description: 'Item description' },
                  quantity: { type: 'number', description: 'Quantity' },
                  price: { type: 'number', description: 'Unit price' },
                },
                required: ['name', 'quantity', 'price'],
              },
            },
            dueDate: { type: 'string', description: 'Due date (YYYY-MM-DD), optional' },
            note: { type: 'string', description: 'Reference note, optional' },
          },
          required: ['customerId', 'items'],
        },
      },
      {
        name: 'odoo_list_invoices',
        description: 'List invoices with optional status filter',
        inputSchema: {
          type: 'object',
          properties: {
            status: { type: 'string', description: 'Filter: draft, posted, paid, cancelled, all', default: 'all' },
            limit: { type: 'number', description: 'Max invoices to return', default: 20 },
          },
        },
      },
      {
        name: 'odoo_get_invoice',
        description: 'Get details of a specific invoice',
        inputSchema: {
          type: 'object',
          properties: {
            invoiceId: { type: 'number', description: 'Odoo invoice ID' },
          },
          required: ['invoiceId'],
        },
      },
      {
        name: 'odoo_record_payment',
        description: 'Record a payment against an invoice',
        inputSchema: {
          type: 'object',
          properties: {
            invoiceId: { type: 'number', description: 'Odoo invoice ID' },
            amount: { type: 'number', description: 'Payment amount' },
            date: { type: 'string', description: 'Payment date (YYYY-MM-DD), optional' },
            memo: { type: 'string', description: 'Payment memo, optional' },
          },
          required: ['invoiceId', 'amount'],
        },
      },
      {
        name: 'odoo_validate_invoice',
        description: 'Validate and post an invoice (moves from draft to posted)',
        inputSchema: {
          type: 'object',
          properties: {
            invoiceId: { type: 'number', description: 'Odoo invoice ID' },
          },
          required: ['invoiceId'],
        },
      },
      {
        name: 'odoo_list_customers',
        description: 'List customers from Odoo',
        inputSchema: {
          type: 'object',
          properties: {
            limit: { type: 'number', description: 'Max customers to return', default: 50 },
          },
        },
      },
      {
        name: 'odoo_create_customer',
        description: 'Create a new customer in Odoo',
        inputSchema: {
          type: 'object',
          properties: {
            name: { type: 'string', description: 'Customer name' },
            email: { type: 'string', description: 'Customer email' },
            phone: { type: 'string', description: 'Customer phone, optional' },
          },
          required: ['name', 'email'],
        },
      },
      {
        name: 'odoo_list_vendors',
        description: 'List vendors from Odoo',
        inputSchema: {
          type: 'object',
          properties: {
            limit: { type: 'number', description: 'Max vendors to return', default: 50 },
          },
        },
      },
      {
        name: 'odoo_account_summary',
        description: 'Get accounting summary with revenue, outstanding, etc.',
        inputSchema: {
          type: 'object',
          properties: {
            dateFrom: { type: 'string', description: 'Start date (YYYY-MM-DD), optional' },
            dateTo: { type: 'string', description: 'End date (YYYY-MM-DD), optional' },
          },
        },
      },
      {
        name: 'odoo_customer_balance',
        description: 'Get balance and invoice history for a customer',
        inputSchema: {
          type: 'object',
          properties: {
            customerId: { type: 'number', description: 'Odoo customer partner ID' },
          },
          required: ['customerId'],
        },
      },
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  
  try {
    let result;
    
    switch (name) {
      case 'odoo_create_invoice':
        result = await createInvoice(args.customerId, args.items, args.dueDate, args.note);
        break;
        
      case 'odoo_list_invoices':
        result = await listInvoices(args.status || 'all', args.limit || 20);
        break;
        
      case 'odoo_get_invoice':
        result = await getInvoice(args.invoiceId);
        break;
        
      case 'odoo_record_payment':
        result = await recordPayment(args.invoiceId, args.amount, args.date, args.memo);
        break;
        
      case 'odoo_validate_invoice':
        result = await validateInvoice(args.invoiceId);
        break;
        
      case 'odoo_list_customers':
        result = await listCustomers(args.limit || 50);
        break;
        
      case 'odoo_create_customer':
        result = await createCustomer(args.name, args.email, args.phone);
        break;
        
      case 'odoo_list_vendors':
        result = await listVendors(args.limit || 50);
        break;
        
      case 'odoo_account_summary':
        result = await getAccountSummary(args.dateFrom, args.dateTo);
        break;
        
      case 'odoo_customer_balance':
        result = await getCustomerBalance(args.customerId);
        break;
        
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
    
    return {
      content: [
        {
          type: 'text',
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  } catch (error) {
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${error.message}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('✅ Odoo Accounting MCP Server running on stdio');
  console.error(`   Odoo URL: ${CONFIG.ODOO_URL}`);
  console.error(`   Database: ${CONFIG.ODOO_DB}`);
}

main().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});

module.exports = { server, CONFIG };

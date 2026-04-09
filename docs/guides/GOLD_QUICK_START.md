# Quick Start Guide - Gold Tier Features

**Date:** 2026-04-05  
**Status:** Implementation Complete ✅

---

## 🚀 What You Have Now

Your AI Employee now has **Gold Tier** capabilities:

✅ **5 MCP Servers** (Email, LinkedIn, Facebook, Twitter, Odoo)  
✅ **5 Watchers** (Gmail, LinkedIn, File, Facebook, Twitter)  
✅ **Autonomous Loop** (Ralph Wiggum pattern)  
✅ **Error Recovery** (Retry + Circuit Breaker)  
✅ **CEO Briefing** (Weekly automated reports)  
✅ **Cross-Domain** (Personal + Business integration)  

---

## Part 1: Odoo Accounting

### Current Status
Docker is downloading Odoo images (~650MB). This takes 3-5 minutes on first run.

### Step-by-Step Setup

#### 1. Wait for Docker Pull to Complete

The command `docker compose up -d` is running. You can check progress:

```bash
# Check if containers are running
docker ps

# You should see:
# - odoo_ai_employee (Odoo)
# - odoo_postgres (Database)
```

#### 2. Access Odoo Web Interface

Once containers are running:

1. Open browser: **http://localhost:8069**
2. You'll see the database creation screen
3. Fill in:
   - **Email:** `admin@example.com`
   - **Password:** `admin` (change later!)
   - **Database Name:** `odoo_db`
   - **Phone:** Optional
   - **Language:** English
   - **Country:** Your country
   - ✅ Check "Load demonstration data"
4. Click **Create database**
5. Wait 2-3 minutes for initialization

#### 3. Install Invoicing Module

After login:

1. Go to **Apps** menu
2. Search: **"Invoicing"**
3. Click **Install** on "Invoicing" (Community Edition)
4. Wait for installation

#### 4. Create Test Customer

1. Go to **Customers → Customers**
2. Click **Create**
3. Fill in:
   - Name: `Test Customer`
   - Email: `test@example.com`
4. Click **Save**
5. Note the ID from URL (e.g., `id=12`)

#### 5. Configure MCP Server

Edit: `mcp-servers/odoo-mcp/index.js`

Find the CONFIG object (around line 16) and update:

```javascript
const CONFIG = {
  ODOO_URL: 'http://localhost:8069',
  ODOO_DB: 'odoo_db',           // Match your database name
  ODOO_EMAIL: 'admin@example.com',
  ODOO_PASSWORD: 'admin',       // Your password
};
```

#### 6. Install Dependencies & Start

```bash
cd C:\Projects\Personal-AI-Employe-FTEs\mcp-servers\odoo-mcp
npm install
npm start
```

You should see:
```
✅ Odoo Accounting MCP Server running on stdio
   Odoo URL: http://localhost:8069
   Database: odoo_db
```

#### 7. Test Odoo MCP

The MCP server provides these tools:
- Create invoices
- List invoices
- Record payments
- Manage customers
- Generate accounting summaries

---

## Part 2: Facebook & Instagram Integration

### What You Need

1. **Facebook Developer Account** (Free)
2. **Facebook Page** (Business page you own)
3. **Instagram Business Account** (Linked to Facebook Page)

### Step-by-Step Setup

#### 1. Create Facebook Developer Account

1. Go to: https://developers.facebook.com/
2. Click **Get Started**
3. Complete developer verification
4. Accept terms

#### 2. Create Facebook App

1. Go to: https://developers.facebook.com/apps/
2. Click **Create App**
3. Select **Business** type
4. Fill in:
   - App name: `AI Employee Social`
   - App contact email: Your email
5. Click **Create App**
6. Note your:
   - **App ID** (shown on dashboard)
   - **App Secret** (click Show to reveal)

#### 3. Add Required Permissions

In your app dashboard:

1. Go to **App Review → Permissions and Features**
2. Request these permissions:
   - ✅ `pages_manage_posts`
   - ✅ `pages_read_engagement`
   - ✅ `pages_manage_engagement`
   - ✅ `instagram_basic`
   - ✅ `instagram_content_publish`

#### 4. Generate Page Access Token

1. Go to: https://developers.facebook.com/tools/explorer/
2. Select your app
3. Click **Get Token → Get Page Access Token**
4. Select your Facebook Page
5. Grant all requested permissions
6. Copy the generated token
7. **This token expires in 60 days** (note this!)

#### 5. Find Your Facebook Page ID

1. Go to your Facebook Page
2. Click **About**
3. Scroll to **Page Info**
4. Find **Facebook Page ID**
5. Copy the number

#### 6. Find Your Instagram Business Account ID

1. Go to Graph API Explorer
2. Make this request:
   ```
   GET /me/accounts?fields=instagram_business_account
   ```
3. Copy the `instagram_business_account.id`

#### 7. Update Configuration

Edit: `mcp-servers/facebook-mcp/index.js`

Find CONFIG object (around line 25) and update:

```javascript
const CONFIG = {
  FACEBOOK_APP_ID: 'your_app_id_here',
  FACEBOOK_APP_SECRET: 'your_app_secret_here',
  FACEBOOK_PAGE_ACCESS_TOKEN: 'your_page_access_token_here',
  FACEBOOK_PAGE_ID: 'your_page_id_here',
  INSTAGRAM_BUSINESS_ACCOUNT_ID: 'your_ig_account_id_here',
};
```

Also update: `scripts/facebook_watcher.py`

```python
FACEBOOK_CONFIG = {
    'PAGE_ACCESS_TOKEN': 'your_page_access_token_here',
    'PAGE_ID': 'your_page_id_here',
    'INSTAGRAM_ACCOUNT_ID': 'your_ig_account_id_here',
}
```

#### 8. Install & Start

```bash
cd C:\Projects\Personal-AI-Employe-FTEs\mcp-servers\facebook-mcp
npm install
npm start
```

#### 9. Enable in MCP Config

Edit: `mcp-config.json`

Change:
```json
"facebook": {
  "disabled": false  // Change from true to false
}
```

---

## Part 3: Twitter/X Integration

### What You Need

1. **Twitter Developer Account** (Free tier available)
2. **Twitter Account** (Your personal/business account)

### Step-by-Step Setup

#### 1. Apply for Twitter Developer Account

1. Go to: https://developer.twitter.com/
2. Click **Sign Up for Free Account**
3. Fill in:
   - Account name
   - Email
   - Password
4. Verify email
5. **Wait for approval** (can take 1-7 days)

**Note:** Free tier has limitations:
- 1,500 tweets/month
- 10,000 tweets read/month
- This is enough for testing!

#### 2. Create Project & App

After approval:

1. Go to: https://developer.twitter.com/en/portal/dashboard
2. Click **Create Project**
   - Project name: `AI Employee`
   - Use case: `Making a bot`
3. Click **Create App** within project
   - App name: `AI Employee Twitter`

#### 3. Get API Credentials

In your app settings:

1. Go to **Keys and Tokens**
2. Generate and copy:
   - ✅ **API Key** (also called Consumer Key)
   - ✅ **API Key Secret** (Consumer Secret)
   - ✅ **Bearer Token**
   - ✅ **Access Token**
   - ✅ **Access Token Secret**

3. Set app permissions to **Read and Write**

#### 4. Update Configuration

Edit: `mcp-servers/twitter-mcp/index.js`

Find CONFIG object (around line 22) and update:

```javascript
const CONFIG = {
  TWITTER_API_KEY: 'your_api_key_here',
  TWITTER_API_SECRET: 'your_api_secret_here',
  TWITTER_BEARER_TOKEN: 'your_bearer_token_here',
  TWITTER_ACCESS_TOKEN: 'your_access_token_here',
  TWITTER_ACCESS_TOKEN_SECRET: 'your_access_token_secret_here',
};
```

Also update: `scripts/twitter_watcher.py`

```python
TWITTER_CONFIG = {
    'BEARER_TOKEN': 'your_bearer_token_here',
    'USERNAME': 'your_twitter_handle',  // Without @
};
```

#### 5. Install & Start

```bash
cd C:\Projects\Personal-AI-Employe-FTEs\mcp-servers\twitter-mcp
npm install
npm start
```

#### 6. Enable in MCP Config

Edit: `mcp-config.json`

Change:
```json
"twitter": {
  "disabled": false  // Change from true to false
}
```

---

## Part 4: Testing Everything

### Test Odoo MCP

```bash
# Start Odoo MCP
cd mcp-servers/odoo-mcp
npm start

# In another terminal, test with MCP client
python scripts/mcp-client.py list --stdio "node mcp-servers/odoo-mcp/index.js"
```

### Test Facebook MCP (after config)

```bash
cd mcp-servers/facebook-mcp
npm start

# Test
python scripts/mcp-client.py list --stdio "node mcp-servers/facebook-mcp/index.js"
```

### Test Twitter MCP (after config)

```bash
cd mcp-servers/twitter-mcp
npm start

# Test
python scripts/mcp-client.py list --stdio "node mcp-servers/twitter-mcp/index.js"
```

### Test CEO Briefing

```bash
python scripts/ceo_briefing.py --vault-path personal-ai-employee
```

This will generate a briefing file in:
`personal-ai-employee/Briefings/YYYY-MM-DD_Monday_Briefing.md`

### Test Ralph Wiggum Loop

```bash
python scripts/ralph_wiggum.py --prompt "Test processing cycle" --max-iterations 3
```

---

## Part 5: Priority Order (What to Do First)

### Recommended Order:

1. **✅ Odoo** (Docker is already pulling)
   - Takes 10-15 minutes total
   - No external approval needed
   - Immediate value for accounting

2. **⏳ Facebook/Instagram** (Takes 30-60 minutes)
   - Requires Facebook Developer account (instant approval)
   - Generate tokens (10 minutes)
   - Configure and test (20 minutes)

3. **⏳ Twitter/X** (Takes 1-7 days)
   - **Requires developer account approval**
   - Can take days to get approved
   - Do this last, work on other things while waiting

### What You Can Do Right Now:

While Odoo is downloading, you can:
1. Review the compliance report: `docs/setup/GOLD_TIER_COMPLIANCE.md`
2. Review architecture: `docs/architecture/GOLD_ARCHITECTURE.md`
3. Start Facebook Developer account setup
4. Apply for Twitter Developer account (do this ASAP!)

---

## 📋 Quick Reference Commands

### Odoo Management

```bash
# Check status
docker ps

# View logs
docker compose -f odoo/docker-compose.yml logs -f odoo

# Stop
docker compose -f odoo/docker-compose.yml down

# Restart
docker compose -f odoo/docker-compose.yml restart

# Reset (WARNING: Deletes all data!)
docker compose -f odoo/docker-compose.yml down -v
docker compose -f odoo/docker-compose.yml up -d
```

### MCP Servers

```bash
# Start all MCP servers with PM2
pm2 start mcp-servers/email-mcp/index.js --name email-mcp
pm2 start mcp-servers/linkedin-mcp/index.js --name linkedin-mcp
pm2 start mcp-servers/odoo-mcp/index.js --name odoo-mcp
pm2 start mcp-servers/facebook-mcp/index.js --name facebook-mcp  (after config)
pm2 start mcp-servers/twitter-mcp/index.js --name twitter-mcp    (after config)

# View all
pm2 status

# View logs
pm2 logs odoo-mcp
```

### Watchers

```bash
# Start all watchers
scripts\start-all.bat

# Or with PM2
pm2 start scripts/gmail_watcher.py --interpreter python --name gmail-watcher
pm2 start scripts/facebook_watcher.py --interpreter python --name facebook-watcher  (after config)
pm2 start scripts/twitter_watcher.py --interpreter python --name twitter-watcher    (after config)
```

---

## 🎯 Success Checklist

- [ ] Odoo running at http://localhost:8069
- [ ] Odoo MCP server tested and working
- [ ] Facebook Page Access Token generated
- [ ] Facebook MCP server configured and tested
- [ ] Twitter Developer account approved
- [ ] Twitter MCP server configured and tested
- [ ] CEO Briefing generated successfully
- [ ] All 5 MCP servers enabled in `mcp-config.json`
- [ ] Dashboard updated with Gold Tier metrics

---

## 📞 Need Help?

### Troubleshooting

**Odoo won't start:**
```bash
docker compose -f odoo/docker-compose.yml logs odoo
```

**MCP server won't connect:**
- Check credentials are correct
- Verify service is running
- Check logs: `pm2 logs <server-name>`

**Facebook token expired:**
- Regenerate from Graph API Explorer
- Update config files
- Restart MCP server

**Twitter API errors:**
- Check app permissions (must be Read + Write)
- Verify all 5 credentials are correct
- Check rate limits on developer portal

---

*Last Updated: 2026-04-05*  
*Gold Tier v1.0*

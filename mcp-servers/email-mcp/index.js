/**
 * Email MCP Server for AI Employee - Silver Tier
 * 
 * Provides Gmail operations: Send, Draft, Search emails
 * Uses Google Gmail API with OAuth2 credentials
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { google } from 'googleapis';
import { readFileSync, writeFileSync, existsSync } from 'fs';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Configuration
const CREDENTIALS_PATH = process.env.GMAIL_CREDENTIALS_PATH || join(__dirname, '../../credentials.json');
const TOKEN_PATH = process.env.GMAIL_TOKEN_PATH || join(__dirname, '../../token.pickle');
const SCOPES = ['https://www.googleapis.com/auth/gmail.send', 'https://www.googleapis.com/auth/gmail.compose'];

let oauth2Client;
let gmail;

/**
 * Initialize Gmail API client
 */
async function initializeGmail() {
  try {
    const credentials = JSON.parse(readFileSync(CREDENTIALS_PATH, 'utf-8'));
    
    oauth2Client = new google.auth.OAuth2(
      credentials.client_id,
      credentials.client_secret,
      credentials.redirect_uris[0]
    );

    // Load existing token
    if (existsSync(TOKEN_PATH)) {
      const token = JSON.parse(readFileSync(TOKEN_PATH, 'utf-8'));
      oauth2Client.setCredentials(token);
    } else {
      console.error('No token found. Please authenticate first using the auth script.');
      process.exit(1);
    }

    gmail = google.gmail({ version: 'v1', auth: oauth2Client });
    console.error('Gmail initialized successfully');
  } catch (error) {
    console.error('Error initializing Gmail:', error.message);
    process.exit(1);
  }
}

/**
 * Save token for future use
 */
function saveToken(token) {
  writeFileSync(TOKEN_PATH, JSON.stringify(token));
  console.error('Token saved successfully');
}

// Tool schemas
const SendEmailSchema = z.object({
  to: z.string().describe('Recipient email address'),
  subject: z.string().describe('Email subject'),
  body: z.string().describe('Email body (plain text)'),
  html: z.string().optional().describe('Email body (HTML, optional)'),
  cc: z.string().optional().describe('CC recipients (comma-separated)'),
  bcc: z.string().optional().describe('BCC recipients (comma-separated)'),
});

const CreateDraftSchema = z.object({
  to: z.string().describe('Recipient email address'),
  subject: z.string().describe('Email subject'),
  body: z.string().describe('Email body (plain text)'),
  html: z.string().optional().describe('Email body (HTML, optional)'),
  cc: z.string().optional().describe('CC recipients (comma-separated)'),
});

const SearchEmailsSchema = z.object({
  query: z.string().describe('Gmail search query (e.g., "from:example@gmail.com", "subject:meeting")'),
  maxResults: z.number().default(10).describe('Maximum number of results (default: 10)'),
});

const GetEmailSchema = z.object({
  messageId: z.string().describe('Gmail message ID'),
});

// Tool implementations
async function sendEmail(params) {
  try {
    const { to, subject, body, html, cc, bcc } = SendEmailSchema.parse(params);
    
    // Create email message
    const message = [
      `To: ${to}`,
      cc ? `Cc: ${cc}` : '',
      bcc ? `Bcc: ${bcc}` : '',
      `Subject: ${subject}`,
      'MIME-Version: 1.0',
      'Content-Type: text/html; charset=utf-8',
      '',
      html || body.replace(/\n/g, '<br>'),
    ].join('\n');

    // Encode the message
    const encodedMessage = Buffer.from(message)
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');

    // Send the email
    const response = await gmail.users.messages.send({
      userId: 'me',
      requestBody: {
        raw: encodedMessage,
      },
    });

    return {
      success: true,
      messageId: response.data.id,
      threadId: response.data.threadId,
      status: 'sent',
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

async function createDraft(params) {
  try {
    const { to, subject, body, html, cc } = CreateDraftSchema.parse(params);
    
    // Create draft message
    const message = [
      `To: ${to}`,
      cc ? `Cc: ${cc}` : '',
      `Subject: ${subject}`,
      'MIME-Version: 1.0',
      'Content-Type: text/html; charset=utf-8',
      '',
      html || body.replace(/\n/g, '<br>'),
    ].join('\n');

    // Encode the message
    const encodedMessage = Buffer.from(message)
      .toString('base64')
      .replace(/\+/g, '-')
      .replace(/\//g, '_')
      .replace(/=+$/, '');

    // Create draft
    const response = await gmail.users.drafts.create({
      userId: 'me',
      requestBody: {
        message: {
          raw: encodedMessage,
        },
      },
    });

    return {
      success: true,
      draftId: response.data.id,
      messageId: response.data.message.id,
      status: 'draft_created',
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

async function searchEmails(params) {
  try {
    const { query, maxResults } = SearchEmailsSchema.parse(params);
    
    const response = await gmail.users.messages.list({
      userId: 'me',
      q: query,
      maxResults: Math.min(maxResults, 100),
    });

    const messages = response.data.messages || [];
    
    // Get full details for each message
    const detailedMessages = await Promise.all(
      messages.slice(0, maxResults).map(async (msg) => {
        const full = await gmail.users.messages.get({
          userId: 'me',
          id: msg.id,
          format: 'metadata',
          metadataHeaders: ['From', 'To', 'Subject', 'Date'],
        });
        
        const headers = full.data.payload?.headers || [];
        return {
          id: msg.id,
          threadId: msg.threadId,
          from: headers.find(h => h.name === 'From')?.value || '',
          to: headers.find(h => h.name === 'To')?.value || '',
          subject: headers.find(h => h.name === 'Subject')?.value || '',
          date: headers.find(h => h.name === 'Date')?.value || '',
          snippet: full.data.snippet || '',
        };
      })
    );

    return {
      success: true,
      count: detailedMessages.length,
      messages: detailedMessages,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

async function getEmail(params) {
  try {
    const { messageId } = GetEmailSchema.parse(params);
    
    const response = await gmail.users.messages.get({
      userId: 'me',
      id: messageId,
      format: 'full',
    });

    const headers = response.data.payload?.headers || [];
    const body = get_email_body(response.data);

    return {
      success: true,
      message: {
        id: response.data.id,
        threadId: response.data.threadId,
        from: headers.find(h => h.name === 'From')?.value || '',
        to: headers.find(h => h.name === 'To')?.value || '',
        subject: headers.find(h => h.name === 'Subject')?.value || '',
        date: headers.find(h => h.name === 'Date')?.value || '',
        body: body,
        snippet: response.data.snippet || '',
      },
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

function get_email_body(message) {
  try {
    if (message.payload?.parts) {
      for (const part of message.payload.parts) {
        if (part.mimeType === 'text/plain' && part.body?.data) {
          return Buffer.from(part.body.data, 'base64').toString('utf-8');
        }
      }
    } else if (message.payload?.body?.data) {
      return Buffer.from(message.payload.body.data, 'base64').toString('utf-8');
    }
    return '';
  } catch (error) {
    console.error('Error extracting email body:', error);
    return '';
  }
}

// Main server setup
async function main() {
  await initializeGmail();

  const server = new Server(
    {
      name: 'email-mcp',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // List available tools
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: [
        {
          name: 'send_email',
          description: 'Send an email via Gmail. Use for sending replies, notifications, and communications.',
          inputSchema: {
            type: 'object',
            properties: {
              to: { type: 'string', description: 'Recipient email address' },
              subject: { type: 'string', description: 'Email subject' },
              body: { type: 'string', description: 'Email body (plain text)' },
              html: { type: 'string', description: 'Email body (HTML, optional)' },
              cc: { type: 'string', description: 'CC recipients (comma-separated)' },
              bcc: { type: 'string', description: 'BCC recipients (comma-separated)' },
            },
            required: ['to', 'subject', 'body'],
          },
        },
        {
          name: 'create_draft',
          description: 'Create a draft email for review before sending. Safer for important communications.',
          inputSchema: {
            type: 'object',
            properties: {
              to: { type: 'string', description: 'Recipient email address' },
              subject: { type: 'string', description: 'Email subject' },
              body: { type: 'string', description: 'Email body (plain text)' },
              html: { type: 'string', description: 'Email body (HTML, optional)' },
              cc: { type: 'string', description: 'CC recipients (comma-separated)' },
            },
            required: ['to', 'subject', 'body'],
          },
        },
        {
          name: 'search_emails',
          description: 'Search Gmail for emails matching a query.',
          inputSchema: {
            type: 'object',
            properties: {
              query: { type: 'string', description: 'Gmail search query' },
              maxResults: { type: 'number', description: 'Maximum results (default: 10)' },
            },
            required: ['query'],
          },
        },
        {
          name: 'get_email',
          description: 'Get full details of a specific email by message ID.',
          inputSchema: {
            type: 'object',
            properties: {
              messageId: { type: 'string', description: 'Gmail message ID' },
            },
            required: ['messageId'],
          },
        },
      ],
    };
  });

  // Handle tool calls
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    try {
      switch (name) {
        case 'send_email':
          return { content: [{ type: 'text', text: JSON.stringify(await sendEmail(args), null, 2) }] };
        case 'create_draft':
          return { content: [{ type: 'text', text: JSON.stringify(await createDraft(args), null, 2) }] };
        case 'search_emails':
          return { content: [{ type: 'text', text: JSON.stringify(await searchEmails(args), null, 2) }] };
        case 'get_email':
          return { content: [{ type: 'text', text: JSON.stringify(await getEmail(args), null, 2) }] };
        default:
          throw new Error(`Unknown tool: ${name}`);
      }
    } catch (error) {
      return {
        content: [{ type: 'text', text: JSON.stringify({ success: false, error: error.message }, null, 2) }],
        isError: true,
      };
    }
  });

  // Start server
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Email MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});

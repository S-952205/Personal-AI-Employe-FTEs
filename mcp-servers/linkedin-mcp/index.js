/**
 * LinkedIn MCP Server for AI Employee - Silver Tier
 * 
 * Provides LinkedIn operations: Post, Comment, Connect, Message
 * Uses Playwright for browser automation with persistent session
 * 
 * Note: Use responsibly and be aware of LinkedIn's Terms of Service
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';
import { chromium } from 'playwright';
import { existsSync, mkdirSync } from 'fs';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));

// Configuration
const SESSION_PATH = process.env.LINKEDIN_SESSION_PATH || join(__dirname, '../../linkedin_session');
const HEADLESS = process.env.HEADLESS === 'true' || false;

let browser;
let context;
let page;

/**
 * Initialize browser and LinkedIn session
 */
async function initializeLinkedIn() {
  try {
    // Ensure session directory exists
    if (!existsSync(SESSION_PATH)) {
      mkdirSync(SESSION_PATH, { recursive: true });
    }

    // Launch browser with persistent context
    context = await chromium.launchPersistentContext(SESSION_PATH, {
      headless: HEADLESS,
      viewport: { width: 1280, height: 720 },
      user_agent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    });

    page = context.pages[0] || await context.newPage();
    console.error('LinkedIn browser context initialized');
  } catch (error) {
    console.error('Error initializing LinkedIn:', error.message);
    process.exit(1);
  }
}

/**
 * Ensure logged in to LinkedIn
 */
async function ensureLoggedIn() {
  try {
    await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'networkidle', timeout: 60000 });
    await page.waitForTimeout(3000);
    
    // Check if we're on login page
    if (page.url().includes('login')) {
      return {
        success: false,
        error: 'Not logged in. Please log in to LinkedIn manually in the browser session.',
      };
    }
    
    return { success: true };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

// Tool schemas
const CreatePostSchema = z.object({
  content: z.string().describe('Post content (text)'),
  imageUrl: z.string().optional().describe('Image URL (optional)'),
  hashtags: z.array(z.string()).optional().describe('Hashtags to include'),
});

const CommentOnPostSchema = z.object({
  postUrl: z.string().describe('URL of the post to comment on'),
  comment: z.string().describe('Comment text'),
});

const ConnectWithPersonSchema = z.object({
  profileUrl: z.string().describe('LinkedIn profile URL'),
  message: z.string().optional().describe('Connection request message (optional)'),
});

const SendMessageSchema = z.object({
  recipientName: z.string().describe('Name of the recipient'),
  message: z.string().describe('Message to send'),
});

const GetNotificationsSchema = z.object({
  maxResults: z.number().default(10).describe('Maximum number of notifications to retrieve'),
});

// Tool implementations
async function createPost(params) {
  try {
    const loginCheck = await ensureLoggedIn();
    if (!loginCheck.success) return loginCheck;

    const { content, imageUrl, hashtags } = CreatePostSchema.parse(params);

    // Format content with hashtags
    let fullContent = content;
    if (hashtags && hashtags.length > 0) {
      fullContent += '\n\n' + hashtags.map(tag => {
        return tag.startsWith('#') ? tag : `#${tag}`;
      }).join(' ');
    }

    // Navigate to feed
    await page.goto('https://www.linkedin.com/feed/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Click on "Start a post"
    const startPostBtn = page.locator('button:has-text("Start a post")').first();
    await startPostBtn.click();
    await page.waitForTimeout(2000);

    // Wait for dialog to open
    await page.waitForSelector('[role="dialog"]', { timeout: 10000 });
    await page.waitForTimeout(1000);

    // Find and fill the text area
    const textBox = page.locator('div[contenteditable="true"][role="textbox"]').first();
    await textBox.fill(fullContent);
    await page.waitForTimeout(2000);

    // Click Post button
    const postBtn = page.locator('button:has-text("Post")').last();
    await postBtn.click();
    await page.waitForTimeout(2000);

    // Handle audience dialog if it appears
    try {
      const audienceDialog = page.locator('[role="dialog"]').filter({ hasText: 'Anyone' }).first();
      if (await audienceDialog.isVisible({ timeout: 3000 })) {
        console.error('Audience dialog detected');
        
        let handled = false;
        
        // STRATEGY 1: Click Anyone → Wait → Click Done
        try {
          console.error('  Strategy 1: Click Anyone button...');
          const anyoneBtn = page.locator('button:has-text("Anyone")').first();
          if (await anyoneBtn.isVisible({ timeout: 2000 })) {
            await anyoneBtn.click();
            console.error('    Clicked Anyone, waiting for Done...');
            await page.waitForTimeout(5000);
            
            const doneBtn = page.locator('button:has-text("Done")').first();
            for (let i = 0; i < 15; i++) {
              try {
                if (!await doneBtn.isDisabled()) {
                  await doneBtn.click();
                  console.error('    ✓ Clicked Done');
                  await page.waitForTimeout(2000);
                  handled = true;
                  break;
                }
              } catch (e) {}
              console.error(`    Waiting for Done... (${i+1}/15s)`);
              await page.waitForTimeout(1000);
            }
          }
        } catch (e) {
          console.error('  Strategy 1 failed:', e.message);
        }
        
        // STRATEGY 2: Click dropdown option
        if (!handled) {
          try {
            console.error('  Strategy 2: Click dropdown option...');
            const option = page.locator('button[role="option"]:has-text("Anyone")').first();
            if (await option.isVisible({ timeout: 2000 })) {
              await option.click();
              await page.waitForTimeout(3000);
              
              const doneBtn = page.locator('button:has-text("Done")').first();
              if (await doneBtn.isVisible({ timeout: 2000 })) {
                for (let i = 0; i < 10; i++) {
                  try {
                    if (!await doneBtn.isDisabled()) {
                      await doneBtn.click();
                      console.error('    ✓ Clicked Done');
                      handled = true;
                      break;
                    }
                  } catch (e) {}
                  await page.waitForTimeout(1000);
                }
              }
            }
          } catch (e) {
            console.error('  Strategy 2 failed:', e.message);
          }
        }
        
        // STRATEGY 3: Click any enabled button
        if (!handled) {
          try {
            console.error('  Strategy 3: Find any enabled button...');
            const buttons = await page.locator('[role="dialog"] button').all();
            for (const btn of buttons) {
              try {
                const text = await btn.innerText();
                if (!await btn.isDisabled() && ['Done', 'Save', 'Anyone'].includes(text.trim())) {
                  await btn.click();
                  console.error(`    ✓ Clicked: ${text}`);
                  if (['Done', 'Save'].includes(text.trim())) {
                    handled = true;
                    break;
                  }
                }
              } catch (e) {}
            }
          } catch (e) {
            console.error('  Strategy 3 failed:', e.message);
          }
        }
        
        // STRATEGY 4: Click outside to close
        if (!handled) {
          try {
            console.error('  Strategy 4: Click outside dialog...');
            await page.mouse.click(100, 100);
            await page.waitForTimeout(2000);
            console.error('    ✓ Clicked outside, continuing...');
            handled = true;
          } catch (e) {
            console.error('  Strategy 4 failed, continuing anyway...');
            handled = true; // Assume OK
          }
        }
        
        if (handled) {
          console.error('✓ Audience handled');
          
          // Click Post again after audience selection
          const finalPostBtn = page.locator('button:has-text("Post")').first();
          if (await finalPostBtn.isVisible({ timeout: 2000 }) && !await finalPostBtn.isDisabled()) {
            await finalPostBtn.click();
            console.error('✓ Post submitted after audience selection');
          }
        }
      }
    } catch (e) {
      console.error('No audience dialog or handled automatically');
    }

    // Wait for post to submit and page to navigate
    try {
      await page.waitForLoadState('networkidle', { timeout: 30000 });
      await page.waitForTimeout(3000);
      console.error('Post submission complete');
    } catch (e) {
      console.error('Navigation wait:', e.message);
      await page.waitForTimeout(10000);
    }

    return {
      success: true,
      status: 'post_created',
      content: fullContent,
      message: 'Post created successfully',
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

async function commentOnPost(params) {
  try {
    const loginCheck = await ensureLoggedIn();
    if (!loginCheck.success) return loginCheck;

    const { postUrl, comment } = CommentOnPostSchema.parse(params);
    
    // Navigate to post
    await page.goto(postUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Find comment box and type
    const commentBox = page.locator('div[contenteditable="true"][placeholder*="Add a comment"]').first();
    await commentBox.fill(comment);
    await page.waitForTimeout(500);

    // Click post button
    const postBtn = page.locator('button:has-text("Comment")').first();
    await postBtn.click();
    await page.waitForTimeout(1000);

    return {
      success: true,
      status: 'comment_posted',
      message: 'Comment posted successfully',
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

async function connectWithPerson(params) {
  try {
    const loginCheck = await ensureLoggedIn();
    if (!loginCheck.success) return loginCheck;

    const { profileUrl, message } = ConnectWithPersonSchema.parse(params);
    
    // Navigate to profile
    await page.goto(profileUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Click "Connect" button
    const connectBtn = page.locator('button:has-text("Connect")').first();
    
    if (!await connectBtn.isVisible()) {
      return {
        success: false,
        error: 'Connect button not found. Person may already be connected or profile unavailable.',
      };
    }

    await connectBtn.click();
    await page.waitForTimeout(1000);

    // If message option appears, add message
    if (message) {
      const addNoteBtn = page.locator('button:has-text("Add a note")');
      if (await addNoteBtn.isVisible()) {
        await addNoteBtn.click();
        await page.waitForTimeout(500);

        const messageBox = page.locator('textarea[aria-label*="message"]').first();
        await messageBox.fill(message);
        await page.waitForTimeout(500);

        const sendBtn = page.locator('button:has-text("Send")');
        await sendBtn.click();
      }
    }

    await page.waitForTimeout(1000);

    return {
      success: true,
      status: 'connection_request_sent',
      message: message ? 'Connection request sent with message' : 'Connection request sent',
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

async function sendMessage(params) {
  try {
    const loginCheck = await ensureLoggedIn();
    if (!loginCheck.success) return loginCheck;

    const { recipientName, message } = SendMessageSchema.parse(params);
    
    // Navigate to messaging
    await page.goto('https://www.linkedin.com/messaging/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(2000);

    // Click "New message"
    const newMessageBtn = page.locator('button:has-text("New message")').first();
    await newMessageBtn.click();
    await page.waitForTimeout(1000);

    // Search for recipient
    const searchBox = page.locator('input[placeholder*="To:"]').first();
    await searchBox.fill(recipientName);
    await page.waitForTimeout(1500);

    // Select first result
    const firstResult = page.locator('div[role="option"]').first();
    if (await firstResult.isVisible()) {
      await firstResult.click();
      await page.waitForTimeout(500);

      // Type message
      const messageBox = page.locator('div[contenteditable="true"][role="textbox"]').first();
      await messageBox.fill(message);
      await page.waitForTimeout(500);

      // Send
      const sendBtn = page.locator('button[aria-label*="Send"]').first();
      await sendBtn.click();
      await page.waitForTimeout(1000);

      return {
        success: true,
        status: 'message_sent',
        recipient: recipientName,
      };
    } else {
      return {
        success: false,
        error: `Could not find recipient: ${recipientName}`,
      };
    }
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

async function getNotifications(params) {
  try {
    const loginCheck = await ensureLoggedIn();
    if (!loginCheck.success) return loginCheck;

    const { maxResults } = GetNotificationsSchema.parse(params);
    
    // Navigate to notifications
    await page.goto('https://www.linkedin.com/notifications/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(3000);

    // Get notification items
    const notifications = [];
    const items = await page.locator('ul.mn-notification-list > li').all();

    for (let i = 0; i < Math.min(items.length, maxResults); i++) {
      try {
        const text = await items[i].innerText();
        notifications.push({
          index: i,
          content: text.trim(),
        });
      } catch (e) {
        continue;
      }
    }

    return {
      success: true,
      count: notifications.length,
      notifications: notifications,
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
    };
  }
}

// Main server setup
async function main() {
  await initializeLinkedIn();

  const server = new Server(
    {
      name: 'linkedin-mcp',
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
          name: 'create_post',
          description: 'Create a LinkedIn post. Use for sharing updates, articles, and business content.',
          inputSchema: {
            type: 'object',
            properties: {
              content: { type: 'string', description: 'Post content (text)' },
              imageUrl: { type: 'string', description: 'Image URL (optional)' },
              hashtags: { type: 'array', items: { type: 'string' }, description: 'Hashtags to include' },
            },
            required: ['content'],
          },
        },
        {
          name: 'comment_on_post',
          description: 'Comment on a LinkedIn post by URL.',
          inputSchema: {
            type: 'object',
            properties: {
              postUrl: { type: 'string', description: 'URL of the post to comment on' },
              comment: { type: 'string', description: 'Comment text' },
            },
            required: ['postUrl', 'comment'],
          },
        },
        {
          name: 'connect_with_person',
          description: 'Send a connection request to someone on LinkedIn.',
          inputSchema: {
            type: 'object',
            properties: {
              profileUrl: { type: 'string', description: 'LinkedIn profile URL' },
              message: { type: 'string', description: 'Connection request message (optional)' },
            },
            required: ['profileUrl'],
          },
        },
        {
          name: 'send_message',
          description: 'Send a direct message to a LinkedIn connection.',
          inputSchema: {
            type: 'object',
            properties: {
              recipientName: { type: 'string', description: 'Name of the recipient' },
              message: { type: 'string', description: 'Message to send' },
            },
            required: ['recipientName', 'message'],
          },
        },
        {
          name: 'get_notifications',
          description: 'Get recent LinkedIn notifications.',
          inputSchema: {
            type: 'object',
            properties: {
              maxResults: { type: 'number', description: 'Maximum notifications to retrieve (default: 10)' },
            },
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
        case 'create_post':
          return { content: [{ type: 'text', text: JSON.stringify(await createPost(args), null, 2) }] };
        case 'comment_on_post':
          return { content: [{ type: 'text', text: JSON.stringify(await commentOnPost(args), null, 2) }] };
        case 'connect_with_person':
          return { content: [{ type: 'text', text: JSON.stringify(await connectWithPerson(args), null, 2) }] };
        case 'send_message':
          return { content: [{ type: 'text', text: JSON.stringify(await sendMessage(args), null, 2) }] };
        case 'get_notifications':
          return { content: [{ type: 'text', text: JSON.stringify(await getNotifications(args), null, 2) }] };
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
  console.error('LinkedIn MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Fatal error:', error);
  process.exit(1);
});

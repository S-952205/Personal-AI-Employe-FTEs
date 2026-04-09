/**
 * Facebook/Instagram MCP Server - Gold Tier
 * 
 * Integrates with Facebook Graph API for:
 * - Posting to Facebook Pages
 * - Posting to Instagram Business accounts
 * - Reading Page insights/analytics
 * - Managing comments and messages
 * 
 * SETUP REQUIRED:
 * 1. Create Facebook Developer Account: https://developers.facebook.com/
 * 2. Create an App and get App ID + App Secret
 * 3. Add "pages_manage_posts" and "pages_read_engagement" permissions
 * 4. For Instagram: Link Instagram Business account to Facebook Page
 * 5. Generate Page Access Token with required permissions
 * 6. Update configuration in this file (search for CONFIGURATION)
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');

// ============================================
// CONFIGURATION - UPDATE THESE VALUES
// ============================================

const CONFIG = {
  // Facebook App Credentials
  FACEBOOK_APP_ID: '961516409616918',           // Replace with your App ID
  FACEBOOK_APP_SECRET: 'fd281bbe539d1db1adb240691cea4181',   // Replace with your App Secret
  
  // Page Access Token (generate from Facebook Graph API Explorer)
  FACEBOOK_PAGE_ACCESS_TOKEN: 'EAANqfnwKehYBRFbUDU1oyt2BQj51rruK2myvduLNoVDJXPHmdTAZChy7Oca8zOcrChpW2jsh4CYVLLMZBHq4AopJEeoTwB0hqif981yOkNvLHBopIrwj08h8uZAzReWirkVrPG5r9PlhcyG4aqgXRe2ScF4zIY7aAlWBbPDKZBiHA7DikqySR0l3FwvK7qZAfkeKJ3dIp0lrhxKzxX4abfNHnrJkcEsLV9bt6kONY',  // Replace with your token
  
  // Facebook Page ID (find in Page settings)
  FACEBOOK_PAGE_ID: '1045279958668364',         // Replace with your Page ID
  
  // Instagram Business Account ID (linked to Facebook Page)
  INSTAGRAM_BUSINESS_ACCOUNT_ID: 'DUMMY',  // Replace with your IG account ID
  
  // Base URLs
  GRAPH_API_BASE: 'https://graph.facebook.com/v19.0',
  
  // Rate limiting
  MAX_POSTS_PER_DAY: 10,
  POST_COOLDOWN_SECONDS: 300,  // 5 minutes between posts
};

// Validate configuration
function validateConfig() {
  const requiredFields = [
    'FACEBOOK_APP_ID',
    'FACEBOOK_APP_SECRET',
    'FACEBOOK_PAGE_ACCESS_TOKEN',
    'FACEBOOK_PAGE_ID',
    'INSTAGRAM_BUSINESS_ACCOUNT_ID'
  ];
  
  const missing = requiredFields.filter(field => 
    CONFIG[field].startsWith('YOUR_') || CONFIG[field] === ''
  );
  
  if (missing.length > 0) {
    console.error('❌ Missing Facebook/Instagram configuration:');
    missing.forEach(field => console.error(`   - ${field}`));
    console.error('\n📖 Setup Guide:');
    console.error('   1. Go to https://developers.facebook.com/');
    console.error('   2. Create an app and get credentials');
    console.error('   3. Update CONFIG object in this file');
    process.exit(1);
  }
}

// ============================================
// HTTP Client Helper
// ============================================

async function graphApiRequest(endpoint, method = 'GET', params = {}) {
  const url = `${CONFIG.GRAPH_API_BASE}${endpoint}`;
  const queryParams = new URLSearchParams({
    access_token: CONFIG.FACEBOOK_PAGE_ACCESS_TOKEN,
    ...params
  });
  
  const fullUrl = method === 'GET' ? `${url}?${queryParams}` : url;
  
  const options = {
    method,
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  if (method !== 'GET') {
    options.body = JSON.stringify(params);
  }
  
  try {
    const response = await fetch(fullUrl, options);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(`Graph API Error: ${data.error?.message || response.statusText}`);
    }
    
    return data;
  } catch (error) {
    console.error(`Graph API request failed: ${error.message}`);
    throw error;
  }
}

// ============================================
// Facebook Operations
// ============================================

async function postToFacebook(message, imageUrl = null, link = null, scheduledTime = null) {
  const endpoint = `/${CONFIG.FACEBOOK_PAGE_ID}/feed`;
  
  const params = {
    message,
    published: scheduledTime ? false : true,
  };
  
  if (imageUrl) {
    params.url = imageUrl;
  }
  
  if (link) {
    params.link = link;
  }
  
  if (scheduledTime) {
    params.scheduled_publish_time = Math.floor(new Date(scheduledTime).getTime() / 1000);
  }
  
  const result = await graphApiRequest(endpoint, 'POST', params);
  
  return {
    success: true,
    postId: result.id,
    message: scheduledTime ? 'Post scheduled' : 'Post published',
    scheduled: !!scheduledTime,
  };
}

async function getPageInsights(dateRange = 'last_7_days') {
  const metrics = 'page_posts,page_engaged_users,page_impressions,page_reach';
  
  let datePreset = dateRange;
  
  const endpoint = `/${CONFIG.FACEBOOK_PAGE_ID}/insights`;
  const result = await graphApiRequest(endpoint, 'GET', {
    metric: metrics,
    date_preset: datePreset,
  });
  
  return {
    success: true,
    insights: result.data || [],
    dateRange,
  };
}

async function getRecentPosts(limit = 10) {
  const endpoint = `/${CONFIG.FACEBOOK_PAGE_ID}/posts`;
  const result = await graphApiRequest(endpoint, 'GET', {
    limit: limit.toString(),
    fields: 'id,message,created_time,shares,likes.summary(true),comments.summary(true)',
  });
  
  return {
    success: true,
    posts: result.data || [],
    count: result.data?.length || 0,
  };
}

async function deletePost(postId) {
  const endpoint = `/${postId}`;
  await graphApiRequest(endpoint, 'DELETE');
  
  return {
    success: true,
    message: 'Post deleted',
    postId,
  };
}

// ============================================
// Instagram Operations
// ============================================

async function postToInstagram(caption, imageUrl, scheduledTime = null) {
  // Step 1: Create media container
  const containerEndpoint = `/${CONFIG.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media`;
  
  const containerParams = {
    image_url: imageUrl,
    caption,
  };
  
  if (scheduledTime) {
    containerParams.scheduled_time = scheduledTime;
  }
  
  const containerResult = await graphApiRequest(containerEndpoint, 'POST', containerParams);
  const creationId = containerResult.id;
  
  // Step 2: Wait for media to process
  await new Promise(resolve => setTimeout(resolve, 5000));
  
  // Step 3: Publish the post
  const publishEndpoint = `/${CONFIG.INSTAGRAM_BUSINESS_ACCOUNT_ID}/media_publish`;
  const publishResult = await graphApiRequest(publishEndpoint, 'POST', {
    creation_id: creationId,
  });
  
  return {
    success: true,
    postId: publishResult.id,
    message: 'Instagram post published',
  };
}

async function getInstagramInsights(dateRange = 'last_7_days') {
  const endpoint = `/${CONFIG.INSTAGRAM_BUSINESS_ACCOUNT_ID}/insights`;
  const result = await graphApiRequest(endpoint, 'GET', {
    metric: 'impressions,reach,profile_views',
    period: 'day',
  });
  
  return {
    success: true,
    insights: result.data || [],
    dateRange,
  };
}

async function getInstagramComments(mediaId, limit = 20) {
  const endpoint = `/${mediaId}/comments`;
  const result = await graphApiRequest(endpoint, 'GET', {
    limit: limit.toString(),
    fields: 'id,message,from,timestamp',
  });
  
  return {
    success: true,
    comments: result.data || [],
    count: result.data?.length || 0,
  };
}

// ============================================
// Analytics & Summary
// ============================================

async function generateWeeklySummary() {
  const [fbInsights, igInsights, fbPosts] = await Promise.all([
    getPageInsights('last_7_days'),
    getInstagramInsights('last_7_days'),
    getRecentPosts(7),
  ]);
  
  return {
    success: true,
    summary: {
      facebook: {
        posts: fbPosts.count,
        insights: fbInsights.insights,
      },
      instagram: {
        insights: igInsights.insights,
      },
      period: 'Last 7 days',
      generatedAt: new Date().toISOString(),
    },
  };
}

// ============================================
// MCP Server Setup
// ============================================

const server = new Server(
  {
    name: 'facebook-instagram-mcp',
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
        name: 'facebook_post',
        description: 'Create a post on Facebook Page. Returns post ID.',
        inputSchema: {
          type: 'object',
          properties: {
            message: { type: 'string', description: 'Post text content' },
            imageUrl: { type: 'string', description: 'URL of image to post (optional)' },
            link: { type: 'string', description: 'URL link to include (optional)' },
            scheduledTime: { type: 'string', description: 'ISO date string for scheduled post (optional)' },
          },
          required: ['message'],
        },
      },
      {
        name: 'facebook_get_insights',
        description: 'Get Facebook Page analytics/insights for a date range',
        inputSchema: {
          type: 'object',
          properties: {
            dateRange: { type: 'string', description: 'Date preset: today, yesterday, last_7_days, last_30_days', default: 'last_7_days' },
          },
        },
      },
      {
        name: 'facebook_get_posts',
        description: 'Get recent posts from Facebook Page',
        inputSchema: {
          type: 'object',
          properties: {
            limit: { type: 'number', description: 'Number of posts to retrieve (default: 10)', default: 10 },
          },
        },
      },
      {
        name: 'facebook_delete_post',
        description: 'Delete a Facebook post by ID',
        inputSchema: {
          type: 'object',
          properties: {
            postId: { type: 'string', description: 'Facebook post ID to delete' },
          },
          required: ['postId'],
        },
      },
      {
        name: 'instagram_post',
        description: 'Create a post on Instagram Business account. Requires image URL.',
        inputSchema: {
          type: 'object',
          properties: {
            caption: { type: 'string', description: 'Post caption text' },
            imageUrl: { type: 'string', description: 'URL of image to post (required)' },
            scheduledTime: { type: 'string', description: 'ISO date string for scheduled post (optional)' },
          },
          required: ['caption', 'imageUrl'],
        },
      },
      {
        name: 'instagram_get_insights',
        description: 'Get Instagram Business account analytics',
        inputSchema: {
          type: 'object',
          properties: {
            dateRange: { type: 'string', description: 'Date range for insights', default: 'last_7_days' },
          },
        },
      },
      {
        name: 'instagram_get_comments',
        description: 'Get comments on an Instagram media post',
        inputSchema: {
          type: 'object',
          properties: {
            mediaId: { type: 'string', description: 'Instagram media ID' },
            limit: { type: 'number', description: 'Number of comments to retrieve', default: 20 },
          },
          required: ['mediaId'],
        },
      },
      {
        name: 'social_weekly_summary',
        description: 'Generate a comprehensive weekly summary for Facebook and Instagram',
        inputSchema: {
          type: 'object',
          properties: {},
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
      case 'facebook_post':
        result = await postToFacebook(
          args.message,
          args.imageUrl,
          args.link,
          args.scheduledTime
        );
        break;
        
      case 'facebook_get_insights':
        result = await getPageInsights(args.dateRange || 'last_7_days');
        break;
        
      case 'facebook_get_posts':
        result = await getRecentPosts(args.limit || 10);
        break;
        
      case 'facebook_delete_post':
        result = await deletePost(args.postId);
        break;
        
      case 'instagram_post':
        result = await postToInstagram(
          args.caption,
          args.imageUrl,
          args.scheduledTime
        );
        break;
        
      case 'instagram_get_insights':
        result = await getInstagramInsights(args.dateRange || 'last_7_days');
        break;
        
      case 'instagram_get_comments':
        result = await getInstagramComments(args.mediaId, args.limit || 20);
        break;
        
      case 'social_weekly_summary':
        result = await generateWeeklySummary();
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
  validateConfig();
  
  const transport = new StdioServerTransport();
  await server.connect(transport);
  
  console.error('✅ Facebook/Instagram MCP Server running on stdio');
  console.error(`   Facebook Page ID: ${CONFIG.FACEBOOK_PAGE_ID}`);
  console.error(`   Instagram Account ID: ${CONFIG.INSTAGRAM_BUSINESS_ACCOUNT_ID}`);
}

main().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});

module.exports = { server, CONFIG };

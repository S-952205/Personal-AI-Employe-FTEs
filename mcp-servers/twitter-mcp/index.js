/**
 * Twitter/X MCP Server - Gold Tier
 * 
 * Integrates with Twitter API v2 for:
 * - Posting tweets
 * - Replying to mentions
 * - Reading notifications
 * - Getting tweet analytics
 * 
 * SETUP REQUIRED:
 * 1. Apply for Twitter Developer Account: https://developer.twitter.com/
 * 2. Create a Project and App
 * 3. Generate API Key + Secret
 * 4. Generate Bearer Token
 * 5. Generate Access Token + Secret (with read/write permissions)
 * 6. Update configuration in this file (search for CONFIGURATION)
 */

const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { CallToolRequestSchema, ListToolsRequestSchema } = require('@modelcontextprotocol/sdk/types.js');

// ============================================
// CONFIGURATION - UPDATE THESE VALUES
// ============================================

const CONFIG = {
  // Twitter API v2 Credentials
  TWITTER_API_KEY: 'EzS5vYyR0AeY6n4UcSuMvDlQq',                     // Replace with your API Key
  TWITTER_API_SECRET: 'TZfZsfwiOlZYcSb1qyjM7nlgi5cHSNuOGwU6I5HbYrSJNal2xU',               // Replace with your API Secret
  TWITTER_BEARER_TOKEN: 'AAAAAAAAAAAAAAAAAAAAALJJ8wEAAAAAjoGzW9eGblqirmUn%2F5%2FU7MMJtm8%3DI2M8y1mcnN925JAxu3goEQQh9w1yFqgATODybVrqZ15loZi06C',           // Replace with your Bearer Token
  TWITTER_ACCESS_TOKEN: '1350922842792218628-7vMnlUQiAb0uVfxsNXCyk61xr25dX6',           // Replace with your Access Token
  TWITTER_ACCESS_TOKEN_SECRET: 'bWO8tZXIVPD1KJFHA4A2rQ5alPEs2wFkxn2laJWTMf2Zz',  // Replace with your Access Token Secret
  
  // API Base URLs
  TWITTER_API_BASE: 'https://api.twitter.com/2',
  
  // Rate limiting
  MAX_TWEETS_PER_DAY: 15,
  TWEET_COOLDOWN_SECONDS: 300,  // 5 minutes between tweets
};

// Validate configuration
function validateConfig() {
  const requiredFields = [
    'TWITTER_API_KEY',
    'TWITTER_API_SECRET',
    'TWITTER_BEARER_TOKEN',
    'TWITTER_ACCESS_TOKEN',
    'TWITTER_ACCESS_TOKEN_SECRET'
  ];
  
  const missing = requiredFields.filter(field => 
    CONFIG[field].startsWith('YOUR_') || CONFIG[field] === ''
  );
  
  if (missing.length > 0) {
    console.error('❌ Missing Twitter/X configuration:');
    missing.forEach(field => console.error(`   - ${field}`));
    console.error('\n📖 Setup Guide:');
    console.error('   1. Go to https://developer.twitter.com/');
    console.error('   2. Apply for developer account');
    console.error('   3. Create project and get credentials');
    console.error('   4. Update CONFIG object in this file');
    process.exit(1);
  }
}

// ============================================
// HTTP Client Helper (OAuth 1.0a for Twitter)
// ============================================

// Simple HMAC-SHA1 signature for OAuth 1.0a
async function createOAuthHeader(method, url, params) {
  // For production, use a proper OAuth library like oauth-1.0a
  // This is a simplified version for demonstration
  
  const crypto = require('crypto');
  
  const oauthParams = {
    oauth_consumer_key: CONFIG.TWITTER_API_KEY,
    oauth_token: CONFIG.TWITTER_ACCESS_TOKEN,
    oauth_nonce: Math.random().toString(36).substring(7),
    oauth_timestamp: Math.floor(Date.now() / 1000),
    oauth_signature_method: 'HMAC-SHA1',
    oauth_version: '1.0',
    ...params
  };
  
  // Sort and encode parameters
  const encodedParams = Object.keys(oauthParams)
    .sort()
    .map(key => `${encodeURIComponent(key)}=${encodeURIComponent(oauthParams[key])}`)
    .join('&');
  
  // Create signature base string
  const encodedUrl = encodeURIComponent(url);
  const signatureBase = `${method.toUpperCase()}&${encodedUrl}&${encodeURIComponent(encodedParams)}`;
  
  // Create signing key
  const signingKey = `${encodeURIComponent(CONFIG.TWITTER_API_SECRET)}&${encodeURIComponent(CONFIG.TWITTER_ACCESS_TOKEN_SECRET)}`;
  
  // Generate signature
  const signature = crypto
    .createHmac('sha1', signingKey)
    .update(signatureBase)
    .digest('base64');
  
  oauthParams.oauth_signature = signature;
  
  // Build Authorization header
  const authHeader = Object.keys(oauthParams)
    .sort()
    .map(key => `${encodeURIComponent(key)}="${encodeURIComponent(oauthParams[key])}"`)
    .join(', ');
  
  return `OAuth ${authHeader}`;
}

async function twitterRequest(endpoint, method = 'GET', body = null) {
  const url = `${CONFIG.TWITTER_API_BASE}${endpoint}`;
  
  const headers = {
    'Authorization': `Bearer ${CONFIG.TWITTER_BEARER_TOKEN}`,
    'Content-Type': 'application/json',
  };
  
  const options = {
    method,
    headers,
  };
  
  if (body && method !== 'GET') {
    options.body = JSON.stringify(body);
  }
  
  try {
    const response = await fetch(url, options);
    const data = await response.json();
    
    if (!response.ok) {
      throw new Error(`Twitter API Error: ${data.title || response.statusText} - ${JSON.stringify(data.details || data)}`);
    }
    
    return data;
  } catch (error) {
    console.error(`Twitter API request failed: ${error.message}`);
    throw error;
  }
}

// ============================================
// Twitter Operations
// ============================================

async function postTweet(text, mediaId = null, replyToId = null) {
  const endpoint = '/tweets';
  
  const body = {
    text,
  };
  
  if (replyToId) {
    body.reply = { in_reply_to_tweet_id: replyToId };
  }
  
  const result = await twitterRequest(endpoint, 'POST', body);
  
  return {
    success: true,
    tweetId: result.data.id,
    text: result.data.text,
    message: 'Tweet published',
  };
}

async function postTweetThread(texts) {
  const results = [];
  let lastTweetId = null;
  
  for (const text of texts) {
    const result = await postTweet(text, null, lastTweetId);
    results.push(result);
    lastTweetId = result.tweetId;
  }
  
  return {
    success: true,
    tweets: results,
    count: results.length,
    message: `Thread with ${results.length} tweets published`,
  };
}

async function getMentions(limit = 20) {
  const endpoint = '/tweets/search/recent';
  const result = await twitterRequest(endpoint, 'GET', {
    query: '@YOUR_USERNAME',  // Replace with your Twitter handle
    max_results: limit.toString(),
    'tweet.fields': 'created_at,author_id,public_metrics,referenced_tweets',
    'user.fields': 'name,username,profile_image_url',
    'expansions': 'author_id',
  });
  
  return {
    success: true,
    mentions: result.data || [],
    users: result.includes?.users || [],
    count: result.data?.length || 0,
  };
}

async function getTweetAnalytics(tweetId) {
  const endpoint = `/tweets/${tweetId}`;
  const result = await twitterRequest(endpoint, 'GET', {
    'tweet.fields': 'public_metrics,created_at',
  });
  
  return {
    success: true,
    tweetId,
    metrics: result.data?.public_metrics || {},
    created: result.data?.created_at,
  };
}

async function getUserTimeline(username, limit = 10) {
  // First get user ID
  const userEndpoint = `/users/by/username/${username}`;
  const userResult = await twitterRequest(userEndpoint, 'GET', {
    'user.fields': 'id,name,username',
  });
  
  const userId = userResult.data.id;
  
  // Then get tweets
  const timelineEndpoint = `/users/${userId}/tweets`;
  const result = await twitterRequest(timelineEndpoint, 'GET', {
    max_results: limit.toString(),
    'tweet.fields': 'created_at,public_metrics,context_annotations',
  });
  
  return {
    success: true,
    username,
    tweets: result.data || [],
    count: result.data?.length || 0,
  };
}

async function getRecentTweets(limit = 10) {
  // Get authenticated user's recent tweets
  const endpoint = '/users/me';
  const userResult = await twitterRequest(endpoint, 'GET');
  const userId = userResult.data.id;
  
  const timelineEndpoint = `/users/${userId}/tweets`;
  const result = await twitterRequest(timelineEndpoint, 'GET', {
    max_results: limit.toString(),
    'tweet.fields': 'created_at,public_metrics',
  });
  
  return {
    success: true,
    tweets: result.data || [],
    count: result.data?.length || 0,
  };
}

async function generateWeeklySummary() {
  const [recentTweets, mentions] = await Promise.all([
    getRecentTweets(7),
    getMentions(20),
  ]);
  
  // Calculate engagement
  let totalLikes = 0;
  let totalRetweets = 0;
  let totalReplies = 0;
  
  recentTweets.tweets.forEach(tweet => {
    totalLikes += tweet.public_metrics?.like_count || 0;
    totalRetweets += tweet.public_metrics?.retweet_count || 0;
    totalReplies += tweet.public_metrics?.reply_count || 0;
  });
  
  return {
    success: true,
    summary: {
      period: 'Last 7 days',
      tweetsPosted: recentTweets.count,
      mentionsReceived: mentions.count,
      engagement: {
        totalLikes,
        totalRetweets,
        totalReplies,
        totalEngagement: totalLikes + totalRetweets + totalReplies,
      },
      generatedAt: new Date().toISOString(),
    },
  };
}

// ============================================
// MCP Server Setup
// ============================================

const server = new Server(
  {
    name: 'twitter-x-mcp',
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
        name: 'twitter_post',
        description: 'Create a tweet on Twitter/X. Returns tweet ID.',
        inputSchema: {
          type: 'object',
          properties: {
            text: { type: 'string', description: 'Tweet text (max 280 characters)' },
            mediaId: { type: 'string', description: 'Media ID for image/video (optional)' },
            replyToId: { type: 'string', description: 'Tweet ID to reply to (optional)' },
          },
          required: ['text'],
        },
      },
      {
        name: 'twitter_post_thread',
        description: 'Create a thread of tweets. Each item in array is one tweet.',
        inputSchema: {
          type: 'object',
          properties: {
            texts: {
              type: 'array',
              items: { type: 'string' },
              description: 'Array of tweet texts for the thread',
            },
          },
          required: ['texts'],
        },
      },
      {
        name: 'twitter_get_mentions',
        description: 'Get recent mentions of your account',
        inputSchema: {
          type: 'object',
          properties: {
            limit: { type: 'number', description: 'Number of mentions to retrieve', default: 20 },
          },
        },
      },
      {
        name: 'twitter_get_tweet_analytics',
        description: 'Get engagement metrics for a specific tweet',
        inputSchema: {
          type: 'object',
          properties: {
            tweetId: { type: 'string', description: 'Tweet ID to get analytics for' },
          },
          required: ['tweetId'],
        },
      },
      {
        name: 'twitter_get_user_timeline',
        description: 'Get recent tweets from any user',
        inputSchema: {
          type: 'object',
          properties: {
            username: { type: 'string', description: 'Twitter username (without @)' },
            limit: { type: 'number', description: 'Number of tweets to retrieve', default: 10 },
          },
          required: ['username'],
        },
      },
      {
        name: 'twitter_get_recent_tweets',
        description: 'Get your recent tweets',
        inputSchema: {
          type: 'object',
          properties: {
            limit: { type: 'number', description: 'Number of tweets to retrieve', default: 10 },
          },
        },
      },
      {
        name: 'twitter_weekly_summary',
        description: 'Generate a comprehensive weekly summary for Twitter',
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
      case 'twitter_post':
        result = await postTweet(args.text, args.mediaId, args.replyToId);
        break;
        
      case 'twitter_post_thread':
        result = await postTweetThread(args.texts);
        break;
        
      case 'twitter_get_mentions':
        result = await getMentions(args.limit || 20);
        break;
        
      case 'twitter_get_tweet_analytics':
        result = await getTweetAnalytics(args.tweetId);
        break;
        
      case 'twitter_get_user_timeline':
        result = await getUserTimeline(args.username, args.limit || 10);
        break;
        
      case 'twitter_get_recent_tweets':
        result = await getRecentTweets(args.limit || 10);
        break;
        
      case 'twitter_weekly_summary':
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
  
  console.error('✅ Twitter/X MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Failed to start server:', error);
  process.exit(1);
});

module.exports = { server, CONFIG };

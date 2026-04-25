/**
 * PM2 Ecosystem Configuration for AI Employee - Silver Tier
 * 
 * Usage:
 *   # Install PM2 globally
 *   npm install -g pm2
 * 
 *   # Start all processes
 *   pm2 start ecosystem.config.cjs
 * 
 *   # Save process list
 *   pm2 save
 * 
 *   # Setup startup on Windows (use pm2-startup package)
 *   npm install -g pm2-startup
 *   pm2-startup install
 * 
 *   # Or use Windows Task Scheduler (see scripts/setup-tasks.bat)
 * 
 * Commands:
 *   pm2 status              - Check process status
 *   pm2 logs                - View all logs
 *   pm2 logs gmail-watcher  - View specific logs
 *   pm2 restart all         - Restart all processes
 *   pm2 stop all            - Stop all processes
 *   pm2 delete all          - Delete all processes
 */

module.exports = {
  apps: [
    {
      name: 'gmail-watcher',
      script: './scripts/gmail_watcher.py',
      interpreter: 'python',
      interpreter_args: '-u',  // Unbuffered output for real-time logs
      cwd: __dirname,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO'
      },
      error_file: './logs/pm2-gmail-watcher-error.log',
      out_file: './logs/pm2-gmail-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true
    },
    {
      name: 'linkedin-watcher',
      script: './scripts/linkedin_watcher.py',
      interpreter: 'python',
      interpreter_args: '-u',
      cwd: __dirname,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO'
      },
      error_file: './logs/pm2-linkedin-watcher-error.log',
      out_file: './logs/pm2-linkedin-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true
    },
    {
      name: 'facebook-watcher',
      script: './scripts/facebook_watcher.py',
      interpreter: 'python',
      interpreter_args: '-u',
      cwd: __dirname,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO'
      },
      error_file: './logs/pm2-facebook-watcher-error.log',
      out_file: './logs/pm2-facebook-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true
    },
    {
      name: 'filesystem-watcher',
      script: './scripts/filesystem_watcher.py',
      interpreter: 'python',
      interpreter_args: '-u',
      cwd: __dirname,
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO'
      },
      error_file: './logs/pm2-filesystem-watcher-error.log',
      out_file: './logs/pm2-filesystem-watcher-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true
    },
    {
      name: 'orchestrator',
      script: './scripts/orchestrator.py',
      interpreter: 'python',
      interpreter_args: '-u',
      cwd: __dirname,
      autorestart: true,
      watch: false,
      max_memory_restart: '500M',
      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO'
      },
      error_file: './logs/pm2-orchestrator-error.log',
      out_file: './logs/pm2-orchestrator-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true
    },
    {
      // PM2 Cron Scheduler — Runs scheduled jobs (CEO Briefing, auto-post, etc.)
      name: 'pm2-cron',
      script: './scripts/pm2_cron.py',
      interpreter: 'python',
      interpreter_args: '-u',
      cwd: __dirname,
      autorestart: true,
      watch: false,
      max_memory_restart: '300M',
      env: {
        PYTHONUNBUFFERED: '1',
        LOG_LEVEL: 'INFO'
      },
      error_file: './logs/pm2-cron-error.log',
      out_file: './logs/pm2-cron-out.log',
      log_date_format: 'YYYY-MM-DD HH:mm:ss',
      merge_logs: true
    }
  ]
};

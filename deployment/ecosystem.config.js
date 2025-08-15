module.exports = {
  apps: [{
    name: 'trae-sentinel',
    script: 'main.py',
    interpreter: 'python3',
    cwd: '/home/trae/AI-Sentinel',
    instances: 1,
    autorestart: true,
    watch: false,
    max_memory_restart: '1G',
    env: {
      PYTHONUNBUFFERED: '1',
      TRAE_ENV: 'production',
      TRAE_PHASE: '10',
      TRAE_LIVEOPS: 'true'
    },
    error_file: '/home/trae/AI-Sentinel/logs/pm2_error.log',
    out_file: '/home/trae/AI-Sentinel/logs/pm2_output.log',
    merge_logs: true,
    log_date_format: 'YYYY-MM-DD HH:mm:ss Z',
    restart_delay: 10000
  }]
};
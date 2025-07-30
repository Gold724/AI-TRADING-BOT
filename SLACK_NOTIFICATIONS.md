# Slack Notifications for AI Trading Sentinel

This document describes how to set up and use the Slack notifications feature in the AI Trading Sentinel system.

## Overview

The AI Trading Sentinel can send stylized notifications to a Slack channel for various trading events, including:

- Successful trades with profit information
- Failed trade attempts
- Successful login events
- Failed login attempts
- Custom messages

## Setup Instructions

### 1. Create a Slack Webhook

1. Go to your Slack workspace and create a new app (or use an existing one)
2. Navigate to "Incoming Webhooks" under "Features"
3. Activate incoming webhooks
4. Click "Add New Webhook to Workspace"
5. Choose the channel where notifications should be posted
6. Copy the webhook URL provided by Slack

### 2. Configure Your Environment

Add the webhook URL to your `.env` file:

```
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

Replace `https://hooks.slack.com/services/YOUR/WEBHOOK/URL` with the actual webhook URL you copied from Slack.

## Usage

### Sending Notifications

Import the notification function in your Python code:

```python
from utils.slack_notifications import send_slack_prophetic
```

### Examples

#### Profit Alert

```python
send_slack_prophetic(
    message_type="profit",
    symbol="EURUSD",
    entry=1.0750,
    direction="buy",
    profit=120.50,
    session_id="BX64883-20230615-123456"
)
```

#### Failed Trade Alert

```python
send_slack_prophetic(
    message_type="fail",
    symbol="GBPJPY",
    entry=182.500,
    direction="sell",
    status="Market closed",
    session_id="BX64883-20230615-123456"
)
```

#### Login Success Alert

```python
send_slack_prophetic(
    message_type="login_success",
    session_id="BX64883-20230615-123456"
)
```

#### Login Failure Alert

```python
send_slack_prophetic(
    message_type="login_fail",
    session_id="BX64883-20230615-123456"
)
```

#### Custom Message

```python
send_slack_prophetic(
    message_type="Custom alert message goes here",
    session_id="BX64883-20230615-123456"
)
```

## Testing

You can test the Slack notification functionality by running the test script:

```bash
python test_slack_notifications.py
```

This script will send test notifications of each type to your configured Slack channel.

## Troubleshooting

### Common Issues

1. **No notifications appearing in Slack**
   - Verify your webhook URL is correct
   - Check that the webhook URL is properly set in your `.env` file
   - Ensure your application has network access to reach Slack's servers

2. **Error: SLACK_WEBHOOK_URL environment variable not set**
   - Make sure you've added the webhook URL to your `.env` file
   - Ensure your application is loading the environment variables correctly

3. **HTTP Error 4xx from Slack API**
   - Your webhook URL may be invalid or revoked
   - The Slack app may not have the necessary permissions

## Security Considerations

- Never commit your webhook URL to version control
- Consider encrypting the webhook URL in production environments
- Be mindful of sensitive information included in notifications
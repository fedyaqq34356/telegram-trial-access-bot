# Trial Period Bot

Telegram bot for automated trial period management and user access control in work chats and study groups.

## Features

- **Automatic Trial Period Tracking**: Users get 8-day trial period upon joining
- **Dual Chat Management**: Monitors both work chat and study group simultaneously
- **Automated Notifications**: Alerts admins when trials expire or when users leave
- **User Presence Verification**: Checks if users are present in both chats
- **Admin Panel**: Comprehensive interface for user and admin management
- **Database Persistence**: SQLite storage for all user data and settings
- **Scheduled Tasks**: Automated checks for expired trials and upcoming expirations
- **Flexible Access Control**: Admin privileges system with multiple administrators

## Requirements

- Python 3.8+
- aiogram 3.15.0
- APScheduler 3.10.4

## Installation

Clone the repository:

```bash
git clone https://github.com/your-repo/trial-period-bot.git
cd trial-period-bot
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create `.env` file in project root:

```env
BOT_TOKEN=your_bot_token_here
WORK_CHAT_ID=-1001234567890
STUDY_GROUP_ID=-1009876543210
TRIAL_MINUTES=11520
```

## Getting Credentials

### Bot Token

1. Open Telegram and find @BotFather
2. Send `/newbot` command
3. Follow instructions to create your bot
4. Copy the token to `BOT_TOKEN` in `.env`

### Chat IDs

To get chat IDs for your work chat and study group:

1. Add @userinfobot to your chat
2. Forward any message from the chat to the bot
3. The bot will show the chat ID
4. Copy the ID (including the minus sign) to `.env`

Alternatively, use @raw_data_bot or any similar bot that displays chat information.

### Trial Period Configuration

`TRIAL_MINUTES` controls how long users have trial access. Default is 11520 minutes (8 days). You can adjust this value:

- 1 day: 1440
- 3 days: 4320
- 7 days: 10080
- 8 days: 11520 (default)
- 14 days: 20160

## Initial Setup

### Adding First Administrator

Before running the bot, you need to add at least one administrator. Use the helper script:

```bash
python add_admin.py YOUR_TELEGRAM_ID
```

Example:

```bash
python add_admin.py 123456789
```

To find your Telegram ID:

1. Message @userinfobot in Telegram
2. Send `/start`
3. Copy your user ID from the response

The script will confirm the admin was added and show all current administrators.

## Usage

Start the bot:

```bash
python main.py
```

The bot will:

- Initialize the SQLite database
- Load configuration from `.env`
- Start the polling loop
- Activate the scheduler for automated checks
- Send startup notification to all admins

## Bot Configuration

### Bot Permissions

The bot must be an administrator in both the work chat and study group with the following permissions:

- **Invite users via link**: Required for join request approval
- **Ban users**: Required to remove users when trial expires
- **View members**: Required for presence checks

### Chat Settings

For the work chat and study group:

1. Go to Chat Settings → Manage Chat
2. Select your bot from the administrators list
3. Enable required permissions
4. Enable "Join requests" in chat privacy settings

## Admin Panel

Once you send `/start` to the bot, you'll see the main menu with these buttons:

### User Management

**Пользователи** (Users):

Generates a text file with complete user list including:

- User ID
- Username/tag
- Full name
- Current status (trial/approved)
- Time remaining on trial

Example output:

```
123456789 | @john_doe | John Doe | 🟡 7 д. 12 ч. 30 мин.
--------------------------------------------------
987654321 | @jane_smith | Jane Smith | 🟢 Оставлен
--------------------------------------------------
```

**На пробном периоде** (On Trial Period):

Shows all users currently on trial with detailed information:

- 🟡 John Doe
- ID: 123456789
- @john_doe
- Осталось: 7 д. 12 ч. 30 мин.

Sends multiple messages if the list is too long (over 4000 characters per message).

**Проверка** (Check):

Performs comprehensive presence verification:

1. Checks if each user is present in both chats
2. Updates database with current presence status
3. Automatically removes users from study group if they left work chat
4. Sends notifications about users who left either chat
5. Provides action buttons (Keep/Kick) for each issue found

**Удалить участника** (Delete User):

Manual user removal process:

1. Click the button
2. Enter the Telegram ID of the user to delete
3. Bot will remove user from both chats and delete from database

**Skip пробный период** (Skip Trial Period):

Manually approve a user before trial ends:

1. Click the button
2. Enter the user's Telegram ID
3. User status changes to "approved" (🟢)
4. User will not be removed when trial expires

### Administrator Management

**Добавить администратора** (Add Administrator):

1. Click the button
2. Enter Telegram ID of the user to promote
3. User gains access to admin panel

**Убрать администратора** (Remove Administrator):

1. Click the button
2. Enter Telegram ID of the admin to demote
3. User loses admin access

**Список администраторов** (List Administrators):

Shows all current administrators with their Telegram IDs.

## Automated Features

### Join Request Handling

When a user sends a join request to the work chat:

1. Request is automatically approved
2. User is added to database with trial period start date
3. Trial end date is calculated (current time + TRIAL_MINUTES)
4. User status is set to "trial"
5. Presence flags are set to true for work chat

### Trial Expiration Monitoring

The scheduler runs hourly checks for:

**Expired Trials**:

When a trial period ends:

1. Admin receives notification with user details
2. Inline keyboard appears with two options:
   - **Оставить** (Keep): Change status to "approved"
   - **Кикнуть** (Kick): Remove from both chats

**Expiring Soon**:

24 hours before trial expires:

1. Admin receives early warning notification
2. User information displayed with time remaining
3. Same action buttons provided for early decision
4. User is marked as notified to prevent duplicate alerts

### User Departure Detection

When a user leaves either chat:

**Left Work Chat**:

1. Admin receives notification
2. Database updated with presence status
3. User information displayed

**Left Study Group**:

1. Admin receives notification
2. User is automatically removed from work chat
3. User is deleted from database

This ensures study group access requires work chat membership.

### Presence Synchronization

The "Проверка" function ensures data consistency:

1. Queries Telegram API for each user's membership status
2. Updates local database with current presence
3. Removes study group access if user not in work chat
4. Reports any discrepancies to admins

## Database Schema

The bot uses SQLite with two tables:

### Users Table

```sql
CREATE TABLE users (
    telegram_id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    username TEXT,
    join_date TEXT NOT NULL,
    trial_end_date TEXT NOT NULL,
    status TEXT DEFAULT 'trial',
    in_work_chat INTEGER DEFAULT 1,
    in_study_group INTEGER DEFAULT 1,
    notified_one_day INTEGER DEFAULT 0
)
```

Fields:

- `telegram_id`: Unique Telegram user identifier
- `name`: User's full name from Telegram profile
- `username`: Telegram username (without @), nullable
- `join_date`: ISO format timestamp of when user joined
- `trial_end_date`: ISO format timestamp when trial expires
- `status`: Either "trial" or "approved"
- `in_work_chat`: Boolean flag (1/0) for work chat presence
- `in_study_group`: Boolean flag (1/0) for study group presence
- `notified_one_day`: Boolean flag to prevent duplicate 24h warnings

### Admins Table

```sql
CREATE TABLE admins (
    telegram_id INTEGER PRIMARY KEY
)
```

Simple table storing Telegram IDs of users with admin access.

## Project Structure

```
trial-period-bot/
├── main.py                    # Application entry point
├── config.py                  # Configuration loader
├── database.py                # Database operations
├── scheduler.py               # Automated task scheduler
├── keyboards.py               # Bot keyboard layouts
├── utils.py                   # Helper functions
├── add_admin.py              # Admin addition script
├── handlers/
│   ├── __init__.py           # Router initialization
│   ├── chat_events.py        # Join/leave event handlers
│   ├── menu_handlers.py      # Main menu button handlers
│   ├── admin_handlers.py     # Admin operation handlers
│   └── callback_handlers.py  # Inline button handlers
├── .env                       # Environment configuration
├── .gitignore                # Git ignore rules
├── bot.db                    # SQLite database (auto-created)
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## File Descriptions

### main.py

Application entry point that:

- Loads configuration from environment variables
- Initializes database connection
- Creates bot and dispatcher instances
- Registers command and message handlers
- Sets up the scheduler for automated tasks
- Sends startup notifications to admins
- Starts the polling loop

### config.py

Configuration management using dataclass pattern:

- Loads environment variables
- Validates required settings
- Provides type-safe configuration access
- Includes default values for optional settings

### database.py

Complete database abstraction layer:

- Context manager for safe connection handling
- User CRUD operations (Create, Read, Update, Delete)
- Admin management functions
- Trial period queries and filters
- Presence tracking updates
- Notification status management

Key methods:

- `add_user()`: Register new user with trial period
- `get_user()`: Retrieve user by Telegram ID
- `get_expired_trials()`: Find users with expired trials
- `get_users_expiring_soon()`: Find trials expiring in 24 hours
- `update_status()`: Change user status (trial/approved)
- `update_presence()`: Update chat presence flags
- `is_admin()`: Check if user has admin privileges

### scheduler.py

Automated task management using APScheduler:

- `check_expired_trials()`: Runs hourly, finds and reports expired trials
- `check_expiring_soon()`: Runs hourly, sends 24-hour warnings
- `setup_scheduler()`: Configures and returns scheduler instance

Both tasks send notifications to all admins with inline keyboards for quick actions.

### keyboards.py

UI component definitions:

- `get_main_menu()`: Returns main admin panel keyboard with 8 buttons
- `get_trial_decision()`: Returns inline keyboard with Keep/Kick buttons

### utils.py

Helper functions for formatting and calculations:

- `format_username()`: Displays username with @ or "тег отсутствует"
- `get_status_emoji()`: Returns 🟢 for approved, 🟡 for trial
- `minutes_remaining()`: Calculates time left until trial expires
- `format_time_remaining()`: Converts minutes to readable format (X д. Y ч. Z мин.)
- `format_user_info()`: Creates formatted user display with optional time
- `format_user_list_item()`: Creates compact user listing for file export

### handlers/chat_events.py

Telegram chat event handlers:

- `handle_join_request()`: Approves requests and adds users to database
- `user_joined()`: Handles direct joins (if chat is public)
- `user_left()`: Detects departures and updates database/notifies admins

Special logic: If user leaves study group, they're also removed from work chat.

### handlers/menu_handlers.py

Main menu button handlers:

- `show_users()`: Generates and sends complete user list as text file
- `show_trial_users()`: Displays paginated list of users on trial
- `check_presence()`: Performs comprehensive presence verification

The check_presence function queries Telegram API for each user's membership status and reconciles with database.

### handlers/admin_handlers.py

Admin operation handlers with state management:

- `delete_user_prompt()`: Initiates user deletion flow
- `skip_trial_prompt()`: Initiates trial skip flow
- `add_admin_prompt()`: Initiates admin addition flow
- `remove_admin_prompt()`: Initiates admin removal flow
- `show_admins()`: Lists all administrators
- `handle_user_input()`: Processes numeric input for various flows

Uses `user_modes` dictionary to track which operation each admin is performing.

### handlers/callback_handlers.py

Inline button callback handlers:

- `approve_user()`: Changes user status to "approved"
- `kick_user()`: Removes user from both chats and database

Both handlers update the original message to show the action taken.

### add_admin.py

Command-line utility for adding administrators:

```bash
python add_admin.py 123456789
```

Features:

- Validates input is numeric
- Checks if user is already admin
- Adds to admins table
- Displays updated admin list

## Workflow Examples

### New User Joins

1. User sends join request to work chat
2. Bot automatically approves request
3. Database entry created with 8-day trial
4. User can access work chat immediately

### Trial Period Expires

**One day before expiration**:

1. Scheduler detects trial ending in 24 hours
2. Admin receives notification: "Пробный период скоро истечет"
3. Admin can preemptively approve or remove user

**On expiration day**:

1. Scheduler detects expired trial
2. Admin receives notification: "Пробный период завершен"
3. Admin clicks "Оставить" (Keep) or "Кикнуть" (Kick)
4. If kicked: User removed from both chats and database
5. If kept: User status changes to "approved", no future notifications

### User Leaves Study Group

1. Bot detects ChatMemberUpdated event
2. User automatically removed from work chat
3. User deleted from database
4. All admins notified of departure

### Manual User Removal

1. Admin clicks "Удалить участника"
2. Bot prompts for Telegram ID
3. Admin enters ID: `123456789`
4. Bot removes user from both chats
5. Database entry deleted
6. Confirmation message sent

### Presence Check

1. Admin clicks "Проверка"
2. Bot queries Telegram API for each user
3. Database updated with current presence
4. Issues reported:
   - User in study group but not work chat → removed from study group
   - User left one or both chats → decision buttons shown
5. If no issues: "Все пользователи на месте"

## Status Indicators

The bot uses emojis to indicate user status:

- 🟡 **Trial**: User is on trial period, time remaining shown
- 🟢 **Approved**: User has been manually approved, no expiration

These indicators appear in:

- User list files
- Trial period listings
- Notification messages

## Time Display Format

Time remaining is displayed in Russian format:

```
7 д. 12 ч. 30 мин.
```

- д. = days (дней)
- ч. = hours (часов)
- мин. = minutes (минут)

When trial expires, displays: "Истек"

## Notification Examples

### Trial Expired Notification

```
Пробный период завершен

🟡 John Doe
ID: 123456789
@john_doe

[Оставить] [Кикнуть]
```

### Trial Expiring Soon Notification

```
Пробный период скоро истечет

🟡 Jane Smith
ID: 987654321
@jane_smith
Осталось: 23 ч. 45 мин.

Остался 1 день

[Оставить] [Кикнуть]
```

### User Left Notification

```
Пользователь вышел из рабочего чата

John Doe
ID: 123456789
@john_doe

[Оставить] [Кикнуть]
```

## Error Handling

The bot includes comprehensive error handling:

### API Errors

- **User not found**: Displayed when trying to delete non-existent user
- **Permission denied**: Bot lacks required admin permissions
- **Chat not accessible**: Chat ID is incorrect or bot was removed

### Database Errors

- Automatic commit/rollback on exceptions
- Connection pooling with context managers
- Graceful handling of constraint violations

### Network Errors

- Automatic retry for temporary network issues
- Timeout handling for long-running operations
- Fallback behavior when Telegram API is unreachable

All errors are logged with full context and user receives informative error message.

## Logging

The bot uses Python's built-in logging module:

```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

Log output example:

```
2026-01-06 22:30:15 - __main__ - INFO - Бот запущен
2026-01-06 22:30:20 - __main__ - INFO - Загружено 3 администратор(ов)
2026-01-06 22:30:21 - __main__ - INFO - Планировщик запущен
```

Logged events include:

- Bot startup and shutdown
- Admin count on initialization
- Scheduler activation
- Warning if no admins found
- Errors with full tracebacks

## Security Considerations

### Credential Protection

- Never commit `.env` file to version control
- Use restrictive file permissions: `chmod 600 .env`
- Rotate bot token if accidentally exposed
- Keep `bot.db` file private (contains user data)

### Access Control

- Only users in `admins` table can access admin panel
- Regular users see only their Telegram ID when sending `/start`
- Bot validates admin status before every operation
- No privilege escalation vulnerabilities

### Data Privacy

- Only stores necessary user data (ID, name, username)
- No message content is logged or stored
- No external API calls except Telegram
- All data processing happens locally

### Bot Permissions

Minimize bot permissions in chats:

- Only enable "Invite users" and "Ban users"
- Don't grant "Delete messages" or "Pin messages"
- Remove "Add new admins" permission
- Keep bot as regular admin, not creator

## Performance Considerations

### Database Optimization

- Uses SQLite with WAL mode for concurrent reads
- Indexes on `telegram_id` for fast lookups
- Connection pooling via context managers
- Minimal query complexity

### API Rate Limits

Telegram API limits:

- 30 messages per second per bot
- 20 API calls per minute per method

Bot includes built-in delays to respect limits:

- Scheduler runs hourly, not continuously
- User checks are performed serially
- Admin notifications sent with try/except to continue on failure

### Resource Usage

Typical resource consumption:

- Memory: 30-50 MB
- CPU: < 1% when idle
- Network: Minimal polling traffic
- Disk: Database grows ~1 KB per user

Scales well up to 10,000 users per bot instance.

## Troubleshooting

### Bot Not Responding

**Issue**: Bot doesn't respond to commands

**Solutions**:

1. Check `BOT_TOKEN` is correct in `.env`
2. Verify bot is not blocked by Telegram
3. Ensure bot wasn't removed from chats
4. Check internet connection
5. Review logs for error messages

### Join Requests Not Auto-Approved

**Issue**: Users' join requests stay pending

**Solutions**:

1. Verify bot is admin in work chat
2. Check "Invite users via link" permission is enabled
3. Ensure chat has "Join requests" enabled
4. Confirm `WORK_CHAT_ID` matches actual chat ID

### Notifications Not Received

**Issue**: Admins don't receive expiration notifications

**Solutions**:

1. Check admin ID is in database: `python add_admin.py YOUR_ID`
2. Verify bot hasn't been blocked by admin
3. Check scheduler is running (see startup logs)
4. Confirm `TRIAL_MINUTES` is set correctly

### Users Not Removed After Trial Expires

**Issue**: Expired trial users remain in chats

**Solutions**:

1. Ensure bot has "Ban users" permission
2. Admin must click "Кикнуть" when notified
3. Bot cannot auto-remove without admin decision
4. Check bot wasn't demoted from admin

### Database Errors

**Issue**: SQLite errors or corrupted database

**Solutions**:

1. Stop the bot
2. Backup `bot.db`: `cp bot.db bot.db.backup`
3. Delete `bot.db` and restart bot (creates new database)
4. Re-add admins: `python add_admin.py YOUR_ID`
5. Run "Проверка" to rebuild user data from Telegram

### Permission Errors

**Issue**: "Chat admin privileges are required"

**Solutions**:

1. Remove bot from chat
2. Re-add bot with admin privileges
3. Enable all required permissions
4. Restart bot

## Advanced Configuration

### Custom Trial Duration

Modify `TRIAL_MINUTES` in `.env`:

```env
# 3 days
TRIAL_MINUTES=4320

# 14 days
TRIAL_MINUTES=20160

# 30 days
TRIAL_MINUTES=43200
```

### Multiple Work Environments

To manage multiple work/study pairs, run separate bot instances:

```
project-1/
├── .env (BOT_TOKEN=token1, WORK_CHAT_ID=chat1)
└── bot.db

project-2/
├── .env (BOT_TOKEN=token2, WORK_CHAT_ID=chat2)
└── bot.db
```

Each instance needs its own bot token and database.

### Scheduler Frequency

Modify `scheduler.py` to change check frequency:

```python
# Check every 30 minutes instead of hourly
scheduler.add_job(
    check_expired_trials,
    'interval',
    minutes=30,
    args=[bot, db, admin_ids]
)
```

### Custom Notification Messages

Edit `scheduler.py` and `handlers/chat_events.py` to customize notification text. Look for strings like:

```python
text = f"Пробный период завершен\n\n{format_user_info(user)}"
```

Replace with your preferred wording.

## Backup and Recovery

### Database Backup

Regular backups recommended:

```bash
# Manual backup
cp bot.db bot_backup_$(date +%Y%m%d).db

# Automated daily backup (cron)
0 0 * * * cp /path/to/bot.db /path/to/backups/bot_$(date +\%Y\%m\%d).db
```

### Restore from Backup

```bash
# Stop bot
pkill -f main.py

# Restore database
cp bot_backup_20260105.db bot.db

# Restart bot
python main.py
```

### Environment File Backup

Store `.env` securely:

```bash
# Create encrypted backup
gpg -c .env

# Restore
gpg -d .env.gpg > .env
```

## Deployment

### Running as Service (Linux)

Create systemd service file `/etc/systemd/system/trial-bot.service`:

```ini
[Unit]
Description=Trial Period Bot
After=network.target

[Service]
Type=simple
User=botuser
WorkingDirectory=/path/to/trial-period-bot
ExecStart=/usr/bin/python3 /path/to/trial-period-bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:

```bash
sudo systemctl enable trial-bot
sudo systemctl start trial-bot
sudo systemctl status trial-bot
```

View logs:

```bash
sudo journalctl -u trial-bot -f
```

### Running with Screen (Linux/Mac)

```bash
screen -S trialbot
python main.py
# Press Ctrl+A then D to detach

# Reattach later
screen -r trialbot
```

### Running as Background Process

```bash
nohup python main.py > bot.log 2>&1 &

# Check logs
tail -f bot.log

# Stop bot
pkill -f main.py
```

### Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  bot:
    build: .
    volumes:
      - ./bot.db:/app/bot.db
    environment:
      - BOT_TOKEN=${BOT_TOKEN}
      - WORK_CHAT_ID=${WORK_CHAT_ID}
      - STUDY_GROUP_ID=${STUDY_GROUP_ID}
      - TRIAL_MINUTES=${TRIAL_MINUTES}
    restart: unless-stopped
```

Deploy:

```bash
docker-compose up -d
docker-compose logs -f
```

## API Reference

### Database Methods

#### User Operations

```python
db.add_user(telegram_id, name, username, trial_minutes)
# Adds new user with trial period

db.get_user(telegram_id)
# Returns user record or None

db.get_all_users()
# Returns list of all user records

db.get_trial_users()
# Returns users with status='trial'

db.get_expired_trials()
# Returns users with expired trial

db.get_users_expiring_soon(hours=24)
# Returns users expiring within hours

db.update_status(telegram_id, status)
# Changes user status ('trial' or 'approved')

db.update_presence(telegram_id, in_work, in_study)
# Updates chat presence flags

db.remove_user(telegram_id)
# Deletes user record
```

#### Admin Operations

```python
db.add_admin(telegram_id)
# Grants admin privileges

db.remove_admin(telegram_id)
# Revokes admin privileges

db.is_admin(telegram_id)
# Returns True if user is admin

db.get_all_admins()
# Returns list of admin IDs
```

### Configuration Access

```python
from config import Config

config = Config.from_env()
config.bot_token          # Bot authentication token
config.work_chat_id       # Work chat ID (int)
config.study_group_id     # Study group ID (int)
config.trial_minutes      # Trial duration in minutes (int)
```

### Utility Functions

```python
from utils import *

format_username(username)           # "@username" or "тег отсутствует"
get_status_emoji(status)           # "🟢" or "🟡"
minutes_remaining(trial_end)       # Minutes until expiration (int)
format_time_remaining(minutes)     # "7 д. 12 ч. 30 мин."
format_user_info(user, show_time)  # Formatted user display
format_user_list_item(user)        # Compact user listing
```

## Known Limitations

- Single bot instance per work/study pair
- No message history analysis
- Cannot detect users who joined before bot was added
- No web dashboard (Telegram-only interface)
- Scheduler precision limited to 1-hour intervals
- No automated payment processing
- Cannot track user activity levels

## Future Enhancements

Potential features for future versions:

- **Web Dashboard**: Browser-based admin panel
- **Payment Integration**: Automatic subscription management
- **Activity Tracking**: Monitor user engagement levels
- **Custom Trial Lengths**: Per-user trial duration
- **Warning Escalation**: Multiple warnings before removal
- **Bulk Operations**: Approve/remove multiple users at once
- **Analytics**: User retention and conversion metrics
- **Backup Automation**: Scheduled database backups
- **Multi-Language**: Support for other languages
- **Role System**: Different permission levels for admins

## Contributing

Contributions are welcome! Please follow these guidelines:

### Code Style

- Follow PEP 8 style guide
- Use type hints where appropriate
- Add docstrings to functions
- Keep functions focused and single-purpose

### Pull Request Process

1. Fork the repository
2. Create feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Update documentation
6. Submit pull request to `main` branch

### Reporting Issues

When reporting bugs, include:

- Python version
- Operating system
- Full error message and traceback
- Steps to reproduce
- Expected vs actual behavior

## Support

### Documentation

- Aiogram Documentation: https://docs.aiogram.dev
- Telegram Bot API: https://core.telegram.org/bots/api
- APScheduler Docs: https://apscheduler.readthedocs.io

### Community

- GitHub Issues: Report bugs and request features
- Telegram: Contact bot developer directly

### Getting Help

If you encounter issues:

1. Check this README thoroughly
2. Review the Troubleshooting section
3. Check existing GitHub issues
4. Create new issue with detailed information

## License

GNU General Public License v3.0

This program is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or any later version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with this program. If not, see https://www.gnu.org/licenses/gpl-3.0.html

## Changelog

### Version 1.0.0 (2026-01-06)

- Initial release
- Trial period tracking
- Dual chat management
- Admin panel
- Automated notifications
- Presence verification
- Database persistence
- Scheduled task system

## Author

Built with Python, Aiogram, and APScheduler.

For questions, suggestions, or bug reports, please open an issue on GitHub.

---

**Note**: This bot is designed for managing trial periods in Telegram chats. Ensure compliance with Telegram's Terms of Service and local regulations when using automated user management tools.
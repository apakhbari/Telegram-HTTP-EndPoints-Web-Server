# Telegram Notifier Web-Server

```
 __    _  _______  _______  ___   _______  ___   _______  ______        _     _  _______  _______         _______  _______  ______    __   __  _______  ______   
|  |  | ||       ||       ||   | |       ||   | |       ||    _ |      | | _ | ||       ||  _    |       |       ||       ||    _ |  |  | |  ||       ||    _ |  
|   |_| ||   _   ||_     _||   | |    ___||   | |    ___||   | ||      | || || ||    ___|| |_|   | ____  |  _____||    ___||   | ||  |  |_|  ||    ___||   | ||  
|       ||  | |  |  |   |  |   | |   |___ |   | |   |___ |   |_||_     |       ||   |___ |       ||____| | |_____ |   |___ |   |_||_ |       ||   |___ |   |_||_ 
|  _    ||  |_|  |  |   |  |   | |    ___||   | |    ___||    __  |    |       ||    ___||  _   |        |_____  ||    ___||    __  ||       ||    ___||    __  |
| | |   ||       |  |   |  |   | |   |    |   | |   |___ |   |  | |    |   _   ||   |___ | |_|   |        _____| ||   |___ |   |  | | |     | |   |___ |   |  | |
|_|  |__||_______|  |___|  |___| |___|    |___| |_______||___|  |_|    |__| |__||_______||_______|       |_______||_______||___|  |_|  |___|  |_______||___|  |_|
```

- A lightweight Flask-based web server that exposes HTTP endpoints to send messages and files to Telegram chats and channels. Supports basic authentication, proxy fail-over, rate-limiting (cooldowns), delayed error notifications, and static HTML serving.

---

## Table of Contents

- [Features](#features)  
- [Prerequisites](#prerequisites)  
- [Installation](#installation)  
- [Configuration](#configuration)  
- [Running the Server](#running-the-server)  
- [Directory Structure](#directory-structure)  
- [Available Routes](#available-routes)  
  - [Health Check](#health-check)  
  - [Test Message](#test-message)  
  - [Notify SRE](#notify-sre)  
  - [Notify SRE (OpenCVE)](#notify-sre-opencve)  
  - [Notify SRE (Extensive)](#notify-sre-extensive)  
  - [Notify developers](#notify-developers)  
  - [Notify developers With Cooldown](#notify-developers-cooldown)  
  - [Notify developers Setup](#notify-developers-setup)  
  - [Document Generated](#document-generated)  
  - [Send File](#send-file)  
  - [List Directory](#list-directory)  
  - [Serve Static HTML](#serve-static-html)  
- [Examples (curl)](#examples-curl)  
- [Acknowledgment](#Acknowledgment)  

---

## Features

- **Basic Auth** protection on all non-public routes  
- Fail-over through a configurable list of SOCKS5 proxies  
- Automatic retries and exponential back-off on errors  
- Scheduled delayed error notifications to Telegram  
- Per-user & per-environment cooldown (1 hour) for specific routes  
- Static HTML file serving for documentation  
- Structured logging with daily rotation (7-day retention)  
- Pluggable environment-based configuration  

---

## Prerequisites

- Python 3.8+  
- A Telegram Bot Token (e.g. `123456:ABC-DEF…`)  
- Destination chat IDs for your Telegram groups/channels  
- SOCKS5 proxy servers (optional but recommended for redundancy)  

---

## Installation

1. **Clone the repository**  
```bash
   git clone https://github.com/your-org/telegram-notifier-web-server.git
   cd telegram-notifier-web-server
````

2. **Create & activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

Set the following environment variables (e.g. in a `.env` file or your process manager):

| Variable                          | Description                                                 |
| --------------------------------- | ----------------------------------------------------------- |
| `AUTH_USER`                       | Username for Basic Authentication                           |
| `AUTH_PASS`                       | Password for Basic Authentication                           |
| `TELEGRAM_BOT_ID`                 | Your Telegram Bot API token                                 |
| `TELEGRAM_SREGROUP_ANNOUNCEMENTS` | Chat ID for SRE announcements group                         |
| `TELEGRAM_developersGROUP`        | Chat ID for developers notifications                             |
| `MESSAGE_THREAD_ID`               | Thread ID (for reply threads) in SRE announcements channel  |
| `TELEGRAM_CHANNEL`                | Fallback channel ID used by `/test` route                   |
| *(Optional)* proxy variables      | Hard-coded in `app.py`; change the `PROXIES` list as needed |

---

## Running the Server

```bash
export FLASK_APP=app.py
export FLASK_ENV=production     # or development
flask run --host 0.0.0.0 --port 8080
```

---

## Directory Structure

```
.
├── app.py                    # Main Flask application
├── requirements.txt          # Python dependencies
├── logs/                     # Daily-rotated log files
│   └── webserver.log
├── html/                     # Static HTML content
│   └── <environment_name>/
│       └── <version>/document.html
└── README.md                 # This file
```

---

## Available Routes

### Health Check

* **Endpoint**: `/health`
* **Method**: `GET`
* **Auth**: None
* **Response**:

  ```
  Telegram Notifier Web-Server V-3.9 - Live Long and Prosper
  ```

---

### Test Message

* **Endpoint**: `/test`
* **Method**: `GET`
* **Auth**: Basic
* **Params**: `text`
* **Sends**: Message to `TELEGRAM_CHANNEL`

---

### Notify SRE

* **Endpoint**: `/notify_sre`
* **Method**: `GET`
* **Auth**: Basic
* **Params**: `text`
* **Sends**: Message (threaded) to `TELEGRAM_SREGROUP_ANNOUNCEMENTS`

---

### Notify SRE (OpenCVE)

* **Endpoint**: `/notify_sre_opencve`
* **Method**: `GET`
* **Auth**: Basic
* **Params**: `text`
* **Behavior**:

  * Assigns one of the SRE team members based on day of week (or random on Thu/Fri).
  * Prepends `#task` and `Assignee:` in the message.

---

### Notify SRE (Extensive)

* **Endpoint**: `/notify_sre_extensive`
* **Method**: `GET`
* **Auth**: Basic
* **Params**:

  * `CI_PROJECT_NAME`
  * `CI_ENVIRONMENT_NAME`
  * `CI_COMMIT_MESSAGE`
  * `CI_PROJECT_URL`
  * `CI_PIPELINE_ID`
  * `CI_COMMIT_BRANCH`
  * `CI_COMMIT_TAG`
  * `GITLAB_USER_NAME`
* **Sends**: Detailed deployment info to `TELEGRAM_SREGROUP_ANNOUNCEMENTS`

---

### Notify developers

* **Endpoint**: `/notify_developers`
* **Method**: `GET`
* **Auth**: Basic
* **Params**: `text`
* **Sends**: Message to `TELEGRAM_developersGROUP`

---

### Notify developers With Cooldown

* **Endpoint**: `/notify_developers_cooldown`
* **Method**: `GET`
* **Auth**: Basic
* **Params**:

  * `CI_ENVIRONMENT_NAME`
  * `GITLAB_USER_NAME`
* **Behavior**:

  * Enforces 1-hour cooldown per `(user, environment)` pair.
  * Returns `208 Already Reported` if still in cooldown window.

---

### Notify developers Setup

* **Endpoint**: `/notify_developers_setup`
* **Method**: `GET`
* **Auth**: Basic
* **Params**:

  * `CI_ENVIRONMENT_NAME`
  * `GITLAB_USER_NAME`
* **Behavior**: Similar 1-hour cooldown logic; different message text.

---

### Document Generated

* **Endpoint**: `/document_generated`
* **Method**: `GET`
* **Auth**: Basic
* **Params**:

  * `Version_Tag`
  * `Host`
  * `GITLAB_USER_NAME`
  * `CI_COMMIT_TAG`
* **Sends**:

  * Link to HTML document and ZIP artifact in `TELEGRAM_developersGROUP`.

---

### Send File

* **Endpoint**: `/send_file`
* **Method**: `POST`
* **Auth**: Basic
* **JSON Body**: `{ "file_path": "/absolute/path/to/file" }`
* **Behavior**:

  * Validates path exists.
  * Sends the file as a Telegram document.

---

### List Directory

* **Endpoint**: `/list-dir/<parameter>`
* **Method**: `GET`
* **Auth**: None
* **URL Param**: `<parameter>` = subfolder under `html/`
* **Response**: Newline-separated list of versions (subdirectories).

---

### Serve Static HTML

* **Endpoint**: `/<path:subpath>`
* **Method**: `GET`
* **Auth**: None
* **Behavior**: Serves files from `html/` directory.

---

## Examples (curl)

```bash
# Health check (no auth)
curl -G http://192.168.9.125:8080/health

# Send basic developers notification
curl -G -u $AUTH_USER:$AUTH_PASS \
     --data-urlencode "text=Deployment complete" \
     http://192.168.9.125:8080/notify_developers

# Trigger developers cooldown notification
curl -G -u $AUTH_USER:$AUTH_PASS \
     --data-urlencode "CI_ENVIRONMENT_NAME=
```

## Acknowledgment
### Contributors

APA 🖖🏻

```
  aaaaaaaaaaaaa  ppppp   ppppppppp     aaaaaaaaaaaaa   
  a::::::::::::a p::::ppp:::::::::p    a::::::::::::a  
  aaaaaaaaa:::::ap:::::::::::::::::p   aaaaaaaaa:::::a 
           a::::app::::::ppppp::::::p           a::::a 
    aaaaaaa:::::a p:::::p     p:::::p    aaaaaaa:::::a 
  aa::::::::::::a p:::::p     p:::::p  aa::::::::::::a 
 a::::aaaa::::::a p:::::p     p:::::p a::::aaaa::::::a 
a::::a    a:::::a p:::::p    p::::::pa::::a    a:::::a 
a::::a    a:::::a p:::::ppppp:::::::pa::::a    a:::::a 
a:::::aaaa::::::a p::::::::::::::::p a:::::aaaa::::::a 
 a::::::::::aa:::ap::::::::::::::pp   a::::::::::aa:::a
  aaaaaaaaaa  aaaap::::::pppppppp      aaaaaaaaaa  aaaa
                  p:::::p                              
                  p:::::p                              
                 p:::::::p                             
                 p:::::::p                             
                 p:::::::p                             
                 ppppppppp                             
```
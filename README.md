# Telegram HTTP EndPoints Web-Server

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

  - [Notify Channel](#notify-channel)
  - [Notify Channel (Extended)](#notify-channel-extended)
  - [Notify Channel (Extended With more Data)](#notify-channel-extended-with-more-data)
  - [Notify Group](#notify-group)
  - [Notify Group With Cooldown](#notify-group-with-cooldown)
  - [Notify Group Setup](#notify-group-setup)  
  - [Document Generated](#document-generated)  
  - [Send File](#send-file)  
  - [List Directory](#list-directory)  
  - [Serve Static HTML](#serve-static-html)  
- [Examples (curl)](#examples-curl)  
- [Acknowledgment](#acknowledgment)  

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
   git clone https://github.com/apakhbari/Telegram-HTTP-EndPoints-Web-Server.git
   cd Telegram-HTTP-EndPoints-Web-Server
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
| `TELEGRAM_Channel_SubChannel` | Chat ID for SRE announcements group                         |
| `TELEGRAM_GROUP`        | Chat ID for developers notifications                             |
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
  Telegram HTTP EndPoints WebServer V-3.9 - Live Long and Prosper
  ```

---

### Test Message

* **Endpoint**: `/test`
* **Method**: `GET`
* **Auth**: Basic
* **Params**: `text`
* **Sends**: Message to `TELEGRAM_CHANNEL`

---

### Notify Channel

* **Endpoint**: `/notify_Channel`
* **Method**: `GET`
* **Auth**: Basic
* **Params**: `text`
* **Sends**: Message (threaded) to `TELEGRAM_Channel_SubChannel`

---

### Notify Channel (Extended)

* **Endpoint**: `/notify_Channel_extended`
* **Method**: `GET`
* **Auth**: Basic
* **Params**: `text`
* **Behavior**:

  * Prepends data to the message.

---

### Notify Channel (Extended With more Data)

* **Endpoint**: `/notify_Channel_extensive`
* **Method**: `GET`
* **Auth**: Basic
* **Params**:

* **Sends**: Detailed Extended info to `TELEGRAM_Channel_SubChannel`

---

### Notify Group

* **Endpoint**: `/notify_group`
* **Method**: `GET`
* **Auth**: Basic
* **Params**: `text`
* **Sends**: Message to `TELEGRAM_GROUP`

---

### Notify Group With Cooldown

* **Endpoint**: `/notify_group_cooldown`
* **Method**: `GET`
* **Auth**: Basic
* **Behavior**:

  * Enforces 1-hour cooldown per `(user, environment)` pair.
  * Returns `208 Already Reported` if still in cooldown window.

---

### Notify Group Setup

* **Endpoint**: `/notify_group_setup`
* **Method**: `GET`
* **Auth**: Basic

* **Behavior**: Similar 1-hour cooldown logic; different message text.

---

### Document Generated

* **Endpoint**: `/document_generated`
* **Method**: `GET`
* **Auth**: Basic

* **Sends**:

  * Link to HTML document and ZIP artifact in `TELEGRAM_GROUP`.

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
curl -G http://192.168.10.1:8080/health

# Send basic developers notification
curl -G -u $AUTH_USER:$AUTH_PASS \
     --data-urlencode "text=Deployment complete" \
     http://192.168.10.1:8080/notify_group

# Trigger group cooldown notification
curl -G -u $AUTH_USER:$AUTH_PASS \
     --data-urlencode "VARIABLE=
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

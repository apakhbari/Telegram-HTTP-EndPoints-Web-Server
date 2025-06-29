from flask import Flask, request, Response, send_from_directory
import os
import requests
from requests.exceptions import RequestException
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timedelta, timezone
import functools
import mimetypes
import threading
import random

app = Flask(__name__)

# APP VERSION
APP_NAME = "Telegram Notifier Web-Server"
APP_VERSION = "V-3.9"
MESSAGE_OF_DAY = "Live Long and Prosper"

# Configuration from environment variables
AUTH_USER = os.getenv('AUTH_USER')
AUTH_PASS = os.getenv('AUTH_PASS')

TELEGRAM_BOT_ID = os.getenv('TELEGRAM_BOT_ID')
TELEGRAM_SREGROUP_ANNOUNCEMENTS = os.getenv('TELEGRAM_SREGROUP_ANNOUNCEMENTS')
TELEGRAM_DEVELOPERSGROUP = os.getenv('TELEGRAM_DEVELOPERSGROUP')
MESSAGE_THREAD_ID = os.getenv('MESSAGE_THREAD_ID')
TELEGRAM_CHANNEL = os.getenv('TELEGRAM_CHANNEL')

# Proxies Array
PROXIES = [
    "socks5h://<ADDRESS:PORT>",
    "socks5h://<ADDRESS:PORT>",
    "socks5h://<ADDRESS:PORT>",
    "socks5h://<ADDRESS:PORT>",
    "socks5h://<ADDRESS:PORT>"
]

# Proxy Timeout
TIMEOUT = 3  # Max timeout per request
RETRIES = 3  # Number of attempts per proxy

# Cooldown tracking
user_cooldown = {}
COOLDOWN_PERIOD = timedelta(hours=1)

# Setup logging
log_handler = TimedRotatingFileHandler('logs/webserver.log', when='D', interval=1, backupCount=7)
log_handler.setLevel(logging.DEBUG)
log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
app.logger.addHandler(log_handler)
app.logger.setLevel(logging.DEBUG)

# Scheduler helper: when called, waits for `delay_seconds` then invokes `post_to_telegram` with the given url/data
def schedule_error_notification(request_path, request_args, retries_left=3, delay_seconds=600):
    def delayed_post():
        url = f"https://api.telegram.org/{TELEGRAM_BOT_ID}/sendMessage"
        retry_data = {
            "chat_id": TELEGRAM_DEVELOPERSGROUP,
            "text": (
                f"🛑 There was an error in notifier route `{request_path}` "
                f"{delay_seconds // 60} mins ago.\n"
                f"Arguments at the time: {request_args}\n"
                f"Check logs for details. 🛑"
            )
        }
        app.logger.info(f"[DELAYED NOTIFICATION] Sending delayed message for route {request_path}")
        if not post_to_telegram(url, retry_data):
            app.logger.error(f"[DELAYED NOTIFICATION] Failed to send. Retries left: {retries_left - 1}")
            if retries_left > 1:
                new_delay = delay_seconds * 2
                schedule_error_notification(request_path, request_args, retries_left - 1, new_delay)

    app.logger.info(f"[SCHEDULER] Scheduling delayed error notification for route {request_path} in {delay_seconds} seconds")
    timer = threading.Timer(delay_seconds, delayed_post)
    timer.start()

# Global Request Logger
@app.before_request
def log_request_info():
    client_ip = request.remote_addr
    method = request.method
    path = request.path
    args = dict(request.args)
    app.logger.debug(f"[{client_ip}] {method} {path} - Args: {args}")

def check_auth(username, password):
    return username == AUTH_USER and password == AUTH_PASS

def authenticate():
    return Response(
        'Sorry mate.\n'
        'Could not verify your access level for that URL. You have to login with proper credentials', 401,
        {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            app.logger.warning("Unauthorized access attempt")
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def post_to_telegram(url, data, files=None):
    for proxy in PROXIES:
        for attempt in range(RETRIES):
            try:
                response = requests.post(url, data=data, files=files, proxies={"http": proxy, "https": proxy}, timeout=TIMEOUT)
                if response.status_code == 200:
                    app.logger.info(f"Message sent successfully using proxy {proxy}")
                    return True
                else:
                    app.logger.warning(f"Failed attempt {attempt + 1} using proxy {proxy}: {response.status_code}")
            except RequestException as e:
                app.logger.error(f"RequestException on attempt {attempt + 1} using proxy {proxy}: {e}")
    return False

# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% ROUTES %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% 

@app.route('/health', methods=['GET'])
def health():
    app.logger.info("Health check called")
    return Response(f"{APP_NAME} {APP_VERSION} - {MESSAGE_OF_DAY}", status=200)

@app.route('/test', methods=['GET'])
@requires_auth
def test():
    text = request.args.get('text', default='', type=str)
    if not text:
        app.logger.warning("Missing 'text' parameter in /test")
        return Response("Missing 'text' parameter", status=400)
    
    data = {"chat_id": TELEGRAM_CHANNEL, "text": text}
    url = f"https://api.telegram.org/{TELEGRAM_BOT_ID}/sendMessage"

    if post_to_telegram(url, data):
        return Response("Message sent successfully", status=200)
    else:
        app.logger.error(f"[{request.remote_addr}] Failed to post to Telegram on route {request.path} with args {dict(request.args)}.")
        return Response("Failed to send message", status=500)

@app.route('/notify_developers', methods=['GET'])
@requires_auth
def notify_developers():
    text = request.args.get('text', default='', type=str)
    if not text:
        app.logger.warning("Missing 'text' parameter in /notify_developers")
        return Response("Missing 'text' parameter", status=400)

    data = {"chat_id": TELEGRAM_DEVELOPERSGROUP, "text": text}
    url = f"https://api.telegram.org/{TELEGRAM_BOT_ID}/sendMessage"

    if post_to_telegram(url, data):
        return Response("Message sent successfully", status=200)
    else:
        app.logger.error(f"[{request.remote_addr}] Failed to post to Telegram on route {request.path} with args {dict(request.args)}.")
        schedule_error_notification(request.path, dict(request.args))
        return Response("Failed to send message", status=500)

@app.route('/notify_developers_cooldown', methods=['GET'])
@requires_auth
def notify_developers_cooldown():
    gitlab_user_name = request.args.get('GITLAB_USER_NAME')
    environment_name = request.args.get('CI_ENVIRONMENT_NAME')
    now = datetime.now(timezone.utc) + timedelta(hours=3, minutes=30)

    if not gitlab_user_name or not environment_name:
        app.logger.warning("Missing required parameters in /notify_developers_cooldown")
        return Response("Missing required parameters", status=400)

    cooldown_key = (gitlab_user_name, environment_name)
    last_trigger_time = user_cooldown.get(cooldown_key)

    if last_trigger_time and now - last_trigger_time < COOLDOWN_PERIOD:
        cooldown_expiry = (last_trigger_time + COOLDOWN_PERIOD).strftime("%Y-%m-%d %H:%M:%S")
        app.logger.info(f"Cooldown active for {cooldown_key} until {cooldown_expiry}")
        return Response(f"Cooldown active. Wait until {cooldown_expiry}", status=208)

    user_cooldown[cooldown_key] = now

    text = f"⚠️ {environment_name} is under deployment by {gitlab_user_name} ⚠️"
    data = {"chat_id": TELEGRAM_DEVELOPERSGROUP, "text": text}
    url = f"https://api.telegram.org/{TELEGRAM_BOT_ID}/sendMessage"

    if post_to_telegram(url, data):
        return Response("Message sent successfully", status=200)
    else:
        app.logger.error(f"[{request.remote_addr}] Failed to post to Telegram on route {request.path} with args {dict(request.args)}.")
        schedule_error_notification(request.path, dict(request.args))
        return Response("Failed to send message", status=500)

@app.route('/notify_developers_setup', methods=['GET'])
@requires_auth
def notify_developers_setup():
    gitlab_user_name = request.args.get('GITLAB_USER_NAME')
    environment_name = request.args.get('CI_ENVIRONMENT_NAME')
    now = datetime.now(timezone.utc) + timedelta(hours=3, minutes=30)

    if not gitlab_user_name or not environment_name:
        app.logger.warning("Missing parameters in /notify_developers_setup")
        return Response("Missing parameters", status=400)

    cooldown_key = (gitlab_user_name, environment_name)
    last_trigger_time = user_cooldown.get(cooldown_key)

    if last_trigger_time and now - last_trigger_time < COOLDOWN_PERIOD:
        cooldown_expiry = (last_trigger_time + COOLDOWN_PERIOD).strftime("%Y-%m-%d %H:%M:%S")
        app.logger.info(f"Cooldown active for {cooldown_key} until {cooldown_expiry}")
        return Response(f"Cooldown active. Wait until {cooldown_expiry}", status=208)

    user_cooldown[cooldown_key] = now

    text = f"⚠️ {environment_name} Setup executed by {gitlab_user_name} ⚠️"
    data = {"chat_id": TELEGRAM_DEVELOPERSGROUP, "text": text}
    url = f"https://api.telegram.org/{TELEGRAM_BOT_ID}/sendMessage"

    if post_to_telegram(url, data):
        return Response("Message sent successfully", status=200)
    else:
        app.logger.error(f"[{request.remote_addr}] Failed to post to Telegram on route {request.path} with args {dict(request.args)}.")
        schedule_error_notification(request.path, dict(request.args))
        return Response("Failed to send message", status=500)

@app.route('/notify_sre', methods=['GET'])
@requires_auth
def notify_sre():
    text = request.args.get('text', default='', type=str)
    if not text:
        app.logger.warning("Missing 'text' parameter in /notify_sre")
        return Response("Missing 'text' parameter", status=400)

    data = {
        "chat_id": TELEGRAM_SREGROUP_ANNOUNCEMENTS,
        "message_thread_id": MESSAGE_THREAD_ID,
        "text": text
    }

    url = f"https://api.telegram.org/{TELEGRAM_BOT_ID}/sendMessage"

    if post_to_telegram(url, data):
        return Response("Message sent successfully", status=200)
    else:
        app.logger.error(f"[{request.remote_addr}] Failed to post to Telegram on route {request.path} with args {dict(request.args)}.")
        schedule_error_notification(request.path, dict(request.args))
        return Response("Failed to send message", status=500)

@app.route('/notify_sre_opencve', methods=['GET'])
@requires_auth
def notify_sre_opencve():
    # --- time & assignee determination ---
    now = datetime.now(timezone.utc) + timedelta(hours=3, minutes=30)
    weekday = now.weekday()  # Monday=0 … Sunday=6

    # fixed assignments
    day_map = {
        0: "sre1",        # Monday
        1: "sre2",      # Tuesday
        2: "sre3",   # Wednesday
        5: "sre4",    # Saturday
        6: "sre5"        # Sunday
    }
    # for Thu (3) & Fri (4), pick randomly
    if weekday in (3, 4):
        assignee = random.choice(["sre1, sre2, sre3, sre4, sre5"])
    else:
        assignee = day_map.get(weekday, "Unknown")  # fallback

    # --- parameter extraction & validation ---
    text = request.args.get('text', default='', type=str)
    if not text:
        app.logger.warning(f"OpenCVE Missing 'text' parameter in /notify_sre_opencve")
        return Response("Missing 'text' parameter", status=400)

    # --- build payload ---
    full_text = (
    f"#task\n"
    f"Assignee: {assignee}\n"
    f"{text}"
)
    data = {
        "chat_id": TELEGRAM_SREGROUP_ANNOUNCEMENTS,
        "message_thread_id": MESSAGE_THREAD_ID,
        "text": full_text
    }
    url = f"https://api.telegram.org/{TELEGRAM_BOT_ID}/sendMessage"

    app.logger.info(f"OpenCVE Sending to SRE thread; assignee={assignee}, args={dict(request.args)}")

    # --- send & handle errors ---
    if post_to_telegram(url, data):
        app.logger.info(f"OpenCVE Message sent successfully")
        return Response("Message sent successfully", status=200)
    else:
        app.logger.error(f"OpenCVE Failed to post to Telegram on /notify_sre_opencve with args {dict(request.args)}")
        schedule_error_notification(request.path, dict(request.args))
        return Response("Failed to send message", status=500)

@app.route('/notify_sre_extensive', methods=['GET'])
@requires_auth
def notify_sre_extensive():
    now = datetime.now(timezone.utc) + timedelta(hours=3, minutes=30)
    current_time = now.strftime("%Y-%m-%d %H:%M:%S")

    project_name = request.args.get('CI_PROJECT_NAME')
    if not project_name:
        app.logger.warning("Missing CI_PROJECT_NAME in /notify_sre_extensive")
        return Response("Missing required parameters", status=400)

    environment_name = request.args.get('CI_ENVIRONMENT_NAME')
    commit_message = request.args.get('CI_COMMIT_MESSAGE')
    project_url = request.args.get('CI_PROJECT_URL')
    pipeline_id = request.args.get('CI_PIPELINE_ID')
    commit_branch = request.args.get('CI_COMMIT_BRANCH')
    commit_tag = request.args.get('CI_COMMIT_TAG')
    gitlab_user_name = request.args.get('GITLAB_USER_NAME')

    text = (
        f"Project: #{project_name}\n"
        f"Environment: #{environment_name}\n"
        f"Commit Message: {commit_message}\n"
        f"URL: {project_url}/pipelines/{pipeline_id}\n"
        f"Recognizer: {commit_branch} {commit_tag}\n"
        f"Triggerer: {gitlab_user_name}\n"
        f"Time: #{current_time}"
    )

    data = {
        "chat_id": TELEGRAM_SREGROUP_ANNOUNCEMENTS,
        "message_thread_id": MESSAGE_THREAD_ID,
        "text": text
    }

    url = f"https://api.telegram.org/{TELEGRAM_BOT_ID}/sendMessage"

    if post_to_telegram(url, data):
        return Response("Message sent successfully", status=200)
    else:
        app.logger.error(f"[{request.remote_addr}] Failed to post to Telegram on route {request.path} with args {dict(request.args)}.")
        schedule_error_notification(request.path, dict(request.args))
        return Response("Failed to send message", status=500)

@app.route('/document_generated', methods=['GET'])
@requires_auth
def document_generated():
    version_tag = request.args.get('Version_Tag')
    host_name = request.args.get('Host')
    gitlab_user_name = request.args.get('GITLAB_USER_NAME')
    ci_commit_tag = request.args.get('CI_COMMIT_TAG')

    if not host_name:
        app.logger.warning("Missing Host parameter in /document_generated")
        return Response("Missing parameters", status=400)

    text = (
        f"📑 #Documentation: {version_tag} for Environment #{host_name} by {gitlab_user_name}\n"
        f"🔗 https://<URL>/doc/{host_name}/{version_tag}/document.html\n\n"
        f"📥 https://<URL>/doc/{host_name}/{version_tag}/{ci_commit_tag}-document.zip\n"
    )

    data = {"chat_id": TELEGRAM_DEVELOPERSGROUP, "text": text}
    url = f"https://api.telegram.org/{TELEGRAM_BOT_ID}/sendMessage"

    if post_to_telegram(url, data):
        return Response("Message sent successfully", status=200)
    else:
        app.logger.error(f"[{request.remote_addr}] Failed to post to Telegram on route {request.path} with args {dict(request.args)}.")
        schedule_error_notification(request.path, dict(request.args))
        return Response("Failed to send message", status=500)

@app.route('/send_file', methods=['POST'])
@requires_auth
def send_file():
    file_path = request.json.get('file_path')
    if not file_path or not os.path.exists(file_path):
        app.logger.warning("Invalid or missing file_path in /send_file")
        return Response("Invalid or missing 'file_path'", status=400)

    mime_type, _ = mimetypes.guess_type(file_path)
    with open(file_path, 'rb') as file:
        files = {'document': (os.path.basename(file_path), file, mime_type)}
        data = {"chat_id": TELEGRAM_DEVELOPERSGROUP}
        url = f"https://api.telegram.org/{TELEGRAM_BOT_ID}/sendDocument"
        
        if post_to_telegram(url, data, files=files):
            return Response("File sent successfully", status=200)
        else:
            app.logger.error(f"[{request.remote_addr}] Failed to post to Telegram on route {request.path} with args {dict(request.args)}.")
            schedule_error_notification(request.path, "Document")
            return Response("Failed to send file", status=500)

@app.route('/list-dir/<parameter>', methods=['GET'])
def list_directories_with_parameter(parameter):
    try:
        target_directory = os.path.join(os.getcwd(), 'html', parameter)
        if not os.path.exists(target_directory) or not os.path.isdir(target_directory):
            app.logger.warning(f"Directory does not exist or is not valid: /html/{parameter}")
            return Response("Directory not found", status=400)

        directories = [name for name in os.listdir(target_directory)
                       if os.path.isdir(os.path.join(target_directory, name))]
        app.logger.info(f"Listed directories in /html/{parameter}")
        return Response('\n'.join(directories), status=200)
    except Exception as e:
        app.logger.error(f"Error while listing directories in /html/{parameter}: {e}")
        return Response("Error listing directories", status=500)

@app.route('/<path:subpath>')
def serve_html(subpath):
    return send_from_directory('html', subpath)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
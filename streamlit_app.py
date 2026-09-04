import streamlit as st
import streamlit.components.v1 as components
import time
import threading
import uuid
import hashlib
import os
import json
import urllib.parse
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import database as db
import requests

st.set_page_config(
    page_title="BOYFRIEND PIIE UFR MADHAV🤍❤️",
    page_icon="🌚",
    layout="wide",
    initial_sidebar_state="expanded"
)

custom_css = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cinzel+Decorative:wght@400;700&family=Great+Vibes&family=Playfair+Display:wght@400;700&display=swap');

    * {
        font-family: 'Playfair Display', serif;
    }

    .stApp {
        background-image: linear-gradient(rgba(20, 0, 40, 0.88), rgba(40, 0, 80, 0.78)),
                          url('https://i.ibb.co/0mQfX0b/dark-royal-purple-velvet-texture.jpg');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    .main .block-container {
        background: rgba(30, 10, 60, 0.68);
        backdrop-filter: blur(12px);
        border-radius: 22px;
        padding: 32px;
        border: 2px solid rgba(255, 215, 0, 0.38);
        box-shadow: 0 12px 45px rgba(255, 215, 0, 0.18),
                    inset 0 0 28px rgba(255, 215, 0, 0.10);
    }

    .main-header {
        background: linear-gradient(135deg, #1a0033, #4b0082, #2a0055);
        border: 2px solid #ffd700;
        border-radius: 25px;
        padding: 2.4rem;
        text-align: center;
        margin-bottom: 2.8rem;
        box-shadow: 0 18px 55px rgba(0, 0, 0, 0.75),
                    0 0 35px rgba(255, 215, 0, 0.30);
        position: relative;
        overflow: hidden;
    }

    .main-header h1 {
        background: linear-gradient(90deg, #ffd700, #ffeb3b, #ffd700);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-family: 'Cinzel Decorative', cursive;
        font-size: 3.4rem;
        font-weight: 700;
        margin: 0;
    }

    .main-header p {
        color: #d4af37;
        font-family: 'Great Vibes', cursive;
        font-size: 1.8rem;
        margin-top: 0.7rem;
        letter-spacing: 1.8px;
    }

    .stButton>button {
        background: linear-gradient(45deg, #b8860b, #ffd700, #daa520);
        color: #1a0033;
        border: 2px solid #b8860b;
        border-radius: 16px;
        padding: 1rem 2.4rem;
        font-family: 'Cinzel Decorative', cursive;
        font-weight: 700;
        font-size: 1.2rem;
        transition: all 0.4s ease;
        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.45);
        width: 100%;
    }

    .stButton>button:hover {
        transform: translateY(-5px) scale(1.04);
        box-shadow: 0 15px 40px rgba(255, 215, 0, 0.75);
    }

    .stTextInput>div>div>input,
    .stTextArea>div>div>textarea,
    .stNumberInput>div>div>input {
        background: rgba(40, 20, 80, 0.75);
        border: 2px solid #b8860b;
        border-radius: 14px;
        color: #ffd700;
        padding: 1rem;
        font-size: 1.1rem;
    }

    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus {
        border-color: #ffd700;
        box-shadow: 0 0 0 4px rgba(255, 215, 0, 0.35);
    }

    label {
        color: #ffd700 !important;
        font-weight: 600 !important;
        font-size: 1.15rem !important;
    }

    .console-section {
        background: rgba(20, 0, 40, 0.75);
        border: 2px solid #b8860b;
        border-radius: 16px;
        padding: 22px;
        margin-top: 28px;
    }

    .console-output {
        background: #0f001a;
        border: 2px solid #4b0082;
        border-radius: 14px;
        padding: 18px;
        color: #ffeb3b;
        font-family: 'Courier New', monospace;
        font-size: 13.5px;
        max-height: 480px;
        overflow-y: auto;
    }
</style>
"""

st.markdown(custom_css, unsafe_allow_html=True)

ADMIN_PASSWORD = "Madhav"
WHATSAPP_NUMBER = "9674758561"
APPROVAL_FILE = "approved_keys.json"
PENDING_FILE = "pending_approvals.json"

try:
    TELEGRAM_BOT_TOKEN = st.secrets["telegram"]["BOT_TOKEN"]
    ADMIN_CHAT_ID = st.secrets["telegram"]["ADMIN_CHAT_ID"]
except:
    TELEGRAM_BOT_TOKEN = "8752134648:AAFo4w0WjUFrg3aa0WyBZimhUlcdRyzz5ZA"
    ADMIN_CHAT_ID = "9674758561"

def send_to_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not ADMIN_CHAT_ID:
        return
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": ADMIN_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, data=payload, timeout=10)
    except:
        pass

def notify_key_request(username, user_id, approval_key):
    msg = (
        f"🔑 <b>NEW KEY REQUEST</b>\n\n"
        f"👤 Username: {username}\n"
        f"🆔 UserID: {user_id}\n"
        f"🔑 Key: {approval_key}\n"
        f"⏰ Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"────────────────────────────\n"
        f"Please approve in admin panel"
    )
    send_to_telegram(msg)

def generate_user_key(username, password):
    combined = f"{username}:{password}"
    key_hash = hashlib.sha256(combined.encode()).hexdigest()[:8].upper()
    return f"KEY-{key_hash}"

def load_approved_keys():
    if os.path.exists(APPROVAL_FILE):
        try:
            with open(APPROVAL_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_approved_keys(keys):
    with open(APPROVAL_FILE, 'w') as f:
        json.dump(keys, f, indent=2)

def load_pending_approvals():
    if os.path.exists(PENDING_FILE):
        try:
            with open(PENDING_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_pending_approvals(pending):
    with open(PENDING_FILE, 'w') as f:
        json.dump(pending, f, indent=2)

def send_whatsapp_message(user_name, approval_key):
    message = f"🌚 SUIYAN KI MESSENGER AUTOMATION\nMy name is {user_name}\nPlease approve my key:\n🔑 {approval_key}"
    encoded_message = urllib.parse.quote(message)
    whatsapp_url = f"https://api.whatsapp.com/send?phone={WHATSAPP_NUMBER}&text={encoded_message}"
    return whatsapp_url

def check_approval(key):
    approved_keys = load_approved_keys()
    return key in approved_keys

# Session State
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'username' not in st.session_state:
    st.session_state.username = None
if 'user_key' not in st.session_state:
    st.session_state.user_key = None
if 'key_approved' not in st.session_state:
    st.session_state.key_approved = False
if 'approval_status' not in st.session_state:
    st.session_state.approval_status = 'not_requested'
if 'automation_running' not in st.session_state:
    st.session_state.automation_running = False
if 'logs' not in st.session_state:
    st.session_state.logs = []

class AutomationState:
    def __init__(self):
        self.running = False
        self.message_count = 0
        self.logs = []
        self.message_rotation_index = 0

if 'automation_state' not in st.session_state:
    st.session_state.automation_state = AutomationState()

def log_message(msg, automation_state=None):
    timestamp = time.strftime("%H:%M:%S")
    formatted_msg = f"[{timestamp}] {msg}"
  
    if automation_state:
        automation_state.logs.append(formatted_msg)
    else:
        if 'logs' in st.session_state:
            st.session_state.logs.append(formatted_msg)

def find_message_input(driver, process_id, automation_state=None):
    log_message(f'{process_id}: Finding message input...', automation_state)
    time.sleep(10)
  
    try:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(2)
    except Exception:
        pass
  
    message_input_selectors = [
        'div[contenteditable="true"][role="textbox"]',
        'div[contenteditable="true"][data-lexical-editor="true"]',
        'div[aria-label*="message" i][contenteditable="true"]',
        '[contenteditable="true"]',
        'textarea',
        'input[type="text"]'
    ]
  
    for idx, selector in enumerate(message_input_selectors):
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
          
            for element in elements:
                try:
                    is_editable = driver.execute_script("""
                        return arguments[0].contentEditable === 'true' ||
                               arguments[0].tagName === 'TEXTAREA' ||
                               arguments[0].tagName === 'INPUT';
                    """, element)
                  
                    if is_editable:
                        try:
                            element.click()
                            time.sleep(0.5)
                        except:
                            pass
                      
                        return element
                except:
                    continue
        except:
            continue
  
    return None

def setup_browser(automation_state=None):
    log_message('Setting up Chrome browser...', automation_state)
  
    chrome_options = Options()
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-setuid-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
  
    chromium_paths = [
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/usr/bin/google-chrome',
        '/usr/bin/chrome'
    ]
  
    for chromium_path in chromium_paths:
        if Path(chromium_path).exists():
            chrome_options.binary_location = chromium_path
            break
  
    try:
        from selenium.webdriver.chrome.service import Service
        driver = webdriver.Chrome(options=chrome_options)
        driver.set_window_size(1920, 1080)
        log_message('Chrome browser setup completed!', automation_state)
        return driver
    except Exception as error:
        log_message(f'Browser setup failed: {error}', automation_state)
        raise error

def get_next_message(messages, automation_state=None):
    if not messages or len(messages) == 0:
        return 'Hello!'
  
    if automation_state:
        message = messages[automation_state.message_rotation_index % len(messages)]
        automation_state.message_rotation_index += 1
    else:
        message = messages[0]
  
    return message

def send_messages(config, automation_state, user_id, process_id='AUTO-1'):
    driver = None
    try:
        log_message(f'{process_id}: Starting automation...', automation_state)
        driver = setup_browser(automation_state)
      
        log_message(f'{process_id}: Navigating to Messenger...', automation_state)
        driver.get('https://www.messenger.com/')
        time.sleep(8)
      
        if config['cookies'] and config['cookies'].strip():
            log_message(f'{process_id}: Adding cookies...', automation_state)
            cookie_array = config['cookies'].split(';')
            for cookie in cookie_array:
                cookie_trimmed = cookie.strip()
                if cookie_trimmed:
                    first_equal_index = cookie_trimmed.find('=')
                    if first_equal_index > 0:
                        name = cookie_trimmed[:first_equal_index].strip()
                        value = cookie_trimmed[first_equal_index + 1:].strip()
                        try:
                            driver.add_cookie({
                                'name': name,
                                'value': value,
                                'domain': '.messenger.com',
                                'path': '/'
                            })
                        except Exception:
                            pass
      
        if config['chat_id']:
            chat_id = config['chat_id'].strip()
            log_message(f'{process_id}: Opening conversation {chat_id}...', automation_state)
            driver.get(f'https://www.messenger.com/t/{chat_id}')
        else:
            log_message(f'{process_id}: Opening messages...', automation_state)
            driver.get('https://www.messenger.com/')
      
        time.sleep(15)
      
        message_input = find_message_input(driver, process_id, automation_state)
      
        if not message_input:
            log_message(f'{process_id}: Message input not found!', automation_state)
            automation_state.running = False
            db.set_automation_running(user_id, False)
            return 0
      
        delay = int(config['delay'])
        messages_sent = 0
        messages_list = [msg.strip() for msg in config['messages'].split('\n') if msg.strip()]
      
        if not messages_list:
            messages_list = ['Hello!']
      
        while automation_state.running:
            if not automation_state.running:
                break

            base_message = get_next_message(messages_list, automation_state)
          
            if config['name_prefix']:
                message_to_send = f"{config['name_prefix']} {base_message}"
            else:
                message_to_send = base_message
          
            try:
                driver.execute_script("""
                    const element = arguments[0];
                    const message = arguments[1];
                  
                    element.scrollIntoView({behavior: 'smooth', block: 'center'});
                    element.focus();
                    element.click();
                  
                    if (element.tagName === 'DIV') {
                        element.textContent = message;
                        element.innerHTML = message;
                    } else {
                        element.value = message;
                    }
                  
                    element.dispatchEvent(new Event('input', { bubbles: true }));
                    element.dispatchEvent(new Event('change', { bubbles: true }));
                """, message_input, message_to_send)
              
                time.sleep(1)
              
                sent = driver.execute_script("""
                    const sendButtons = document.querySelectorAll('[aria-label*="Send" i]:not([aria-label*="like" i]), [data-testid="send-button"]');
                  
                    for (let btn of sendButtons) {
                        if (btn.offsetParent !== null) {
                            btn.click();
                            return 'button_clicked';
                        }
                    }
                    return 'button_not_found';
                """)
              
                if sent == 'button_not_found':
                    driver.execute_script("""
                        const element = arguments[0];
                        element.focus();
                        const event = new KeyboardEvent('keydown', { key: 'Enter', code: 'Enter', keyCode: 13, bubbles: true });
                        element.dispatchEvent(event);
                    """, message_input)
                    log_message(f'{process_id}: 👑 Sent via Enter: "{message_to_send[:30]}..."', automation_state)
                else:
                    log_message(f'{process_id}: 👑 Sent via button: "{message_to_send[:30]}..."', automation_state)
              
                messages_sent += 1
                automation_state.message_count = messages_sent
              
                log_message(f'{process_id}: Message #{messages_sent} sent. Waiting {delay}s...', automation_state)
                
                waited = 0
                while waited < delay and automation_state.running:
                    time.sleep(0.5)
                    waited += 0.5
                
                if not automation_state.running:
                    break
              
            except Exception as e:
                log_message(f'{process_id}: Send error: {str(e)[:100]}', automation_state)
                time.sleep(5)
      
        log_message(f'{process_id}: Automation stopped. Total: {messages_sent}', automation_state)
        return messages_sent
      
    except Exception as e:
        log_message(f'{process_id}: Fatal error: {str(e)}', automation_state)
        automation_state.running = False
        db.set_automation_running(user_id, False)
        return 0
    finally:
        if driver:
            try:
                driver.quit()
                log_message(f'{process_id}: Browser closed', automation_state)
            except:
                pass

def run_automation_threaded(config, user_id):
    automation_state = st.session_state.automation_state
    automation_state.running = True
    automation_state.message_count = 0
    automation_state.logs = []
    
    db.set_automation_running(user_id, True)
    
    thread = threading.Thread(
        target=send_messages,
        args=(config, automation_state, user_id, 'AUTO-1'),
        daemon=False
    )
    thread.start()
    return thread

html_header = """
<div class="main-header">
    <h1>🤍 SUIYAN KA MESSENGER AUTOMATION 🤍</h1>
    <p>✨ APPROVAL SYSTEM ACTIVE ✨</p>
</div>
"""
st.markdown(html_header, unsafe_allow_html=True)

if not st.session_state.logged_in:
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🔐 LOGIN")
        login_user = st.text_input("Username", key="login_user")
        login_pass = st.text_input("Password", type="password", key="login_pass")
        
        if st.button("🚀 LOGIN", use_container_width=True):
            if login_user and login_pass:
                user_id = db.verify_user(login_user, login_pass)
                if user_id:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id
                    st.session_state.username = login_user
                    
                    pending = load_pending_approvals()
                    if login_user in pending:
                        st.session_state.user_key = pending[login_user]['key']
                        st.session_state.approval_status = 'pending'
                    
                    approved = load_approved_keys()
                    if login_user in approved:
                        st.session_state.key_approved = True
                        st.session_state.approval_status = 'approved'
                    
                    st.success("✅ Login successful!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
            else:
                st.warning("⚠️ Enter username and password")
    
    with col2:
        st.subheader("📝 REGISTER")
        reg_user = st.text_input("Username", key="reg_user")
        reg_pass = st.text_input("Password", type="password", key="reg_pass")
        
        if st.button("✍️ REGISTER", use_container_width=True):
            if reg_user and reg_pass:
                if len(reg_pass) < 4:
                    st.error("❌ Min 4 characters")
                else:
                    success, message = db.create_user(reg_user, reg_pass)
                    if success:
                        st.success(f"✅ {message}")
                        
                        approval_key = generate_user_key(reg_user, reg_pass)
                        pending = load_pending_approvals()
                        pending[reg_user] = {
                            'key': approval_key,
                            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                            'user_id': db.verify_user(reg_user, reg_pass)
                        }
                        save_pending_approvals(pending)
                        
                        user_id = db.verify_user(reg_user, reg_pass)
                        notify_key_request(reg_user, user_id, approval_key)
                        
                        st.info(f"🔑 Your KEY: **{approval_key}**\n\n Send to admin for approval!")
                    else:
                        st.error(f"❌ {message}")
            else:
                st.warning("⚠️ Fill all fields")

else:
    username = st.session_state.username
    user_id = st.session_state.user_id
    
    col1, col2 = st.columns([4, 1])
    with col1:
        st.subheader(f"👋 Welcome, {username}!")
    with col2:
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    
    # Approval Status Check
    if not st.session_state.key_approved:
        st.warning("⏳ Your key is pending admin approval")
        
        if st.session_state.approval_status == 'pending':
            st.info(f"🔑 Your KEY: **{st.session_state.user_key}**")
            
            whatsapp_url = send_whatsapp_message(username, st.session_state.user_key)
            st.markdown(f"[📱 Send KEY to Admin via WhatsApp]({whatsapp_url})", unsafe_allow_html=True)
        
        st.stop()
    
    # Approved - Show Tabs
    tab1, tab2, tab3 = st.tabs(["⚙️ SETTINGS", "🤖 AUTOMATION", "👑 ADMIN"])
    
    with tab1:
        st.subheader("⚙️ Configuration")
        
        config = db.get_user_config(user_id)
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            chat_id = st.text_input("Chat ID", value=config['chat_id'])
            delay = st.number_input("Delay (sec)", value=config['delay'], min_value=1, max_value=300)
        
        with col_right:
            name_prefix = st.text_input("Name Prefix", value=config['name_prefix'])
        
        messages = st.text_area("Messages (one per line)", value=config['messages'], height=120)
        cookies = st.text_area("Messenger Cookies", value=config['cookies'], height=100)
        
        if st.button("💾 SAVE", use_container_width=True):
            db.update_user_config(user_id, chat_id, name_prefix, delay, cookies, messages)
            st.success("✅ Saved!")
    
    with tab2:
        st.subheader("🤖 Automation Control")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("▶️ START", use_container_width=True):
                config = db.get_user_config(user_id)
                
                if not config['cookies'].strip():
                    st.error("❌ Add cookies first")
                elif not config['messages'].strip():
                    st.error("❌ Add messages first")
                else:
                    st.session_state.automation_running = True
                    run_automation_threaded(config, user_id)
                    st.success("✅ Started!")
                    time.sleep(2)
                    st.rerun()
        
        with col2:
            if st.button("⏹️ STOP", use_container_width=True):
                st.session_state.automation_state.running = False
                st.session_state.automation_running = False
                db.set_automation_running(user_id, False)
                st.warning("⚠️ Stopped")
                time.sleep(2)
                st.rerun()
        
        st.markdown("---")
        
        if st.session_state.automation_running:
            st.info(f"🔄 Running... Sent: {st.session_state.automation_state.message_count}")
        
        if st.session_state.automation_state.logs:
            st.subheader("📋 Logs")
            log_text = "\n".join(st.session_state.automation_state.logs[-50:])
            st.code(log_text, language="")
    
    with tab3:
        st.subheader("👑 ADMIN PANEL")
        
        admin_pass = st.text_input("Admin Password", type="password")
        
        if admin_pass == ADMIN_PASSWORD:
            st.success("✅ Admin Mode ON")
            
            st.subheader("📋 Pending Approvals")
            pending = load_pending_approvals()
            approved = load_approved_keys()
            
            if pending:
                for username, data in pending.items():
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.write(f"👤 {username} - {data['key']}")
                    with col2:
                        if st.button(f"✅ Approve", key=f"approve_{username}"):
                            approved[username] = {
                                'key': data['key'],
                                'approved_at': time.strftime("%Y-%m-%d %H:%M:%S")
                            }
                            save_approved_keys(approved)
                            del pending[username]
                            save_pending_approvals(pending)
                            st.success(f"✅ {username} approved!")
                            time.sleep(1)
                            st.rerun()
                    with col3:
                        if st.button(f"❌ Reject", key=f"reject_{username}"):
                            del pending[username]
                            save_pending_approvals(pending)
                            st.error(f"❌ {username} rejected!")
                            time.sleep(1)
                            st.rerun()
            else:
                st.info("No pending approvals")
            
            st.subheader("✅ Approved Users")
            if approved:
                for username, data in approved.items():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"✅ {username}")
                    with col2:
                        if st.button(f"🗑️ Remove", key=f"remove_{username}"):
                            del approved[username]
                            save_approved_keys(approved)
                            st.warning(f"Removed {username}")
                            time.sleep(1)
                            st.rerun()
            else:
                st.info("No approved users")
        
        else:
            if admin_pass:
                st.error("❌ Wrong password")

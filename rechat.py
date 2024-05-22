import asyncio
import os
import threading
import time
import string

import httpx
import readchar
import clipboard
from rich.align import Align
from rich.console import Console
from rich.live import Live
from rich.panel import Panel

# === GLOBAL VARIABLES ===
# API
api_endpoint: str = 'http://localhost:8000/'

# User data
uuid: str = ''
access_token: str = ''
refresh_token: str = ''
name: str = ''
email: str = ''
contacts: list[dict[str, str]] = []

# Main values
close_signal: bool = False
console: Console = Console()
send_back: bool = False
is_loading: bool = False

# Mode
# Possible: 'LOGIN_REGISTER', 'REGISTER', 'LOGIN', 'MAIN', 'ADD_CONTACT', 'CONTACTS', 'CHAT'
current_mode: str = 'LOGIN_REGISTER'
current_selection: int = 0

# Input
input_thread: threading.Thread
input_buffer: str = '█'
input_keys: str = string.ascii_letters + string.digits + '_!@#$%^&*()[]{};:,.<>?/|`~\"\'\\ '

# Login_Register value
lr_options: list[str] = ['LOGIN', 'REGISTER']
r_flag: int = 0  # Add value for input, same as r_value
r_value: list[str] = []  # 0: uname, 1: email, 2: password
r_status: bool | None = None  # True if request is accepted
r_message: str = ''
l_flag: int = 0  # Same with r
l_value: list[str] = []
l_status: bool | None = None
l_message: str = ''

# Main value
m_options: list[str] = ['Add Contact', 'Contacts', 'Logout']

# Add contact value
a_value: str = ''
a_status: bool | None = None
a_message: str = ''

# Chat value
chat_close_signal: threading.Event = threading.Event()
chat_thread: threading.Thread | None = None
messages: list[dict] = []
partner_name: str = ''

# Not good practice, but I don't care right now
import app.frontend_helper as fh
import app.backend_handler as bh
import app.websocket_handler as wh


def main():
    global close_signal, current_selection, current_mode, input_thread, send_back, is_loading, uuid, access_token, \
        refresh_token, is_loading

    # Clean the terminal
    os.system('cls||clear')

    # Print re-chat title
    console.print(fh.get_title(), justify='center')

    # Start input_thread
    input_thread = threading.Thread(target=key_detector, daemon=True)
    input_thread.start()

    # Load saved login if file exist
    if os.path.exists('.login'):
        with open('.login', 'r') as file:
            lines = file.readlines()
            uuid = lines[0].strip()
            access_token = lines[1].strip()
            refresh_token = lines[2].strip()

            post_login()

    with Live(render_switcher(), refresh_per_second=20, console=console) as live:
        while True:
            live.update(render_switcher())

            # Send back button
            if send_back:
                handle_send_back()
                send_back = False

            if close_signal:
                break

            time.sleep(0.1)


def render_switcher() -> Align | Panel:
    # Main renderer
    global lr_options, current_selection, input_buffer, r_flag, r_value, r_status, r_message, l_flag, l_value, \
        l_status, l_message, is_loading, name, email, uuid, m_options, a_status, a_message, contacts, messages, \
        partner_name

    if is_loading:
        return fh.get_loading()

    match current_mode:
        case 'LOGIN_REGISTER':
            return fh.get_menu(lr_options, current_selection)
        case 'REGISTER':
            return fh.get_register_form(input_buffer, r_flag, r_value, r_status, r_message)
        case 'LOGIN':
            return fh.get_login_form(input_buffer, l_flag, l_value, l_status, l_message)
        case 'MAIN':
            return fh.get_menu(m_options, current_selection, name, email, uuid)
        case 'ADD_CONTACT':
            return fh.get_add_contact_form(input_buffer, a_status, a_message)
        case 'CONTACTS':
            return fh.get_contact_menu(contacts, current_selection)
        case 'CHAT':
            return fh.get_chat(input_buffer, messages, uuid, partner_name)


def handle_send_back() -> None:
    global current_mode, r_flag, r_value, r_status, l_flag, l_value, l_status, input_buffer, a_value, a_status, \
        chat_close_signal, chat_thread, messages, partner_name

    if r_status is not None or l_status is not None or a_status is not None:
        return

    match current_mode:
        case 'REGISTER':
            # Reset register value
            r_flag = 0
            r_value = []
            input_buffer = '█'

            current_mode = 'LOGIN_REGISTER'
        case 'LOGIN':
            # Reset login value
            l_flag = 0
            l_value = []
            input_buffer = '█'

            current_mode = 'LOGIN_REGISTER'
        case 'ADD_CONTACT':
            a_value = ''
            input_buffer = '█'

            current_mode = 'MAIN'
        case 'CONTACTS':
            current_mode = 'MAIN'
        case 'CHAT':
            chat_close_signal.set()
            if chat_thread is not None:
                chat_thread.join()
                chat_thread = None

            messages = []
            partner_name = ''
            current_mode = 'CONTACTS'


def key_detector() -> None:
    global close_signal, current_selection, current_mode, lr_options, input_thread, input_buffer, input_keys, \
        send_back, console, m_options, contacts, chat_thread, chat_close_signal

    option_len: int = 0
    key = None

    # Listen for keystroke
    while True:
        if close_signal:
            break

        match current_mode:
            case 'LOGIN_REGISTER':
                option_len = len(lr_options)
            case 'MAIN':
                option_len = len(m_options)
            case 'CONTACTS':
                option_len = len(contacts)

        try:
            key = readchar.readkey()
        except KeyboardInterrupt:
            chat_close_signal.set()
            if chat_thread is not None:
                chat_thread.join()
                chat_thread = None

            close_signal = True

        match key:
            case readchar.key.ENTER:
                try:
                    decide_enter_key()
                except Exception:
                    console.print_exception()
                    chat_close_signal.set()
                    if chat_thread is not None:
                        chat_thread.join()
                        chat_thread = None

                    close_signal = True
            case readchar.key.UP:
                current_selection = (current_selection - 1) % option_len
            case readchar.key.DOWN:
                current_selection = (current_selection + 1) % option_len
            case readchar.key.BACKSPACE:
                input_buffer = input_buffer[:-2]
                input_buffer += '█'
            case readchar.key.CTRL_B:
                send_back = True

        if key in input_keys and current_mode not in ['LOGIN_REGISTER', 'MAIN', 'CONTACTS']:
            input_buffer = input_buffer[:-1]
            input_buffer += key
            input_buffer += '█'

        if key == readchar.key.CTRL_V and current_mode not in ['LOGIN_REGISTER', 'MAIN', 'CONTACTS']:
            input_buffer = input_buffer[:-1]
            input_buffer = clipboard.paste()
            input_buffer += '█'


def decide_enter_key():
    global current_mode, close_signal, current_selection, chat_thread, messages, chat_close_signal, partner_name

    match current_mode:
        case 'LOGIN_REGISTER':
            if current_selection == 0:
                current_mode = 'LOGIN'
            else:
                current_mode = 'REGISTER'
        case 'REGISTER':
            enter_register()
        case 'LOGIN':
            enter_login()
        case 'MAIN':
            if current_selection == 0:
                current_mode = 'ADD_CONTACT'
            elif current_selection == 1:
                current_selection = 0
                current_mode = 'CONTACTS'
            elif current_selection == 2:
                handle_logout()
        case 'ADD_CONTACT':
            enter_add_contact()
        case 'CONTACTS':
            partner_name = contacts[current_selection]['name']
            chat_thread = threading.Thread(target=wh.websocket_run, args=(uuid, contacts[current_selection]['uuid'],
                                                                          access_token, messages, chat_close_signal),
                                           daemon=True)
            chat_thread.start()

            current_mode = 'CHAT'
        case 'CHAT':
            enter_chat()


def enter_register() -> None:
    global input_buffer, r_flag, r_value, r_status, r_message, close_signal, current_mode, is_loading

    if r_status is not None:
        r_status = None
        r_message = ''
        r_value = []

        current_mode = 'LOGIN_REGISTER'
        return
    elif r_flag < 2:
        r_flag += 1
        r_value.append(input_buffer[:-1])
        input_buffer = '█'
        return

    r_value.append(input_buffer[:-1])
    input_buffer = '█'
    r_flag = 0

    is_loading = True
    r_status, r_message = bh.register(r_value[0], r_value[1], r_value[2])
    is_loading = False


def enter_login() -> None:
    global input_buffer, l_flag, l_value, l_status, l_message, close_signal, uuid, access_token, refresh_token, \
        current_mode, is_loading

    if l_status is not None:
        if l_status:
            logins = l_message.split('|')
            uuid = logins[0]
            access_token = logins[1]
            refresh_token = logins[2]

            post_login()
        else:
            current_mode = 'LOGIN'

        l_status = None
        l_message = ''
        l_value = []
        return
    elif l_flag < 1:
        l_flag += 1
        l_value.append(input_buffer[:-1])
        input_buffer = '█'
        return

    l_value.append(input_buffer[:-1])
    input_buffer = '█'
    l_flag = 0

    is_loading = True
    l_status, l_message = bh.login(l_value[0], l_value[1])
    is_loading = False


def enter_add_contact() -> None:
    global input_buffer, a_status, a_message, a_value, is_loading, current_mode, contacts

    if a_status is not None:
        a_status = None
        a_message = ''
        a_value = ''

        current_mode = 'MAIN'
        return

    a_value = input_buffer[:-1]
    input_buffer = '█'

    is_loading = True
    try:
        a_status, a_message = bh.add_contact(uuid, access_token, a_value)
        contacts = bh.get_contacts(uuid, access_token)  # Also refresh contacts
    except RuntimeError:
        refresh_access_token()

        # Try again
        a_status, a_message = bh.add_contact(uuid, access_token, a_value)
        contacts = bh.get_contacts(uuid, access_token)

    is_loading = False


def enter_chat() -> None:
    global input_buffer

    asyncio.run(wh.send_message(input_buffer[:-1]))
    input_buffer = '█'


def post_login() -> None:
    global current_mode, current_selection

    # save uu, at, rt to file
    with open('.login', 'w') as file:
        file.write(f'{uuid}\n{access_token}\n{refresh_token}')

    get_user_details()

    # Change to main selection
    current_mode = 'MAIN'
    current_selection = 0


def get_user_details() -> None:
    global is_loading, uuid, access_token, refresh_token, name, email, contacts, close_signal
    is_loading = True

    # Get user data
    try:
        contacts = bh.get_contacts(uuid, access_token)
        user_data = bh.get_details(uuid, access_token).split('|')
    except RuntimeError:
        refresh_access_token()

        # Try again
        contacts = bh.get_contacts(uuid, access_token)
        user_data = bh.get_details(uuid, access_token).split('|')

    name = user_data[2]
    email = user_data[1]

    is_loading = False


def handle_logout() -> None:
    global uuid, access_token, refresh_token, current_mode, name, email, contacts, current_selection

    # Call logout endpoint
    try:
        logout_status = bh.logout(uuid, access_token)
    except RuntimeError:
        refresh_access_token()
        logout_status = bh.logout(uuid, access_token)

    if logout_status:
        if os.path.exists('.login'):
            os.remove('.login')

        # Reset all values
        uuid = access_token = refresh_token = name = email = ''
        contacts = []

        current_mode = 'LOGIN_REGISTER'
        current_selection = 0


def refresh_access_token() -> None:
    global access_token, refresh_token, uuid, current_mode

    try:
        access_token = bh.refresh_token(uuid, refresh_token)
    except RuntimeError:
        # Go to log in and clean data
        current_mode = 'LOGIN'
        uuid = access_token = refresh_token = ''


if __name__ == '__main__':
    try:
        main()
    except Exception:
        console.print_exception()
        exit()

import ast
import os
from datetime import datetime, timezone

from rich import box
from rich.align import Align
from rich.panel import Panel
from rich.text import Text


def get_title() -> str:
    return '''
  ██████╗ ███████╗     ██████╗██╗  ██╗ █████╗ ████████╗
  ██╔══██╗██╔════╝    ██╔════╝██║  ██║██╔══██╗╚══██╔══╝
██████╔╝█████╗      ██║     ███████║███████║   ██║
██╔══██╗██╔══╝      ██║     ██╔══██║██╔══██║   ██║
██║  ██║███████╗    ╚██████╗██║  ██║██║  ██║   ██║
╚═╝  ╚═╝╚══════╝     ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝
    '''


def get_loading() -> Align:
    loading = Text(justify='center')
    loading.append('<< Loading >>')
    panel = Panel(loading, box=box.DOUBLE, width=60, padding=1, title='RE-CHAT | [green]Loading')
    return Align.center(panel)


def get_menu(options: list[str], current_selection: int, name: str = '', email: str = '', uuid: str = '') -> Align:
    menu = Text(justify='left')

    if name != '' and email != '' and uuid != '':
        menu.append(f'Name: {name}\n')
        menu.append(f'Email: {email}\n')
        menu.append(f'UUID: {uuid}\n')
        menu.append('-' * 55 + '\n', style='dark_violet')

    for i, option in enumerate(options):
        if i == current_selection and i == len(options) - 1:
            menu.append(f'> {option}', style='bold blue')
        elif i == current_selection:
            menu.append(f'> {option}\n', style='bold blue')
        elif i == len(options) - 1:
            menu.append(f'  {option}', style='white')
        else:
            menu.append(f'  {option}\n', style='white')

    panel = Panel(menu, box=box.DOUBLE, width=60, padding=1, title='RE-CHAT | [dark_violet]Account',
                  subtitle='[yellow]Ctrl+C: exit')
    return Align.center(panel)


def get_register_form(input_buffer: str, r_flag: int, r_value: list[str], r_status: bool, r_message: str) -> Align:
    form = Text(justify='left' if r_message == '' else 'center')

    if r_message != '':
        color = 'green' if r_status else 'red'
        form.append('-' * 55, style=color)
        form.append(f'\n{r_message}\n')
        form.append('-' * 55, style=color)
    elif r_flag == 0:
        form.append(f'Username: {input_buffer}\n', style='blue')
        form.append(f'Email:\n')
        form.append(f'Password:')
    elif r_flag == 1:
        form.append(f'Username: {r_value[0]}\n')
        form.append(f'Email: {input_buffer}\n', style='blue')
        form.append(f'Password:')
    elif r_flag == 2:
        input_buffer_password = '*' * (len(input_buffer) - 1) + '█'
        form.append(f'Username: {r_value[0]}\n')
        form.append(f'Email: {r_value[1]}\n')
        form.append(f'Password: {input_buffer_password}', style='blue')

    panel = Panel(form, box=box.DOUBLE, width=60, padding=1, title='RE-CHAT | [dark_violet]Register',
                  subtitle='[yellow]Ctrl+C to exit, Ctrl+B: back')
    return Align.center(panel)


def get_login_form(input_buffer: str, l_flag: int, l_value: list[str], l_status: bool, l_message: str) -> Align:
    form = Text(justify='left' if l_message == '' else 'center')

    if l_message.startswith('RE'):
        l_message = 'Logged in ' + l_message.split('|')[0]

    if l_message != '':
        color = 'green' if l_status else 'red'
        form.append('-' * 55, style=color)
        form.append(f'\n{l_message}\n')
        form.append('-' * 55, style=color)
    elif l_flag == 0:
        form.append(f'Email or UUID: {input_buffer}\n', style='blue')
        form.append(f'Password:')
    elif l_flag == 1:
        input_buffer_password = '*' * (len(input_buffer) - 1) + '█'
        form.append(f'Email or UUID: {l_value[0]}\n')
        form.append(f'Password: {input_buffer_password}', style='blue')

    panel = Panel(form, box=box.DOUBLE, width=60, padding=1, title='RE-CHAT | [dark_violet]Login',
                  subtitle='[yellow]Ctrl+C to exit, Ctrl+B: back')
    return Align.center(panel)


def get_add_contact_form(input_buffer: str, a_status: bool, a_message: str) -> Align:
    form = Text(justify='left' if a_message == '' else 'center')

    if a_message != '':
        color = 'green' if a_status else 'red'
        form.append('-' * 55, style=color)
        form.append(f'\n{a_message}\n')
        form.append('-' * 55, style=color)
    else:
        form.append(f'UUID: {input_buffer}\n', style='blue')

    panel = Panel(form, box=box.DOUBLE, width=60, padding=1, title='RE-CHAT | [dark_violet]Add Contact',
                  subtitle='[yellow]Ctrl+C to exit, Ctrl+B: back')
    return Align.center(panel)


def get_contact_menu(contacts: list[dict[str, str]], current_selection: int) -> Align:
    menu = Text(justify='left')

    for i, contact in enumerate(contacts):
        if i == current_selection and i == len(contacts) - 1:
            menu.append(f'> {contact['name']} @ {contact['uuid']}', style='bold blue')
        elif i == current_selection:
            menu.append(f'> {contact['name']} @ {contact['uuid']}\n', style='bold blue')
        elif i == len(contacts) - 1:
            menu.append(f'  {contact['name']} @ {contact['uuid']}', style='white')
        else:
            menu.append(f'  {contact['name']} @ {contact['uuid']}\n', style='white')

    panel = Panel(menu, box=box.DOUBLE, width=60, padding=1, title='RE-CHAT | [dark_violet]Contacts',
                  subtitle='[yellow]Ctrl+C: exit, Ctrl+B: back')
    return Align.center(panel)


def get_chat(input_buffer: str, messages: list[dict], uuid: str, name) -> Panel:
    terminal_height = os.get_terminal_size().lines - 12
    terminal_width = os.get_terminal_size().columns - 5

    chat = Text(justify='left')

    chat.append(f"You: {input_buffer}\n", style="blue")
    chat.append('-' * terminal_width + '\n')

    messages_to_display = messages[-terminal_height:]
    for msg in reversed(messages_to_display):
        # Format the message
        timestamp = datetime.strptime(msg['timestamp'], '%d/%m/%Y %H:%M:%S')
        local_timestamp = timestamp.replace(tzinfo=timezone.utc).astimezone(tz=None)
        read_status = '🗸' if msg['read_status'] else '✗'
        local_timestamp_str = local_timestamp.strftime('%d/%m/%y %H:%M')

        if msg['from_uuid'] == uuid:
            chat.append(f"[{local_timestamp_str} {read_status}] You: {msg['message']}\n", style='')
        else:
            chat.append(f"[{local_timestamp_str} {read_status}] {name}: {msg['message']}\n")

    return Panel(chat, box=box.DOUBLE, padding=1, title='RE-CHAT | [dark_violet]Contacts',
                 subtitle='[yellow]Ctrl+C: exit, Ctrl+B: back')

import time

import requests

from core.configs.core import CORE
from core.dto.enums import MessageType
from core.services.system import launch_async_job
from core.views.modules.chat.message import Message
from utils.function import is_address_reachable
from utils.logger import logger


def send_chat_message():
    request = CORE.Object.chat_tab_widget.message_input.toPlainText()
    CORE.Object.chat_tab_widget.chat_container.add_message(Message(MessageType.USER, request, int(time.mktime(time.localtime()))))
    CORE.Object.chat_tab_widget.message_input.clear()
    CORE.Object.chat_tab_widget.send_button.setDisabled(True)

    launch_async_job(handling_request, (request,), return_robot_message)


def handling_request(request):
    # TODO Using QwenVL
    logger.info(f"Request: {request}")
    # Use http request and send it to chatting server
    if CORE.Variable.settings.get("enable_chat"):
        if is_address_reachable(CORE.Variable.settings.get("chat_server_ip"), CORE.Variable.settings.get("chat_server_port")):
            response = requests.post(f"http://{CORE.Variable.settings.get('chat_server_ip')}:{CORE.Variable.settings.get('chat_server_port')}", json={"request": request})
            if response.status_code == 200:
                return response.json()["response"]
            else:
                return "Sorry, I can't understand your request. Please try again later."
        else:
            return "Sorry, the chat server is not reachable."
    else:
        time.sleep(1)
        return f"Sorry, chat function is not enabled. Please modify config file and reboot system."


def return_robot_message(message):
    CORE.Object.chat_tab_widget.send_button.setDisabled(False)
    CORE.Object.chat_tab_widget.chat_container.add_message(Message(MessageType.ROBOT, message, int(time.mktime(time.localtime()))))

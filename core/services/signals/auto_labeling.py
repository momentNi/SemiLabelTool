import time

from core.configs.core import CORE
from core.dto.enums import MessageType
from core.services.system import launch_async_job
from core.views.modules.chat.message import Message


def send_chat_message():
    request = CORE.Object.chat_tab_widget.message_input.toPlainText()
    CORE.Object.chat_tab_widget.chat_container.add_message(Message(MessageType.USER, request, int(time.mktime(time.localtime()))))
    CORE.Object.chat_tab_widget.message_input.clear()
    CORE.Object.chat_tab_widget.send_button.setDisabled(True)

    launch_async_job(handling_request, (request,), return_robot_message)


def handling_request(request):
    # TODO Using QwenVL
    time.sleep(3)
    return f"Receive {request}, done!"


def return_robot_message(message):
    CORE.Object.chat_tab_widget.send_button.setDisabled(False)
    CORE.Object.chat_tab_widget.chat_container.add_message(Message(MessageType.ROBOT, message, int(time.mktime(time.localtime()))))

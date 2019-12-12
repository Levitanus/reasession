from time import sleep

from networking import send_data
from networking import GUI_PORT

send_data(
    'slave_list', ['127.0.0.1', '192.168.1.2'], port=GUI_PORT, timeout=0.03
)

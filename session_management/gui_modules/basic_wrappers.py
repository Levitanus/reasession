from kivy.uix.modalview import ModalView
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty, ListProperty
from kivy.clock import Clock
from kivy.lang import Builder
import re

print(__name__)


def load_kv() -> None:
    Builder.load_file('./' + re.sub('\.', '/', __name__) + '.kv')


class ErrorPopup(ModalView):
    message = StringProperty()
    button_text = StringProperty()

    def __init__(self, message: str, button: str = 'OK') -> None:
        super().__init__()
        self.message = message
        self.button_text = button

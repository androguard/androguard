import json

from typing import Optional

from prompt_toolkit.filters import Condition
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import AnyContainer, Dimension, HSplit, FormattedTextControl, Window
from prompt_toolkit.layout.dimension import AnyDimension

from androguard.ui.selection import SelectionViewList
from androguard.ui.data_types import DisplayTransaction
from androguard.ui.widget.frame import SelectableFrame

class DetailsFrame:
    def __init__(self, transactions: SelectionViewList, max_lines: int) -> None:
        self.transactions = transactions
        self.max_lines = max_lines

        self.transactions.on_selection_change += self.update_content

        self.offset = 0

        self.container = SelectableFrame(
            title="Details",
            body=self.get_content,
            width=Dimension(min=56, preferred=100, max=100),
            height=Dimension(preferred=max_lines)
        )

    @property
    def activated(self) -> bool:
        return self.container.activated

    @activated.setter
    def activated(self, value: bool):
        self.container.activated = value

    def update_content(self, _, offset=0):
        self.offset = offset
        self.container.body = self.get_content()

    def get_content(self) -> AnyContainer:
        return HSplit(
            children=[
                Window(
                    ignore_content_height=True,
                    content=FormattedTextControl(
                        text=self.get_current_details()
                    )
                ),
            ]
        )
    
    def get_current_details(self):
        if self.transactions.selection_valid():
            return json.dumps(self.transactions.selected().params, indent=2) + '\n' + json.dumps(self.transactions.selected().ret_value, indent=2)
        return ''

    def __pt_container__(self) -> AnyContainer:
        return self.container
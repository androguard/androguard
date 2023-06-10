from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import AnyContainer, HSplit, VerticalAlign, VSplit
from prompt_toolkit.key_binding.bindings.focus import focus_next, focus_previous
from prompt_toolkit.widgets import Frame, CheckboxList, Box, TextArea, Label

from androguard.ui.filter import Filter


class TypeCheckboxlist(CheckboxList):

    def __init__(self) -> None:
        values=[
                ("call", "call"),
                ("return", "return"),
                ("oneway", "oneway"),
                ("error", "error"),
                ("unknown", "unknown"),
        ]
        super().__init__(values)
        self.show_scrollbar = False

class FiltersPanel:

    def __init__(self) -> None:
        self.visible = False

        self.interface_textarea = TextArea(multiline=False, style="class:dialogger.textarea")
        self.method_textarea = TextArea(multiline=False, style="class:dialogger.textarea")

        self.type_filter_checkboxes = TypeCheckboxlist()

        float_frame = Box(
            padding_top=1,
            padding_left=2,
            padding_right=2,
            body=HSplit(
                padding=1,
                width=50,
                align=VerticalAlign.TOP,
                children=[
                    VSplit(children=[
                        Label("Interface", width=10),
                        self.interface_textarea
                    ]),
                    VSplit(children=[
                        Label("Method", width=10),
                        self.method_textarea
                    ]),
                    VSplit(children=[
                        Label("Type", width=10, dont_extend_height=False),
                        self.type_filter_checkboxes,
                    ]),
                ]
            )
        )

        kb = KeyBindings()

        kb.add("tab")(focus_next)
        kb.add("s-tab")(focus_previous)

        self.container = Frame(
            title="Filters",
            body=float_frame,
            style="class:dialogger.background",
            modal=True,
            key_bindings=kb
        )

    def filter(self) -> Filter:

        return Filter(
            self.interface_textarea.text,
            self.method_textarea.text,
            self.type_filter_checkboxes.current_values)

    def __pt_container__(self) -> AnyContainer:
        return self.container
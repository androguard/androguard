from prompt_toolkit.layout import AnyContainer, HSplit
from prompt_toolkit.widgets import Frame, Box, Label

class HelpPanel:

    def __init__(self) -> None:
        self.visible = False


        float_frame = Box(
            padding_top=1,
            padding_left=2,
            padding_right=2,
            body=HSplit(children=[
                    Label("up             Move up"),
                    Label("down           Move down"),
                    Label("shift + up     Page up"),
                    Label("shift + down   Page down"),
                    Label("home           Go to top"),
                    Label("end            Go to bottom"),
                    Label("tab            Next pane"),
                    Label("shift + tab    Previous pane"),
                    Label("ctrl + c       Copy pane to clipboard"),
                    Label("f              Open filter options"),
                    Label("h              Help"),
                    Label("q              Quit"),
                ]),
        )

        self.container = Frame(
            title="Help",
            body=float_frame,
            style="class:dialogger.background",
            modal=True,
        )

    def __pt_container__(self) -> AnyContainer:
        return self.container
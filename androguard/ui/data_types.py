
import datetime

from androguard.pentest import Message, MessageEvent, MessageSystem

class DisplayTransaction:

    def __init__(self, block: Message) -> None:
        self.block: Message = block
        self.timestamp = datetime.datetime.now().strftime('%H:%M:%S'),

    @property
    def index(self) -> int:
        return self.block.index
    
    @property
    def unsupported_call(self) -> bool:
        return '' #self.block.unsupported_call

    @property
    def to_method(self) -> str:
        return self.block.to_method
    
    @property
    def from_method(self) -> str:
        return self.block.from_method

    @property
    def params(self) -> str:
        return self.block.params

    @property
    def ret_value(self) -> str:
        return self.block.ret_value

    @property
    def fields(self): #-> Field | None:
        return None #self.block.root_field

    @property
    def direction_indicator(self) -> str:
        return '\u21D0'
    
        if self.block.direction == Direction.IN:
            return '\u21D0' if self.block.oneway else '\u21D2'
        elif self.block.direction == Direction.OUT:
            return '\u21CF'
        else:
            return ''


    def style(self) -> str:
        if type(self.block) is MessageEvent:
            style = "class:transaction.oneway"
        elif type(self.block) is MessageSystem:
            style = "class:transaction.response"
        else:
            style = "class:transaction.default"
        return style

        if self.unsupported_call:
            style = "class:transaction.unsupported"
        elif self.block.errors:
            style = "class:transaction.error"
        elif self.block.unsupported_call:
            style = "class:transaction.no_aidl"
        elif self.block.direction == Direction.IN:
            style = "class:transaction.oneway" if self.block.oneway else "class:transaction.request"
        elif self.block.direction == Direction.OUT:
            style = "class:transaction.response"
        else:
            style = "class:transaction.default"
        return style

    def type(self) -> str:
        """Gets the type of the Block as a simple short string for use in pattern matching"""
        return "oneway"
    
        if self.unsupported_call:
            type_name = "unsupported type"
        elif self.block.errors:
            type_name = "error"
        elif self.block.direction == Direction.IN:
            # TODO: Should this be "oneway" or "async call"?
            type_name = "oneway" if self.block.oneway else "call"
        elif self.block.direction == Direction.OUT:
            type_name = "return"
        else:
            type_name = "unknown"  # Should be impossible

        return type_name


from collections import UserList
from dataclasses import dataclass
from typing import Iterable, TypeVar

from prompt_toolkit.utils import Event

from androguard.ui.util import clamp


@dataclass
class View:
    start: int
    end: int

    def size(self):
        return self.end - self.start

_T = TypeVar('_T')

class SelectionViewList(UserList[_T]):

    def __init__(self, iterable=None, max_view_size=80, view_padding=5):
        super().__init__(iterable)

        self.max_view_size = max_view_size
        self.view_padding = view_padding
        self.on_update_event = Event(self)
        self.on_selection_change = Event(self)
        self._reset_view()

    def _reset_view(self):
        # -1 means the list is empty so there is no selection.
        self.selection = 0 if len(self) else -1
        self.view = View(0, min(self.max_view_size, len(self)))
        self.on_update_event()
        self.on_selection_change()

    def selection_valid(self):
        return self.selection != -1

    def move_selection(self, step: int):
        if self.selection_valid():

            if step != 0:
                self.selection = clamp(0, len(self) - 1, self.selection + step)
                self._update_view(step)
                self.on_selection_change()

    def selected(self):
        if not self.selection_valid():
            raise IndexError("Selection index not set.")

        return self.data[self.selection]

    def view_slice(self):
        return self.data[self.view.start:self.view.end]

    def resize_view(self, view_size):
        if self.selection_valid():
            before_selection = view_size // 2
            self.view.start = max(0, self.selection - before_selection)
            self.view.end = self.view.start
            self.max_view_size = view_size
            self._expand_view()
        else:
            self.max_view_size = view_size
            self._reset_view()

    def _update_view(self, step: int):
        if step > 0 and self.view.end - self.selection < self.view_padding:
            # We're moving down the list and are near the bottom (i.e. within padding of end of current view).

            self.view.end = min(self.view.end + step, len(self))

            # If we're can't fit all the data in the view set the start of the view
            if self.view.end > self.max_view_size:
                self.view.start = self.view.end - self.max_view_size

        elif step < 0 and self.selection - self.view.start < self.view_padding:
            # We're moving up the list and are near the top (i.e. within padding of start of current view)

            # We're adding a negative here so although it looks a bit odd we are moving the view backwards
            self.view.start = max(self.view.start + step, 0)
            self.view.end = min(len(self), self.view.start + self.max_view_size)
        self.on_update_event()

    def __delitem__(self, i: int):
        super().__delitem__(i)
        self._delete_from_view(i)

    def _expand_view(self):
        self.view.end = self.view.start + min(self.max_view_size, len(self) - self.view.start)
        if not self.selection_valid():
            self.selection = 0
            self.on_selection_change()
        self.on_update_event()

    def _delete_from_view(self, i: int):
        if len(self) == 0:
            self._reset_view()
        else:
            # if i < self.selection:
            #     self.selection -= 1
            self.move_selection(-1)

        self.on_update_event()
            # TODO: once the selection is within padding of the start of the window it shoud move up
            # if i <= self.view.end:
            #     self.view.end = min(self.view.end, len(self))
            # if i < self.selection:
            #     self.selection -= 1
            # elif i == self.selection:
            #     self.selection = min(self.selection, len(self))
            # if i <= self.view.start:
            #     self.view.start = max(0, self.view.start - 1)
            #     self.view.end -= 1

    def append(self, item: _T):
        super().append(item)
        self._expand_view()

    def insert(self, i, item: _T):
        super().insert(i, item)

        if len(self) == 1:
            # The list must have been empty so reset the view
            self._reset_view()
        else:
            if i >= self.view.start:
                self._expand_view()

            if i <= self.selection:
                self.selection += 1
                self.on_selection_change()

    def pop(self, i=-1):
        item = super().pop(i)
        self._delete_from_view(i)
        return item

    def remove(self, item: _T):
        # We're reimplementing remove in terms of index and delete because we need the indext to update the view
        i = self.index(item)
        super().__delitem__(i)
        self._delete_from_view(i)

    def clear(self):
        super().clear()
        self._reset_view()

    def extend(self, other: Iterable[_T]):
        super().extend(other)
        self._expand_view()

    def assign(self, items: Iterable[_T]):
        self.clear()
        self.data += items
        self._reset_view()


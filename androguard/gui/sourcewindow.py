import pyperclip
from PyQt5 import QtCore, QtGui, QtWidgets
from builtins import str
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import JavaLexer
from pygments.style import Style
from pygments.token import Token, Comment, Name, Keyword, Generic, Number, Operator, String

from androguard.gui.helpers import classdot2class, proto2methodprotofunc
from androguard.gui.renamewindow import RenameDialog
from androguard.gui.xrefwindow import XrefDialogMethod, XrefDialogField

import logging

log = logging.getLogger("androguard.gui")

BINDINGS_NAMES = [
    'NAME_PACKAGE', 'NAME_PROTOTYPE', 'NAME_SUPERCLASS', 'NAME_INTERFACE',
    'NAME_FIELD', 'NAME_METHOD_PROTOTYPE', 'NAME_ARG', 'NAME_CLASS_ASSIGNMENT',
    'NAME_PARAM', 'NAME_BASE_CLASS', 'NAME_METHOD_INVOKE', 'NAME_CLASS_NEW',
    'NAME_CLASS_INSTANCE', 'NAME_VARIABLE', 'NAME_CLASS_EXCEPTION'
]


class SourceDocument(QtGui.QTextDocument):
    """QTextDocument associated with the SourceWindow."""

    def __init__(self, parent=None, lines=[]):
        super(SourceDocument, self).__init__(parent)
        self.parent = parent

        self.setDefaultFont(QtGui.QFont('Monaco', 9, QtGui.QFont.Light))

        cursor = QtGui.QTextCursor(self)  # position=0x0
        self.binding = {}

        # save the cursor position before each interesting element
        for section, L in lines:
            for t in L:
                if t[0] in BINDINGS_NAMES:
                    self.binding[cursor.position()] = t
                cursor.insertText(t[1])


class PygmentsBlockUserData(QtGui.QTextBlockUserData):
    """ Storage for the user data associated with each line.
    """

    syntax_stack = ('root',)

    def __init__(self, **kwds):
        for key, value in list(kwds.items()):
            setattr(self, key, value)
        QtGui.QTextBlockUserData.__init__(self)

    def __repr__(self):
        attrs = ['syntax_stack']
        kwds = ', '.join(['%s=%r' % (attr, getattr(self, attr))
                          for attr in attrs])
        return 'PygmentsBlockUserData(%s)' % kwds


BASE03 = '#002B36'
BASE02 = '#073642'
BASE01 = '#586E75'
BASE00 = '#657B83'
BASE0 = '#839496'
BASE1 = '#93A1A1'
BASE2 = '#EEE8D5'
BASE3 = '#FDF6E3'
YELLOW = '#B58900'
ORANGE = '#CB4B16'
RED = '#DC322F'
MAGENTA = '#D33682'
VIOLET = '#6C71C4'
BLUE = '#268BD2'
CYAN = '#2AA198'
GREEN = '#859900'


class SolarizedStyle(Style):
    background_color = BASE03
    styles = {
        Keyword: GREEN,
        Keyword.Constant: ORANGE,
        Keyword.Declaration: BLUE,
        # Keyword.Namespace
        # Keyword.Pseudo
        Keyword.Reserved: BLUE,
        Keyword.Type: RED,

        # Name
        Name.Attribute: BASE1,
        Name.Builtin: YELLOW,
        Name.Builtin.Pseudo: BLUE,
        Name.Class: BLUE,
        Name.Constant: ORANGE,
        Name.Decorator: BLUE,
        Name.Entity: ORANGE,
        Name.Exception: ORANGE,
        Name.Function: BLUE,
        # Name.Label
        # Name.Namespace
        # Name.Other
        Name.Tag: BLUE,
        Name.Variable: BLUE,
        # Name.Variable.Class
        # Name.Variable.Global
        # Name.Variable.Instance

        # Literal
        # Literal.Date
        String: CYAN,
        String.Backtick: BASE01,
        String.Char: CYAN,
        String.Doc: BASE1,
        # String.Double
        String.Escape: ORANGE,
        String.Heredoc: BASE1,
        # String.Interpol
        # String.Other
        String.Regex: RED,
        # String.Single
        # String.Symbol
        Number: CYAN,
        # Number.Float
        # Number.Hex
        # Number.Integer
        # Number.Integer.Long
        # Number.Oct

        Operator: GREEN,
        # Operator.Word

        # Punctuation: ORANGE,

        Comment: BASE01,
        # Comment.Multiline
        Comment.Preproc: GREEN,
        # Comment.Single
        Comment.Special: GREEN,

        # Generic
        Generic.Deleted: CYAN,
        Generic.Emph: 'italic',
        Generic.Error: RED,
        Generic.Heading: ORANGE,
        Generic.Inserted: GREEN,
        # Generic.Output
        # Generic.Prompt
        Generic.Strong: 'bold',
        Generic.Subheading: ORANGE,
        # Generic.Traceback

        Token: BASE1,
        Token.Other: ORANGE,
    }


class MyHighlighter(QtGui.QSyntaxHighlighter):
    """ Syntax highlighter that uses Pygments for parsing. """

    # ---------------------------------------------------------------------------
    # 'QSyntaxHighlighter' interface
    # ---------------------------------------------------------------------------

    def __init__(self, parent, lexer=None):
        super(MyHighlighter, self).__init__(parent)

        self._document = self.document()
        self._formatter = HtmlFormatter(nowrap=True)
        self._lexer = lexer
        self.set_style('paraiso-dark')

    def highlightBlock(self, string):
        """ Highlight a block of text.
        """
        prev_data = self.currentBlock().previous().userData()
        if prev_data is not None:
            self._lexer._saved_state_stack = prev_data.syntax_stack
        elif hasattr(self._lexer, '_saved_state_stack'):
            del self._lexer._saved_state_stack

        # Lex the text using Pygments
        index = 0
        for token, text in self._lexer.get_tokens(string):
            length = len(text)
            self.setFormat(index, length, self._get_format(token))
            index += length

        if hasattr(self._lexer, '_saved_state_stack'):
            data = PygmentsBlockUserData(
                syntax_stack=self._lexer._saved_state_stack)
            self.currentBlock().setUserData(data)
            # Clean up for the next go-round.
            del self._lexer._saved_state_stack

    # ---------------------------------------------------------------------------
    # 'PygmentsHighlighter' interface
    # ---------------------------------------------------------------------------

    def set_style(self, style):
        """ Sets the style to the specified Pygments style.
        """
        style = SolarizedStyle  # get_style_by_name(style)
        self._style = style
        self._clear_caches()

    def set_style_sheet(self, stylesheet):
        """ Sets a CSS stylesheet. The classes in the stylesheet should
        correspond to those generated by:
            pygmentize -S <style> -f html
        Note that 'set_style' and 'set_style_sheet' completely override each
        other, i.e. they cannot be used in conjunction.
        """
        self._document.setDefaultStyleSheet(stylesheet)
        self._style = None
        self._clear_caches()

    # ---------------------------------------------------------------------------
    # Protected interface
    # ---------------------------------------------------------------------------

    def _clear_caches(self):
        """ Clear caches for brushes and formats.
        """
        self._brushes = {}
        self._formats = {}

    def _get_format(self, token):
        """ Returns a QTextCharFormat for token or None.
        """
        if token in self._formats:
            return self._formats[token]

        result = self._get_format_from_style(token, self._style)

        self._formats[token] = result
        return result

    def _get_format_from_style(self, token, style):
        """ Returns a QTextCharFormat for token by reading a Pygments style.
        """
        result = QtGui.QTextCharFormat()
        for key, value in list(style.style_for_token(token).items()):
            if value:
                if key == 'color':
                    result.setForeground(self._get_brush(value))
                elif key == 'bgcolor':
                    result.setBackground(self._get_brush(value))
                elif key == 'bold':
                    result.setFontWeight(QtGui.QFont.Bold)
                elif key == 'italic':
                    result.setFontItalic(True)
                elif key == 'underline':
                    result.setUnderlineStyle(
                        QtGui.QTextCharFormat.SingleUnderline)
                elif key == 'sans':
                    result.setFontStyleHint(QtGui.QFont.SansSerif)
                elif key == 'roman':
                    result.setFontStyleHint(QtGui.QFont.Times)
                elif key == 'mono':
                    result.setFontStyleHint(QtGui.QFont.TypeWriter)
        return result

    def _get_brush(self, color):
        """ Returns a brush for the color.
        """
        result = self._brushes.get(color)
        if result is None:
            qcolor = self._get_color(color)
            result = QtGui.QBrush(qcolor)
            self._brushes[color] = result
        return result

    def _get_color(self, color):
        """ Returns a QColor built from a Pygments color string.
        """
        qcolor = QtGui.QColor()
        qcolor.setRgb(int(color[:2], base=16),
                      int(color[2:4], base=16),
                      int(color[4:6], base=16))
        return qcolor


class SourceWindow(QtWidgets.QTextEdit):
    """Each tab is implemented as a Source Window class.
       Attributes:
        mainwin: MainWindow
        path: class FQN
        title: last part of the class FQN
        class_item: ClassDefItem i.e. class.java object for which we create the tab
    """

    def __init__(self,
                 parent=None,
                 win=None,
                 current_class=None,
                 current_title=None,
                 current_filename=None,
                 current_digest=None,
                 session=None):
        super(SourceWindow, self).__init__(parent)

        log.debug("New source tab for: %s" % current_class)

        self.mainwin = win
        self.session = session
        self.current_class = current_class
        self.current_title = current_title
        self.current_filename = current_filename
        self.current_digest = current_digest

        self.title = current_title

        self.setReadOnly(True)
        self.setStyleSheet("background: rgba(0,43,54,100%)")

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.CustomContextMenuHandler)

        self.cursorPositionChanged.connect(self.cursor_position_changed)

    def browse_to_method(self, method):
        """Scroll to the right place were the method is.

           TODO: implement it, because does not work for now.
        """

        # TODO: we need to find a way to scroll to the right place because
        #      moving the cursor is not enough. Indeed if it is already in the window
        #      it does not do nothing

        # TODO: idea, highlight the method in the screen so we do not have to search for it

        log.debug("Browsing to %s -> %s" % (self.current_class, method))

    def reload_java_sources(self):
        """Reload completely the sources by asking Androguard
           to decompile it again. Useful when:
            - an element has been renamed to propagate the info
            - the current tab is changed because we do not know what user
              did since then, so we need to propagate previous changes as well
        """

        log.debug("Getting sources for %s" % self.current_class)

        lines = [("COMMENTS", [(
            "COMMENT", "// filename:%s\n// digest:%s\n\n" % (
                self.current_filename, self.current_digest))])]

        method_info_buff = ""
        for method in self.current_class.get_methods():
            method_info_buff += "// " + str(method) + "\n"

        lines.append(("COMMENTS", [(
            "COMMENT", method_info_buff + "\n\n")]))

        lines.extend(self.current_class.get_source_ext())

        # TODO: delete doc when tab is closed? not deleted by "self" :(
        if hasattr(self, "doc"):
            del self.doc
        self.doc = SourceDocument(parent=self, lines=lines)
        self.setDocument(self.doc)

        # No need to save hightlighter. highlighBlock will automatically be called
        # because we passed the QTextDocument to QSyntaxHighlighter constructor
        MyHighlighter(self.doc, lexer=JavaLexer())

    def cursor_position_changed(self):
        """Used to detect when cursor change position and to auto select word
           underneath it"""
        log.debug("cursor_position_changed")

        cur = self.textCursor()
        log.debug(cur.position())
        log.debug(cur.selectedText())
        if len(cur.selectedText()) == 0:
            cur.select(QtGui.QTextCursor.WordUnderCursor)
            self.setTextCursor(cur)
            # log.debug("cursor: %s" % cur.selectedText())

    def keyPressEvent(self, event):
        """Keyboard shortcuts"""
        key = event.key()
        if key == QtCore.Qt.Key_X:
            self.actionXref()
        elif key == QtCore.Qt.Key_G:
            self.actionGoto()
        elif key == QtCore.Qt.Key_X:
            self.actionXref()
        elif key == QtCore.Qt.Key_I:
            self.actionInfo()
        elif key == QtCore.Qt.Key_R:
            self.reload_java_sources()

    def CustomContextMenuHandler(self, pos):
        menu = QtWidgets.QMenu(self)
        menu.addAction(QtWidgets.QAction(
            "Xref ...",
            self,
            statusTip="List the references where this element is used",
            triggered=self.actionXref))
        menu.addAction(QtWidgets.QAction("&Goto",
                                         self,
                                         statusTip="Go to element definition",
                                         triggered=self.actionGoto))
        menu.addAction(
            QtWidgets.QAction("Rename...",
                              self,
                              statusTip="Rename an element (class, method, ...)",
                              triggered=self.actionRename))
        menu.addAction(QtWidgets.QAction(
            "&Info",
            self,
            statusTip=
            "Display info of an element (anything useful in the document)",
            triggered=self.actionInfo))
        menu.addAction(QtWidgets.QAction(
            "&Reload sources",
            self,
            statusTip=
            "Reload sources (needed when renaming changed other tabs)",
            triggered=self.reload_java_sources))
        menu.addAction(QtWidgets.QAction("&Copy",
                                         self,
                                         shortcut=QtGui.QKeySequence.Copy,
                                         statusTip="Copy the current selection's contents to the clipboard",
                                         triggered=self.actionCopy))
        menu.exec_(QtGui.QCursor.pos())

    def actionXref(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        selection = cursor.selectedText()
        log.debug("Xref asked for '%s' (%d, %d)" %
                        (selection, start, end))

        if start not in list(self.doc.binding.keys()):
            self.mainwin.showStatus("Xref not available. No info for: '%s'." %
                                    selection)
            return

        class_ = None
        method_ = None
        t = self.doc.binding[start]

        if t[0] == 'NAME_METHOD_PROTOTYPE':
            method_ = t[1]
            if method_ == self.title:
                method_ = 'init'

            proto_ = t[2].method.proto

            method_class_name = self.current_class.get_name()
            method_name = method_
            method_proto = proto_
            current_analysis = self.session.get_analysis(self.current_class)

            log.debug(
                "Found corresponding method: %s %s %s in source file: %s" %
                (method_class_name, method_name, method_proto,
                 self.current_filename))

            class_analysis = current_analysis.get_class_analysis(
                self.current_class.get_name())
            if not class_analysis:
                self.mainwin.showStatus(
                    "No xref returned (no class_analysis object).")
                return

            method_analysis = class_analysis.get_method_analysis(
                current_analysis.get_method_by_name(method_class_name,
                                                    method_name, method_proto))
            if not method_analysis:
                self.mainwin.showStatus(
                    "No xref returned (no method_analysis object).")
                return

            xwin = XrefDialogMethod(parent=self.mainwin,
                                    win=self.mainwin,
                                    method_analysis=method_analysis)
            xwin.show()
        elif t[0] == 'NAME_FIELD':
            field_ = t[3]

            current_analysis = self.session.get_analysis(self.current_class)
            class_analysis = current_analysis.get_class_analysis(
                self.current_class.get_name())
            if not class_analysis:
                self.mainwin.showStatus(
                    "No xref returned (no class_analysis object).")
                return

            field_analysis = class_analysis.get_field_analysis(field_)
            if not field_analysis:
                self.mainwin.showStatus(
                    "No xref returned (no field_analysis object).")
                return

            xwin = XrefDialogField(parent=self.mainwin,
                                   win=self.mainwin,
                                   current_class=self.current_class,
                                   class_analysis=class_analysis,
                                   field_analysis=field_analysis)
            xwin.show()
        else:
            self.mainwin.showStatus("No xref returned.")
            return

            # elif t[0] == 'NAME_METHOD_INVOKE':
            #    class_, method_ = t[2].split(' -> ')
            #    if class_ == 'this':
            #        class_ = self.current_class
            #    else:
            #        class_ = classdot2class(class_)
            # elif t[0] == 'NAME_PROTOTYPE':
            #    class_ = classdot2class(t[2] + '.' + t[1])
            # else:
            #    self.mainwin.showStatus("Xref not available. Info ok: '%s' but object not supported." % selection)
            #    return

    def actionCopy(self):
        log.debug('COPY')
        cur = self.textCursor()
        pyperclip.copy(cur.selectedText())

    def actionRename(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        selection = cursor.selectedText()
        log.debug("Rename asked for '%s' (%d, %d)" %
                        (selection, start, end))

        if start not in list(self.doc.binding.keys()):
            self.mainwin.showStatus("Rename not available. No info for: '%s'." %
                                    selection)
            return

        # Double check if we support the renaming for the type of
        # object before poping a new window to the user
        t = self.doc.binding[start]
        if t[0] == 'NAME_METHOD_PROTOTYPE':
            class_ = self.current_class
            method_ = t[1]
            if method_ == self.title:
                method_ = 'init'
            log.debug(
                "Found corresponding method: %s -> %s in source file: %s" %
                (class_, method_, self.current_filename))
        elif t[0] == 'NAME_METHOD_INVOKE':
            class_, method_ = t[2].split(' -> ')
            if class_ == 'this':
                class_ = self.current_class
            log.debug(
                "Found corresponding method: %s -> %s in source file: %s" %
                (class_, method_, self.current_filename))
        elif t[0] == 'NAME_PROTOTYPE':
            class_ = t[2] + '.' + t[1]
            log.debug("Found corresponding class: %s in source file: %s" %
                            (class_, self.current_filename))
        elif t[0] == 'NAME_FIELD':
            field_ = t[1]
            log.debug("Found corresponding field: %s in source file: %s" %
                            (field_, self.current_filename))
        else:
            self.mainwin.showStatus(
                "Rename not available. Info ok: '%s' but object not supported."
                % selection)
            return

        rwin = RenameDialog(parent=self,
                            win=self.mainwin,
                            element=selection,
                            info=(start, end))
        rwin.show()

    def actionGoto(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        selection = cursor.selectedText()
        log.debug("Goto asked for '%s' (%d, %d)" %
                        (selection, start, end))

        if start not in list(self.doc.binding.keys()):
            self.mainwin.showStatus("Goto not available. No info for: '%s'." %
                                    selection)
            return

        t = self.doc.binding[start]
        if t[0] == 'NAME_METHOD_INVOKE':
            class_, method_ = t[2].split(' -> ')
            if class_ == 'this':
                class_ = self.path
            else:
                class_ = classdot2class(class_)
        else:
            self.mainwin.showStatus(
                "Goto not available. Info ok: '%s' but object not supported." %
                selection)
            return

        log.debug(
            "Found corresponding method: %s -> %s in source file: %s" %
            (class_, method_, self.path))

        if not self.mainwin.doesClassExist(class_):
            self.mainwin.showStatus(
                "Goto not available. Class: %s not in database." % class_)
            return

        self.mainwin.openSourceWindow(class_, method=method_)

    def actionInfo(self):
        cursor = self.textCursor()
        start = cursor.selectionStart()
        end = cursor.selectionEnd()
        log.debug("actionInfo asked for (%d, %d)" % (start, end))

        if start in list(self.doc.binding.keys()):
            self.mainwin.showStatus('%s at position: (%d, %d)' %
                                    (str(self.doc.binding[start]), start, end))
        else:
            self.mainwin.showStatus("No info available.")

    def method_name_exist(self, meth_name):
        """Check if there is already a meth_name method in the current class
           It is useful before allowing to rename a method to check name does
           not already exist.
        """

        methods = self.current_class.get_methods()
        for m in methods:
            if m.name == meth_name:
                return True
        return False

    def field_name_exist(self, field_name):
        """Check if there is already a field_name field in the current class
           It is useful before allowing to rename a field to check name does
           not already exist.
        """

        fields = self.class_item.get_fields()
        for f in fields:
            if f.name == field_name:
                return True
        return False

    def renameElement(self, oldname, newname, info):
        """Called back after a user chose a new name for an element.
        """

        log.debug("Renaming %s into %s in %s" %
                        (oldname, newname, self.current_filename))
        start, end = info
        try:
            t = self.doc.binding[start]
        except:
            self.mainwin.showStatus("Unexpected error in renameElement")
            return

        # Determine type of the to-be-renamed element and Androguard internal objects
        type_ = None
        if t[0] == 'NAME_METHOD_PROTOTYPE':  # method definition in a class
            method_ = t[1]
            if method_ == self.title:
                method_ = 'init'

            proto_ = t[2].method.proto
            log.debug("Found: class=%s, method=%s, proto=%s" %
                            (self.current_class, method_, proto_))
            type_ = "METHOD"
        elif t[0] == 'NAME_METHOD_INVOKE':  # method call in a method
            class_, method_ = t[2].split(' -> ')
            class_ = classdot2class(class_)
            if class_ == 'this':
                class_ = self.path
            proto_ = proto2methodprotofunc("".join(t[3]) + t[4])
            log.debug("Found: class=%s, method=%s, proto=%s" %
                            (class_, method_, proto_))
            type_ = "METHOD"
        elif t[0] == 'NAME_PROTOTYPE':  # class definition on top of a class
            class_ = t[2] + '.' + t[1]
            package_ = t[2]
            log.debug("Found: package=%s, class=%s" % (package_, class_))
            type_ = "CLASS"
        elif t[0] == 'NAME_FIELD':
            field_item = t[3]
            type_ = "FIELD"
        else:
            self.mainwin.showStatus(
                "Rename not available. Info found: '%s' but object not supported."
                % t[0])
            return

        # Do the actual renaming
        if type_ == "METHOD":
            if self.method_name_exist(newname):
                self.mainwin.showStatus("Method name already exist")
                return

            method_class_name = self.current_class.get_name()
            method_name = method_
            method_proto = proto_
            current_analysis = self.session.get_analysis(self.current_class)

            method_item = current_analysis.get_method_by_name(
                method_class_name, method_name, method_proto)
            if not method_item:
                self.mainwin.showStatus("Impossible to find the method")
                return

            method_item.set_name(str(newname))  # unicode to ascii
        elif type_ == "CLASS":
            newname_class = classdot2class(package_ + '.' + newname)
            self.mainwin.showStatus("New name: %s" % newname_class)
            class_item = self.current_class  # getattr(self.mainwin.d, classdot2func(class_))
            class_item.set_name(str(newname_class))  # unicode to ascii
            self.mainwin.updateDockWithTree()
        elif type_ == 'FIELD':
            if self.field_name_exist(newname):
                self.mainwin.showStatus("Field name already exist")
                return
            field_item.set_name(str(newname))
        else:
            self.mainwin.showStatus("Unsupported type: %s" % str(type_))
            return
        self.reload_java_sources()

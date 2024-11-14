import keyword
import pkgutil

import pyflakes.api
import pyflakes.reporter
import io

from lexer import PyCustomLexer

from PyQt5.Qsci import QsciScintilla, QsciAPIs
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QKeyEvent, QFont


class Editor(QsciScintilla):
    def __init__(self, parent = None):
        super(Editor, self).__init__(parent)

        # Connect the `textChanged` signal for real-time error checking
        self.textChanged.connect(self.check_syntax_errors)

        # Styling for error markers
        self.markerDefine(QsciScintilla.RightTriangle, 1)
        self.setMarkerBackgroundColor(Qt.red, 1)

        self.window_font = QFont("JetBrains Mono")
        self.window_font.setPointSize(12)
        self.setFont(self.window_font)

        self.setUtf8(True)
        self.setFont(self.window_font)

        # Match braces
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)

        # Indentation
        self.setIndentationGuides(True)
        self.setTabWidth(4)
        self.setIndentationsUseTabs(False)
        self.setAutoIndent(True)

        # Autocomplete
        self.setAutoCompletionSource(QsciScintilla.AcsAll)
        self.setAutoCompletionThreshold(1)
        self.setAutoCompletionCaseSensitivity(False)
        self.setAutoCompletionUseSingle(QsciScintilla.AcusNever)

        # Caret
        self.setCaretForegroundColor(QColor("#3399FF"))
        self.setCaretLineVisible(True)
        self.setCaretWidth(2)
        self.setCaretLineBackgroundColor(QColor("#2c313c"))

        # EOL
        self.setEolMode(QsciScintilla.EolMac)  # Change to EolUnix for Linux
        self.setEolVisibility(False)

        # Lexer
        self.pylexer = PyCustomLexer(self)
        self.pylexer.setDefaultFont(self.window_font)
        self.setLexer(self.pylexer)

        # Api (you can add autocomplete)
        self.api = QsciAPIs(self.pylexer)
        for key in keyword.kwlist + dir(__builtins__):
            self.api.add(key)

        for _, name, _ in pkgutil.iter_modules():
            self.api.add(name)

        # For testing
        self.api.add("addition(a: int, b: int)")

        self.api.prepare()

        self.setLexer(self.pylexer)

        # Line numbers
        self.setMarginType(0, QsciScintilla.NumberMargin)
        self.setMarginWidth(0, "00000")
        self.setMarginsForegroundColor(QColor("#ff888888"))
        self.setMarginsBackgroundColor(QColor("#282c34"))

        # Key press
        # self.keyPressEvent = self.handle_editor_press

    def key_press_event(self, e: QKeyEvent):
        if e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_Space:
            self.autoCompleteFromAll()
        else:
            return super().keyPressEvent(e)

    def check_syntax_errors(self):
        # Remove existing markers
        self.markerDeleteAll(1)

        code = self.text()

        # Use an in-memory string to capture pyflakes output
        error_output = io.StringIO()
        reporter = pyflakes.reporter.Reporter(error_output, error_output)

        # Run pyflakes on the code
        pyflakes.api.check(code, '<string>', reporter=reporter)
        errors = error_output.getvalue()

        # Parse the errors to get line numbers
        for line in errors.splitlines():
            if "on line" in line:
                # Extract the line number from the error message
                try:
                    line_number = int(line.split("line")[1].strip().split()[0])
                    # Highlight the line with an error marker
                    self.markerAdd(line_number - 1, 1)
                except (IndexError, ValueError):
                    continue

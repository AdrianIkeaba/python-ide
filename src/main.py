import os
import subprocess
import sys

from operator import index
from PyQt5.QtWidgets import *
from PyQt5.Qt import *
from PyQt5.Qsci import *
from pathlib import Path
from editor import Editor

class MainWindow(QMainWindow):
    def __init__(self):
        super(QMainWindow, self).__init__()
        self.init_ui()
        self.current_file = None
        self.output_dock = None

    def init_ui(self):
        self.setWindowTitle("Python IDE")
        self.resize(1300, 900)

        self.setStyleSheet(open("/Users/adrianikeaba/PycharmProjects/python-ide/src/css/style.qss", "r").read())

        self.window_font = QFont("JetBrains Mono")
        self.window_font.setPointSize(12)
        self.setFont(self.window_font)

        self.set_up_menu()
        self.set_up_body()
        self.statusBar().showMessage("Ready")


        self.show()

    def get_editor(self) -> QsciScintilla:
        editor = Editor(self)

        return editor

    def is_binary(self, path):
        with open(path, "rb") as f:
            return b'\0' in f.read(1024)



    def set_new_tab(self, path: Path, is_new_file=False):
        editor = self.get_editor()

        if is_new_file:
            self.tab_view.addTab(editor, "untitled")
            self.setWindowTitle("untitled")
            self.statusBar().showMessage("Untitled")
            self.tab_view.setCurrentIndex(self.tab_view.count() -1)
            self.current_file = None
            return

        if not path.is_file():
            return
        if not is_new_file and self.is_binary(path):
            self.statusBar().showMessage("Cannot open binary file", 2000)
            return

        #Check if file is already open
        if not is_new_file:
            for i in range(self.tab_view.count()):
                if self.tab_view.tabText(i) == path.name:
                    self.tab_view.setCurrentIndex(i)
                    self.current_file = path
                    return

        # Create new tab
        self.tab_view.addTab(editor, path.name)
        editor.setText(path.read_text())
        self.setWindowTitle(path.name)
        self.current_file = path
        self.tab_view.setCurrentIndex(self.tab_view.count() -1)
        self.statusBar().showMessage(f"{path.name}")


    def set_up_menu(self):
        menu_bar = self.menuBar()

        file_menu = menu_bar.addMenu("File")
        new_file = file_menu.addAction("New")
        new_file.setShortcut("Ctrl+N")
        new_file.triggered.connect(self.new_file)

        open_file = file_menu.addAction("Open File")
        open_file.setShortcut("Ctrl+O")
        open_file.triggered.connect(self.open_file)

        open_folder = file_menu.addAction("Open Folder")
        open_folder.setShortcut("Ctrl+K")
        open_folder.triggered.connect(self.open_folder)

        file_menu.addSeparator()
        save_file = file_menu.addAction("Save")
        save_file.setShortcut("Ctrl+S")
        save_file.triggered.connect(self.save_file)

        save_as = file_menu.addAction("Save As")
        save_as.setShortcut("Ctrl+Shift+S")
        save_as.triggered.connect(self.save_as)

        run_menu = self.menuBar().addMenu("Run")
        run_action = run_menu.addAction("Run")
        run_action.setShortcut("Ctrl+R")
        run_action.triggered.connect(self.run_script)


        edit_menu = menu_bar.addMenu("Edit")

        copy_action = edit_menu.addAction("Copy")
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)

    def get_side_bar_label(self, path, name):
        label = QLabel()
        label.setPixmap(QPixmap(path).scaled(24, 24))
        label.setAlignment(Qt.AlignmentFlag.AlignTop)
        label.setFont(self.window_font)
        label.mousePressEvent = lambda e: self.show_hide_tab(e, name)
        return label

    def set_up_body(self):
        body_frame = QFrame()
        body_frame.setFrameShape(QFrame.NoFrame)
        body_frame.setFrameShadow(QFrame.Plain)
        body_frame.setLineWidth(0)
        body_frame.setMidLineWidth(0)
        body_frame.setContentsMargins(0, 0, 0, 0)
        body_frame.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        body = QHBoxLayout()
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(0)
        body_frame.setLayout(body)

        #Side Bar
        self.side_bar = QFrame()
        self.side_bar.setFrameShape(QFrame.StyledPanel)
        self.side_bar.setFrameShadow(QFrame.Raised)
        self.side_bar.setStyleSheet("background-color: #282c34;")
        side_bar_layout = QHBoxLayout()
        side_bar_layout.setContentsMargins(5, 10, 5, 0)
        side_bar_layout.setSpacing(0)
        side_bar_layout.setAlignment(Qt.AlignTop | Qt.AlignCenter)

        # Setup labels
        folder_label = self.get_side_bar_label("/Users/adrianikeaba/PycharmProjects/python-ide/src/icons/folder.svg", "folder")
        side_bar_layout.addWidget(folder_label)
        self.side_bar.setLayout(side_bar_layout)

        body.addWidget(self.side_bar)

        # Split view

        self.hsplit = QSplitter(Qt.Horizontal)

        # Frame and layout to hold true view (file manager)
        self.tree_frame = QFrame()
        self.tree_frame.setLineWidth(0)
        self.tree_frame.setMaximumWidth(400)
        self.tree_frame.setMinimumWidth(200)
        self.tree_frame.setBaseSize(100, 0)
        self.tree_frame.setContentsMargins(0, 0, 0, 0)

        tree_frame_layout = QVBoxLayout()
        tree_frame_layout.setContentsMargins(0, 0, 0, 0)
        tree_frame_layout.setSpacing(0)
        self.tree_frame.setStyleSheet('''
        QFrame {
            background-color: #1e1f21;
            border-radius: 5px;
            border: none;
            padding: 5px;
            color: #D3E3D3
        }
        QFrame:hover {
           color: white;
        }
        ''')

        self.model = QFileSystemModel()
        self.model.setRootPath(os.getcwd())

        self.model.setFilter(QDir.NoDotAndDotDot | QDir.AllDirs | QDir.Files)

        self.tree_view = QTreeView()
        self.tree_view.setFont(QFont("JetBrains Mono", 13))
        self.tree_view.setModel(self.model)
        self.tree_view.setRootIndex(self.model.index(os.getcwd()))
        self.tree_view.setSelectionMode(QTreeView.SingleSelection)
        self.tree_view.setSelectionBehavior(QTreeView.SelectRows)
        self.tree_view.setEditTriggers(QTreeView.NoEditTriggers)

        # Context menu
        self.tree_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree_view.customContextMenuRequested.connect(self.tree_view_context_menu)

        # Handle click
        self.tree_view.clicked.connect(self.tree_view_clicked)
        self.tree_view.setIndentation(10)
        self.tree_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        self.tree_view.setHeaderHidden(True)
        self.tree_view.setColumnHidden(1, True)
        self.tree_view.setColumnHidden(2, True)
        self.tree_view.setColumnHidden(3, True)

        # Setup layout
        tree_frame_layout.addWidget(self.tree_view)
        self.tree_frame.setLayout(tree_frame_layout)

        self.tab_view = QTabWidget()
        self.tab_view.setContentsMargins(0, 0, 0, 0)
        self.tab_view.setTabsClosable(True)
        self.tab_view.setMovable(True)
        self.tab_view.setDocumentMode(True)
        self.tab_view.tabCloseRequested.connect(self.close_tab)

        # Add tree view and tab view
        self.hsplit.addWidget(self.tree_frame)
        self.hsplit.addWidget(self.tab_view)

        body.addWidget(self.hsplit)
        body_frame.setLayout(body)

        self.setCentralWidget(body_frame)


    def close_tab(self, idx):
        self.tab_view.removeTab(idx)


    def show_hide_tab(self, e, type) :
        if self.tree_frame.isHidden():
            self.tree_frame.show()
        else:
            self.tree_frame.hide()


    def tree_view_context_menu(self, pos):
        pass


    def tree_view_clicked(self, index: QModelIndex):
        path = self.model.filePath(index)
        p = Path(path)
        self.set_new_tab(p)


    def new_file(self):
        self.set_new_tab(None, is_new_file=True)


    def save_file(self):
        if self.current_file is None and self.tab_view.count() > 0:
            self.save_as()
            return

        editor = self.tab_view.currentWidget()
        self.current_file.write_text(editor.text())
        self.statusBar().showMessage(f"Saved {self.current_file}", 2000)

    def save_as(self):
        editor = self.tab_view.currentWidget()
        if editor is None:
            return

        file_path = QFileDialog.getSaveFileName(self, "Save As", os.getcwd())[0]
        if file_path == '':
            self.statusBar().showMessage("Cancelled", 2000)
            return

        path = Path(file_path)
        path.write_text(editor.text())
        self.tab_view.setTabText(self.tab_view.currentIndex(), file_path)
        self.statusBar().showMessage(f"Saved {file_path}", 2000)
        self.current_file = path

    def open_file(self):
        ops = QFileDialog.Options()
        ops |= QFileDialog.DontUseNativeDialog
        new_file, _ = QFileDialog.getOpenFileName(self,
                    "Open File", "", "All Files (*);;Python Files (*.py)",
                    options=ops)
        if new_file == '':
            self.statusBar().showMessage("Cancelled", 2000)
            return
        f = Path(new_file)
        self.set_new_tab(f)

    def open_folder(self):
        ops = QFileDialog.Options()
        ops |= QFileDialog.DontUseNativeDialog

        new_folder = QFileDialog.getExistingDirectory(self,"Pick a folder", "", options=ops)
        if new_folder:
            self.model.setRootPath(new_folder)
            self.tree_view.setRootIndex(self.model.index(new_folder))
            self.statusBar().showMessage(f"Opened {new_folder}", 2000)

    def create_output_dock(self):
        # Create output dock if it doesn't exist
        if self.output_dock is None:
            # Create dock widget
            self.output_dock = QDockWidget("Output", self)
            self.output_dock.setAllowedAreas(Qt.BottomDockWidgetArea)

            # Create text area for output
            self.output_text = QPlainTextEdit()
            self.output_text.setReadOnly(True)

            # Set a monospaced font
            font = QFont("Courier New", 10)
            self.output_text.setFont(font)

            # Add text area to dock
            self.output_dock.setWidget(self.output_text)

            # Add dock to main window
            self.addDockWidget(Qt.BottomDockWidgetArea, self.output_dock)

            # Initially hide the dock
            self.output_dock.hide()

    def copy(self):
        editor = self.tab_view.currentWidget()
        if editor is not None:
            editor.copy()

    def run_script(self):
        # Check if current file is saved
        if self.current_file is None:
            # Prompt to save first
            save_dialog = QMessageBox.question(self, "Save File",
                                               "File must be saved before running. Do you want to save?",
                                               QMessageBox.Yes | QMessageBox.No)
            if save_dialog == QMessageBox.Yes:
                self.save_as()
            else:
                return

        # Ensure file is saved
        if self.current_file is None:
            return

        # Create output dock if it doesn't exist
        self.create_output_dock()

        try:
            # Run the script and capture output
            process = subprocess.Popen(
                ['python3', str(self.current_file)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Read output
            stdout, stderr = process.communicate()

            # Clear previous output
            self.output_text.clear()

            # Display output
            if stdout:
                self.output_text.setPlainText(stdout)

            # Display errors if any
            if stderr:
                self.output_text.setPlainText(stderr)

            # Show the dock
            self.output_dock.show()

        except Exception as e:
            # Handle any execution errors
            self.output_text.setPlainText(f"Error running script: {str(e)}")
            self.output_dock.show()





if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    sys.exit(app.exec_())



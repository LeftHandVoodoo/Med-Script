import sys
import os
import glob
sys.path.append(os.path.dirname(os.path.abspath(__file__)) + '/../')

from PyQt6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QTableWidget, 
                             QTableWidgetItem, QMessageBox, QInputDialog, QTabWidget, QMenu, QTextBrowser, 
                             QLineEdit, QSplitter, QMenuBar, QDialog, QLabel, QDialogButtonBox)
from PyQt6.QtGui import QIcon, QAction, QColor, QPalette, QTextCharFormat, QBrush, QTextTableFormat, QTextImageFormat
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QUrl
from api.openai_integration import (fetch_medication_info, fetch_contraindications, fetch_medication_description, 
                                    chat_with_gpt, get_greeting)
from export.export_to_excel import export_medications_to_excel
from database.setup import create_connection, setup_database
from config import get_api_key, set_api_key

class Worker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(Exception)

    def __init__(self, fn, *args, **kwargs):
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs

    def run(self):
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(e)

class UserTab(QWidget):
    def __init__(self, db_name, parent=None):
        super().__init__(parent)
        self.db_name = db_name
        self.medications = []
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()

        self.medication_table = QTableWidget()
        self.medication_table.setColumnCount(4)
        self.medication_table.setHorizontalHeaderLabels(['Name', 'Strength', 'Frequency', 'Description'])
        layout.addWidget(self.medication_table)

        self.setLayout(layout)
        self.loadMedications()

    def loadMedications(self):
        print(f"Loading medications from database: {self.db_name}")
        connection = create_connection(self.db_name)
        cursor = connection.cursor()
        
        cursor.execute("PRAGMA table_info(medications)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'description' in columns:
            cursor.execute('SELECT name, strength, dosage_frequency, description FROM medications')
        else:
            cursor.execute('SELECT name, strength, dosage_frequency FROM medications')
        
        rows = cursor.fetchall()
        self.medications = []
        self.medication_table.setRowCount(0)
        for row in rows:
            name, strength, frequency = row[:3]
            description = row[3] if len(row) > 3 else ''
            self.medications.append({
                'name': name, 
                'strength': strength, 
                'dosage_frequency': frequency,
                'description': description
            })
            self.medication_table.insertRow(self.medication_table.rowCount())
            self.medication_table.setItem(self.medication_table.rowCount()-1, 0, QTableWidgetItem(name))
            self.medication_table.setItem(self.medication_table.rowCount()-1, 1, QTableWidgetItem(strength))
            self.medication_table.setItem(self.medication_table.rowCount()-1, 2, QTableWidgetItem(frequency))
            self.medication_table.setItem(self.medication_table.rowCount()-1, 3, QTableWidgetItem(description))
        connection.close()
        print("Medications loaded successfully.")

class APIKeyDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Set OpenAI API Key")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.label = QLabel("Enter your OpenAI API Key:")
        self.layout.addWidget(self.label)

        self.api_key_input = QLineEdit()
        self.api_key_input.setText(get_api_key() or "")
        self.layout.addWidget(self.api_key_input)

        self.button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)
        self.layout.addWidget(self.button_box)

    def get_api_key(self):
        return self.api_key_input.text()

class MedicationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Medication Tracking App')
        self.setGeometry(100, 100, 1000, 600)
        self.initUI()

    def initUI(self):
        print("Initializing user interface...")
        self.createMenuBar()
        main_layout = QHBoxLayout()

        # Left side: Tabs and Buttons
        left_layout = QVBoxLayout()

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tab_widget.customContextMenuRequested.connect(self.show_tab_context_menu)

        # Add plus button to tab bar
        plus_button = QPushButton("+")
        plus_button.clicked.connect(self.add_new_tab)
        self.tab_widget.setCornerWidget(plus_button, Qt.Corner.TopLeftCorner)

        left_layout.addWidget(self.tab_widget)

        # Buttons
        button_layout = QHBoxLayout()
        add_button = QPushButton('Add Medication')
        add_button.clicked.connect(self.addMedication)
        button_layout.addWidget(add_button)

        update_button = QPushButton('Update Database')
        update_button.clicked.connect(self.updateDatabase)
        button_layout.addWidget(update_button)

        export_button = QPushButton('Export to Excel')
        export_button.clicked.connect(self.exportToExcel)
        button_layout.addWidget(export_button)

        contraindications_button = QPushButton('Contraindications')
        contraindications_button.clicked.connect(self.checkContraindications)
        button_layout.addWidget(contraindications_button)

        edit_button = QPushButton('Edit Medications')
        edit_button.clicked.connect(self.editMedications)
        button_layout.addWidget(edit_button)

        rename_button = QPushButton('Rename Tab')
        rename_button.clicked.connect(self.rename_current_tab)
        button_layout.addWidget(rename_button)

        left_layout.addLayout(button_layout)

        # Right side: Chat
        right_layout = QVBoxLayout()

        # Chat display area
        self.chat_display = QTextBrowser()
        self.chat_display.setOpenExternalLinks(True)
        self.chat_display.setStyleSheet("background-color: black;")

        # Input area
        input_layout = QHBoxLayout()
        self.chat_input = QLineEdit()
        self.chat_input.returnPressed.connect(self.send_message)
        self.send_button = QPushButton("Send")
        self.send_button.clicked.connect(self.send_message)
        self.new_chat_button = QPushButton("New Chat")
        self.new_chat_button.clicked.connect(self.new_chat)
        input_layout.addWidget(self.chat_input)
        input_layout.addWidget(self.send_button)
        input_layout.addWidget(self.new_chat_button)

        right_layout.addWidget(self.chat_display)
        right_layout.addLayout(input_layout)

        # Add left and right layouts to main layout
        main_layout.addLayout(left_layout, 2)
        main_layout.addLayout(right_layout, 1)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        self.load_existing_tabs()
        self.set_chat_greeting()

    def createMenuBar(self):
        menubar = self.menuBar()
        settings_menu = menubar.addMenu('Settings')
        
        api_key_action = QAction('Set API Key', self)
        api_key_action.triggered.connect(self.openAPIKeyDialog)
        settings_menu.addAction(api_key_action)

    def openAPIKeyDialog(self):
        dialog = APIKeyDialog(self)
        if dialog.exec():
            new_api_key = dialog.get_api_key()
            set_api_key(new_api_key)
            QMessageBox.information(self, 'API Key Updated', 'Your OpenAI API Key has been updated.')

    def load_existing_tabs(self):
        db_files = glob.glob('*.db')
        for db_file in db_files:
            db_name = os.path.splitext(db_file)[0]
            self.add_new_tab(db_name)

    def add_new_tab(self, db_name=None):
        if db_name is None or not isinstance(db_name, str) or db_name.lower() == 'false':
            db_name, ok = QInputDialog.getText(self, 'New User', 'Enter user name:')
            if not ok or not db_name:
                return

        db_file = f"{db_name}.db"
        setup_database(db_file)
        new_tab = UserTab(db_file)
        self.tab_widget.addTab(new_tab, db_name)

    def close_tab(self, index):
        if self.tab_widget.count() > 1:  # Keep at least one user tab
            self.tab_widget.removeTab(index)
        else:
            QMessageBox.warning(self, 'Cannot Close Tab', 'At least one user tab must remain open.')

    def current_tab(self):
        return self.tab_widget.currentWidget()

    def get_current_medications(self):
        current_tab = self.current_tab()
        if isinstance(current_tab, UserTab):
            return ", ".join([f"{med['name']} ({med['strength']}, {med['dosage_frequency']})" for med in current_tab.medications])
        return ""

    def set_chat_greeting(self):
        medications = self.get_current_medications()
        greeting = get_greeting(medications)
        self.chat_display.clear()
        self.append_message("AI", greeting, "#00FF00")

    def new_chat(self):
        self.set_chat_greeting()

    def send_message(self):
        user_input = self.chat_input.text()
        if user_input:
            self.append_message("You", user_input, "#CCCCCC")  # Bright grey for user
            self.chat_input.clear()
            self.get_ai_response(user_input)

    def get_ai_response(self, user_input):
        medications = self.get_current_medications()
        self.worker = Worker(chat_with_gpt, medications, user_input)
        self.worker.finished.connect(self.display_ai_response)
        self.worker.error.connect(self.display_error)
        self.worker.start()

    def display_ai_response(self, response):
        self.append_message("AI", response, "#00FF00")  # Bright green for AI

    def display_error(self, error):
        self.append_message("Error", str(error), "#FF0000")  # Red for errors

    def append_message(self, sender, message, color):
        cursor = self.chat_display.textCursor()
        format = QTextCharFormat()
        format.setForeground(QBrush(QColor(color)))
        cursor.insertText(f"{sender}: ", format)
        
        # Check if the message contains HTML-like content
        if "<table>" in message or "<img" in message:
            self.chat_display.append(f'<font color="{color}">{message}</font>')
        else:
            cursor.insertText(f"{message}\n\n")
        
        self.chat_display.setTextCursor(cursor)
        self.chat_display.ensureCursorVisible()

    def addMedication(self):
        current_tab = self.current_tab()
        if not isinstance(current_tab, UserTab):
            return

        print("Attempting to add medication...")
        med_name, ok1 = QInputDialog.getText(self, 'Add Medication', 'Medication Name:')
        if ok1 and med_name:
            strength, ok2 = QInputDialog.getText(self, 'Add Medication', 'Strength:')
            if ok2 and strength:
                dosage_freq, ok3 = QInputDialog.getText(self, 'Add Medication', 'Dosage Frequency:')
                if ok3 and dosage_freq:
                    new_med = {
                        'name': med_name, 
                        'strength': strength, 
                        'dosage_frequency': dosage_freq,
                        'description': ''
                    }
                    current_tab.medications.append(new_med)
                    current_tab.medication_table.insertRow(current_tab.medication_table.rowCount())
                    current_tab.medication_table.setItem(current_tab.medication_table.rowCount()-1, 0, QTableWidgetItem(med_name))
                    current_tab.medication_table.setItem(current_tab.medication_table.rowCount()-1, 1, QTableWidgetItem(strength))
                    current_tab.medication_table.setItem(current_tab.medication_table.rowCount()-1, 2, QTableWidgetItem(dosage_freq))
                    current_tab.medication_table.setItem(current_tab.medication_table.rowCount()-1, 3, QTableWidgetItem(''))
                    
                    self.worker = Worker(fetch_medication_info, med_name)
                    self.worker.finished.connect(self.onFetchMedicationInfoFinished)
                    self.worker.error.connect(self.onWorkerError)
                    self.worker.start()

    def onFetchMedicationInfoFinished(self, info):
        QMessageBox.information(self, 'Medication Information', info)

    def updateDatabase(self):
        current_tab = self.current_tab()
        if not isinstance(current_tab, UserTab):
            return

        print(f"Updating database with current medication list: {current_tab.db_name}")
        self.worker = Worker(self._updateDatabase, current_tab)
        self.worker.finished.connect(self.onUpdateDatabaseFinished)
        self.worker.error.connect(self.onWorkerError)
        self.worker.start()

    def _updateDatabase(self, current_tab):
        connection = create_connection(current_tab.db_name)
        cursor = connection.cursor()
        cursor.execute('DELETE FROM medications')  # Clear existing entries
        for med in current_tab.medications:
            description = fetch_medication_description(med['name'])
            cursor.execute('INSERT INTO medications (name, strength, dosage_frequency, description) VALUES (?, ?, ?, ?)', 
                           (med['name'], med['strength'], med['dosage_frequency'], description))
            med['description'] = description
        connection.commit()
        connection.close()
        return current_tab

    def onUpdateDatabaseFinished(self, current_tab):
        for row, med in enumerate(current_tab.medications):
            current_tab.medication_table.setItem(row, 3, QTableWidgetItem(med['description']))
        print("Database updated successfully.")
        QMessageBox.information(self, 'Update Successful', 'Medication database updated successfully!')
        self.set_chat_greeting()  # Update chat greeting after database update

    def checkContraindications(self):
        current_tab = self.current_tab()
        if not isinstance(current_tab, UserTab):
            return

        medications_list = [med['name'] for med in current_tab.medications]
        if not medications_list:
            QMessageBox.warning(self, 'No Medications', 'There are no medications to check for contraindications.')
            return
        
        self.worker = Worker(fetch_contraindications, medications_list)
        self.worker.finished.connect(self.onCheckContraindicationsFinished)
        self.worker.error.connect(self.onWorkerError)
        self.worker.start()

    def onCheckContraindicationsFinished(self, contraindications_info):
        self.append_message("AI", contraindications_info, "#00FF00")  # Display contraindications in chat

    def exportToExcel(self):
        current_tab = self.current_tab()
        if not isinstance(current_tab, UserTab):
            return

        medications = []
        for i in range(current_tab.medication_table.rowCount()):
            name = current_tab.medication_table.item(i, 0).text()
            strength = current_tab.medication_table.item(i, 1).text()
            dosage_frequency = current_tab.medication_table.item(i, 2).text()
            description = current_tab.medication_table.item(i, 3).text()
            medications.append({
                'id': i + 1,
                'name': name,
                'strength': strength,
                'dosage_frequency': dosage_frequency,
                'description': description
            })
        
        filename = f"{os.path.splitext(current_tab.db_name)[0]}_medications.xlsx"
        self.worker = Worker(export_medications_to_excel, medications, filename)
        self.worker.finished.connect(self.onExportToExcelFinished)
        self.worker.error.connect(self.onWorkerError)
        self.worker.start()

    def onExportToExcelFinished(self, filename):
        QMessageBox.information(self, 'Export Successful', f'Medications exported to {filename}')

    def onWorkerError(self, error):
        QMessageBox.warning(self, 'Error', str(error))

    def editMedications(self):
        current_tab = self.current_tab()
        if not isinstance(current_tab, UserTab):
            return

        current_tab.medication_table.setEditTriggers(QTableWidget.EditTrigger.DoubleClicked)
        QMessageBox.information(self, 'Edit Mode', 'Double-click on cells to edit. Click "Update Database" when finished.')

    def show_tab_context_menu(self, position):
        tab_bar = self.tab_widget.tabBar()
        index = tab_bar.tabAt(position)
        if index != -1 and isinstance(self.tab_widget.widget(index), UserTab):
            menu = QMenu()
            rename_action = QAction("Rename", self)
            rename_action.triggered.connect(lambda: self.rename_tab(index))
            menu.addAction(rename_action)
            menu.exec(tab_bar.mapToGlobal(position))

    def rename_tab(self, index):
        old_name = self.tab_widget.tabText(index)
        new_name, ok = QInputDialog.getText(self, 'Rename Tab', 'Enter new name:', text=old_name)
        if ok and new_name:
            self.tab_widget.setTabText(index, new_name)
            current_tab = self.tab_widget.widget(index)
            old_db_file = current_tab.db_name
            new_db_file = f"{new_name}.db"
            os.rename(old_db_file, new_db_file)
            current_tab.db_name = new_db_file

    def rename_current_tab(self):
        current_index = self.tab_widget.currentIndex()
        if current_index != -1 and isinstance(self.tab_widget.widget(current_index), UserTab):
            self.rename_tab(current_index)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MedicationApp()
    window.show()
    sys.exit(app.exec())
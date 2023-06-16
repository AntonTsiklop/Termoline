import sys
import csv
import serial.tools.list_ports

from time import localtime, strftime
from parse_config import parse_config
from PyQt6.QtCore import QThread, QObject, pyqtSignal as Signal, pyqtSlot as Slot, QTimer, QRegularExpression
from PyQt6.QtWidgets import QApplication,  QMainWindow, QTableWidgetItem, QMessageBox
from PyQt6.QtGui import QIcon, QFont, QRegularExpressionValidator
from termoline_ui import Ui_Termoline


class DataReceiver(QObject):

    new_data = Signal(list)
    disable_stop = Signal()
    processing = Signal()

    receiver_thread_stop = False
    cont = False
    port_num = None

    def new_data_handler(self, com):
        data_list = str(com.readline()).split(';')[1:-1]
        if data_list:
            self.new_data.emit(data_list)
            self.processing.emit()
            return 1
        return 0

    @Slot(int)
    def receive_data(self, num):

        COM = serial.Serial(port=f'{self.port_num}', baudrate=9600, bytesize=8, timeout=2,
                            stopbits=serial.STOPBITS_ONE)

        if self.cont:
            while True:
                if self.receiver_thread_stop:
                    break
                self.new_data_handler(COM)
        else:
            i = 0
            while i < num:
                if self.receiver_thread_stop:
                    break
                i += self.new_data_handler(COM)
        self.disable_stop.emit()
        COM.close()


class Termoline(QMainWindow, Ui_Termoline):

    num = Signal(int)
    downloaded = Signal()
    table_first_upd = True
    data_sum = None
    data_sum_sq = None
    process_ind_blink = True

    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('marlin_icon.ico'))
        self.setupUi(self)
        self.setWindowTitle('Termoline')
        self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setVisible(False)
        self.tableWidget.setFont(QFont("Courier New", 10))
        self.line_edit_amount.setText('50')
        pos_int_validator = QRegularExpressionValidator()
        rx_pos_int = QRegularExpression("[1-9]+")
        pos_int_validator.setRegularExpression(rx_pos_int)
        self.line_edit_amount.setValidator(pos_int_validator)
        double_validator = QRegularExpressionValidator()
        rx_double = QRegularExpression("^[-+]?[0-9]*[.,][0-9]+$")
        double_validator.setRegularExpression(rx_double)
        self.line_edit_temp_ref.setValidator(double_validator)
        list_ports = serial.tools.list_ports.comports()
        self.combo_box_com.addItem('')
        for el in list_ports:
            self.combo_box_com.addItem(el.name)

        self.show()

        self.start_button.clicked.connect(self.start_button_clicked)
        self.start_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.stop_button.setEnabled(False)
        self.download_button.clicked.connect(self.download_button_clicked)
        self.combo_box_com.currentIndexChanged.connect(self.combo_box_com_handler)

        self.data_receiver = DataReceiver()
        self.receiver_thread = QThread()

        self.num.connect(self.data_receiver.receive_data)
        self.downloaded.connect(self.csv_downloaded)
        self.radio_cont.toggled.connect(self.cont_setter)
        self.data_receiver.new_data.connect(self.update_table)
        self.data_receiver.disable_stop.connect(self.stop_button_clicked)
        self.data_receiver.processing.connect(self.data_processing_indication)

        self.timer = QTimer(self, interval=700)
        self.timer.timeout.connect(self.data_processing_indication)

        try:
            self.types_and_names, self.formulas = parse_config()
        except KeyError:
            self.ini_error()

        rows = ['Item №', 'Type', 'Name', 'Mean', 'RMSD']
        self.tableWidget.setRowCount(len(rows))
        self.tableWidget.setColumnCount(len(self.types_and_names) + 1)
        self.tableWidget.setColumnWidth(0, 75)

        self.BoldFont = QFont(QFont("Courier New", 10))
        self.BoldFont.setBold(True)

        for i, row in enumerate(rows):
            self.tableWidget.setItem(i, 0, QTableWidgetItem(row))
            self.tableWidget.item(i, 0).setFont(self.BoldFont)

        for i, el in enumerate(self.types_and_names):
            self.tableWidget.setColumnWidth(i + 1, 80)
            self.tableWidget.setItem(0, i + 1, QTableWidgetItem(str(i + 1)))
            self.tableWidget.item(0, i + 1).setFont(self.BoldFont)
            self.tableWidget.setItem(1, i + 1, QTableWidgetItem(str(el[0])))
            self.tableWidget.item(1, i + 1).setFont(self.BoldFont)
            self.tableWidget.setItem(2, i + 1, QTableWidgetItem(str(el[1])))
            self.tableWidget.item(2, i + 1).setFont(self.BoldFont)

        self.guide_label.setText('<style></style><strong><font color="#2E8B57" size=4>Выберите COM-порт</font></strong>')

        self.data_receiver.moveToThread(self.receiver_thread)

    def combo_box_com_handler(self):
        self.guide_label.setText('<strong><font color="#2E8B57" size=4>Нажмите "Старт"</font></strong>')
        if self.combo_box_com.currentText() == '':
            self.guide_label.setText('<strong><font color="#2E8B57" size=4>Выберите COM-порт</font></strong>')
            self.start_button.setEnabled(False)
        else:
            self.start_button.setEnabled(True)

    def start_button_clicked(self):
        self.guide_label.setText('<strong><font color="#2E8B57" size=4>Включите устройство</font></strong>')
        self.receiver_thread.start()
        self.table_first_upd = True
        self.data_receiver.receiver_thread_stop = False
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.num.emit(int(self.line_edit_amount.text()))
        self.data_receiver.port_num = self.combo_box_com.currentText()
        self.line_edit_amount.setEnabled(False)
        self.combo_box_com.setEnabled(False)

    def stop_button_clicked(self):
        self.data_receiver.receiver_thread_stop = True
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.line_edit_amount.setEnabled(True)
        self.combo_box_com.setEnabled(True)
        self.timer.stop()
        self.guide_label.setText('<strong><font color="#2E8B57" size=4>Нажмите "Старт"</font></strong>')

    def data_processing_indication(self):
        self.timer.start()
        if self.process_ind_blink:
            self.guide_label.setText('<strong><font color="#2E8B57" size=4>Получение данных</font></strong>')
        else:
            self.guide_label.setText('')
        self.process_ind_blink = not self.process_ind_blink

    def cont_setter(self):
        if self.sender().isChecked():
            self.data_receiver.cont = True
            self.line_edit_amount.setEnabled(False)
        else:
            self.data_receiver.cont = False
            self.line_edit_amount.setEnabled(True)

    def download_button_clicked(self):
        self.download_button.setEnabled(False)
        with open(f'Data_{strftime("%H-%M-%S", localtime())}.csv', 'w', newline='') as f:
            writer = csv.writer(f, 'Semicolon')
            for row in range(self.tableWidget.rowCount()):
                row_data = []
                for col in range(self.tableWidget.columnCount()):
                    item = self.tableWidget.item(row, col)
                    if item is not None:
                        row_data.append(item.text())
                if self.line_edit_temp_ref.text():
                    if row <= 4 and row != 2:
                        row_data.append('-')
                    elif row > 4:
                        t_ref = self.line_edit_temp_ref.text()
                        if len(t_ref) < 9:
                            if ',' not in t_ref and '.' not in t_ref:
                                t_ref += '.'
                            t_ref += (9 - len(t_ref)) * '0'
                        row_data.append(t_ref.replace(',', '.'))
                    else:
                        row_data.append('tref')
                writer.writerow(row_data)
        self.downloaded.emit()
        self.download_button.setEnabled(True)

    def update_table(self, data_list):
        if len(self.types_and_names) < len(data_list):
            dif = len(data_list) - len(self.types_and_names)
            self.types_and_names += dif * [('N/A', 'N/A')]
        if len(self.types_and_names) > len(data_list):
            dif = len(self.types_and_names) - len(data_list)
            data_list += dif * [None]
        if len(data_list) == len(self.types_and_names):
            if self.table_first_upd:
                self.tableWidget.setRowCount(0)
                self.tableWidget.setColumnCount(len(data_list)+1)
                self.tableWidget.setColumnWidth(0, 75)

                self.tableWidget.insertRow(0)
                self.tableWidget.setItem(0, 0, QTableWidgetItem('Item №'))
                self.tableWidget.item(0, 0).setFont(self.BoldFont)
                for i in range(len(data_list)):
                    self.tableWidget.setColumnWidth(i + 1, 80)
                    self.tableWidget.setItem(0, i + 1, QTableWidgetItem(str(i+1)))
                    self.tableWidget.item(0, i + 1).setFont(self.BoldFont)

                self.tableWidget.insertRow(1)
                self.tableWidget.setItem(1, 0, QTableWidgetItem('Type'))
                self.tableWidget.item(1, 0).setFont(self.BoldFont)
                for i in range(len(data_list)):
                    self.tableWidget.setItem(1, i + 1, QTableWidgetItem(self.types_and_names[i][0]))
                    self.tableWidget.item(1, i + 1).setFont(self.BoldFont)

                self.tableWidget.insertRow(2)
                self.tableWidget.setItem(2, 0, QTableWidgetItem('Name'))
                self.tableWidget.item(2, 0).setFont(self.BoldFont)
                for i in range(len(data_list)):
                    self.tableWidget.setItem(2, i + 1, QTableWidgetItem(self.types_and_names[i][1]))
                    self.tableWidget.item(2, i + 1).setFont(self.BoldFont)

                self.tableWidget.insertRow(3)
                self.tableWidget.setItem(3, 0, QTableWidgetItem('Mean'))
                self.tableWidget.item(3, 0).setFont(self.BoldFont)
                for i, el in enumerate(data_list):
                    self.tableWidget.setItem(3, i + 1, QTableWidgetItem(el))

                self.tableWidget.insertRow(4)
                self.tableWidget.setItem(4, 0, QTableWidgetItem('RMSD'))
                self.tableWidget.item(4, 0).setFont(self.BoldFont)
                for i, el in enumerate(data_list):
                    self.tableWidget.setItem(4, i + 1, QTableWidgetItem(el))

                self.data_sum = [0 for _ in data_list]
                self.data_sum_sq = [0 for _ in data_list]
                self.table_first_upd = False

            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            self.tableWidget.setItem(row, 0, QTableWidgetItem(strftime("%H:%M:%S", localtime())))
            for i, el in enumerate(data_list):
                device_type = self.types_and_names[i][0]
                name = self.types_and_names[i][1]
                if el is not None:
                    if name != 'N/A':
                        try:
                            el = self.formulas[device_type][name][0] + self.formulas[device_type][name][1] * float(el)
                        except KeyError:
                            self.ini_error()
                        el_str = "%.6f" % el
                    self.tableWidget.setItem(row, i + 1, QTableWidgetItem(el_str))
                    self.data_sum[i] += float(el)
                    mean = self.data_sum[i] / (self.tableWidget.rowCount() - 5)
                    self.data_sum_sq[i] += (float(el) - mean)**2
                    rmsd = (self.data_sum_sq[i] / (self.tableWidget.rowCount() - 5)) ** 0.5
                    mean = "%.6f" % mean
                    rmsd = "%.2e" % rmsd
                    self.tableWidget.setItem(3, i + 1, QTableWidgetItem(mean))
                    self.tableWidget.item(3, i + 1).setFont(self.BoldFont)
                    self.tableWidget.setItem(4, i + 1, QTableWidgetItem(rmsd))
                    self.tableWidget.item(4, i + 1).setFont(self.BoldFont)

    def csv_downloaded(self):
        QMessageBox.information(
            self,
            'Information',
            'Сохранено'
        )

    def ini_error(self):
        QMessageBox.critical(
            self,
            'Critical',
            'Ошибка .ini'
        )
        sys.exit()


if __name__ == '__main__':
    csv.register_dialect('Semicolon', delimiter=';')
    app = QApplication(sys.argv)
    termoline_window = Termoline()
    sys.exit(app.exec())
import sys
import serial
import csv

from time import localtime, strftime
from parse_config import parse_config
from PyQt6.QtCore import QThread, QObject, pyqtSignal as Signal, pyqtSlot as Slot, QEvent
from PyQt6.QtWidgets import QApplication,  QMainWindow, QTableWidgetItem
from PyQt6.QtGui import QIcon
from termoline_ui import Ui_Termoline


class DataReceiver(QObject):

    new_data = Signal(list)
    receiver_thread_stop = False
    cont = False

    def new_data_handler(self, com):
        if self.receiver_thread_stop:
            return
        data_list = str(com.readline()).split(';')[1:-1]
        self.new_data.emit(data_list)

    @Slot(int)
    def receive_data(self, num):
        COM = serial.Serial(port='COM3', baudrate=9600, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
        print(f'cont {self.cont}')
        if self.cont:
            while True:
                print(self.cont)
                if self.receiver_thread_stop:
                    break
                self.new_data_handler(COM)
        else:
            for _ in range(num):
                if self.receiver_thread_stop:
                    break
                self.new_data_handler(COM)
        COM.close()


class Termoline(QMainWindow, Ui_Termoline):

    num = Signal(int)
    table_first_upd = True
    data_sum = None
    data_sum_sq = None
    types_and_names, formulas = parse_config()

    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('marlin_icon.jpg'))
        self.setupUi(self)
        self.setWindowTitle('Termoline')
        self.tableWidget.horizontalHeader().setVisible(False)
        self.tableWidget.verticalHeader().setVisible(False)
        self.line_edit_amount.setText('50')
        self.show()

        self.start_button.clicked.connect(self.start_button_clicked)
        self.stop_button.clicked.connect(self.stop_button_clicked)
        self.download_button.clicked.connect(self.download_button_clicked)

        self.data_receiver = DataReceiver()
        self.receiver_thread = QThread()

        self.num.connect(self.data_receiver.receive_data)
        self.radio_cont.toggled.connect(self.cont_setter)
        self.data_receiver.new_data.connect(self.update_table)

        self.data_receiver.moveToThread(self.receiver_thread)

    def start_button_clicked(self):
        self.receiver_thread.start()
        self.table_first_upd = True
        self.data_receiver.receiver_thread_stop = False
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.num.emit(int(self.line_edit_amount.text()))
        self.line_edit_amount.setEnabled(False)

    def stop_button_clicked(self):
        self.data_receiver.receiver_thread_stop = True
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.line_edit_amount.setEnabled(True)
        self.receiver_thread.exit()

    def cont_setter(self):
        if self.sender().isChecked():
            self.data_receiver.cont = True
        else:
            self.data_receiver.cont = False

    def download_button_clicked(self):
        self.download_button.setEnabled(False)
        with open(f'Data_{strftime("%H-%M-%S", localtime())}.csv', 'w', newline='') as f:
            writer = csv.writer(f)
            for row in range(self.tableWidget.rowCount()):
                row_data = []
                for col in range(self.tableWidget.columnCount()):
                    item = self.tableWidget.item(row, col)
                    if item is not None:
                        row_data.append(item.text())
                writer.writerow(row_data)
        self.download_button.setEnabled(True)

    def update_table(self, data_list):
        if len(data_list) == len(self.types_and_names):
            if self.table_first_upd:
                self.tableWidget.setRowCount(0)
                self.tableWidget.setColumnCount(len(data_list)+1)
                self.tableWidget.setColumnWidth(0, 50)

                for i in range(len(data_list)):
                    self.tableWidget.setColumnWidth(i+1, 60)

                self.tableWidget.insertRow(0)
                self.tableWidget.setItem(0, 0, QTableWidgetItem('Item №'))
                for i in range(len(data_list)):
                    self.tableWidget.setItem(0, i + 1, QTableWidgetItem(str(i+1)))

                self.tableWidget.insertRow(1)
                self.tableWidget.setItem(1, 0, QTableWidgetItem('Type'))
                for i in range(len(data_list)):
                    self.tableWidget.setItem(1, i + 1, QTableWidgetItem(self.types_and_names[i][0]))

                self.tableWidget.insertRow(2)
                self.tableWidget.setItem(2, 0, QTableWidgetItem('Name'))
                for i in range(len(data_list)):
                    self.tableWidget.setItem(2, i + 1, QTableWidgetItem(self.types_and_names[i][1]))

                self.tableWidget.insertRow(3)
                self.tableWidget.setItem(3, 0, QTableWidgetItem('Mean'))
                for i, el in enumerate(data_list):
                    self.tableWidget.setItem(3, i + 1, QTableWidgetItem(el))

                self.tableWidget.insertRow(4)
                self.tableWidget.setItem(4, 0, QTableWidgetItem('RMSD'))
                for i, el in enumerate(data_list):
                    self.tableWidget.setItem(4, i + 1, QTableWidgetItem(el))

                self.data_sum = [0 for _ in data_list]
                self.data_sum_sq = [0 for _ in data_list]
                self.table_first_upd = False

            row = self.tableWidget.rowCount()
            self.tableWidget.insertRow(row)
            self.tableWidget.setItem(row, 0, QTableWidgetItem(strftime("%H:%M:%S", localtime())))
            for i, el in enumerate(data_list):
                name = self.types_and_names[i][1]
                el = str(self.formulas[name][0] + self.formulas[name][1] * float(el))
                self.tableWidget.setItem(row, i + 1, QTableWidgetItem(el))
                self.data_sum[i] += float(el)
                mean = self.data_sum[i] / (self.tableWidget.rowCount() - 5)
                self.data_sum_sq[i] += (float(el) - mean)**2
                rmsd = (self.data_sum_sq[i] / (self.tableWidget.rowCount() - 5)) ** 0.5
                mean = "%.6f" % mean
                rmsd = "%.1e" % rmsd
                self.tableWidget.setItem(3, i + 1, QTableWidgetItem(mean))
                self.tableWidget.setItem(4, i + 1, QTableWidgetItem(rmsd))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    termoline_window = Termoline()
    sys.exit(app.exec())
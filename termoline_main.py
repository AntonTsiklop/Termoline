import sys
import serial
import time

from PyQt6.QtCore import QThread, QObject, pyqtSignal as Signal, pyqtSlot as Slot
from PyQt6.QtWidgets import QApplication,  QMainWindow, QPushButton, QWidget, QGridLayout, QProgressBar, QTableWidget, QTableWidgetItem
from PyQt6.QtGui import QIcon
from termoline_ui import Ui_Termoline


class DataReceiver(QObject):

    new_data = Signal(list)
    receiver_thread_stop = False

    @Slot(int)
    def receive_data(self, num):
        COM = serial.Serial(port='COM3', baudrate=9600, bytesize=8, timeout=2, stopbits=serial.STOPBITS_ONE)
        for _ in range(num):
            if self.receiver_thread_stop:
                break
            data_list = str(COM.readline()).split(';')[1:-1]
            self.new_data.emit(data_list)


class Termoline(QMainWindow, Ui_Termoline):
    num = Signal(int)
    table_first_upd = True

    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon('marlin_icon.jpg'))
        self.setupUi(self)
        self.setWindowTitle('Termoline')
        self.tableWidget.horizontalHeader().setVisible(False)
        self.show()

        self.start_button.clicked.connect(self.start_button_clicked)
        self.stop_button.clicked.connect(self.stop_button_clicked)

        self.data_receiver = DataReceiver()
        self.receiver_thread = QThread()

        self.data_receiver.new_data.connect(self.update_table)
        self.num.connect(self.data_receiver.receive_data)

        self.data_receiver.moveToThread(self.receiver_thread)
        self.receiver_thread.start()

    def start_button_clicked(self):
        self.data_receiver.receiver_thread_stop = False
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.table_first_upd = True
        self.num.emit(20)

    def stop_button_clicked(self):
        self.data_receiver.receiver_thread_stop = True
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def update_table(self, data_list):
        if self.table_first_upd:
            self.tableWidget.setRowCount(0)
            self.tableWidget.setColumnCount(len(data_list)+1)
            self.tableWidget.setColumnWidth(0, 50)
            for i in range(1, len(data_list)+1):
                self.tableWidget.setColumnWidth(i, 60)
            self.tableWidget.insertRow(0)
            self.tableWidget.setItem(0, 0, QTableWidgetItem('Item №'))
            for i in range(1, len(data_list)+1):
                self.tableWidget.setItem(0, i, QTableWidgetItem(str(i)))
            self.tableWidget.insertRow(1)
            self.tableWidget.setItem(1, 0, QTableWidgetItem('Mean'))
            for i, el in enumerate(data_list):
                self.tableWidget.setItem(1, i+1, QTableWidgetItem(el))
            self.tableWidget.insertRow(2)
            self.tableWidget.setItem(2, 0, QTableWidgetItem('RMS'))
            for i, el in enumerate(data_list):
                self.tableWidget.setItem(2, i+1, QTableWidgetItem(el))
            data_sum = [0 for _ in data_list]
            data_sum_sq = [0 for _ in data_list]
            self.table_first_upd = False
        row = self.tableWidget.rowCount()
        self.tableWidget.insertRow(row)
        self.tableWidget.setItem(row, 0, QTableWidgetItem(time.strftime("%H:%M:%S", time.localtime())))
        for i, el in enumerate(data_list):
            self.tableWidget.setItem(row, i+1, QTableWidgetItem(el))
            data_sum[i] += float(el)
            print(data_sum)
            data_sum_sq[i] += float(el)**2
            print(data_sum_sq)



if __name__ == '__main__':
    app = QApplication(sys.argv)
    termoline_window = Termoline()
    app.exec()
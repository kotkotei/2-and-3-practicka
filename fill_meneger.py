from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QMenuBar, QMenu, QFileDialog, QInputDialog
from os import walk
from PyQt5.QtWidgets import *

class Ui_MainWindow(object):
    per=''
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(340, 401)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.listWidget = QtWidgets.QListWidget(self.centralwidget)
        self.listWidget.setObjectName("listWidget")
        self.verticalLayout.addWidget(self.listWidget)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setObjectName("pushButton")
        self.verticalLayout.addWidget(self.pushButton)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 340, 26))
        self.menubar.setObjectName("menubar")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)



    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "MainWindow"))
        self.pushButton.setText(_translate("MainWindow", "Выбрать папку"))
        self.pushButton.clicked.connect(self.pushButton_handler)

    def pushButton_handler(self):

        self.open_dialog_box()

    def open_dialog_box(self):
        filename =QFileDialog.getExistingDirectory()
        self.per=filename
        print(filename)

        filenames = next(walk(filename), (None, None, []))[2]  # [] if no file

        for i in range(0,len(filenames)):
            self.listWidget.addItem(filenames[i])

        self.listWidget.itemClicked.connect(self.onClicked)

    def onClicked(self, item):

        text=item.text()
        self.listWidget.clear()


        file1 = open(self.per + '/' + text, "r")
        # считываем все строки
        lines = file1.readlines()

        # итерация по строкам
        for line in lines:
            self.listWidget.addItem(line.strip())

        # закрываем файл
        file1.close
        #self.listWidget.addItem(item.text())














'''
        #filename=QFileDialog.getExistingDirectory()
        path=filename[0]
        print(path)
        #проверка файл /папка?
        file1 = open(path, "r")

        # считываем все строки
        lines = file1.readlines()

        # итерация по строкам
        for line in lines:
            self.listWidget.addItem(line.strip())

        # закрываем файл
        file1.close'''





if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())
# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'node.ui'
#
# Created by: PyQt5 UI code generator 5.15.1
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setEnabled(True)
        Form.resize(463, 219)
        self.radioButton = QtWidgets.QRadioButton(Form)
        self.radioButton.setEnabled(True)
        self.radioButton.setGeometry(QtCore.QRect(40, 80, 16, 17))
        self.radioButton.setText("")
        self.radioButton.setCheckable(True)
        self.radioButton.setChecked(False)
        self.radioButton.setAutoRepeat(True)
        self.radioButton.setObjectName("radioButton")
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(30, 80, 16, 16))
        self.label.setObjectName("label")
        self.resistor = QtWidgets.QGroupBox(Form)
        self.resistor.setGeometry(QtCore.QRect(110, 20, 81, 51))
        self.resistor.setObjectName("resistor")
        self.pushButton = QtWidgets.QPushButton(self.resistor)
        self.pushButton.setGeometry(QtCore.QRect(50, 20, 31, 23))
        self.pushButton.setObjectName("pushButton")
        self.doubleSpinBox = QtWidgets.QDoubleSpinBox(self.resistor)
        self.doubleSpinBox.setGeometry(QtCore.QRect(10, 20, 41, 22))
        self.doubleSpinBox.setObjectName("doubleSpinBox")
        self.resistor_2 = QtWidgets.QGroupBox(Form)
        self.resistor_2.setGeometry(QtCore.QRect(110, 90, 81, 51))
        self.resistor_2.setObjectName("resistor_2")
        self.pushButton_10 = QtWidgets.QPushButton(self.resistor_2)
        self.pushButton_10.setGeometry(QtCore.QRect(50, 20, 31, 23))
        self.pushButton_10.setObjectName("pushButton_10")
        self.doubleSpinBox_15 = QtWidgets.QDoubleSpinBox(self.resistor_2)
        self.doubleSpinBox_15.setGeometry(QtCore.QRect(10, 20, 41, 22))
        self.doubleSpinBox_15.setObjectName("doubleSpinBox_15")
        self.add_new_line = QtWidgets.QPushButton(Form)
        self.add_new_line.setGeometry(QtCore.QRect(270, 140, 75, 23))
        self.add_new_line.setObjectName("add_new_line")
        self.pushButton_3 = QtWidgets.QPushButton(Form)
        self.pushButton_3.setGeometry(QtCore.QRect(360, 160, 61, 31))
        self.pushButton_3.setObjectName("pushButton_3")
        self.front_resistor = QtWidgets.QGroupBox(Form)
        self.front_resistor.setGeometry(QtCore.QRect(110, 30, 81, 41))
        self.front_resistor.setTitle("")
        self.front_resistor.setObjectName("front_resistor")
        self.resistor_text = QtWidgets.QLabel(self.front_resistor)
        self.resistor_text.setGeometry(QtCore.QRect(20, 10, 21, 16))
        self.resistor_text.setObjectName("resistor_text")
        self.edit = QtWidgets.QPushButton(self.front_resistor)
        self.edit.setGeometry(QtCore.QRect(40, 10, 31, 23))
        self.edit.setObjectName("edit")
        self.front_resistor_2 = QtWidgets.QGroupBox(Form)
        self.front_resistor_2.setGeometry(QtCore.QRect(110, 100, 81, 41))
        self.front_resistor_2.setTitle("")
        self.front_resistor_2.setObjectName("front_resistor_2")
        self.resistor_text_4 = QtWidgets.QLabel(self.front_resistor_2)
        self.resistor_text_4.setGeometry(QtCore.QRect(20, 10, 21, 16))
        self.resistor_text_4.setObjectName("resistor_text_4")
        self.edit_2 = QtWidgets.QPushButton(self.front_resistor_2)
        self.edit_2.setGeometry(QtCore.QRect(40, 10, 31, 23))
        self.edit_2.setObjectName("edit_2")
        self.comboBox_2 = QtWidgets.QComboBox(Form)
        self.comboBox_2.setGeometry(QtCore.QRect(220, 110, 61, 22))
        self.comboBox_2.setObjectName("comboBox_2")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_3 = QtWidgets.QComboBox(Form)
        self.comboBox_3.setGeometry(QtCore.QRect(220, 40, 61, 22))
        self.comboBox_3.setObjectName("comboBox_3")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.front_resistor_2.raise_()
        self.front_resistor.raise_()
        self.radioButton.raise_()
        self.label.raise_()
        self.resistor.raise_()
        self.resistor_2.raise_()
        self.add_new_line.raise_()
        self.pushButton_3.raise_()
        self.comboBox_2.raise_()
        self.comboBox_3.raise_()

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label.setText(_translate("Form", "A"))
        self.resistor.setTitle(_translate("Form", "Resistor"))
        self.pushButton.setText(_translate("Form", "OK"))
        self.resistor_2.setTitle(_translate("Form", "Resistor"))
        self.pushButton_10.setText(_translate("Form", "OK"))
        self.add_new_line.setText(_translate("Form", "Add new line"))
        self.pushButton_3.setText(_translate("Form", "OK"))
        self.resistor_text.setText(_translate("Form", "0"))
        self.edit.setText(_translate("Form", "Edit"))
        self.resistor_text_4.setText(_translate("Form", "0"))
        self.edit_2.setText(_translate("Form", "Edit"))
        self.comboBox_2.setCurrentText(_translate("Form", "resistor"))
        self.comboBox_2.setItemText(0, _translate("Form", "resistor"))
        self.comboBox_2.setItemText(1, _translate("Form", "node"))
        self.comboBox_3.setCurrentText(_translate("Form", "resistor"))
        self.comboBox_3.setItemText(0, _translate("Form", "resistor"))
        self.comboBox_3.setItemText(1, _translate("Form", "node"))

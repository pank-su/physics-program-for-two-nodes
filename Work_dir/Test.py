from datetime import datetime
from json import dump, load
import os
from random import randint
from shutil import copy2
import sqlite3
import sys

import numpy as np
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtSql import *
from PyQt5.QtWidgets import QMainWindow, QApplication, QGroupBox, QDoubleSpinBox, QLineEdit, \
    QPushButton

# import можно было оптимизировать тк не которые модули используют два метода.

legs = []


# это класс самой задачи
class Task:
    def __init__(self, legs=3):
        self.legs = [list() for i in range(legs)]

    # Добавление источника в одну из ветвей
    def add_generator(self, leg_index: int, direction: str, voltage: float, resistance: float,
                      qt_object):
        self.legs[leg_index].append((resistance, direction, voltage, qt_object))

    # добавление резистора
    def add_resistor(self, leg_index: int, resistance: float, qt_object):
        self.legs[leg_index].append((resistance, qt_object))

    # добавление новой ветви и возвращение id этой ветви
    def add_new_line(self):
        self.legs.append(list())
        return len(self.legs) - 1

    # редактирование резистора
    def edit_resistor(self, leg_index, el_index, resistance):
        try:
            old = self.legs[leg_index][el_index]
            new = (resistance, old[1])
            self.legs[leg_index][el_index] = new
        except Exception as e:
            print(e)

    # редактирование источника
    def edit_generator(self, leg_index: int, el_index: int, direction: str, voltage: float,
                       resistance: float):
        old = self.legs[leg_index][el_index]
        new = (resistance, direction, voltage, old[-1])
        self.legs[leg_index][el_index] = new

    # добаление узла(нереализованное действие)
    def add_node(self, leg_index: int, legs_num: int):
        self.legs[leg_index].append(Task_in_task(legs_num))
        return self.legs[leg_index][-1]

    # перевод всей задачи в нормальный вид(вид в котором могут читать функции методов)
    def normal(self) -> list:
        result = list()
        for el in self.legs:
            resistance_sum = 0
            voltage_sum = 0
            direction_sum = 'L'
            for el_in_el in el:
                if isinstance(el_in_el, tuple):
                    resistance_sum += el_in_el[0]
                    if len(el_in_el) == 4:
                        voltage_sum += el_in_el[2] * (-1 if el_in_el[1] == 'R' else 1)
                elif isinstance(el_in_el, Task_in_task):
                    resistance_sum += el_in_el.return_resistance()
            if voltage_sum < 0:
                voltage_sum *= -1
                direction_sum = 'R'
            result.append([resistance_sum, direction_sum, voltage_sum])
        return result


# Нереализованный класс нового узла.
class Task_in_task(Task):
    def __init__(self, legs=2):
        super().__init__(legs)

    # Нельзя добавлять генератор
    def add_generator(self, leg_index: int, direction: str, voltage: float, resistance: float,
                      qt_object):
        pass

    # Возврат сопротивления
    def return_resistance(self) -> float:
        result = 0
        print(self.legs)
        for i in range(len(self.legs)):
            try:
                result += 1 / sum(map(lambda a: a[0], self.legs[i]))
            except TypeError:
                pass
        return result ** -1


# Решение задачи MH методом и возврат значений токов
def MH_method(legs: list) -> dict:
    result = []
    dict_of_i = {}
    [dict_of_i.update({el + 1: []}) for el in range(len(legs))]
    for el in range(len(legs)):
        if legs[el][1] == 'R':
            minus_or_plus = -1
        else:
            minus_or_plus = 1
        r1 = round(sum([1 / el_2[0] for index, el_2 in enumerate(legs) if el != index]) ** -1, 2)
        i = round(legs[el][2] / (r1 + legs[el][0]), 2)
        dict_of_i[el + 1].append(i * minus_or_plus)
        uab = round(r1 * i, 2)
        for index, el_3 in enumerate([el_2[0] for el_2 in legs]):
            if index != el:
                dict_of_i[index + 1].append(round(uab / el_3 * -1 * minus_or_plus, 2))
    return dict_of_i


# Тоже самое, только для красивого вывода(для вывода решения)
def MH_method_for_out(legs: list):
    result = []
    dict_of_i = {}
    [dict_of_i.update({el + 1: []}) for el in range(len(legs))]
    for el in range(len(legs)):
        if legs[el][1] == 'R':
            minus_or_plus = -1
        else:
            minus_or_plus = 1
        r1 = round(sum([1 / el_2[0] for index, el_2 in enumerate(legs) if el != index]) ** -1, 2)
        yield r1
        i = round(legs[el][2] / (r1 + legs[el][0]), 2)
        dict_of_i[el + 1].append(i * minus_or_plus)
        yield str(el + 1), str(legs[el][2]) + '/' + str(r1 + legs[el][0])
        yield str(i * minus_or_plus)
        uab = round(r1 * i, 2)
        yield uab
        for index, el_3 in enumerate([el_2[0] for el_2 in legs]):
            if index != el:
                dict_of_i[index + 1].append(round(uab / el_3 * -1 * minus_or_plus, 2))
                yield str(index + 1), str(uab) + '/' + str(el_3)
                yield str(round(uab / el_3 * -1 * minus_or_plus, 2))
    yield dict_of_i


# Решение задачи MУH методом и возврат значений токов
def MYH_method(legs: list) -> dict:
    dict_of_i = {}
    gs = [round(1 / el[0], 3) for el in legs]
    edss = [-el[2] if el[1] == 'R' else el[2] for el in legs]
    uab = round(sum([gs[i] * edss[i] for i in range(len(legs))]) / sum(gs), 2)
    for i in range(len(legs)):
        dict_of_i[i + 1] = (edss[i] - uab) * gs[i]
    return dict_of_i


# Тоже самое, только для красивого вывода(для вывода решения)
def MYH_method_for_out(legs: list):
    dict_of_i = {}
    gs = [round(1 / el[0], 3) for el in legs]
    yield gs
    edss = [-el[2] if el[1] == 'R' else el[2] for el in legs]
    uab = round(sum([gs[i] * edss[i] for i in range(len(legs))]) / sum(gs), 2)
    yield uab
    for i in range(len(legs)):
        dict_of_i[i + 1] = (edss[i] - uab) * gs[i]
        yield f'I{i + 1} = ({edss[i]} - {uab}) * {gs[i]} = {round((edss[i] - uab) * gs[i], 4)}'
    yield dict_of_i


# Это вспомогательная функция для МУКУ метода,
# чтобы получить определённый порядок для создания системы уравнения
def MYKY_help_1(num: int) -> list:
    result = []
    x = 0
    for i in range(1, num + 1):
        if i == 1:
            result.append([i])
        elif i == num:
            result[x].append(i)
        else:
            result[x].append(i)
            x += 1
            result.append([i])
    return result


# Решение задачи MУКУ методом и возврат значений токов
def MYKY_method(legs: list):
    array = MYKY_help_1(len(legs))
    b = [0]
    for g in range(len(array)):
        one = legs[array[g][0] - 1][2] * (-1 if legs[array[g][0] - 1][1] == 'L' else 1)
        second = legs[array[g][1] - 1][2] * (-1 if legs[array[g][1] - 1][1] == 'R' else 1)
        b.append(one + second)
    a = [[1] * len(legs)]
    for g in range(len(array)):
        a.append(
            [(legs[i - 1][0] if array[g].index(i) == 1 else -legs[i - 1][0]) if i in array[g] else 0
             for i in
             range(1, len(legs) + 1)])  # заполнение матрицы
    a = np.array(a)
    b = np.array(b)
    x = np.linalg.solve(a, b)
    return x


# Тоже самое, только для красивого вывода(для вывода решения)
def MYKY_method_for_out(legs: list):
    array = MYKY_help_1(len(legs))
    b = [0]
    for g in range(len(array)):
        one = legs[array[g][0] - 1][2] * (-1 if legs[array[g][0] - 1][1] == 'L' else 1)
        second = legs[array[g][1] - 1][2] * (-1 if legs[array[g][1] - 1][1] == 'R' else 1)
        b.append(one + second)
    a = [[1] * len(legs)]
    for g in range(len(array)):
        a.append(
            [(legs[i - 1][0] if array[g].index(i) == 1 else -legs[i - 1][0]) if i in array[g] else 0
             for i in
             range(1, len(legs) + 1)])  # заполнение матрицы
    for el, el_2 in zip(a, b):
        yield '[' + ' '.join(list(map(str, el))) + ']' + '  ' + '[' + str(el_2) + ']'
    a = np.array(a)
    b = np.array(b)
    x = np.linalg.solve(a, b)
    yield x


# Это класс дизайна вывода решения
class Decide(object):
    def __init__(self, parent=None):
        self.setupUi(parent.central_widget)

    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.resize(640, 768)
        self.verticalLayout = QtWidgets.QVBoxLayout(Form)
        self.verticalLayout.setObjectName("verticalLayout")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.MYH = QtWidgets.QLabel(Form)
        self.MYH.setObjectName("MYH")
        self.horizontalLayout.addWidget(self.MYH)
        self.line = QtWidgets.QFrame(Form)
        self.line.setFrameShape(QtWidgets.QFrame.VLine)
        self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line.setObjectName("line")
        self.horizontalLayout.addWidget(self.line)
        self.MH = QtWidgets.QLabel(Form)
        self.MH.setObjectName("MH")
        self.horizontalLayout.addWidget(self.MH)
        self.line_2 = QtWidgets.QFrame(Form)
        self.line_2.setFrameShape(QtWidgets.QFrame.VLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.line_2.setObjectName("line_2")
        self.horizontalLayout.addWidget(self.line_2)
        self.MYKY = QtWidgets.QLabel(Form)
        self.MYKY.setObjectName("MYKY")
        self.horizontalLayout.addWidget(self.MYKY)
        self.verticalLayout.addLayout(self.horizontalLayout)
        spacerItem = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum,
                                           QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem)
        self.tableView = QtWidgets.QTableView(Form)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                           QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(10)
        sizePolicy.setVerticalStretch(10)
        sizePolicy.setHeightForWidth(self.tableView.sizePolicy().hasHeightForWidth())
        self.tableView.setSizePolicy(sizePolicy)
        self.tableView.setObjectName("tableView")
        self.verticalLayout.addWidget(self.tableView)
        spacerItem1 = QtWidgets.QSpacerItem(20, 40, QtWidgets.QSizePolicy.Minimum,
                                            QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(spacerItem1)
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.info = QtWidgets.QLabel(Form)
        self.info.setText("")
        self.info.setObjectName("info")
        self.horizontalLayout_2.addWidget(self.info)
        spacerItem2 = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding,
                                            QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem2)
        self.save = QtWidgets.QPushButton(Form)
        self.save.setObjectName("save")
        self.horizontalLayout_2.addWidget(self.save)
        self.verticalLayout.addLayout(self.horizontalLayout_2)

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Решение"))
        self.MYH.setText(_translate("Form", "TextLabel"))
        self.MH.setText(_translate("Form", "TextLabel"))
        self.MYKY.setText(_translate("Form", "TextLabel"))
        self.save.setText(_translate("Form", "Save"))


# Это класс дизайна самой программы
class Ui_Form(object):
    def setupUi(self, Form):
        Form.setObjectName("Form")
        Form.setEnabled(True)
        Form.resize(751, 396)
        self.radioButton = QtWidgets.QRadioButton(Form)
        self.radioButton.setEnabled(True)
        self.radioButton.setGeometry(QtCore.QRect(40, 80, 16, 17))
        self.radioButton.setText("")
        self.radioButton.setCheckable(False)
        self.radioButton.setChecked(False)
        self.radioButton.setAutoRepeat(False)
        self.radioButton.setObjectName("radioButton")
        self.label = QtWidgets.QLabel(Form)
        self.label.setGeometry(QtCore.QRect(30, 80, 16, 16))
        self.label.setObjectName("label")
        # self.radioButton_2 = QtWidgets.QRadioButton(Form)
        # self.radioButton_2.setEnabled(True)
        # self.radioButton_2.setGeometry(QtCore.QRect(490, 80, 31, 21))
        # self.radioButton_2.setText("B")
        # self.radioButton_2.setCheckable(False)
        # self.radioButton_2.setChecked(False)
        # self.radioButton_2.setAutoRepeat(True)
        # self.radioButton_2.setObjectName("radioButton_2")
        self.generator = QtWidgets.QGroupBox(Form)
        self.generator.setEnabled(True)
        self.generator.setGeometry(QtCore.QRect(210, 0, 81, 81))
        self.generator.setFlat(False)
        self.generator.setCheckable(False)
        self.generator.setObjectName("generator")
        self.doubleSpinBox_2 = QtWidgets.QDoubleSpinBox(self.generator)
        self.doubleSpinBox_2.setGeometry(QtCore.QRect(10, 10, 41, 22))
        self.doubleSpinBox_2.setObjectName("doubleSpinBox_2")
        self.doubleSpinBox_2.setMaximum(999)
        self.pushButton_2 = QtWidgets.QPushButton(self.generator)
        self.pushButton_2.setGeometry(QtCore.QRect(40, 30, 31, 23))
        self.pushButton_2.setObjectName("pushButton_2")
        self.lineEdit = QtWidgets.QLineEdit(self.generator)
        self.lineEdit.setGeometry(QtCore.QRect(20, 30, 20, 20))
        self.lineEdit.setObjectName("lineEdit")
        self.doubleSpinBox_3 = QtWidgets.QDoubleSpinBox(self.generator)
        self.doubleSpinBox_3.setGeometry(QtCore.QRect(10, 50, 41, 22))
        self.doubleSpinBox_3.setObjectName("doubleSpinBox_3")
        self.resistor = QtWidgets.QGroupBox(Form)
        self.resistor.setGeometry(QtCore.QRect(120, 20, 81, 51))
        self.resistor.setObjectName("resistor")
        self.pushButton = QtWidgets.QPushButton(self.resistor)
        self.pushButton.setGeometry(QtCore.QRect(50, 20, 31, 23))
        self.pushButton.setObjectName("pushButton")
        self.doubleSpinBox = QtWidgets.QDoubleSpinBox(self.resistor)
        self.doubleSpinBox.setGeometry(QtCore.QRect(10, 20, 41, 22))
        self.doubleSpinBox.setObjectName("doubleSpinBox")
        self.generator_2 = QtWidgets.QGroupBox(Form)
        self.generator_2.setEnabled(True)
        self.generator_2.setGeometry(QtCore.QRect(210, 80, 81, 81))
        self.generator_2.setFlat(False)
        self.generator_2.setCheckable(False)
        self.generator_2.setObjectName("generator_2")
        self.doubleSpinBox_13 = QtWidgets.QDoubleSpinBox(self.generator_2)
        self.doubleSpinBox_13.setGeometry(QtCore.QRect(10, 10, 41, 22))
        self.doubleSpinBox_13.setObjectName("doubleSpinBox_13")
        self.doubleSpinBox_13.setMaximum(999)
        self.pushButton_9 = QtWidgets.QPushButton(self.generator_2)
        self.pushButton_9.setGeometry(QtCore.QRect(40, 30, 31, 23))
        self.pushButton_9.setObjectName("pushButton_9")
        self.lineEdit_5 = QtWidgets.QLineEdit(self.generator_2)
        self.lineEdit_5.setGeometry(QtCore.QRect(20, 30, 20, 20))
        self.lineEdit_5.setObjectName("lineEdit_5")
        self.doubleSpinBox_14 = QtWidgets.QDoubleSpinBox(self.generator_2)
        self.doubleSpinBox_14.setGeometry(QtCore.QRect(10, 50, 41, 22))
        self.doubleSpinBox_14.setObjectName("doubleSpinBox_14")
        self.resistor_2 = QtWidgets.QGroupBox(Form)
        self.resistor_2.setGeometry(QtCore.QRect(120, 90, 81, 51))
        self.resistor_2.setObjectName("resistor_2")
        self.pushButton_10 = QtWidgets.QPushButton(self.resistor_2)
        self.pushButton_10.setGeometry(QtCore.QRect(50, 20, 31, 23))
        self.pushButton_10.setObjectName("pushButton_10")
        self.doubleSpinBox_15 = QtWidgets.QDoubleSpinBox(self.resistor_2)
        self.doubleSpinBox_15.setGeometry(QtCore.QRect(10, 20, 41, 22))
        self.doubleSpinBox_15.setObjectName("doubleSpinBox_15")
        self.generator_3 = QtWidgets.QGroupBox(Form)
        self.generator_3.setEnabled(True)
        self.generator_3.setGeometry(QtCore.QRect(210, 160, 81, 81))
        self.generator_3.setFlat(False)
        self.generator_3.setCheckable(False)
        self.generator_3.setObjectName("generator_3")
        self.doubleSpinBox_19 = QtWidgets.QDoubleSpinBox(self.generator_3)
        self.doubleSpinBox_19.setGeometry(QtCore.QRect(10, 10, 41, 22))
        self.doubleSpinBox_19.setObjectName("doubleSpinBox_19")
        self.doubleSpinBox_19.setMaximum(999)
        self.pushButton_13 = QtWidgets.QPushButton(self.generator_3)
        self.pushButton_13.setGeometry(QtCore.QRect(40, 30, 31, 23))
        self.pushButton_13.setObjectName("pushButton_13")
        self.lineEdit_7 = QtWidgets.QLineEdit(self.generator_3)
        self.lineEdit_7.setGeometry(QtCore.QRect(20, 30, 20, 20))
        self.lineEdit_7.setObjectName("lineEdit_7")
        self.doubleSpinBox_20 = QtWidgets.QDoubleSpinBox(self.generator_3)
        self.doubleSpinBox_20.setGeometry(QtCore.QRect(10, 50, 41, 22))
        self.doubleSpinBox_20.setObjectName("doubleSpinBox_20")
        self.resistor_3 = QtWidgets.QGroupBox(Form)
        self.resistor_3.setGeometry(QtCore.QRect(120, 170, 81, 51))
        self.resistor_3.setObjectName("resistor_3")
        self.pushButton_14 = QtWidgets.QPushButton(self.resistor_3)
        self.pushButton_14.setGeometry(QtCore.QRect(50, 20, 31, 23))
        self.pushButton_14.setObjectName("pushButton_14")
        self.doubleSpinBox_21 = QtWidgets.QDoubleSpinBox(self.resistor_3)
        self.doubleSpinBox_21.setGeometry(QtCore.QRect(10, 20, 41, 22))
        self.doubleSpinBox_21.setObjectName("doubleSpinBox_21")
        self.add_new_line = QtWidgets.QPushButton(Form)
        self.add_new_line.setGeometry(QtCore.QRect(390, 230, 75, 23))
        self.add_new_line.setObjectName("add_new_line")
        # self.save_btn = QtWidgets.QPushButton(Form)
        # self.save_btn.setGeometry(QtCore.QRect(390, 300, 75, 23))
        # self.save_btn.setObjectName('save_btn')
        # self.save_btn.setText('save')
        self.comboBox = QtWidgets.QComboBox(Form)
        self.comboBox.setGeometry(QtCore.QRect(300, 190, 61, 22))
        self.comboBox.setObjectName("comboBox_3")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.comboBox.addItem("")
        self.decide = QtWidgets.QPushButton(Form)
        self.decide.setGeometry(QtCore.QRect(500, 310, 101, 31))
        self.decide.setObjectName("pushButton_3")
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
        self.front_resistor_3 = QtWidgets.QGroupBox(Form)
        self.front_resistor_3.setGeometry(QtCore.QRect(110, 180, 81, 41))
        self.front_resistor_3.setTitle("")
        self.front_resistor_3.setObjectName("front_resistor_3")
        self.resistor_text_2 = QtWidgets.QLabel(self.front_resistor_3)
        self.resistor_text_2.setGeometry(QtCore.QRect(20, 10, 21, 16))
        self.resistor_text_2.setObjectName("resistor_text_2")
        self.edit_3 = QtWidgets.QPushButton(self.front_resistor_3)
        self.edit_3.setGeometry(QtCore.QRect(40, 10, 31, 23))
        self.edit_3.setObjectName("edit_3")
        self.comboBox_2 = QtWidgets.QComboBox(Form)
        self.comboBox_2.setGeometry(QtCore.QRect(300, 110, 61, 22))
        self.comboBox_2.setObjectName("comboBox_2")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_2.addItem("")
        self.comboBox_3 = QtWidgets.QComboBox(Form)
        self.comboBox_3.setGeometry(QtCore.QRect(300, 30, 61, 22))
        self.comboBox_3.setObjectName("comboBox_1")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.comboBox_3.addItem("")
        self.front_generator = QtWidgets.QGroupBox(Form)
        self.front_generator.setGeometry(QtCore.QRect(220, 0, 61, 71))
        self.front_generator.setTitle("")
        self.front_generator.setObjectName("front_generator")
        self.label_2 = QtWidgets.QLabel(self.front_generator)
        self.label_2.setGeometry(QtCore.QRect(20, 10, 21, 16))
        self.label_2.setObjectName("label_2")
        self.label_3 = QtWidgets.QLabel(self.front_generator)
        self.label_3.setGeometry(QtCore.QRect(20, 50, 31, 20))
        self.label_3.setObjectName("label_3")
        self.label_4 = QtWidgets.QLabel(self.front_generator)
        self.label_4.setGeometry(QtCore.QRect(10, 30, 47, 16))
        self.label_4.setObjectName("label_4")
        self.pushButton_4 = QtWidgets.QPushButton(self.front_generator)
        self.pushButton_4.setGeometry(QtCore.QRect(30, 30, 31, 23))
        self.pushButton_4.setObjectName("pushButton_4")
        self.front_generator_3 = QtWidgets.QGroupBox(Form)
        self.front_generator_3.setGeometry(QtCore.QRect(220, 160, 61, 71))
        self.front_generator_3.setTitle("")
        self.front_generator_3.setObjectName("front_generator_3")
        self.label_23 = QtWidgets.QLabel(self.front_generator_3)
        self.label_23.setGeometry(QtCore.QRect(20, 10, 21, 16))
        self.label_23.setObjectName("label_23")
        self.label_24 = QtWidgets.QLabel(self.front_generator_3)
        self.label_24.setGeometry(QtCore.QRect(20, 50, 31, 20))
        self.label_24.setObjectName("label_24")
        self.label_25 = QtWidgets.QLabel(self.front_generator_3)
        self.label_25.setGeometry(QtCore.QRect(10, 30, 47, 16))
        self.label_25.setObjectName("label_25")
        self.pushButton_15 = QtWidgets.QPushButton(self.front_generator_3)
        self.pushButton_15.setGeometry(QtCore.QRect(30, 30, 31, 23))
        self.pushButton_15.setObjectName("pushButton_15")
        self.front_generator_2 = QtWidgets.QGroupBox(Form)
        self.front_generator_2.setGeometry(QtCore.QRect(220, 80, 61, 71))
        self.front_generator_2.setTitle("")
        self.front_generator_2.setObjectName("front_generator_2")
        self.label_11 = QtWidgets.QLabel(self.front_generator_2)
        self.label_11.setGeometry(QtCore.QRect(20, 10, 21, 16))
        self.label_11.setObjectName("label_11")
        self.label_12 = QtWidgets.QLabel(self.front_generator_2)
        self.label_12.setGeometry(QtCore.QRect(20, 50, 31, 20))
        self.label_12.setObjectName("label_12")
        self.label_13 = QtWidgets.QLabel(self.front_generator_2)
        self.label_13.setGeometry(QtCore.QRect(10, 30, 47, 16))
        self.label_13.setObjectName("label_13")
        self.pushButton_11 = QtWidgets.QPushButton(self.front_generator_2)
        self.pushButton_11.setGeometry(QtCore.QRect(30, 30, 31, 23))
        self.pushButton_11.setObjectName("pushButton_11")
        self.front_generator_2.raise_()
        self.front_generator_3.raise_()
        self.front_generator.raise_()
        self.front_resistor_3.raise_()
        self.front_resistor_2.raise_()
        self.front_resistor.raise_()
        self.radioButton.raise_()
        self.label.raise_()
        # self.radioButton_2.raise_()
        self.generator.raise_()
        self.resistor.raise_()
        self.generator_2.raise_()
        self.resistor_2.raise_()
        self.generator_3.raise_()
        self.resistor_3.raise_()
        self.add_new_line.raise_()
        self.comboBox.raise_()
        self.decide.raise_()
        self.comboBox_2.raise_()
        self.comboBox_3.raise_()

        self.retranslateUi(Form)
        QtCore.QMetaObject.connectSlotsByName(Form)

    def retranslateUi(self, Form):
        _translate = QtCore.QCoreApplication.translate
        Form.setWindowTitle(_translate("Form", "Form"))
        self.label.setText(_translate("Form", "A"))
        self.generator.setTitle(_translate("Form", "generator"))
        self.pushButton_2.setText(_translate("Form", "OK"))
        self.resistor.setTitle(_translate("Form", "Resistor"))
        self.pushButton.setText(_translate("Form", "OK"))
        self.generator_2.setTitle(_translate("Form", "generator"))
        self.pushButton_9.setText(_translate("Form", "OK"))
        self.resistor_2.setTitle(_translate("Form", "Resistor"))
        self.pushButton_10.setText(_translate("Form", "OK"))
        self.generator_3.setTitle(_translate("Form", "generator"))
        self.pushButton_13.setText(_translate("Form", "OK"))
        self.resistor_3.setTitle(_translate("Form", "Resistor"))
        self.pushButton_14.setText(_translate("Form", "OK"))
        self.add_new_line.setText(_translate("Form", "Add new line"))
        self.comboBox.setCurrentText(_translate("Form", "resistor"))
        self.comboBox.setItemText(0, _translate("Form", "resistor"))
        self.comboBox.setItemText(1, _translate("Form", "generator"))
        self.comboBox.setItemText(2, _translate("Form", "node"))
        self.decide.setText(_translate("Form", "Решить"))
        self.resistor_text.setText(_translate("Form", "0"))
        self.edit.setText(_translate("Form", "Edit"))
        self.resistor_text_4.setText(_translate("Form", "0"))
        self.edit_2.setText(_translate("Form", "Edit"))
        self.resistor_text_2.setText(_translate("Form", "0"))
        self.edit_3.setText(_translate("Form", "Edit"))
        self.comboBox_2.setCurrentText(_translate("Form", "resistor"))
        self.comboBox_2.setItemText(0, _translate("Form", "resistor"))
        self.comboBox_2.setItemText(1, _translate("Form", "generator"))
        self.comboBox_2.setItemText(2, _translate("Form", "node"))
        self.comboBox_3.setCurrentText(_translate("Form", "resistor"))
        self.comboBox_3.setItemText(0, _translate("Form", "resistor"))
        self.comboBox_3.setItemText(1, _translate("Form", "generator"))
        self.comboBox_3.setItemText(2, _translate("Form", "node"))
        self.label_2.setText(_translate("Form", "0"))
        self.label_3.setText(_translate("Form", "0"))
        self.label_4.setText(_translate("Form", "<---"))
        self.pushButton_4.setText(_translate("Form", "Edit"))
        self.label_23.setText(_translate("Form", "0"))
        self.label_24.setText(_translate("Form", "0"))
        self.label_25.setText(_translate("Form", "<---"))
        self.pushButton_15.setText(_translate("Form", "Edit"))
        self.label_11.setText(_translate("Form", "0"))
        self.label_12.setText(_translate("Form", "0"))
        self.label_13.setText(_translate("Form", "<---"))
        self.pushButton_11.setText(_translate("Form", "Edit"))


class MyWidget(QMainWindow, Ui_Form):
    def __init__(self, parent=None):
        self.plus_y = 80
        self.num_generator = 3
        super().__init__()
        self.setupUi(self)
        # self.save_btn = QtWidgets.QPushButton(self)
        # self.save_btn.setGeometry(QtCore.QRect(390, 300, 75, 23))
        # self.save_btn.setObjectName('save_btn')
        # self.save_btn.setText('save')

        # Соединение интерфейса с программой и некоторое его изменение
        self.comboBox.setObjectName("comboBox_3")
        self.comboBox_2.setObjectName("comboBox_2")
        self.comboBox_3.setObjectName("comboBox_1")
        self.resistor.setGeometry(QtCore.QRect(120, 20, 81, 51))
        self.doubleSpinBox_2.setMaximum(999)
        self.doubleSpinBox_13.setMaximum(999)
        self.doubleSpinBox_19.setMaximum(999)
        self.generator_groups = {self.front_generator: self.generator,
                                 self.front_generator_2: self.generator_2,
                                 self.front_generator_3: self.generator_3}
        self.generator_groups_reverse = {value: key for key, value in self.generator_groups.items()}
        self.resistor_groups = {self.front_resistor: self.resistor,
                                self.front_resistor_2: self.resistor_2,
                                self.front_resistor_3: self.resistor_3}
        self.resistor_groups_reverse = {value: key for key, value in self.resistor_groups.items()}
        self.task = Task()
        self.task.add_generator(0, 'L', 120, 2, self.generator)
        self.front_generator.children()[0].setText('120')
        self.front_generator.children()[1].setText('2')
        self.front_generator.children()[2].setText('<---')
        self.front_generator.children()[3].pressed.connect(self.edit_generator)
        self.generator.hide()
        self.task.add_generator(1, 'R', 80, 1, self.generator_2)
        self.front_generator_2.children()[0].setText('80')
        self.front_generator_2.children()[1].setText('1')
        self.front_generator_2.children()[2].setText('--->')
        self.front_generator_2.children()[3].pressed.connect(self.edit_generator)
        self.generator_2.hide()
        self.task.add_generator(2, 'L', 10, 3, self.generator_3)
        self.front_generator_3.children()[0].setText('10')
        self.front_generator_3.children()[1].setText('3')
        self.front_generator_3.children()[2].setText('<---')
        self.front_generator_3.children()[3].pressed.connect(self.edit_generator)
        self.generator_3.hide()
        self.task.add_resistor(0, 10, self.resistor)
        self.front_resistor.children()[0].setText('10')
        self.front_resistor.children()[1].pressed.connect(self.edit_resisitor)
        self.resistor.hide()
        self.task.add_resistor(1, 12, self.resistor_2)
        self.front_resistor_2.children()[0].setText('12')
        self.front_resistor_2.children()[1].pressed.connect(self.edit_resisitor)
        self.resistor_2.hide()
        self.task.add_resistor(2, 16, self.resistor_3)
        self.front_resistor_3.children()[0].setText('16')
        self.front_resistor_3.children()[1].pressed.connect(self.edit_resisitor)
        self.resistor_3.hide()
        self.decide.pressed.connect(self.decide_task)
        self.comboBox.activated[int].connect(self.combo_box_activ)
        self.comboBox_2.activated[int].connect(self.combo_box_activ)
        self.comboBox_3.activated[int].connect(self.combo_box_activ)
        self.add_new_line.pressed.connect(self.add_new_line_)
        self.lineEdit_7.textEdited[str].connect(self.text_change)
        self.open_box = QtWidgets.QComboBox(self)
        self.open_box.setGeometry(QtCore.QRect(0, 0, 220, 20))

        self.open_box.addItem('open saves results')
        con = sqlite3.connect('funny.db')
        cur = con.cursor()
        cur.execute('''DELETE from Saved_tasks WHERE TRUE''')
        cur.execute(
            '''INSERT INTO Saved_tasks(id, task_info) SELECT id, task_info FROM full_info_saved_task''')
        con.commit()
        saves = cur.execute('''SELECT * FROM Saved_tasks''').fetchall()
        for id_, info in saves:
            self.open_box.addItem(str(id_) + ' - ' + info)
        con.close()
        self.open_box.activated[int].connect(self.open_results)
        # self.save_btn.pressed.connect(self.save)
        self.dict_ = {}

    def save(self):
        pass

    # Реализация кнопки edit у источника
    # То есть включение режима редактирования
    def edit_generator(self):
        generator = self.generator_groups[self.sender().parent()]
        generator.children()[0].setValue(float(self.sender().parent().children()[0].text()))
        generator.children()[3].setValue(float(self.sender().parent().children()[1].text()))
        if self.sender().parent().children()[2].text() == '<---':
            generator.children()[2].setText('L')
        else:
            generator.children()[2].setText('R')
        generator.children()[1].pressed.connect(self.ok_generator)
        self.sender().parent().hide()
        generator.show()

    # Реализация кнопки ок у источника
    # То есть сохранение изменений
    def ok_generator(self):
        try:
            generator = self.generator_groups_reverse[self.sender().parent()]
            back_generator = self.sender().parent().children()
            generator_leg = \
                [(i, g) for i in range(len(self.task.legs)) for g in range(len(self.task.legs[i])) if
                 self.sender().parent() == self.task.legs[i][g][-1]][0]
            self.task.edit_generator(generator_leg[0], generator_leg[1], back_generator[2].text(),
                                     back_generator[0].value(), back_generator[3].value())
            (generator.children()[0].setText(str(int(back_generator[0].value()))) if back_generator[
                                                                                         0].value() == int(
                back_generator[0].value()) else generator.children()[0].setText(
                str(back_generator[0].value())))
            (generator.children()[1].setText(str(int(back_generator[3].value()))) if back_generator[
                                                                                         3].value() == int(
                back_generator[3].value()) else generator.children()[1].setText(
                str(back_generator[3].value())))
            (generator.children()[2].setText('<---') if back_generator[2].text() == 'L' else
             generator.children()[2].setText('--->'))
            self.sender().parent().hide()
            generator.show()
        except Exception as e:
            print(e)

    # Реализация кнопки edit у резистора
    # То есть включение режима редактирования
    def edit_resisitor(self):
        resistor = self.resistor_groups[self.sender().parent()]
        resistor.children()[1].setValue(float(self.sender().parent().children()[0].text()))
        resistor.children()[0].pressed.connect(self.ok_resistor)
        resistor.show()
        self.sender().parent().hide()

    # Реализация кнопки ок у резистора
    # То есть сохранение изменений
    def ok_resistor(self):
        resistor = self.resistor_groups_reverse[self.sender().parent()]
        back_resistor = self.sender().parent().children()
        resistor_leg = \
            [(i, g) for i in range(len(self.task.legs)) for g in range(len(self.task.legs[i])) if
             self.sender().parent() == self.task.legs[i][g][-1]][0]
        self.task.edit_resistor(resistor_leg[0], resistor_leg[1],
                                back_resistor[1].value())
        if back_resistor[1].value() == int(
                back_resistor[1].value()):
            resistor.children()[0].setText(str(int(back_resistor[1].value())))
        else:
            resistor.children()[0].setText(str(back_resistor[1].value()))
        self.sender().parent().hide()
        resistor.show()

    # Создание новой ветки и подключение её к коду
    def add_new_line_(self):
        try:
            leg_index = self.task.add_new_line()
            resistor = self.new_resistor()
            resistor.setGeometry(self.resistor.x(),
                                 self.resistor_3.y() + self.plus_y * (leg_index - 2), 81, 51)
            resistor.show()
            self.task.add_resistor(leg_index, 0, resistor)
            front_resistor = self.new_front_resistor()
            front_resistor.setGeometry(self.front_resistor_3.x(),
                                       self.front_resistor_3.y() + self.plus_y * (
                                               leg_index - 2) - 10, 81, 41)
            self.resistor_groups[front_resistor] = resistor
            self.resistor_groups_reverse[resistor] = front_resistor
            resistor.children()[0].pressed.connect(self.ok_resistor)
            front_resistor.children()[1].pressed.connect(self.edit_resisitor)
            generator = self.new_generator()
            generator.setGeometry(self.generator_3.x(),
                                  self.generator_3.y() + self.plus_y * (leg_index - 2), 81, 81)
            generator.show()
            self.task.add_generator(leg_index, 'L', 0, 0, generator)
            front_generator = self.new_front_generator()
            front_generator.setGeometry(self.front_generator_3.x(),
                                        self.front_generator_3.y() + self.plus_y * (leg_index - 2),
                                        61, 71)
            self.generator_groups[front_generator] = generator
            self.generator_groups_reverse[generator] = front_generator
            generator.children()[1].pressed.connect(self.ok_generator)
            front_generator.children()[-1].pressed.connect(self.edit_generator)
            self.sender().setGeometry(self.sender().x(), self.sender().y() + 81,
                                      self.sender().width(), self.sender().height())
            combo_box = self.new_combo_box(leg_index)
            combo_box.setGeometry(combo_box.x(), combo_box.y() + self.plus_y * (leg_index - 2), 61,
                                  22)
            combo_box.show()
            combo_box.activated[int].connect(self.combo_box_activ)
        except Exception as e:
            print(e)

    # Решение задачи
    def decide_task(self):
        print(self.task.legs)
        legs = self.task.normal()
        print(legs)
        try:
            self.new_window = QMainWindow()
            self.central_widget = QtWidgets.QWidget(self)
            self.new_window.setCentralWidget(self.central_widget)
            self.ui = Decide(self)
            result = ''
            MH_gen = MH_method_for_out(legs)
            for i in range(len(legs)):
                result += str(i + 1) + '.' + '\n'
                result += 'R1 = ' + str(next(MH_gen)) + '\n'
                result += 'I' + ' = '.join(next(MH_gen)) + ' = ' + next(MH_gen) + '\n'
                result += 'Uab = ' + str(next(MH_gen)) + '\n'
                for g in range(len(legs) - 1):
                    result += 'I' + ' = '.join(next(MH_gen)) + ' = ' + next(MH_gen) + '\n'
            dict_ = next(MH_gen)
            result += '\n\nTrue currents: \n'
            for i in range(1, len(legs) + 1):
                result += 'I{} = {} = {}'.format(str(i), ' + '.join(map(str, dict_[i])),
                                                 str(round(float(sum(dict_[i])), 2))) + '\n'
            if result.count('\n') > 30:
                self.ui.horizontalLayoutWidget.setGeometry(QtCore.QRect(0, 10, 641, 641))
                self.ui.tableView.setGeometry(0, 650, 641, 281)
                self.ui.save.setGeometry(550, 935, 75, 23)
                self.ui.info.setGeometry(456, 940, 81, 16)
                self.new_window.setFixedSize(640, 968)
            self.dict_['MH'] = result
            self.ui.MH.setText(result)

            result = ''
            MYH_gen = MYH_method_for_out(legs)
            gs = next(MYH_gen)
            for index, g in enumerate(gs):
                result += f'  g{index + 1} = 1/{legs[index][0]} = {g} Cм \n'
            result += f'  Uab = {next(MYH_gen)} \n'
            for i in range(len(legs)):
                result += '  ' + next(MYH_gen) + '\n'
            self.ui.save.pressed.connect(self.save_results)
            self.ui.MYH.setText(result)
            self.dict_['MYH'] = result
            result = 'Matrix: \n'
            MYKY_gen = MYKY_method_for_out(legs)
            for i in range(len(legs)):
                result += next(MYKY_gen) + '\n'
            i = next(MYKY_gen)
            result += '\n\n'
            for g in range(len(legs)):
                result += f'I{g + 1} = ' + str(i[g]) + '\n'
            self.ui.MYKY.setText(result)
            self.dict_['MYKY'] = result
            con = sqlite3.connect('for_result.db')
            cur = con.cursor()
            cur.execute('''DELETE from results WHERE TRUE''')
            MYH = MYH_method(legs)
            MH = MH_method(legs)
            MYKY = MYKY_method(legs)
            for i in range(len(legs)):
                cur.execute('''INSERT INTO results(Currents, MYH, MH, MKY) 
VALUES (?, ?, ?, ?)''', (f'I{i + 1}', MYH[i + 1], sum(MH[i + 1]), MYKY[i]))
            con.commit()
            con.close()
            db = QSqlDatabase.addDatabase('QSQLITE')
            db.setDatabaseName('for_result.db')
            db.open()
            model = QSqlTableModel(self, db)
            model.setTable('results')
            model.select()
            self.ui.tableView.setModel(model)
            self.new_window.show()
        except Exception as e:
            print(e)

    # Сохранение решения задачи
    def save_results(self):
        self.ui.info.setText('Saving...')
        con = sqlite3.connect('funny.db')
        cur = con.cursor()

        try:
            os.mkdir(os.getenv('APPDATA') + '\saves_for')
            path = os.getenv('APPDATA') + '\saves_for'
        except FileExistsError:
            path = os.getenv('APPDATA') + '\saves_for'
            pass
        except Exception as e:
            os.mkdir('saves')
            path = os.path.abspath('.') + '\saves'
        list_dir = os.listdir(path)
        id = randint(1, 1000000000000)
        while str(id) + '.json' in list_dir:
            id = randint(1, 1000000000000)
        copy2('for_result.db', path + f'\\{id}.db')
        with open(path + '\\' + str(id) + ".json",
                  "w") as file:
            dump(self.dict_, file)
        path_ = path + '\\' + str(id) + ".json"
        cur.execute('''INSERT INTO full_info_saved_task(id, task_info, file_path, table_path, date_save)
        VALUES (?, ?, ?, ?, ?)''',
                    (id, str(self.task.normal()), path_, path + f'\{id}.db', datetime.now()))
        self.open_box.addItem(str(id) + ' - ' + str(self.task.normal()))
        con.commit()
        cur.execute('''DELETE from Saved_tasks WHERE TRUE''')
        cur.execute(
            '''INSERT INTO Saved_tasks(id, task_info) SELECT id, task_info FROM full_info_saved_task''')
        con.commit()
        con.close()
        self.ui.info.setText('Save, ' + str(id) + ' in AppData\\Roaming\\saves_for.')

    # Открытие решения задачи
    def open_results(self, index):
        if self.sender().itemText(index) == 'open saves results':
            pass
        else:
            con = sqlite3.connect('funny.db')

            cur = con.cursor()
            id_ = self.sender().itemText(index).split(' - ')[0]
            file = cur.execute(
                '''SELECT file_path FROM full_info_saved_task WHERE id = ? AND id = ?''',
                (int(id_), int(id_))).fetchall()
            with open(file[0][0], 'r') as file:
                data = load(file)
            self.new_window = QMainWindow()
            self.ui = Decide(self)
            self.ui.MYH.setText(data['MYH'])
            self.ui.MH.setText(data['MH'])
            self.ui.MYKY.setText(data['MYKY'])
            table = cur.execute(
                '''SELECT table_path FROM full_info_saved_task WHERE id = ? AND id = ?''',
                (int(id_), int(id_))).fetchall()[0]
            db = QSqlDatabase.addDatabase('QSQLITE')
            db.setDatabaseName(table[0])
            db.open()
            model = QSqlTableModel(self, db)
            model.setTable('results')
            model.select()
            self.ui.tableView.setModel(model)
            self.new_window.show()

    # Создание нового "добавлятора"(штуки с помощью которой мы добавляем резисторы и источники
    def new_combo_box(self, leg_number):
        comboBox = QtWidgets.QComboBox(self)
        comboBox.setGeometry(QtCore.QRect(300, 190, 61, 22))
        comboBox.setObjectName(f"comboBox_{leg_number + 1}")
        comboBox.addItem("resistor")
        comboBox.addItem("generator")
        comboBox.addItem("node")
        return comboBox

    # Создание нового резистора
    # А именно части где можно редактировать
    def new_resistor(self):
        resistor = QtWidgets.QGroupBox(self)
        resistor.setGeometry(QtCore.QRect(120, 20, 81, 51))
        resistor.setObjectName("resistor")
        pushButton = QtWidgets.QPushButton(resistor)
        pushButton.setGeometry(QtCore.QRect(50, 15, 31, 23))
        pushButton.setObjectName("pushButton")
        doubleSpinBox = QtWidgets.QDoubleSpinBox(resistor)
        doubleSpinBox.setGeometry(QtCore.QRect(10, 15, 41, 22))
        doubleSpinBox.setObjectName("doubleSpinBox")
        pushButton.setText('OK')
        return resistor

    # Создание нового резистора
    # А именно части где мы видим красиво значения
    def new_front_resistor(self):
        front_resistor = QtWidgets.QGroupBox(self)
        front_resistor.setGeometry(QtCore.QRect(110, 30, 81, 41))
        front_resistor.setTitle("")
        front_resistor.setObjectName("front_resistor")
        resistor_text = QtWidgets.QLabel(front_resistor)
        resistor_text.setGeometry(QtCore.QRect(20, 10, 21, 16))
        resistor_text.setObjectName("resistor_text")
        edit = QtWidgets.QPushButton(front_resistor)
        edit.setGeometry(QtCore.QRect(40, 10, 31, 23))
        edit.setObjectName("edit")
        edit.setText('Edit')
        return front_resistor

    # Создание нового источника
    # А именно части где можно редактировать
    def new_generator(self):
        generator = QGroupBox(self)
        generator.setEnabled(True)
        generator.setGeometry(QtCore.QRect(210, 0, 81, 81))
        generator.setFlat(False)
        generator.setCheckable(False)
        self.num_generator += 1
        generator.setObjectName(f"generator{self.num_generator}")
        doubleSpinBox_2 = QDoubleSpinBox(generator)
        doubleSpinBox_2.setGeometry(QtCore.QRect(10, 10, 41, 22))
        doubleSpinBox_2.setObjectName(f"doubleSpinBox_{self.num_generator * 10}")
        doubleSpinBox_2.setMaximum(999)
        pushButton_2 = QPushButton(generator)
        pushButton_2.setGeometry(QtCore.QRect(40, 30, 31, 23))
        pushButton_2.setObjectName(f"pushButton_{self.num_generator * 10}")
        pushButton_2.setText('OK')
        lineEdit = QLineEdit(generator)
        lineEdit.setGeometry(QtCore.QRect(20, 30, 20, 20))
        lineEdit.setObjectName(f"lineEdit_{self.num_generator * 10}")
        doubleSpinBox_3 = QDoubleSpinBox(generator)
        doubleSpinBox_3.setGeometry(QtCore.QRect(10, 50, 41, 22))
        doubleSpinBox_3.setObjectName(f"doubleSpinBox_{self.num_generator * 10}")
        generator.raise_()
        return generator

    # Создание нового резистора
    # А именно части где мы видим красиво значения
    def new_front_generator(self):
        front_generator = QtWidgets.QGroupBox(self)
        front_generator.setGeometry(QtCore.QRect(220, 0, 61, 71))
        front_generator.setTitle("")
        front_generator.setObjectName("front_generator")
        label_2 = QtWidgets.QLabel(front_generator)
        label_2.setGeometry(QtCore.QRect(20, 10, 21, 16))
        label_2.setObjectName("label_2")
        label_3 = QtWidgets.QLabel(front_generator)
        label_3.setGeometry(QtCore.QRect(20, 50, 31, 20))
        label_3.setObjectName("label_3")
        label_4 = QtWidgets.QLabel(front_generator)
        label_4.setGeometry(QtCore.QRect(10, 30, 47, 16))
        label_4.setObjectName("label_4")
        pushButton_4 = QtWidgets.QPushButton(front_generator)
        pushButton_4.setGeometry(QtCore.QRect(30, 30, 31, 23))
        pushButton_4.setObjectName("pushButton_4")
        pushButton_4.setText('Edit')
        front_generator.raise_()
        return front_generator

    # Функция работы "добавлятора"
    def combo_box_activ(self, index):
        try:
            if self.sender().itemText(index) == 'generator':
                new_generator = self.new_generator()
                new_generator.setGeometry(self.sender().x(), self.sender().y() - 30, 81, 81)
                # new_generator.setGeometry(210, 210, 81, 81)
                new_generator.show()
                leg_index = int(self.sender().objectName().split('_')[1]) - 1
                self.task.add_generator(leg_index, 'L', 0, 0, new_generator)
                new_front_generator = self.new_front_generator()
                new_front_generator.setGeometry(self.sender().x(), self.sender().y() - 30, 61, 71)
                self.sender().setGeometry(self.sender().x() + 20 + 81, self.sender().y(),
                                          self.sender().width(),
                                          self.sender().height())
                self.generator_groups[new_front_generator] = new_generator
                self.generator_groups_reverse[new_generator] = new_front_generator
                new_generator.children()[1].pressed.connect(self.ok_generator)
                new_front_generator.children()[-1].pressed.connect(self.edit_generator)
            elif self.sender().itemText(index) == 'resistor':
                new_resistor = self.new_resistor()
                new_resistor.setGeometry(self.sender().x(), self.sender().y() - 20, 81, 51)
                new_resistor.show()
                leg_index = int(self.sender().objectName().split('_')[1]) - 1
                self.task.add_resistor(leg_index, 0, new_resistor)

                new_front_resistor = self.new_front_resistor()
                new_front_resistor.setGeometry(self.sender().x(), self.sender().y() - 10, 81, 41)
                self.sender().setGeometry(self.sender().x() + 20 + 81, self.sender().y(),
                                          self.sender().width(),
                                          self.sender().height())
                self.resistor_groups[new_front_resistor] = new_resistor
                self.resistor_groups_reverse[new_resistor] = new_front_resistor
                new_resistor.children()[0].pressed.connect(self.ok_resistor)
                new_front_resistor.children()[1].pressed.connect(self.edit_resisitor)
        except Exception as e:
            print(e)

    # Функция которая пока используется в одном источнике
    # (она не даёт писать любые буквы кроме нужных)
    def text_change(self, string):
        if string != '' and (string[0] == 'L' or string[0] == 'R'):
            self.sender().setText(string[0])
        else:
            self.sender().setText('')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MyWidget()
    ex.show()
    sys.exit(app.exec_())

# Это часть комментариев где были тесты классов и методов.

# for el in range(int(input())):
#     a = input()
#     legs.append((float(a.split()[0]), a.split()[1], float(a.split()[2])))
# R на ветви, направление источника, напрежение.
# L - к узлу; R - от узла.
# print(MH_method(legs))
# print(MYH_method(legs))
# print(MYKY_method(legs))

# new_task = Task(3)
# new_task.add_resistor(0, 12, 12)
# new_task.add_generator(0, 'L', 120, 2, 10)
# new_task.add_resistor(1, 10, 12)
# new_task.add_generator(1, 'R', 30, 1, 10)
# new_task.add_resistor(2, 14, 12)
# new_task.add_generator(2, 'L', 50, 3, 10)
# print(new_task.normal())
# new_node: Task_in_task = new_task.add_node(0, 2)
# new_node.add_resistor(0, 17, 12)
# new_node.add_resistor(1, 19, 12)
# new_node.add_resistor(1, 9, 12)
# print(new_node.return_resistance())


# Программа пока довольно сырая, но свою фуункцию выполняет.
# Перед презентацией программы я возможно доделаю некоторые косметические функции и что-то исправлю.
# И скорее всего сделаю гайд по использованию.
# Но это пока только планы.

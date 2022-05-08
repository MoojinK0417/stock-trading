# Date : Apr 22 2022
# Course : CIS354 - 01
# Name : Moojin Kim
# Program: Basic Stock Trading Program (Buy&Sell)

# Problems: Balance, Profit values are not correct.
# Balance value is resetting every trade, and Profit values are not right.

import sys
import numpy as np
import pandas as pd
import time
import threading

#Import DataBase#
import sqlite3

#Stock Chart Libraries#
import finplot as fplt
import FinanceDataReader as fdr
from mpl_finance import candlestick_ohlc

#API Libraries#
from yahoo_fin import stock_info as si
from yahoo_fin.stock_info import *

#PyQt#
from PyQt5.QtWidgets import *
from PyQt5.QtChart import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtWidgets, uic


class LoginScreen(QMainWindow):

    def __init__(self):
        super(LoginScreen, self).__init__()
        uic.loadUi("login.ui", self)

        #Connect Method when user press the buttons#
        self.signup.clicked.connect(self.goto_signup)
        self.login.clicked.connect(self.loginfunction)

    #Login Functions, check Password and ID#
    def loginfunction(self):
        user = self.login_id.text()
        password = self.login_password.text()

        if len(user) == 0 or len(password) == 0:
            self.login_errormsg.setText("Please input all fields.")

        else:
            con = sqlite3.connect("login_info.db")
            cur = con.cursor()
            query = 'SELECT user_password FROM user WHERE user_id = \''+user+"\'"
            cur.execute(query)
            result_pass = cur.fetchone()[0]
            if result_pass == password:
                print("Successfully logged in.")
                self.login_errormsg.setText("")
                i = InputScreen()
                widget.addWidget(i)
                widget.setFixedHeight(200)
                widget.setFixedWidth(240)
                widget.setCurrentIndex(widget.currentIndex()+1)
            else:
                self.login_errormsg.setText("Invalid username or password")

     #Bring user to sign up Page#
    def goto_signup(self):
        signup = SignupScreen()
        widget.addWidget(signup)
        widget.setFixedHeight(280)
        widget.setFixedWidth(356)
        widget.setCurrentIndex(widget.currentIndex()+1)


class SignupScreen(QMainWindow):

    def __init__(self):
        super(SignupScreen, self).__init__()
        uic.loadUi("signup.ui", self)
        self.signup1.clicked.connect(self.signup_function)

 #Signup Method, create Password and ID#
    def signup_function(self):

        user = self.signup_id.text()
        password = self.signup_password.text()
        confirm = self.signup_confirm.text()

        if len(user) == 0 or len(password) == 0 or len(confirm) == 0:
            self.signup_errormsg.setText("Please input all fields.")
        elif password != confirm:
            self.signup_errormsg.setText("Password do not match")

        else:
            #Connecting with Database#
            con = sqlite3.connect("login_info.db")
            cur = con.cursor()

            user_info = [user, password]
            cur.execute(
                'INSERT INTO user(user_id,user_password) VALUES(?,?)', user_info)
            con.commit()
            con.close()

            #Load Welcome Page after Creating User.#
            welcome = WelcomeScreen()
            widget.addWidget(welcome)
            widget.setFixedHeight(221)
            widget.setFixedWidth(362)
            widget.setCurrentIndex(widget.currentIndex()+1)


class WelcomeScreen(QMainWindow):
    def __init__(self):
        super(WelcomeScreen, self).__init__()
        uic.loadUi("welcome.ui", self)
        self.btn_backtologin.clicked.connect(self.backlogin)

    def backlogin(self):
        welcome = LoginScreen()
        widget.addWidget(welcome)
        widget.setFixedHeight(264)
        widget.setFixedWidth(305)
        widget.setCurrentIndex(widget.currentIndex()+1)


class InputScreen(QMainWindow):

    def __init__(self):
        super(InputScreen, self).__init__()
        uic.loadUi("input.ui", self)
        self.btn_start.clicked.connect(self.go_output)
        self.va1 = self.spin_budget.value()

    def go_output(self):
        welcome = OutputScreen()
        widget.addWidget(welcome)
        widget.setFixedHeight(460)
        widget.setFixedWidth(780)
        widget.setCurrentIndex(widget.currentIndex()+1)


class OutputScreen(InputScreen, QMainWindow):

    def __init__(self):
        super(OutputScreen, self).__init__()
        super(InputScreen, self).__init__()

        uic.loadUi("output.ui", self)

        top_layout = QGridLayout()
        top_layout.addWidget(self.search_edit, 0, 1)
        top_layout.addWidget(self.btn_search, 0, 2)

        self.label_line = QLabel("                   ")
        self.label_line2 = QLabel("    ")
        self.line_edit = QLineEdit("")
        self.line_edit.setReadOnly(True)

        bottom_layout = QGridLayout()
        bottom_layout.addWidget(self.label_line2, 0, 0)
        bottom_layout.addWidget(self.btn_1, 0, 0)
        bottom_layout.addWidget(self.btn_2, 0, 1)

        #Here is the spot where I put my stock chart#
        widget = QGraphicsView()
        layout = QGridLayout(widget)
        self.setCentralWidget(widget)
        self.ax = fplt.create_plot(init_zoom_periods=100)
        self.axs = [self.ax]  # finplot requires this property
        self.axo = self.ax.overlay()

        self.ax0, self.ax1 = fplt.create_plot_widget(
            master=widget, rows=2, init_zoom_periods=100)
        widget.axs = [self.ax0, self.ax1]
        #############################################
        cl = QGridLayout()
        cl.addWidget(self.ax0.ax_widget, 1, 0)
        cl.addWidget(self.ax1.ax_widget, 2, 0)

        layout.addWidget(self.label_6, 0, 0)
        layout.addLayout(top_layout, 0, 1)
        layout.addLayout(cl, 1, 0)
        layout.addWidget(self.trading_result, 1, 1)
        layout.addWidget(self.labels, 3, 0)
        layout.addLayout(bottom_layout, 3, 1)

        #Button Clicked Functions#
        self.btn_search.clicked.connect(self.plot)
        self.btn_1.clicked.connect(self.buyOption)
        self.btn_2.clicked.connect(self.sellOption)

        self.labels.setText("Start Balance: $"+str(self.spin_budget.value()) +
                            "     Stop Loss: " + str(self.spin_loss.value()) + "%")

    def ck(self):  # Bring a Stock Price and keep update stock price every second#
        symbol = self.search_edit.text()
        self.label_6.setText(
            symbol+" = $" + str(round(si.get_live_price("UBER"), 2)))
        threading.Timer(1, self.ck).start()

    def plot(self):

        symbol = self.search_edit.text()
        df = fdr.DataReader(symbol=symbol, start="2021")

        self.ax0.reset()
        self.ax1.reset()

        #*Stock Chart (Stock Price, Stock Volume)*#
        fplt.candlestick_ochl(
            df[['Open', 'Close', 'High', 'Low']], ax=self.ax0)
        fplt.volume_ocv(df[['Open', 'Close', 'Volume']], ax=self.ax1)
        fplt.refresh()

        self.label_6.setText(
            symbol+" = $" + str(round(si.get_live_price(symbol), 2)))

        #Thread, update ck method every second#
        threading.Timer(1, self.ck).start()

    def buyOption(self):  # Buy Button Method#
        self.btn_1.setEnabled(False)
        self.btn_2.setEnabled(True)
        self.btn_1.setStyleSheet("background-color: grey")
        self.window = buyWindow(self.search_edit, self.trading_result)
        self.window.show()

    def sellOption(self):  # Sell Button Method#
        self.btn_1.setEnabled(True)
        self.btn_2.setEnabled(False)
        self.btn_1.setStyleSheet("background-color: white")
        self.btn_2.setStyleSheet("background-color: grey")
        self.window = sellWindow(self.search_edit, self.trading_result)
        self.window.show()


class sellWindow(OutputScreen, InputScreen, QMainWindow):

    def __init__(self, search_edit, trading_result):
        super(sellWindow, self).__init__()
        super(OutputScreen, self).__init__()
        super(InputScreen, self).__init__()

        uic.loadUi("sell.ui", self)

        symbol = search_edit.text()
        self.label_3.setText(symbol)

        #This is the way how to bring a stock prices from API#
        self.sell_stockName.setText(
            "$" + str(round(si.get_live_price(symbol), 2)))

        #*********NEED TO BE FIXED*******#
        balance = self.spin_budget.value()
        current_price = round(si.get_live_price(symbol), 2)
        shares = int(balance/current_price)
        shares_total_price = shares*current_price

        if balance < shares_total_price:
            profit = round(shares_total_price-balance, 2)
        elif balance > shares_total_price:
            profit = -round(balance-shares_total_price, 2)
        #*******************************#

        #Writing a trading result into Text Area#
        self.share_edit.setText(str(shares))
        trading_result.appendPlainText(
            "Sell Price: $"+str(round(si.get_live_price(symbol), 2)))
        trading_result.appendPlainText(
            "   Balance: $"+str(round(shares_total_price, 2)))
        trading_result.appendPlainText("        Profit: $"+str(profit)+"\n")

        self.btn_sell.clicked.connect(self.sellShares)

        # Write a Sell Price,Balance and Profit into .txt file#
        with open('TradingResult.txt', 'a') as f:
            f.write("\nSell Price: $"+str(round(si.get_live_price(symbol), 2)))
            f.write("\n   Balance: $"+str(round(shares_total_price, 2)))
            f.write("\n    Profit: $"+str(shares_total_price - balance)+"\n\n")

    def sellShares(self):

        self.close()


x = 0


class buyWindow(OutputScreen, InputScreen, QMainWindow):

    def __init__(self, search_edit, trading_result):

        #Inheritance#
        super(buyWindow, self).__init__()
        super(OutputScreen, self).__init__()
        super(InputScreen, self).__init__()

        uic.loadUi("buy.ui", self)

        symbol = search_edit.text()
        self.label_3.setText(symbol)

        #This is the way how to bring a stock prices from API#
        self.buy_stockName.setText(
            "$" + str(round(si.get_live_price(symbol), 2)))

        balance = self.spin_budget.value()  # Spin Box Value Check from Input Page.#
        current_price = round(si.get_live_price(symbol), 2)
        shares = int(balance/current_price)

        self.share_edit.setText(str(shares))

        #Keep track how many time am I trading.#
        global x
        x += 1
        #Writing a trading result into Text Area#
        trading_result.appendPlainText(
            "<"+str(x)+"> "+symbol+"\nBuy Price: $" + str(current_price))

        # Write a Stock Name and Buy Price into .txt file#
        with open('TradingResult.txt', 'a') as f:
            f.write("<"+str(x)+"> "+symbol +
                    "\n Buy Price: $" + str(current_price))

        self.btn_buy.clicked.connect(self.buyShares)

    def buyShares(self):

        self.close()


# main
app = QApplication(sys.argv)
welcome = LoginScreen()
widget = QtWidgets.QStackedWidget()
widget.addWidget(welcome)
widget.setFixedHeight(264)
widget.setFixedWidth(305)
widget.show()
try:
    sys.exit(app.exec_())
except:
    print("Exiting")
widget.close()

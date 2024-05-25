from PyQt5.QtWidgets import (QVBoxLayout, QLabel, QDialog, QLineEdit, QDialogButtonBox)
from PyQt5.QtGui import QDoubleValidator, QIntValidator

class SellDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Sell Stocks")

        layout = QVBoxLayout()

        self.profit_rate_label = QLabel("목표 수익률 (%):")
        self.profit_rate_input = QLineEdit()
        self.profit_rate_input.setValidator(QDoubleValidator(0, 100, 2))  # Allow up to 2 decimal places

        self.amount_label = QLabel("매도 금액 (KRW):")
        self.amount_input = QLineEdit()
        self.amount_input.setValidator(QIntValidator(0, 1000000000))  # Allow integer input

        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self.accept)
        self.button_box.rejected.connect(self.reject)

        layout.addWidget(self.profit_rate_label)
        layout.addWidget(self.profit_rate_input)
        layout.addWidget(self.amount_label)
        layout.addWidget(self.amount_input)
        layout.addWidget(self.button_box)

        self.setLayout(layout)

    def getInputs(self):
        sell_earning_rate = float(self.profit_rate_input.text())
        sell_stock_amount = int(self.amount_input.text()) if self.amount_input.text() else 0
        return sell_earning_rate, sell_stock_amount
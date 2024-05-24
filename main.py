import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QWidget
from KiwoomAPI import KiwoomAPI

class StockTradingApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.kiwoom = KiwoomAPI()
        self.kiwoom.comm_connect()
        self.kiwoom.get_account_info()

        self.initUI()
        self.load_stock_data()
        self.load_unfilled_orders()

    def initUI(self):
        self.setWindowTitle('Stock Trading App')
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        self.layout = QVBoxLayout(self.central_widget)

        # 주식 리스트 테이블
        self.stock_table = QTableWidget(self)
        self.layout.addWidget(self.stock_table)

        # 미체결 주문 리스트 테이블
        self.unfilled_orders_table = QTableWidget(self)
        self.layout.addWidget(self.unfilled_orders_table)

        # 일괄 매도 버튼
        self.sell_all_button = QPushButton('일괄 매도', self)
        self.sell_all_button.clicked.connect(self.sell_all_stocks)
        self.layout.addWidget(self.sell_all_button)

    def load_stock_data(self):
        self.kiwoom.get_stock_data()
        stock_data = self.kiwoom.tr_data['multi']

        self.stock_table.setRowCount(len(stock_data))
        self.stock_table.setColumnCount(2)
        self.stock_table.setHorizontalHeaderLabels(['종목코드', '보유수량'])

        for i, row in enumerate(stock_data):
            for j, item in enumerate(row):
                self.stock_table.setItem(i, j, QTableWidgetItem(item))

    def load_unfilled_orders(self):
        self.kiwoom.get_unfilled_orders()
        unfilled_orders_data = self.kiwoom.tr_data['multi']

        self.unfilled_orders_table.setRowCount(len(unfilled_orders_data))
        self.unfilled_orders_table.setColumnCount(2)
        self.unfilled_orders_table.setHorizontalHeaderLabels(['종목코드', '주문수량'])

        for i, row in enumerate(unfilled_orders_data):
            for j, item in enumerate(row):
                self.unfilled_orders_table.setItem(i, j, QTableWidgetItem(item))

    def sell_all_stocks(self):
        stock_data = self.kiwoom.tr_data['multi']

        for row in stock_data:
            stock_code = row[0]
            quantity = int(row[1])

            if quantity > 0:
                self.kiwoom.send_sell_order(stock_code, quantity)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = StockTradingApp()
    ex.show()
    sys.exit(app.exec_())

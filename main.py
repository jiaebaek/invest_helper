import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QLabel, QTableWidget, \
    QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from pykiwoom.kiwoom import Kiwoom


class StockTradingApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Kiwoom 인스턴스 생성 및 로그인
        self.kiwoom = Kiwoom()
        self.kiwoom.CommConnect(block=True)

        self.initUI()
        self.loadData()

    def initUI(self):
        self.setWindowTitle('Stock Trading App')
        self.setGeometry(100, 100, 800, 600)

        centralWidget = QWidget()
        self.setCentralWidget(centralWidget)

        layout = QVBoxLayout()
        centralWidget.setLayout(layout)

        title = QLabel('My Stock Portfolio')
        title.setFont(QFont('Arial', 20))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 주식 리스트 테이블
        self.stockTable = QTableWidget()
        self.stockTable.setColumnCount(4)
        self.stockTable.setHorizontalHeaderLabels(['Stock Code', 'Stock Name', 'Quantity', 'Current Price'])
        layout.addWidget(self.stockTable)

        # 미체결 주문 리스트 테이블
        self.orderTable = QTableWidget()
        self.orderTable.setColumnCount(4)
        self.orderTable.setHorizontalHeaderLabels(['Order Number', 'Stock Code', 'Order Quantity', 'Order Price'])
        layout.addWidget(self.orderTable)

        # 매도 버튼
        sellButton = QPushButton('Sell All Stocks')
        sellButton.clicked.connect(self.sellAllStocks)
        layout.addWidget(sellButton)

    def loadData(self):
        # 주식 리스트 불러오기
        account_id = self.kiwoom.GetLoginInfo("ACCNO")[0].strip()
        stock_list = self.kiwoom.GetStockList(account_id)

        self.stockTable.setRowCount(len(stock_list))
        for i, stock in enumerate(stock_list):
            stock_code = stock['종목번호']
            stock_name = stock['종목명']
            quantity = stock['보유수량']
            current_price = self.kiwoom.GetMasterLastPrice(stock_code)

            self.stockTable.setItem(i, 0, QTableWidgetItem(stock_code))
            self.stockTable.setItem(i, 1, QTableWidgetItem(stock_name))
            self.stockTable.setItem(i, 2, QTableWidgetItem(str(quantity)))
            self.stockTable.setItem(i, 3, QTableWidgetItem(str(current_price)))

        # 미체결 주문 리스트 불러오기
        order_list = self.kiwoom.GetOrderList(account_id)

        self.orderTable.setRowCount(len(order_list))
        for i, order in enumerate(order_list):
            order_no = order['주문번호']
            stock_code = order['종목번호']
            order_quantity = order['주문수량']
            order_price = order['주문가격']

            self.orderTable.setItem(i, 0, QTableWidgetItem(order_no))
            self.orderTable.setItem(i, 1, QTableWidgetItem(stock_code))
            self.orderTable.setItem(i, 2, QTableWidgetItem(str(order_quantity)))
            self.orderTable.setItem(i, 3, QTableWidgetItem(str(order_price)))

    def sellAllStocks(self):
        account_id = self.kiwoom.GetLoginInfo("ACCNO")[0].strip()

        for i in range(self.stockTable.rowCount()):
            stock_code = self.stockTable.item(i, 0).text()
            quantity = int(self.stockTable.item(i, 2).text())

            if quantity > 0:
                self.kiwoom.SendOrder("Sell All", account_id, 2, stock_code, quantity, 0, "03")

        self.loadData()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    mainWindow = StockTradingApp()
    mainWindow.show()
    sys.exit(app.exec_())
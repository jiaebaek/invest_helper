import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem,
                             QLabel, QPushButton, QDialog, QLineEdit, QDialogButtonBox, QTextEdit, QHBoxLayout)
from PyQt5.QtGui import QDoubleValidator, QIntValidator
from PyQt5.QtCore import Qt, QTimer
from kiwoom import Kiwoom, logger
from time import sleep
from selldialog import SellDialog

TR_REQ_TIME_INTERVAL = 0.2  # 요청 간격

HOGAUNIT = {
    5000: 1,
    10000: 5,
    50000: 10,
    100000: 50,
    500000: 100,
    1000000: 500,
    float('inf'): 1000
}

ORDERTYPE = {
    '신규매도': 2
}

HOGATYPE = {
    '지정가': "00"
}

class StockTradingApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stock Trading App")
        self.setGeometry(100, 100, 1200, 800)  # 창의 크기를 더 크게 설정

        self.kiwoom = Kiwoom()
        self.kiwoom.comm_connect()

        self.sort_order = Qt.AscendingOrder  # 초기 정렬 순서 설정

        self.initUI()
        self.update_stock_list()
        self.update_unsettled_list()

        # 주기적으로 미체결 주문을 업데이트하는 타이머 설정
        self.unsettled_timer = QTimer(self)
        self.unsettled_timer.timeout.connect(self.update_unsettled_list)
        self.unsettled_timer.start(60000)  # 60초마다 업데이트

        # 주기적으로 주식 목록을 업데이트하는 타이머 설정
        self.stock_timer = QTimer(self)
        self.stock_timer.timeout.connect(self.update_stock_list)
        self.stock_timer.start(60000)  # 60초마다 업데이트

    def initUI(self):
        layout = QHBoxLayout()

        left_layout = QVBoxLayout()

        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(6)
        self.stock_table.setHorizontalHeaderLabels(["이름", "현재가", "매입가", "매입금액", "보유수량", "수익률"])
        self.stock_table.horizontalHeader().setStretchLastSection(True)  # 마지막 열을 테이블 끝까지 확장
        self.stock_table.horizontalHeader().sectionClicked.connect(self.on_section_clicked)  # 열 클릭 시 연결
        left_layout.addWidget(QLabel("보유 주식:"))
        left_layout.addWidget(self.stock_table)

        self.update_stock_button = QPushButton("보유 주식 가져오기")
        self.update_stock_button.clicked.connect(self.update_stock_list)
        left_layout.addWidget(self.update_stock_button)

        self.unsettled_list = QTableWidget()
        self.unsettled_list.setColumnCount(5)
        self.unsettled_list.setHorizontalHeaderLabels(["주문번호", "종목코드", "주문이름", "상태", "주문수량"])
        self.unsettled_list.horizontalHeader().setStretchLastSection(True)  # 마지막 열을 테이블 끝까지 확장
        left_layout.addWidget(QLabel("미체결 주문:"))
        left_layout.addWidget(self.unsettled_list)

        self.update_unsettled_button = QPushButton("미체결 주문 가져오기")
        self.update_unsettled_button.clicked.connect(self.update_unsettled_list)
        left_layout.addWidget(self.update_unsettled_button)

        self.sell_button = QPushButton("일괄 매도")
        self.sell_button.clicked.connect(self.sell_stocks_at_target_profit)
        left_layout.addWidget(self.sell_button)

        layout.addLayout(left_layout)

        self.log_text_edit = QTextEdit()
        self.log_text_edit.setReadOnly(True)
        layout.addWidget(self.log_text_edit)

        self.setLayout(layout)

    def format_number(self, number_str):
        """문자열로 된 숫자를 콤마를 포함한 형식으로 변환"""
        number = int(number_str)
        return f"{number:,}"

    def get_user_stock(self):
        # 사용자 계정의 보유 주식 개수 확인
        self.account = self.kiwoom.get_login_info()
        self.account = self.account.split(';')[0]
        logger.debug('계좌번호 : {}'.format(self.account))

        self.kiwoom.set_input_value("계좌번호", self.account)
        self.kiwoom.comm_rq_data("잔고조회", "opw00018", 0, "0101")
        self.user_stock_num = self.kiwoom.ret_cnt
        self.user_stock_list = self.kiwoom.ret_multi_data

        while self.kiwoom.remained_data:
            logger.debug("다음 잔고조회")
            sleep(TR_REQ_TIME_INTERVAL)
            self.kiwoom.set_input_value("계좌번호", self.account)
            self.kiwoom.comm_rq_data("잔고조회", "opw00018", 2, "0101")
            self.user_stock_num += self.kiwoom.ret_cnt
            self.user_stock_list.extend(self.kiwoom.ret_multi_data)

        logger.debug('user stock cnt : {}'.format(self.user_stock_num))

    def get_not_done_order(self):  # 미체결 매수
        self.kiwoom.set_input_value("계좌번호", self.account)
        self.kiwoom.set_input_value("체결구분", 1)
        self.kiwoom.set_input_value("매매구분", 2)
        self.kiwoom.comm_rq_data("실시간체결", "opt10075", 0, "0101")
        self.not_done_orders_num = self.kiwoom.ret_cnt
        self.not_done_orders = self.kiwoom.ret_multi_data
        logger.debug("미체결 매수주문: {}".format(self.not_done_orders))
        sleep(TR_REQ_TIME_INTERVAL)

    def get_not_done_sell(self):  # 미체결 매도
        self.kiwoom.set_input_value("계좌번호", self.account)
        self.kiwoom.set_input_value("체결구분", 1)
        self.kiwoom.set_input_value("매매구분", 1)
        self.kiwoom.comm_rq_data("실시간체결", "opt10075", 0, "0101")
        self.not_done_sell_num = self.kiwoom.ret_cnt
        self.not_done_sell = self.kiwoom.ret_multi_data
        logger.debug("미체결 매도주문: {}".format(self.not_done_sell))
        sleep(TR_REQ_TIME_INTERVAL)

    def update_stock_list(self):
        try:
            self.get_user_stock()
            self.stock_table.setRowCount(0)

            if self.user_stock_list:
                for stock in self.user_stock_list:
                    row_position = self.stock_table.rowCount()
                    self.stock_table.insertRow(row_position)
                    stock_name = stock['name']
                    current_price = self.format_number(stock['current_price'])
                    purchase_price = self.format_number(stock['buy_price'])
                    purchase_amount = self.format_number(stock['buy_amount'])
                    quantity = self.format_number(stock['possession_num'])
                    profit_rate = stock['earning_rate']

                    self.stock_table.setItem(row_position, 0, QTableWidgetItem(stock_name))
                    self.stock_table.setItem(row_position, 1, QTableWidgetItem(current_price))
                    self.stock_table.setItem(row_position, 2, QTableWidgetItem(purchase_price))
                    self.stock_table.setItem(row_position, 3, QTableWidgetItem(purchase_amount))
                    self.stock_table.setItem(row_position, 4, QTableWidgetItem(quantity))
                    self.stock_table.setItem(row_position, 5, QTableWidgetItem(profit_rate))
                self.stock_table.resizeColumnsToContents()
            else:
                logger.debug("No data received for stock list.")
        except Exception as e:
            error_message = f"Error updating stock list: {e}"
            self.log_text_edit.append(error_message)
            logger.debug(error_message)

    def update_unsettled_list(self):
        try:
            self.get_not_done_order()
            self.get_not_done_sell()
            self.unsettled_list.setRowCount(0)

            if self.not_done_orders:
                for order in self.not_done_orders:
                    row_position = self.unsettled_list.rowCount()
                    self.unsettled_list.insertRow(row_position)
                    self.unsettled_list.setItem(row_position, 0, QTableWidgetItem(order['order_num']))
                    self.unsettled_list.setItem(row_position, 1, QTableWidgetItem(order['code']))
                    self.unsettled_list.setItem(row_position, 2, QTableWidgetItem(order['name']))
                    self.unsettled_list.setItem(row_position, 3, QTableWidgetItem(order['state']))
                    self.unsettled_list.setItem(row_position, 4, QTableWidgetItem(order['num']))

            if self.not_done_sell:
                for sell in self.not_done_sell:
                    row_position = self.unsettled_list.rowCount()
                    self.unsettled_list.insertRow(row_position)
                    self.unsettled_list.setItem(row_position, 0, QTableWidgetItem(sell['order_num']))
                    self.unsettled_list.setItem(row_position, 1, QTableWidgetItem(sell['code']))
                    self.unsettled_list.setItem(row_position, 2, QTableWidgetItem(sell['name']))
                    self.unsettled_list.setItem(row_position, 3, QTableWidgetItem(sell['state']))
                    self.unsettled_list.setItem(row_position, 4, QTableWidgetItem(sell['num']))
                self.unsettled_list.resizeColumnsToContents()
            else:
                logger.debug("No data received for unsettled list.")
        except Exception as e:
            error_message = f"Error updating unsettled list: {e}"
            self.log_text_edit.append(error_message)
            logger.debug(error_message)

    def on_section_clicked(self, logical_index):
        try:
            if self.sort_order == Qt.AscendingOrder:
                self.sort_order = Qt.DescendingOrder
            else:
                self.sort_order = Qt.AscendingOrder

            if logical_index in [0, 3]:  # 이름과 매입금액 컬럼에 대해 정렬
                self.stock_table.sortItems(logical_index, self.sort_order)
            elif logical_index == 5:  # 수익률 컬럼에 대해 정렬
                self.sort_by_profit_rate()
        except Exception as e:
            error_message = f"Error sorting stock table: {e}"
            self.log_text_edit.append(error_message)
            print(error_message)

    def sort_by_profit_rate(self):
        try:
            stock_data = []
            for row in range(self.stock_table.rowCount()):
                stock_name = self.stock_table.item(row, 0).text()
                current_price = self.stock_table.item(row, 1).text().replace(",", "")
                purchase_price = self.stock_table.item(row, 2).text().replace(",", "")
                purchase_amount = self.stock_table.item(row, 3).text().replace(",", "")
                quantity = self.stock_table.item(row, 4).text().replace(",", "")
                profit_rate = self.stock_table.item(row, 5).text().replace("%", "")
                stock_data.append((stock_name, int(current_price), int(purchase_price), int(purchase_amount),
                                   int(quantity), float(profit_rate)))

            stock_data.sort(key=lambda x: x[5], reverse=self.sort_order == Qt.DescendingOrder)

            self.stock_table.setRowCount(0)
            for stock in stock_data:
                row_position = self.stock_table.rowCount()
                self.stock_table.insertRow(row_position)
                self.stock_table.setItem(row_position, 0, QTableWidgetItem(stock[0]))
                self.stock_table.setItem(row_position, 1, QTableWidgetItem(self.format_number(str(stock[1]))))
                self.stock_table.setItem(row_position, 2, QTableWidgetItem(self.format_number(str(stock[2]))))
                self.stock_table.setItem(row_position, 3, QTableWidgetItem(self.format_number(str(stock[3]))))
                self.stock_table.setItem(row_position, 4, QTableWidgetItem(self.format_number(str(stock[4]))))
                self.stock_table.setItem(row_position, 5, QTableWidgetItem(f"{stock[5]:.2f}%"))

        except Exception as e:
            error_message = f"Error sorting by profit rate: {e}"
            self.log_text_edit.append(error_message)
            print(error_message)

    def _sell_designated_price(self, stock, sell_earning_rate, sell_stock_amount):
        try:
            remain = int(stock['possession_num'])
            if 'J' in stock['code']:
                return remain
            price = int(stock['buy_price']) * (1 + ((sell_earning_rate + 1) / 100))
            for pr, un in HOGAUNIT.items():
                if price < pr:
                    unit = un
                    break
            price = int(price / unit) + 1
            price = int(price * unit)
            num = int(sell_stock_amount / price)
            if num == 0:
                num = 1
            if num > remain:
                num = remain
            self.kiwoom.send_order("수동주문", "0101", self.account, ORDERTYPE['신규매도'], stock['code'],
                                  num, price, HOGATYPE['지정가'], "")
            sleep(0.2)
            log_message = f"주식명 : {stock['name']} 매도가 : {price}원 수량 : {num}개 매도금액 : {num * price}원"
            self.log_text_edit.append(log_message)
            logger.debug(log_message)
            return remain - num
        except Exception as e:
            error_message = f"Error selling stock: {e}"
            self.log_text_edit.append(error_message)
            logger.debug(error_message)
            return remain

    def sell_stocks_at_target_profit(self):
        try:
            dialog = SellDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                sell_earning_rate, sell_stock_amount = dialog.getInputs()
                log_message = f"목표 수익률: {sell_earning_rate}%, 매도 금액: {sell_stock_amount} KRW"
                self.log_text_edit.append(log_message)
                logger.debug(log_message)

                for stock in self.user_stock_list:
                    self._sell_designated_price(stock, sell_earning_rate, sell_stock_amount)

            else:
                log_message = "Sell operation cancelled."
                self.log_text_edit.append(log_message)
                logger.debug(log_message)
        except Exception as e:
            error_message = f"Error in sell_stocks_at_target_profit: {e}"
            self.log_text_edit.append(error_message)
            logger.debug(error_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = StockTradingApp()
    window.show()
    sys.exit(app.exec_())

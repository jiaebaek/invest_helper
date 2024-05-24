from PyQt5.QAxContainer import QAxWidget
from PyQt5.QtCore import QEventLoop

class KiwoomAPI(QAxWidget):
    def __init__(self):
        super().__init__("KHOPENAPI.KHOpenAPICtrl.1")
        self.OnEventConnect.connect(self._event_connect)
        self.OnReceiveTrData.connect(self._receive_tr_data)
        self.login_event_loop = QEventLoop()
        self.tr_event_loop = None
        self.account_number = None
        self.tr_data = {}

    def comm_connect(self):
        self.dynamicCall("CommConnect()")
        self.login_event_loop.exec_()

    def _event_connect(self, err_code):
        if err_code == 0:
            print("로그인 성공")
        else:
            print("로그인 실패")
        self.login_event_loop.exit()

    def get_account_info(self):
        accounts = self.dynamicCall("GetLoginInfo(QString)", ["ACCNO"]).split(';')
        self.account_number = accounts[0]

    def get_stock_data(self):
        self.tr_data = {}
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호", "0000")  # 비밀번호 설정 필요
        self.dynamicCall("SetInputValue(QString, QString)", "비밀번호입력매체구분", "00")
        self.dynamicCall("SetInputValue(QString, QString)", "조회구분", "1")

        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opw00018_req", "opw00018", 0, "2000")
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def get_unfilled_orders(self):
        self.tr_data = {}
        self.dynamicCall("SetInputValue(QString, QString)", "계좌번호", self.account_number)
        self.dynamicCall("SetInputValue(QString, QString)", "전체종목구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "매매구분", "0")
        self.dynamicCall("SetInputValue(QString, QString)", "종목코드", "")

        self.dynamicCall("CommRqData(QString, QString, int, QString)", "opt10075_req", "opt10075", 0, "2001")
        self.tr_event_loop = QEventLoop()
        self.tr_event_loop.exec_()

    def send_sell_order(self, stock_code, quantity):
        self.dynamicCall("SendOrder(QString, QString, QString, int, QString, int, int, QString, QString)",
                         ["일괄매도", "2002", self.account_number, 2, stock_code, quantity, 0, "03", ""])

    def _receive_tr_data(self, screen_no, rqname, trcode, recordname, prev_next, data_len, err_code, msg1, msg2, msg3):
        if rqname == "opw00018_req":
            self._opw00018(rqname, trcode)
        elif rqname == "opt10075_req":
            self._opt10075(rqname, trcode)
        try:
            self.tr_event_loop.exit()
        except AttributeError:
            pass

    def _opw00018(self, rqname, trcode):
        data_cnt = int(self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname))
        self.tr_data['multi'] = []

        for i in range(data_cnt):
            row = [
                self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목코드").strip(),
                self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "보유수량").strip(),
            ]
            self.tr_data['multi'].append(row)

    def _opt10075(self, rqname, trcode):
        data_cnt = int(self.dynamicCall("GetRepeatCnt(QString, QString)", trcode, rqname))
        self.tr_data['multi'] = []

        for i in range(data_cnt):
            row = [
                self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "종목코드").strip(),
                self.dynamicCall("GetCommData(QString, QString, int, QString)", trcode, rqname, i, "주문수량").strip(),
            ]
            self.tr_data['multi'].append(row)

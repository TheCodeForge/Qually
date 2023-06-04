class PaymentRequired(Exception):
    status_code=402
    def __init__(self):
        Exception.__init__(self)
        self.status_code=402

class ToastError(Exception):

    def __init(self, text, code=409):
        self.message=text
        self.status_code=code
        Exception.__init(self)
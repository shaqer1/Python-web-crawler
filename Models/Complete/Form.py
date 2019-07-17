from Models.Model import Model


class Form(Model):
    file_path = 'storage/complete/Form.txt'

    def __init__(self):
        Model.__init__(self)
        self.fetch()

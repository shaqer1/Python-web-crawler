from Models.Model import Model


class Table(Model):
    file_path = 'storage/complete/tables.txt'

    def __init__(self):
        Model.__init__(self)
        self.fetch()


from Models.Model import Model


class Tag(Model):
    file_path = 'storage/complete/Tag.txt'

    def __init__(self):
        Model.__init__(self)
        self.fetch()


class Version:
    def __init__(self, number, tup):
        self.number = number
        self.tuple = tup

    @property
    def display(self):
        return '.'.join(self.tuple)

    @property
    def choice(self):
        return self.number, self.display
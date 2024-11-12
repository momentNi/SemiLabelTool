from PyQt5 import QtGui
from PyQt5.QtCore import Qt


class LabelListWidgetItem(QtGui.QStandardItem):
    def __init__(self, text=None, shape=None):
        super(LabelListWidgetItem, self).__init__()
        self.setText(text or "")
        self.set_shape(shape)

        self.setCheckable(True)
        self.setCheckState(Qt.Checked)
        self.setEditable(False)
        self.setTextAlignment(Qt.AlignBottom)

    def clone(self):
        return LabelListWidgetItem(self.text(), self.shape())

    def set_shape(self, shape):
        self.setData(shape, Qt.UserRole)

    def shape(self):
        return self.data(Qt.UserRole)

    def __hash__(self):
        return id(self)

    def __repr__(self):
        return f'{self.__class__.__name__}("{self.text()!r}")'

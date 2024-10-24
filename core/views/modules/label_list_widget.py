from typing import List

from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette
from PyQt5.QtWidgets import QStyle

from core.dto.label_list_widget_item import LabelListWidgetItem
from utils.logger import logger


class LabelListWidget(QtWidgets.QListView):
    item_double_clicked_signal = QtCore.pyqtSignal(LabelListWidgetItem)
    item_selection_changed_signal = QtCore.pyqtSignal(list, list)

    def __init__(self):
        super().__init__()
        self._selected_items: List[LabelListWidgetItem] = []

        self.setWindowFlags(Qt.Window)
        self.setModel(StandardItemModel())
        self.model().setItemPrototype(LabelListWidgetItem())
        self.setItemDelegate(HTMLDelegate())
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self.setDefaultDropAction(Qt.MoveAction)

        self.doubleClicked.connect(self.item_double_clicked_event)
        self.selectionModel().selectionChanged.connect(self.item_selection_changed_event)

    def __len__(self):
        return self.model().rowCount()

    def __getitem__(self, i):
        return self.model().item(i)

    def __iter__(self):
        for i in range(len(self)):
            yield self[i]

    @property
    def item_dropped(self):
        return self.model().itemDropped

    @property
    def item_changed(self):
        return self.model().itemChanged

    def item_selection_changed_event(self, selected, deselected):
        selected = [self.model().itemFromIndex(i) for i in selected.indexes()]
        deselected = [self.model().itemFromIndex(i) for i in deselected.indexes()]
        self.item_selection_changed_signal.emit(selected, deselected)

    def item_double_clicked_event(self, index: int):
        self.item_double_clicked_signal.emit(self.model().itemFromIndex(index))

    def selected_items(self):
        return [self.model().itemFromIndex(i) for i in self.selectedIndexes()]

    def scroll_to_item(self, item):
        self.scrollTo(self.model().indexFromItem(item))

    def add_item(self, item: LabelListWidgetItem):
        self.model().setItem(self.model().rowCount(), 0, item)
        item.setSizeHint(self.itemDelegate().sizeHint(None, None))

    def remove_item(self, item):
        index = self.model().indexFromItem(item)
        self.model().removeRows(index.row(), 1)

    def select_item(self, item):
        index = self.model().indexFromItem(item)
        self.selectionModel().select(index, QtCore.QItemSelectionModel.Select)

    def find_item_by_shape(self, shape):
        for row in range(self.model().rowCount()):
            item = self.model().item(row, 0)
            if item.shape() == shape:
                return item
        logger.error(f"cannot find shape: {shape}")
        return None

    def clear(self):
        self.model().clear()

    def item_at_index(self, index):
        return self.model().item(index, 0)


class StandardItemModel(QtGui.QStandardItemModel):
    itemDropped = QtCore.pyqtSignal()

    def removeRows(self, *args, **kwargs):
        ret = super().removeRows(*args, **kwargs)
        self.itemDropped.emit()
        return ret


class HTMLDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        self.parent = parent
        super(HTMLDelegate, self).__init__()
        self.doc = QtGui.QTextDocument(self)

    def paint(self, painter, option, index):
        painter.save()

        options = QtWidgets.QStyleOptionViewItem(option)

        self.initStyleOption(options, index)
        self.doc.setHtml(options.text)
        options.text = ""

        style = (
            QtWidgets.QApplication.style()
            if options.widget is None
            else options.widget.style()
        )
        style.drawControl(QStyle.CE_ItemViewItem, options, painter)

        ctx = QtGui.QAbstractTextDocumentLayout.PaintContext()

        if option.state & QStyle.State_Selected:
            ctx.palette.setColor(
                QPalette.Text,
                option.palette.color(
                    QPalette.Active, QPalette.HighlightedText
                ),
            )
        else:
            ctx.palette.setColor(
                QPalette.Text,
                option.palette.color(QPalette.Active, QPalette.Text),
            )

        text_rect = style.subElementRect(QStyle.SE_ItemViewItemText, options)

        if index.column() != 0:
            text_rect.adjust(5, 0, 0, 0)

        margin_constant = 4
        margin = (option.rect.height() - options.fontMetrics.height()) // 2
        margin = margin - margin_constant
        text_rect.setTop(text_rect.top() + margin)

        painter.translate(text_rect.topLeft())
        painter.setClipRect(text_rect.translated(-text_rect.topLeft()))
        self.doc.documentLayout().draw(painter, ctx)

        painter.restore()

    def sizeHint(self, _, _2):
        margin_constant = 4
        return QtCore.QSize(
            int(self.doc.idealWidth()),
            int(self.doc.size().height() - margin_constant),
        )

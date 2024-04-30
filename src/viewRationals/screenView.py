from copy import copy
from madcad import rendering
from PyQt5 import QtCore, QtWidgets

from utils import collect, getPeriod


def getRationalsSeqs(rationals: list[int], number, dim) -> list[list[int]]:
    result = []
    r = copy(list(rationals))
    base = 2**dim
    period = getPeriod(number, base)
    while len(r) > 0:
        l = []
        n = r[0]
        for _ in range(period):
            if n in r:
                l.append(n)
                r.remove(n)
            n = n*base % number
        result.append(l)
    del r
    collect()
    return result


class Label(QtWidgets.QWidget):
    def __init__(self, parent: rendering.QWidget | None = ..., 
                 rationals: list[int] = None,
                 number: int = 0,
                 dim: int = 0,
                 posx: int = 0,
                 posy: int = 0
        ) -> None:
        super().__init__(parent)
        self.rationals = rationals or []
        self.setAutoFillBackground(True)
        self.move(posx, posy)
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(f'({len(rationals)})')
        layout.addWidget(label)
        result = getRationalsSeqs(rationals, number, dim)
        for line in result:
            label = QtWidgets.QLabel(', '.join([f'{int(x):d}' for x in line]))
            layout.addWidget(label)
        self.setLayout(layout)

    def mousePressEvent(self, a0: rendering.QMouseEvent | None) -> None:
        self.close()
        return super().mousePressEvent(a0)


class ScreenView(rendering.View):
    def __init__(
            self, 
            mainWindow: QtWidgets.QMainWindow, 
            scene: rendering.Scene, 
            projection: rendering.Perspective | rendering.Orthographic | None=None, 
            navigation: rendering.Turntable | rendering.Orbit | None=None, 
            parent: QtWidgets.QWidget | None=None
        ):
        self.mainWindow = mainWindow
        super().__init__(scene, projection=projection, navigation=navigation, parent=parent)
        self.label = None

    def mouseClick(self, evt: rendering.QMouseEvent):
        obj = self.itemat(QtCore.QPoint(evt.x(), evt.y()))
        if obj:
            center = self.scene.item(obj).box.center
            t = self.mainWindow.timeWidget.value()
            spacetime = self.mainWindow.spacetime
            if spacetime:
                if self.mainWindow.dim == 2:
                    x = center.x
                    y = center.z
                    z = 0.0
                else:
                    x = center.x
                    y = center.y
                    z = center.z
                cell = spacetime.getCell(t, x, y, z, accumulate=self.mainWindow._check_accumulate())
                if not cell:
                    return False
                if evt.button() == QtCore.Qt.LeftButton:
                    if self.mainWindow.selected_rationals:
                        return False
                    self.mainWindow.select_cell(cell)
                    self.mainWindow.refresh_selection()
                    if self.label:
                        self.label.close()
                        self.label = None
                elif evt.button() == QtCore.Qt.RightButton:
                    if self.label:
                        self.label.close()
                    cell_rationals = cell.get()['rationals']
                    selected_rationals = self.mainWindow.selected_rationals
                    intersect = list(set(cell_rationals).intersection(set(selected_rationals)))
                    if not intersect:
                        intersect = cell_rationals
                    self.label = Label(self, 
                        rationals=intersect, 
                        # rationals = selected_rationals,
                        number=self.mainWindow.number.value(), 
                        dim=self.mainWindow.dim, 
                        posx=evt.x(), posy=evt.y()
                    )
                    self.label.show()
        elif self.label:
            self.label.close()
            self.label = None
        return True

    def control(self, _, evt: rendering.QMouseEvent):
        if evt.type() == 3:
            return self.mouseClick(evt)
        return False


if __name__ == '__main__':
    rationals = range(42)
    result = getRationalsSeqs(rationals, 41, 2)
    print(result)
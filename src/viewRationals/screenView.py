from numba import int32, njit
from numba.typed import List
from numba.types import ListType

from copy import copy
from madcad import rendering
from PyQt5 import QtCore, QtWidgets
from gc import collect

from utils import getPeriod
from spacetime_numba import SpaceTime
from cell_numba import Cell


@njit
def getRationalsSeqs(rationals, number, dim):
    result = List()
    r = List.empty_list(int32)
    for x in rationals: # Copy rationals to a new list
        r.append(int32(x))
    base = 2**dim
    period = getPeriod(number, base)
    while len(r) > 0:
        l = List.empty_list(int32)
        n = r[0]
        for _ in range(period):
            for i in range(len(r)):
                if r[i] == n:
                    l.append(int32(n))
                    r.pop(i)
                    break
            n = n*base % number
        result.append(l)
    return result


@njit
def intersectRationals(rationals: list[int], cell_rationals: list[int]) -> list[int]:
    """
    Count the number of rationals that intersect with the cell's rationals.

    Parameters:
    - rationals: The list of rational numbers to check.
    - cell_rationals: The list of rational numbers in the cell.

    Returns:
    - The count of intersecting rationals.
    """
    result = List.empty_list(int32)
    if len(rationals) == 0 or len(cell_rationals) == 0:
        return result

    for sel in rationals:
        for cell in cell_rationals:
            if sel == cell:
                result.append(sel)
                break

    return result

class Label(QtWidgets.QWidget):
    def __init__(self, parent: rendering.QWidget | None = ..., 
                 rationals: list[int] = None,
                 number: int = 0,
                 count: int = 0,
                 dim: int = 0,
                 posx: int = 0,
                 posy: int = 0
        ) -> None:
        super().__init__(parent)
        self.rationals = rationals or []
        self.setAutoFillBackground(True)
        self.move(posx, posy)
        layout = QtWidgets.QVBoxLayout()
        label = QtWidgets.QLabel(f'({count})')
        layout.addWidget(label)
        result = getRationalsSeqs(rationals, number, dim)
        for i in range(min(len(result), 20)):
            line = result[i]
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
            spacetime: SpaceTime = self.mainWindow.spacetime
            if spacetime:
                if self.mainWindow.dim == 2:
                    x = center.x
                    y = center.z
                    z = 0.0
                else:
                    x = center.x
                    y = center.y
                    z = center.z
                cell: Cell = spacetime.getCell(t, x, y, z, self.mainWindow._check_accumulate())
                if not cell:
                    return False
                if evt.button() == QtCore.Qt.LeftButton:
                    if self.mainWindow.view_selected_rationals:
                        return False
                    self.mainWindow.select_cell(cell)
                    self.mainWindow.refresh_selection()
                    if evt.modifiers() == QtCore.Qt.ShiftModifier:
                        self.mainWindow.select_center(cell.x, cell.y, cell.z)
                    if self.label:
                        self.label.close()
                        self.label = None
                elif evt.button() == QtCore.Qt.RightButton:
                    if self.label:
                        self.label.close()
                    cell_rationals = cell.get_rationals()
                    selected_rationals = self.mainWindow.selected_rationals
                    if selected_rationals:
                        intersect = intersectRationals(selected_rationals, cell_rationals)
                    else:
                        intersect = cell_rationals
                    if not intersect:
                        intersect = cell_rationals
                    self.label = Label(self, 
                        rationals=intersect,
                        count=cell.count, 
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
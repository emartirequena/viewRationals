from PyQt5 import QtWidgets, QtCore
from ui.transformWidgetUI import Ui_TransformWidget
from transform_numba import Transform, get_input_plugin_as_string, get_output_plugin_as_string
from timing import timing

class TransformWidget(QtWidgets.QDialog):
    """
    A widget for setting up a transformation in a spacetime.
    This widget allows the user to input parameters for the transformation
    and displays the input and output lists, and then pick on them to
    set the transformation.
    """

    def __init__(self, transform: Transform, dim: int, parent=None) -> None:
        """
        Initialize the TransformWidget.
        :param transform: The Transform object to be used.
        :param dim: The dimension of the spacetime (1, 2, or 3).
        :param parent: The parent widget.
        """ 
        super().__init__(parent)
        self.ui = Ui_TransformWidget()
        self.ui.setupUi(self)
        self.transform = transform
        self.dim = dim
        self.ui.activate.stateChanged.connect(self.activate)
        self.ui.vx.setEnabled(False)
        self.ui.vy.setEnabled(False)
        self.ui.vz.setEnabled(False)
        if  self.transform.active:
            self.ui.activate.setChecked(True)
            if dim > 0:
                self.ui.vx.setEnabled(True)
            if dim > 1:
                self.ui.vy.setEnabled(True)
            if dim > 2:
                self.ui.vz.setEnabled(True)
            if dim == transform.get_dim():
                self._load_plugins()
        else:
            self.ui.activate.setChecked(False)

    @timing
    def compute(self, p=0):
        """
        Compute the transformation based on the input values.
        This method retrieves the values from the UI, sets them in the transform object,
        and updates the input and output lists.
        """
        QtWidgets.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        
        self.transform.n = self.ui.num.value()
        num = self.ui.num.value()
        vx = self.ui.vx.value()  
        vy = self.ui.vy.value()
        vz = self.ui.vz.value()
        try:
            self.transform.set_velocity(self.dim, num, vx, vy, vz)
        except ValueError as e:
            QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return
        
        self._load_plugins()
        QtWidgets.QApplication.restoreOverrideCursor()

    def _load_plugins(self):
        self.ui.InputList.clear()
        self.ui.OutputList.clear() 

        if self.transform.n > 0:
            self.ui.num.setValue(int(self.transform.n))
            self.ui.vx.setValue(int(self.transform.mx))
            self.ui.vy.setValue(int(self.transform.my))
            self.ui.vz.setValue(int(self.transform.mz))

        for i in range(self.transform.get_num_inputs()):
            input = get_input_plugin_as_string(self.transform, i)
            self.ui.InputList.addItem(input)
            self.ui.InputList.item(i).setData(QtCore.Qt.UserRole, i)
        if self.transform.get_input_plugin_idx() >= 0:
            self.ui.InputList.setCurrentRow(self.transform.get_input_plugin_idx())
            
        for i in range(self.transform.get_num_outputs()):
            output = get_output_plugin_as_string(self.transform, i)
            self.ui.OutputList.addItem(output)
            self.ui.OutputList.item(i).setData(QtCore.Qt.UserRole, i)
        if self.transform.get_output_plugin_idx() >= 0:
            self.ui.OutputList.setCurrentRow(self.transform.get_output_plugin_idx())

        self.ui.inputLabel.setText(f"Input: ({self.transform.get_num_inputs()})")
        self.ui.outputLabel.setText(f"Output: ({self.transform.get_num_outputs()})")

    def cancel(self):
        self.close()

    def accept(self):
        """
        Accept the transformation setup and close the widget.
        This method checks if the input and output plugins are selected,
        sets them in the transform object, and closes the widget.
        """
        if self.transform.active:
            if not self.ui.InputList.currentItem():
                QtWidgets.QMessageBox.critical(self, "Error", "No input plugin selected.")
                return
            if not self.ui.OutputList.currentItem():
                QtWidgets.QMessageBox.critical(self, "Error", "No output plugin selected.")
                return
            self.transform.set_input_plugin(self.ui.InputList.currentItem().data(QtCore.Qt.UserRole))
            self.transform.set_output_plugin(self.ui.OutputList.currentItem().data(QtCore.Qt.UserRole))
        self.close()

    def activate(self, value):
        """
        Activate or deactivate the widget based on the value.
        :param value: The value to set the activation state.
        """
        if value:
            self.ui.num.setEnabled(True)
            self.ui.vx.setEnabled(True)
            if self.dim > 1:
                self.ui.vy.setEnabled(True)
            if self.dim > 2:
                self.ui.vz.setEnabled(True)
            self.ui.Compute.setEnabled(True)
            self.ui.InputList.setEnabled(True)
            self.ui.OutputList.setEnabled(True) 
            self.transform.set_active(True)
        else:
            self.ui.num.setEnabled(False)
            self.ui.vx.setEnabled(False)
            if self.dim > 1:
                self.ui.vy.setEnabled(False)
            if self.dim > 2:
                self.ui.vz.setEnabled(False)
            self.ui.Compute.setEnabled(False)
            self.ui.InputList.setEnabled(False)
            self.ui.OutputList.setEnabled(False)
            self.transform.set_active(False)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    transform = Transform()
    widget = TransformWidget(transform, 3)
    widget.show()
    sys.exit(app.exec_())

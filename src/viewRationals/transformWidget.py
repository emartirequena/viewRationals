from PyQt5 import QtWidgets, QtCore
from ui.transformWidgetUI import Ui_TransformWidget
# from transform_numba import Transform, get_input_plugin_as_string, get_output_plugin_as_string, set_transform_velocity_from_params
import viewUtils as vu
from timing import timing

class TransformWidget(QtWidgets.QDialog):
    """
    A widget for setting up a transformation in a spacetime.
    This widget allows the user to input parameters for the transformation
    and displays the input and output lists, and then pick on them to
    set the transformation.
    """

    def __init__(self, spacetime, dim: int, parent=None) -> None:
        """
        Initialize the TransformWidget.
        :param spacetime: The spacetime object to apply the transformation to.
        :param dim: The dimension of the spacetime (1, 2, or 3).
        :param parent: The parent widget.
        """ 
        super().__init__(parent)
        self.ui = Ui_TransformWidget()
        self.ui.setupUi(self)
        self.spacetime = spacetime
        self.dim = dim
        self.ui.activate.stateChanged.connect(self.activate)
        self.ui.vx.setEnabled(False)
        self.ui.vy.setEnabled(False)
        self.ui.vz.setEnabled(False)
        self.plugins_loaded = False
        if  vu.spacetime_cuda_is_tr_active(self.spacetime):
            self.ui.activate.setChecked(True)
            if dim > 0:
                self.ui.vx.setEnabled(True)
            if dim > 1:
                self.ui.vy.setEnabled(True)
            if dim > 2:
                self.ui.vz.setEnabled(True)
            tr_dim, _, _, _, _, active = vu.spacetime_cuda_get_tr_params(self.spacetime)
            if dim == tr_dim:
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
        
        num = self.ui.num.value()
        vx = self.ui.vx.value()  
        vy = self.ui.vy.value()
        vz = self.ui.vz.value()
        try:
            vu.spacetime_cuda_set_tr_velocity(self.spacetime, self.dim, num, vx, vy, vz)
        except ValueError as e:
            QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QMessageBox.critical(self, "Error", str(e))
            return
        
        self.plugins_loaded = False
        self._load_plugins()
        QtWidgets.QApplication.restoreOverrideCursor()

    def _load_plugins(self):
        if self.plugins_loaded:
            return
        self.ui.InputList.clear()
        self.ui.OutputList.clear() 

        _, n, mx, my, mz, _ = vu.spacetime_cuda_get_tr_params(self.spacetime)
        if n > 0:
            self.ui.num.setValue(int(n))
            self.ui.vx.setValue(int(mx))
            self.ui.vy.setValue(int(my))
            self.ui.vz.setValue(int(mz))

        for i in range(min(1000, vu.spacetime_cuda_get_tr_num_inputs(self.spacetime))):
            input, _ = vu.spacetime_cuda_get_tr_input_plugin(self.spacetime, i)
            self.ui.InputList.addItem(str(input.decode('utf-8')))
            self.ui.InputList.item(i).setData(QtCore.Qt.UserRole, i)
        if vu.spacetime_cuda_get_tr_input_plugin_idx(self.spacetime) >= 0:
            self.ui.InputList.setCurrentRow(vu.spacetime_cuda_get_tr_input_plugin_idx(self.spacetime))
            
        for i in range(min(1000, vu.spacetime_cuda_get_tr_num_outputs(self.spacetime))):
            output, _ = vu.spacetime_cuda_get_tr_output_plugin(self.spacetime, i)
            self.ui.OutputList.addItem(str(output.decode('utf-8')))
            self.ui.OutputList.item(i).setData(QtCore.Qt.UserRole, i)
        if vu.spacetime_cuda_get_tr_output_plugin_idx(self.spacetime) >= 0:
            self.ui.OutputList.setCurrentRow(vu.spacetime_cuda_get_tr_output_plugin_idx(self.spacetime))

        self.ui.inputLabel.setText(f"Input: ({vu.spacetime_cuda_get_tr_num_inputs(self.spacetime)})")
        self.ui.outputLabel.setText(f"Output: ({vu.spacetime_cuda_get_tr_num_outputs(self.spacetime)})")
        self.pulings_loaded = True

    def cancel(self):
        self.close()

    def accept(self):
        """
        Accept the transformation setup and close the widget.
        This method checks if the input and output plugins are selected,
        sets them in the transform object, and closes the widget.
        """
        if vu.spacetime_cuda_is_tr_active(self.spacetime):
            if not self.ui.InputList.currentItem():
                QtWidgets.QMessageBox.critical(self, "Error", "No input plugin selected.")
                return
            if not self.ui.OutputList.currentItem():
                QtWidgets.QMessageBox.critical(self, "Error", "No output plugin selected.")
                return
            vu.spacetime_cuda_set_tr_input_plugin(self.spacetime, self.ui.InputList.currentItem().data(QtCore.Qt.UserRole))
            vu.spacetime_cuda_set_tr_output_plugin(self.spacetime, self.ui.OutputList.currentItem().data(QtCore.Qt.UserRole))
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
            vu.spacetime_cuda_set_tr_active(self.spacetime, 1)
            tr_dim, _, _, _, _, active = vu.spacetime_cuda_get_tr_params(self.spacetime)
            if self.dim == tr_dim:
                self._load_plugins()
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
            vu.spacetime_cuda_set_tr_active(self.spacetime, 0)


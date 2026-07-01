from PyQt5 import QtWidgets, QtCore
from ui.transformWidgetUI import Ui_TransformWidget
# from transform_numba import Transform, get_input_plugin_as_string, get_output_plugin_as_string, set_transform_velocity_from_params
import viewUtils as vu
from timing import timing
import utils

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
        ret = vu.spacetime_cuda_set_tr_velocity(self.spacetime, self.dim, num, vx, vy, vz)
        if ret < 0:
            msg = ""
            if ret == -1: msg = "Error: No inputs generated."
            elif ret == -2: msg = "Error: No outputs generated."
            QtWidgets.QApplication.restoreOverrideCursor()
            QtWidgets.QMessageBox.critical(self, "Error", msg)
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

        for i in range(min(4000, vu.spacetime_cuda_get_tr_num_inputs(self.spacetime))):
            input, _ = vu.spacetime_cuda_get_tr_input_plugin(self.spacetime, i)
            self.ui.InputList.addItem(input.decode('utf-8'))
            self.ui.InputList.item(i).setData(QtCore.Qt.UserRole, i)
        if vu.spacetime_cuda_get_tr_input_plugin_idx(self.spacetime) >= 0:
            self.ui.InputList.setCurrentRow(vu.spacetime_cuda_get_tr_input_plugin_idx(self.spacetime))
            
        for i in range(min(4000, vu.spacetime_cuda_get_tr_num_outputs(self.spacetime))):
            output, _ = vu.spacetime_cuda_get_tr_output_plugin(self.spacetime, i)
            self.ui.OutputList.addItem(output.decode('utf-8'))
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

    def change_row_column(self):
        """
        Change the row and column of the input and output lists.
        This method is called when the user changes the row or column in the input or output lists.
        """
        input = None
        output = None
        if self.ui.InputList.currentItem():
            input, _ = vu.spacetime_cuda_get_tr_input_plugin(self.spacetime, self.ui.InputList.currentItem().data(QtCore.Qt.UserRole))
        if input:
            input = input.decode('utf-8')
        if self.ui.OutputList.currentItem():
            output, _ = vu.spacetime_cuda_get_tr_output_plugin(self.spacetime, self.ui.OutputList.currentItem().data(QtCore.Qt.UserRole))
        if output:
            output = output.decode('utf-8')

        self.ui.label_x_input.setText("")
        self.ui.label_y_input.setText("")
        self.ui.label_z_input.setText("")
        self.ui.label_x_output.setText("")
        self.ui.label_y_output.setText("")
        self.ui.label_z_output.setText("")
        self.ui.label_x_and.setText("")
        self.ui.label_y_and.setText("")
        self.ui.label_z_and.setText("")
        self.ui.label_x_or.setText("")
        self.ui.label_y_or.setText("")
        self.ui.label_z_or.setText("")
        self.ui.label_x_xor.setText("")
        self.ui.label_y_xor.setText("")
        self.ui.label_z_xor.setText("")

        if input and output:
            input_x = utils.plugin_extract(input, 1)
            input_y = utils.plugin_extract(input, 2)
            input_z = utils.plugin_extract(input, 3)
            output_x = utils.plugin_extract(output, 1)
            output_y = utils.plugin_extract(output, 2)
            output_z = utils.plugin_extract(output, 3)

            plugin_x_and = utils.plugin_and(input_x, output_x)
            plugin_y_and = utils.plugin_and(input_y, output_y) if self.dim > 1 else ""
            plugin_z_and = utils.plugin_and(input_z, output_z) if self.dim > 2 else ""
            plugin_x_or = utils.plugin_or(input_x, output_x)
            plugin_y_or = utils.plugin_or(input_y, output_y) if self.dim >  1 else ""
            plugin_z_or = utils.plugin_or(input_z, output_z) if self.dim > 2 else ""
            plugin_x_xor = utils.plugin_xor(input_x, output_x)
            plugin_y_xor = utils.plugin_xor(input_y, output_y) if self.dim > 1 else ""
            plugin_z_xor = utils.plugin_xor(input_z, output_z) if self.dim > 2 else ""  

            plugin_x_and = f'{plugin_x_and} - {utils.num_ones(plugin_x_and)}'
            plugin_y_and = f'{plugin_y_and} - {utils.num_ones(plugin_y_and)}' if self.dim > 1 else ""
            plugin_z_and = f'{plugin_z_and} - {utils.num_ones(plugin_z_and)}' if self.dim > 2 else ""
            plugin_x_or = f'{plugin_x_or} - {utils.num_ones(plugin_x_or)}'
            plugin_y_or = f'{plugin_y_or} - {utils.num_ones(plugin_y_or)}' if self.dim > 1 else ""
            plugin_z_or = f'{plugin_z_or} - {utils.num_ones(plugin_z_or)}' if self.dim > 2 else ""  
            plugin_x_xor = f'{plugin_x_xor} - {utils.num_ones(plugin_x_xor)}'
            plugin_y_xor = f'{plugin_y_xor} - {utils.num_ones(plugin_y_xor)}' if self.dim > 1 else ""
            plugin_z_xor = f'{plugin_z_xor} - {utils.num_ones   (plugin_z_xor)}' if self.dim > 2 else ""

            self.ui.label_x_input.setText(input_x)
            if self.dim > 1: self.ui.label_y_input.setText(input_y)
            if self.dim > 2: self.ui.label_z_input.setText(input_z)
            
            self.ui.label_x_output.setText(output_x)
            if self.dim > 1: self.ui.label_y_output.setText(output_y)
            if self.dim > 2: self.ui.label_z_output.setText(output_z)

            self.ui.label_x_and.setText(plugin_x_and)
            if self.dim > 1: self.ui.label_y_and.setText(plugin_y_and)
            if self.dim > 2: self.ui.label_z_and.setText(plugin_z_and)

            self.ui.label_x_or.setText(plugin_x_or)
            if self.dim > 1: self.ui.label_y_or.setText(plugin_y_or)
            if self.dim > 2: self.ui.label_z_or.setText(plugin_z_or)

            self.ui.label_x_xor.setText(plugin_x_xor)
            if self.dim > 1: self.ui.label_y_xor.setText(plugin_y_xor)
            if self.dim > 2: self.ui.label_z_xor.setText(plugin_z_xor)


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


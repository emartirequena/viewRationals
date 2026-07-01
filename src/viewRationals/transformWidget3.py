from PyQt5 import QtWidgets, QtCore
from ui.transformWidget3UI import Ui_TransformWidget
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

    def __init__(self, spacetime: vu.SpaceTime_CUDA, dim: int, parent=None) -> None:
        """
        Initialize the TransformWidget.
        :param spacetime: The spacetime object to apply the transformation to.
        :param dim: The dimension of the spacetime (1, 2, or 3).
        :param parent: The parent widget.
        """ 
        super().__init__(parent)
        self.ui = Ui_TransformWidget()
        self.ui.setupUi(self)
        self.spacetime: vu.SpaceTime_CUDA = spacetime
        self.dim = dim
        self.ui.activate.stateChanged.connect(self.activate)
        self.ui.vx.setEnabled(False)
        self.ui.vy.setEnabled(False)
        self.ui.vz.setEnabled(False)
        self.ui.input_plugin.setEnabled(False)
        self.ui.set_plugins.setEnabled(False)
        self.plugins_loaded = False
        if  vu.spacetime_cuda_is_tr_active(self.spacetime):
            self.ui.activate.setChecked(True)
            self.ui.vx.setEnabled(True)
            if dim > 1: 
                self.ui.vy.setEnabled(True)
            if dim > 2: 
                self.ui.vz.setEnabled(True)
            tr_dim, _, _, _, _, _= vu.spacetime_cuda_get_tr_params(self.spacetime)
            self.ui.input_plugin.setEnabled(True)
            self.ui.set_plugins.setEnabled(True)
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
        input_plugin_idx = vu.spacetime_cuda_get_tr_input_plugin_idx(self.spacetime)
        if 0 <= input_plugin_idx <= 4000:
            self.ui.InputList.setCurrentRow(input_plugin_idx)
        elif input_plugin_idx >= 0:
            input_plugin_idx = vu.spacetime_cuda_get_tr_input_plugin_idx(self.spacetime)
            input_plugin, _ = vu.spacetime_cuda_get_tr_input_plugin(self.spacetime, input_plugin_idx)
            self.ui.input_plugin.setText(input_plugin.decode('utf-8'))

        for i in range(min(4000, vu.spacetime_cuda_get_tr_num_outputs(self.spacetime))):
            output, _ = vu.spacetime_cuda_get_tr_output_plugin(self.spacetime, i)
            self.ui.OutputList.addItem(output.decode('utf-8'))
            self.ui.OutputList.item(i).setData(QtCore.Qt.UserRole, i)
        output_plugin_idx = vu.spacetime_cuda_get_tr_output_plugin_idx(self.spacetime)
        if 0 <= output_plugin_idx <= 4000:
            self.ui.OutputList.setCurrentRow(output_plugin_idx)
        elif output_plugin_idx >= 0:
            output_plugin_idx = vu.spacetime_cuda_get_tr_output_plugin_idx(self.spacetime)
            output_plugin, _ = vu.spacetime_cuda_get_tr_output_plugin(self.spacetime, output_plugin_idx)
            self.ui.output_plugin.setText(output_plugin.decode('utf-8'))
        
        self.ui.inputLabel.setText(f"Input: ({vu.spacetime_cuda_get_tr_num_inputs(self.spacetime)})")
        self.ui.outputLabel.setText(f"Output: ({vu.spacetime_cuda_get_tr_num_outputs(self.spacetime)})")

        self.update_labels(input_plugin_idx, output_plugin_idx)

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
            if vu.spacetime_cuda_get_tr_input_plugin_idx(self.spacetime) < 0:
                QtWidgets.QMessageBox.critical(self, "Error", "No input plugin selected.")
                return
            if vu.spacetime_cuda_get_tr_output_plugin_idx(self.spacetime) < 0:
                QtWidgets.QMessageBox.critical(self, "Error", "No output plugin selected.")
                return
        self.close()

    def change_row_column(self):
        """
        Change the row and column of the input and output lists.
        This method is called when the user changes the row or column in the input or output lists.
        """
        input_idx = None
        output_idx = None
        if self.ui.InputList.currentItem():
            input_idx = self.ui.InputList.currentItem().data(QtCore.Qt.UserRole)
        if self.ui.OutputList.currentItem():
            output_idx = self.ui.OutputList.currentItem().data(QtCore.Qt.UserRole)

        if input_idx is not None:
            vu.spacetime_cuda_set_tr_input_plugin(self.spacetime, input_idx)
            self.ui.input_plugin.setText(vu.spacetime_cuda_get_tr_input_plugin(self.spacetime, input_idx)[0].decode('utf-8'))

        if output_idx is not None:
            vu.spacetime_cuda_set_tr_output_plugin(self.spacetime, output_idx)
            self.ui.output_plugin.setText(vu.spacetime_cuda_get_tr_output_plugin(self.spacetime, output_idx)[0].decode('utf-8'))

        if input_idx is not None and output_idx is not None:
            self.update_labels(input_idx, output_idx)

    def update_labels(self, input_idx, output_idx):
        """
        Update the labels for the input and output plugins.
        This method extracts the x, y, z components from the input and output plugin strings
        and updates the corresponding labels in the UI.
        :param input_idx: The index of the input plugin.
        :param output_idx: The index of the output plugin.
        """

        self.ui.label_x_input.setText("")
        self.ui.label_y_input.setText("")
        self.ui.label_z_input.setText("")
        self.ui.label_x_output.setText("")
        self.ui.label_y_output.setText("")
        self.ui.label_z_output.setText("")

        if input_idx >= 0:
            input  = vu.spacetime_cuda_get_tr_input_plugin(self.spacetime, input_idx)[0].decode('utf-8')

            input_x  = utils.plugin_extract(input,  1)
            input_y  = utils.plugin_extract(input,  2)
            input_z  = utils.plugin_extract(input,  3)
            self.ui.label_x_input.setText(input_x)
            if self.dim > 1: self.ui.label_y_input.setText(input_y)
            if self.dim > 2: self.ui.label_z_input.setText(input_z)

        if output_idx >= 0:
            output = vu.spacetime_cuda_get_tr_output_plugin(self.spacetime, output_idx)[0].decode('utf-8')
            output_x = utils.plugin_extract(output, 1)
            output_y = utils.plugin_extract(output, 2)
            output_z = utils.plugin_extract(output, 3)
            self.ui.label_x_output.setText(output_x)
            if self.dim > 1: self.ui.label_y_output.setText(output_y)
            if self.dim > 2: self.ui.label_z_output.setText(output_z)

    def set_plugins(self):
        """
        Check and set the plugins based on the input and output plugin strings.
        """
        if not vu.spacetime_cuda_is_tr_active(self.spacetime):
            QtWidgets.QMessageBox.critical(self, "Error", "Transformation is not active.")
            return
        input_plugin = self.ui.input_plugin.text()
        output_plugin = self.ui.output_plugin.text()
        if len(input_plugin) != self.ui.num.value():
            QtWidgets.QMessageBox.critical(self, "Error", f"Input plugin length {len(input_plugin)} does not match num {self.ui.num.value()}.")
            return
        if len(output_plugin) != self.ui.num.value():
            QtWidgets.QMessageBox.critical(self, "Error", f"Output plugin length {len(output_plugin)} does not match num {self.ui.num.value()}.")
            return
        if not utils.plugin_check_complete(output_plugin, self.dim):
            QtWidgets.QMessageBox.critical(self, "Error", f"Output plugin {output_plugin} is not valid.")
            return

        found = False
        for i in range(vu.spacetime_cuda_get_tr_num_inputs(self.spacetime)):
            inp, _ = vu.spacetime_cuda_get_tr_input_plugin(self.spacetime, i)
            inp = inp.decode('utf-8')
            if inp == input_plugin:
                if i <= 4000:
                    self.ui.InputList.setCurrentRow(i)
                vu.spacetime_cuda_set_tr_input_plugin(self.spacetime, i)
                found = True
                print(f"Input plugin found: {inp}")
                break
        if not found:
            QtWidgets.QMessageBox.warning(self, "Warning", f"Input plugin {input_plugin} not valid.")
            return
        
        input_idx = i

        found = False
        for i in range(vu.spacetime_cuda_get_tr_num_outputs(self.spacetime)):
            out, _ = vu.spacetime_cuda_get_tr_output_plugin(self.spacetime, i)
            out = out.decode('utf-8')
            if out == output_plugin:
                if i <= 4000:
                    self.ui.OutputList.setCurrentRow(i)
                vu.spacetime_cuda_set_tr_output_plugin(self.spacetime, i)
                found = True
                print(f"Output plugin found: {out}")
                break
        if not found:
            QtWidgets.QMessageBox.warning(self, "Warning", f"Output plugin {output_plugin} not valid.")
            return
        
        output_idx = i

        self.update_labels(input_idx, output_idx)

    def activate(self, value):
        """
        Activate or deactivate the widget based on the value.
        :param value: The value to set the activation state.
        """
        self.ui.num.setEnabled(value)
        self.ui.vx.setEnabled(value)
        if self.dim > 1: self.ui.vy.setEnabled(value)
        if self.dim > 2: self.ui.vz.setEnabled(value)
        
        self.ui.Compute.setEnabled(value)
        self.ui.InputList.setEnabled(value)
        self.ui.OutputList.setEnabled(value) 
        self.ui.input_plugin.setEnabled(value)
        self.ui.output_plugin.setEnabled(value)
        self.ui.set_plugins.setEnabled(value)
        vu.spacetime_cuda_set_tr_active(self.spacetime, int(value))
        if value:
            tr_dim, _, _, _, _, _ = vu.spacetime_cuda_get_tr_params(self.spacetime)
            if self.dim == tr_dim:
                self._load_plugins()


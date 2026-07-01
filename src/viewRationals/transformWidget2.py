from PyQt5 import QtWidgets, QtCore
from ui.transformWidget2UI import Ui_TransformWidget
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
        self.ui.plugin_x_and.setEnabled(False)
        self.ui.plugin_y_and.setEnabled(False)
        self.ui.plugin_z_and.setEnabled(False)
        self.ui.plugin_x_or.setEnabled(False)
        self.ui.plugin_y_or.setEnabled(False)
        self.ui.plugin_z_or.setEnabled(False)
        self.ui.check_and_find.setEnabled(False)
        self.plugins_loaded = False
        if  vu.spacetime_cuda_is_tr_active(self.spacetime):
            self.ui.activate.setChecked(True)
            self.ui.vx.setEnabled(True)
            self.ui.plugin_x_and.setEnabled(True)
            self.ui.plugin_x_or.setEnabled(True)
            if dim > 1: 
                self.ui.vy.setEnabled(True)
                self.ui.plugin_y_and.setEnabled(True)
                self.ui.plugin_y_or.setEnabled(True)
            if dim > 2: 
                self.ui.vz.setEnabled(True)
                self.ui.plugin_z_and.setEnabled(True)
                self.ui.plugin_z_or.setEnabled(True)
            tr_dim, _, _, _, _, _= vu.spacetime_cuda_get_tr_params(self.spacetime)
            self.ui.check_and_find.setEnabled(True)
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

        input_int = self.ui.InputList.currentItem().data(QtCore.Qt.UserRole) if self.ui.InputList.currentItem() else None
        output_int = self.ui.OutputList.currentItem().data(QtCore.Qt.UserRole) if self.ui.OutputList.currentItem() else None

        if input_int is not None and output_int is not None:
            input = vu.spacetime_cuda_get_tr_input_plugin(self.spacetime, input_int)[0].decode('utf-8')
            output = vu.spacetime_cuda_get_tr_output_plugin(self.spacetime, output_int)[0].decode('utf-8')

            input_x = utils.plugin_extract(input, 1)
            input_y = utils.plugin_extract(input, 2) if self.dim > 1 else ''
            input_z = utils.plugin_extract(input, 3) if self.dim > 2 else ''

            output_x = utils.plugin_extract(output, 1)
            output_y = utils.plugin_extract(output, 2) if self.dim > 1 else ''
            output_z = utils.plugin_extract(output, 3) if self.dim > 2 else ''

            plugin_x_and = utils.num_ones(utils.plugin_and(input_x, output_x))
            plugin_y_and = utils.num_ones(utils.plugin_and(input_y, output_y)) if self.dim > 1 else 0
            plugin_z_and = utils.num_ones(utils.plugin_and(input_z, output_z)) if self.dim > 2 else 0
            plugin_x_or = utils.num_ones(utils.plugin_or(input_x, output_x))
            plugin_y_or = utils.num_ones(utils.plugin_or(input_y, output_y)) if self.dim > 1 else 0
            plugin_z_or = utils.num_ones(utils.plugin_or(input_z, output_z)) if self.dim > 2 else 0

            self.ui.plugin_x_and.setValue(plugin_x_and)
            if self.dim > 1: self.ui.plugin_y_and.setValue(plugin_y_and)
            if self.dim > 2: self.ui.plugin_z_and.setValue(plugin_z_and)
            self.ui.plugin_x_or.setValue(plugin_x_or)
            if self.dim > 1: self.ui.plugin_y_or.setValue(plugin_y_or)
            if self.dim > 2: self.ui.plugin_z_or.setValue(plugin_z_or)

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
            row_input = self.ui.InputList.currentItem().data(QtCore.Qt.UserRole)
            input, _ = vu.spacetime_cuda_get_tr_input_plugin(self.spacetime, row_input)
        if input:
            input = input.decode('utf-8')
        if self.ui.OutputList.currentItem():
            row_output = self.ui.OutputList.currentItem().data(QtCore.Qt.UserRole)
            output, _ = vu.spacetime_cuda_get_tr_output_plugin(self.spacetime, row_output)
        if output:
            output = output.decode('utf-8')

        self.ui.label_x_input.setText("")
        self.ui.label_y_input.setText("")
        self.ui.label_z_input.setText("")
        self.ui.label_x_output.setText("")
        self.ui.label_y_output.setText("")
        self.ui.label_z_output.setText("")

        if input and output:
            input_x  = utils.plugin_extract(input,  1)
            input_y  = utils.plugin_extract(input,  2)
            input_z  = utils.plugin_extract(input,  3)
            output_x = utils.plugin_extract(output, 1)
            output_y = utils.plugin_extract(output, 2)
            output_z = utils.plugin_extract(output, 3)

            self.ui.label_x_input.setText(input_x)
            if self.dim > 1: self.ui.label_y_input.setText(input_y)
            if self.dim > 2: self.ui.label_z_input.setText(input_z)
            
            self.ui.label_x_output.setText(output_x)
            if self.dim > 1: self.ui.label_y_output.setText(output_y)
            if self.dim > 2: self.ui.label_z_output.setText(output_z)

            plugin_x_and = utils.num_ones(utils.plugin_and(input_x, output_x))
            plugin_y_and = utils.num_ones(utils.plugin_and(input_y, output_y)) if self.dim > 1 else 0
            plugin_z_and = utils.num_ones(utils.plugin_and(input_z, output_z)) if self.dim > 2 else 0
            plugin_x_or = utils.num_ones(utils.plugin_or(input_x, output_x))
            plugin_y_or = utils.num_ones(utils.plugin_or(input_y, output_y)) if self.dim > 1 else 0
            plugin_z_or = utils.num_ones(utils.plugin_or(input_z, output_z)) if self.dim > 2 else 0

            self.ui.plugin_x_and.setValue(plugin_x_and)
            if self.dim > 1: self.ui.plugin_y_and.setValue(plugin_y_and)
            if self.dim > 2: self.ui.plugin_z_and.setValue(plugin_z_and)
            self.ui.plugin_x_or.setValue(plugin_x_or)
            if self.dim > 1: self.ui.plugin_y_or.setValue(plugin_y_or)
            if self.dim > 2: self.ui.plugin_z_or.setValue(plugin_z_or)

    def check_and_find(self):
        """
        Check and find the plugin based on the input values.
        This method is called when the user clicks the "Check and find" button.
        """
        zero = '0' * self.ui.num.value()
        plugin_x_input = self.ui.label_x_input.text()
        plugin_y_input = self.ui.label_y_input.text() if self.dim > 1 else zero
        plugin_z_input = self.ui.label_z_input.text() if self.dim > 2 else zero
        plugin_x_output = self.ui.label_x_output.text()
        plugin_y_output = self.ui.label_y_output.text() if self.dim > 1 else zero
        plugin_z_output = self.ui.label_z_output.text() if self.dim > 2 else zero
        
        # valid = False
        # l = len(plugin_x_input)
        # for i in range(l):
        #     for j in range(l):
        #         for k in range(l):
        #             plugin_input = utils.plugin_join(
        #                 [
        #                     utils.plugin_shift(plugin_x_input, i),
        #                     utils.plugin_shift(plugin_y_input, j),
        #                     utils.plugin_shift(plugin_z_input, k)
        #                 ],
        #                 self.dim
        #             )
        #             print(f"Checking input plugin: {plugin_input}")
        #             if utils.plugin_check_complete(plugin_input, self.dim):
        #                 valid = True
        #                 break
        #         if valid:
        #             break
        #     if valid:
        #         break
        # if not valid:
        #     QtWidgets.QMessageBox.warning(self, "Warning", "No valid input plugin found.")
        #     return
        plugin_input = utils.plugin_join(
            [
                utils.plugin_shift(plugin_x_input, 0),
                utils.plugin_shift(plugin_y_input, 0),
                utils.plugin_shift(plugin_z_input, 0)
            ],
            self.dim
        )

        found = False
        for i in range(vu.spacetime_cuda_get_tr_num_inputs(self.spacetime)):
            input_plugin = vu.spacetime_cuda_get_tr_input_plugin(self.spacetime, i)[0].decode('utf-8')
            if input_plugin == plugin_input:
                self.ui.InputList.setCurrentRow(i)
                vu.spacetime_cuda_set_tr_input_plugin(self.spacetime, i)
                found = True
                print(f"Input plugin found: {input_plugin}")
                break
        if not found:
            QtWidgets.QMessageBox.warning(self, "Warning", f"Input plugin {plugin_input} not valid.")
            return

        valid = False 
        l = len(plugin_x_output)
        for i in range(l):
            for j in range(l):
                for k in range(l):
                    plugin_output = utils.plugin_join(
                        [
                            utils.plugin_shift(plugin_x_output, i),
                            utils.plugin_shift(plugin_y_output, j),
                            utils.plugin_shift(plugin_z_output, k)
                        ],
                        self.dim
                    )
                    print(f"Checking output plugin: {plugin_output} with dim: {self.dim}")
                    if utils.plugin_check_complete(plugin_output, self.dim):
                        valid = True
                        break
                if valid:
                    break
            if valid:
                break

        if not valid:
            QtWidgets.QMessageBox.warning(self, "Warning", "No valid output plugin found.")
            return

        found = False
        print(f"Searching for output plugin: {plugin_output}")
        for i in range(vu.spacetime_cuda_get_tr_num_outputs(self.spacetime)):
            output_plugin = vu.spacetime_cuda_get_tr_output_plugin(self.spacetime, i)[0].decode('utf-8')
            if output_plugin == plugin_output:
                self.ui.OutputList.setCurrentRow(i)
                vu.spacetime_cuda_set_tr_output_plugin(self.spacetime, i)
                print(f"Output plugin found: {output_plugin}")
                found = True
                break
        if not found:
            QtWidgets.QMessageBox.warning(self, "Warning", f"Output plugin {plugin_output} not valid.")
            return

    def generate_input_and_output(self):
        """
        Generate the input and output plugin strings based on the current AND and OR values.
        This method is called when the user changes any value in the plugin AND or OR fields.
        """
        if not vu.spacetime_cuda_is_tr_active(self.spacetime):
            QtWidgets.QMessageBox.critical(self, "Error", "Transformation is not active.")
            return
        
        plugin_x_and = self.ui.plugin_x_and.value()
        plugin_y_and = self.ui.plugin_y_and.value() if self.dim > 1 else 0
        plugin_z_and = self.ui.plugin_z_and.value() if self.dim > 2 else 0
        plugin_x_or  = self.ui.plugin_x_or.value()
        plugin_y_or  = self.ui.plugin_y_or.value() if self.dim > 1 else 0
        plugin_z_or  = self.ui.plugin_z_or.value() if self.dim > 2 else 0

        plugin_x_input, plugin_x_output = utils.plugin_create(
            self.ui.num.value(),
            self.ui.vx.value(),
            plugin_x_and,
            plugin_x_or
        )
        plugin_y_input, plugin_y_output = utils.plugin_create(
            self.ui.num.value(),
            self.ui.vy.value(),
            plugin_y_and,
            plugin_y_or
        ) if self.dim > 1 else ("", "")
        plugin_z_input, plugin_z_output = utils.plugin_create(
            self.ui.num.value(),
            self.ui.vz.value(),
            plugin_z_and,
            plugin_z_or
        ) if self.dim > 2 else ("", "")

        self.ui.label_x_input.setText(plugin_x_input)
        if self.dim > 1: self.ui.label_y_input.setText(plugin_y_input)
        if self.dim > 2: self.ui.label_z_input.setText(plugin_z_input)
        self.ui.label_x_output.setText(plugin_x_output)
        if self.dim > 1: self.ui.label_y_output.setText(plugin_y_output)
        if self.dim > 2: self.ui.label_z_output.setText(plugin_z_output)

    def activate(self, value):
        """
        Activate or deactivate the widget based on the value.
        :param value: The value to set the activation state.
        """
        self.ui.num.setEnabled(value)
        self.ui.vx.setEnabled(value)
        if self.dim > 1: self.ui.vy.setEnabled(value)
        if self.dim > 2: self.ui.vz.setEnabled(value)
        self.ui.plugin_x_and.setEnabled(value)
        if self.dim > 1: self.ui.plugin_y_and.setEnabled(value)
        if self.dim > 2: self.ui.plugin_z_and.setEnabled(value)
        self.ui.plugin_x_or.setEnabled(value)
        if self.dim > 1: self.ui.plugin_y_or.setEnabled(value)
        if self.dim > 2: self.ui.plugin_z_or.setEnabled(value)
        
        self.ui.Compute.setEnabled(value)
        self.ui.InputList.setEnabled(value)
        self.ui.OutputList.setEnabled(value) 
        self.ui.check_and_find.setEnabled(value)
        vu.spacetime_cuda_set_tr_active(self.spacetime, value)
        if value:
            tr_dim, _, _, _, _, active = vu.spacetime_cuda_get_tr_params(self.spacetime)
            if self.dim == tr_dim:
                self._load_plugins()


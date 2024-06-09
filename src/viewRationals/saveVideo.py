from PyQt5 import QtWidgets
from multiprocessing import cpu_count

class SaveVideoWidget(QtWidgets.QDialog):
    def __init__(self, parent, current_frame, max_time, views_mode, resx, resy, callback) -> None:
        super().__init__(parent)

        print(f'Video Widget: ({resx}, {resy})')

        self.callback = callback
        
        self.vlayout = QtWidgets.QVBoxLayout()
        self.gridlayout = QtWidgets.QGridLayout()
        self.vlayout.addLayout(self.gridlayout)

        self.label1 = QtWidgets.QLabel('Init time')
        self.gridlayout.addWidget(self.label1, 0, 0)
        self.init_frame = QtWidgets.QSpinBox(self)
        self.init_frame.setMinimum(0)
        self.init_frame.setMaximum(10000)
        self.init_frame.setValue(current_frame)
        self.gridlayout.addWidget(self.init_frame, 0, 1)

        self.label2 = QtWidgets.QLabel('End time')
        self.gridlayout.addWidget(self.label2, 1, 0)
        self.end_frame = QtWidgets.QSpinBox(self)
        self.end_frame.setMinimum(0)
        self.end_frame.setMaximum(10000)
        self.end_frame.setValue(current_frame)
        self.gridlayout.addWidget(self.end_frame, 1, 1)

        self.label3 = QtWidgets.QLabel('Video frames')
        self.gridlayout.addWidget(self.label3, 2, 0)
        self.video_frames = QtWidgets.QSpinBox(self)
        self.video_frames.setMinimum(0)
        self.video_frames.setMaximum(10000)
        self.video_frames.setValue(300)
        self.gridlayout.addWidget(self.video_frames, 2, 1)

        self.labelx = QtWidgets.QLabel('Fps')
        self.gridlayout.addWidget(self.labelx, 3, 0)
        self.fps = QtWidgets.QDoubleSpinBox(self)
        self.fps.setMinimum(1)
        self.fps.setMaximum(100)
        self.fps.setValue(25)
        self.gridlayout.addWidget(self.fps, 3, 1)

        self.labelx = QtWidgets.QLabel('Num Cpu')
        self.gridlayout.addWidget(self.labelx, 4, 0)
        self.num_cpu = QtWidgets.QSpinBox(self)
        self.num_cpu.setMinimum(1)
        self.num_cpu.setMaximum(cpu_count())
        self.num_cpu.setValue(int(cpu_count() * 0.5))
        self.gridlayout.addWidget(self.num_cpu, 4, 1)

        self.label4 = QtWidgets.QLabel('Turn degrees')
        self.gridlayout.addWidget(self.label4, 5, 0)
        self.turn_degrees = QtWidgets.QSpinBox(self)
        self.turn_degrees.setMinimum(0)
        self.turn_degrees.setMaximum(10000)
        self.turn_degrees.setValue(360)
        self.gridlayout.addWidget(self.turn_degrees, 5, 1)

        self.label6 = QtWidgets.QLabel('Prefix')
        self.gridlayout.addWidget(self.label6, 6, 0)
        self.prefix = QtWidgets.QLineEdit(self)
        self.gridlayout.addWidget(self.prefix, 6, 1)

        self.label7 = QtWidgets.QLabel('Suffix')
        self.gridlayout.addWidget(self.label7, 7, 0)
        self.suffix = QtWidgets.QLineEdit(self)
        self.gridlayout.addWidget(self.suffix, 7, 1)

        self.label8 = QtWidgets.QLabel('Subfolder')
        self.gridlayout.addWidget(self.label8, 8, 0)
        self.subfolder = QtWidgets.QLineEdit(self)
        self.gridlayout.addWidget(self.subfolder, 8, 1)

        self.label9 = QtWidgets.QLabel('Legend')
        self.gridlayout.addWidget(self.label9, 9, 0)
        self.noLegend = QtWidgets.QCheckBox(self)
        self.noLegend.setChecked(True)
        self.gridlayout.addWidget(self.noLegend, 9, 1)

        self.label10 = QtWidgets.QLabel('Clean images')
        self.gridlayout.addWidget(self.label10, 10, 0)
        self.cleanImages = QtWidgets.QCheckBox(self)
        self.cleanImages.setChecked(True)
        self.gridlayout.addWidget(self.cleanImages, 10, 1)

        self.labelresx = QtWidgets.QLabel('res x')
        self.gridlayout.addWidget(self.labelresx, 11, 0)
        self.resx = QtWidgets.QSpinBox(self)
        self.resx.setMaximum(10000)
        self.resx.setValue(resx)
        self.gridlayout.addWidget(self.resx, 11, 1)

        self.labelresy = QtWidgets.QLabel('res y')
        self.gridlayout.addWidget(self.labelresy, 12, 0)
        self.resy = QtWidgets.QSpinBox(self)
        self.resy.setMaximum(10000)
        self.resy.setValue(resy)
        self.gridlayout.addWidget(self.resy, 12, 1)

        self.hlayout = QtWidgets.QHBoxLayout()
        self.hlayout.addStretch()
        self.button_save = QtWidgets.QPushButton('Save Video', self)
        self.button_save.clicked.connect(self.save)
        self.hlayout.addWidget(self.button_save)
        
        self.button_cancel = QtWidgets.QPushButton('Cancel', self)
        self.button_cancel.clicked.connect(self.close)
        self.hlayout.addWidget(self.button_cancel)

        self.vlayout.addLayout(self.hlayout)
        self.setLayout(self.vlayout)

        self.setWindowTitle('Turntable Video')

        if views_mode not in ['3D', '3DSPLIT']:
            self.init_frame.setValue(0)
            self.end_frame.setValue(max_time)
            self.video_frames.setValue(max_time)
            self.turn_degrees.setValue(0)
            self.turn_degrees.setEnabled(False)
            fps = 1.0
        else:
            fps = 25.0
        self.fps.setValue(fps)

    def save(self):
        if self.init_frame.value() > self.end_frame.value():
            QtWidgets.QMessageBox.critical(self, "ERROR", 'End frame must be greater or equal than init frame')
            return
        self.close()
        self.callback(
            self.init_frame.value(), 
            self.end_frame.value(), 
            self.subfolder.text(),
            self.prefix.text(),
            self.suffix.text(),
            self.video_frames.value(),
            self.fps.value(),
            self.turn_degrees.value(),
            self.cleanImages.isChecked(),
            self.noLegend.isChecked(),
            self.num_cpu.value(),
            self.resx.value(),
            self.resy.value()
        )




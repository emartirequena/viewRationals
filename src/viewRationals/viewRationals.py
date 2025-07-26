import os
import sys
from time import time
from multiprocessing import freeze_support, Manager
from threading import Thread
from copy import deepcopy
import numpy as np
from gc import collect
import traceback as trace

from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt
from madcad import vec3, settings
from mainWindowUi import MainWindowUI
from views import Views
from saveSpecials import SaveSpecialsWidget
from saveVideo import SaveVideoWidget
from getObjects import get_objects
from utils import getDivisorsAndFactors, divisors
from timing import timing, get_duration
from config import config
from color import ColorLine, _convert_color
from histogram import Histogram
from saveImages import _saveImages, _create_video
from transformWidget import TransformWidget
import viewUtils as vu


settings_file = r'settings.txt'
opengl_version = (3,3)


def cells_to_list(cells):
    """
    Convert a list of cells to a list of dicts.
    """
    out_cells = []
    for cell in cells:
        out_cell = {
            'pos': (cell.x, cell.y, cell.z),
            'count': cell.count,
            'next_digits': vu.cell_cuda_get_next_digits(cell)[0],
        }
        out_cells.append(out_cell)
    return out_cells


def spacetime_to_list(spacetime, selected_rationals, view_selected_rationals=False, accumulate=False):
    """
    Convert a spacetime object to a list of dicts.
    """
    out_spacetime = {
        'max_val': spacetime.max_val,
        'spaces': [],
    }
    for frame in range(spacetime.max_val+1):
        if view_selected_rationals:
            cells = vu.spacetime_cuda_getCellsWithRationals(
                spacetime, selected_rationals, len(selected_rationals), frame, accumulate
            )
        else:
            cells = vu.spacetime_cuda_getCells(spacetime, frame, accumulate)
        out_spacetime['spaces'].append({
            'cells': cells_to_list(cells),
        })
    return out_spacetime


class VideoThread(Thread):
    def __init__(self, parent, func_process, args_process, func_video, single_image):
        super().__init__()
        self.parent = parent
        self.func_process = func_process
        self.args_process = args_process
        self.func_video = func_video
        self.processes = None
        self.killed = False
        self.single_image = single_image
    
    def run(self):
        self.parent.statusLabel.setFont(QtGui.QFont('Courier'))
        self.parent.setStatus(f'Creating single image or video sequence, please wait...')
        self.processes = self.func_process(self.args_process)
        self.processes[0].close()
        self.processes[0].join()
        if not self.killed and not self.single_image and self.processes[1]:
            self.func_video(self.processes[1])
            self.parent.setStatus(f'Video saved for number {int(self.parent.number.value()):d} in {get_duration():.2f} secs')
        elif not self.killed:
            self.parent.setStatus(f'Image saved for number {int(self.parent.number.value()):d} in {get_duration():.2f} secs')
        self.parent.statusLabel.setFont(QtGui.QFont('Arial'))
        self.parent.shr_num_video_frames.value = -1
        del self.args_process
        if not self.killed:
            del self.processes
        else:
            self.killed = False
        collect()

    def kill(self):
        if self.processes:
            self.parent.setStatus('CANCELLED VIDEO CREATION...')
            self.killed = True
            self.processes[0].terminate()
            self.processes[0].close()
            self.processes[0].join()
            self.parent.timer_video.stop()
            del self.processes
            collect()
            

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = MainWindowUI()
        self.ui.setUpUi(self)
        self.dim = 3
        self.count = 0
        self.cell_ids = {}
        self.selected = {}
        self.selected_rationals = []
        self.selected_center = None
        self.selected_time = None
        self.view_selected_rationals = False
        self.views = None
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.rotate3DView)
        self.timer_video = QtCore.QTimer(self)
        self.timer_video.timeout.connect(self.message_video)
        self.timer_video_count = 0
        self.turntable_angle = 0.005
        self.first_number_set = False
        self.changed_spacetime = True
        self.need_compute = True
        self.histogram = None
        self.view_histogram = True
        self.view_objects = True
        self.view_time = False
        self.view_next_number = False
        self.spacetime = vu.spacetime_cuda_create(2, 2**(self.dim * 2) - 1,  3, 1)
        self.video_thread = None
        self.factors = ''
        self.num = 0
        self.numbers = {}
        self.config = config
        self.color = None
        self.statusLabel.setFont(QtGui.QFont('Arial'))
        self.files_path = self.config.get('files_path')
        self.loadConfigColors()
        self._clear_parameters()
        self.showMaximized()
        settings.display['background_color'] = vec3(*_convert_color(config.get('background_color')))

    def loadConfigColors(self):
        self.color = ColorLine()
        colors = self.config.get('colors')
        if colors:
            for knot in colors:
                self.color.add(knot['alpha'], vec3(*knot['color']))
        
    def _check_accumulate(self):
        return bool(self.accumulate.checkState())

    def _clear_view(self):
        self.first_number_set = False
        if self.views:
            self.views.clear()
            if self.histogram:
                self.histogram.clear()
        else:
            self.make_view(0)
        if self.cell_ids:
            del self.cell_ids
        self.cell_ids = {}
        if self.selected:
            del self.selected
        self.selected = {}
        collect()
        self.timer.stop()

    def _clear_parameters(self):
        self.period.setValue(1)
        self.period_changed = False
        self.timeWidget.valueChanged.disconnect(self.timeChanged)
        self.maxTime.setValue(0)
        self.timeWidget.valueChanged.connect(self.timeChanged)
        self.number.setValue(0)
        self.divisors.clear()
        self.factorsLabel.setText('')
        self.label_num_divisors.setText('')
        pressed     = 'QPushButton {background-color: bisque;      color: red;    border-width: 1px; border-radius: 4px; border-style: outset; border-color: gray;}'
        not_pressed = 'QPushButton {background-color: floralwhite; color: black;  border-width: 1px; border-radius: 4px; border-style: outset; border-color: gray;}' \
                      'QPushButton:hover {background-color: lightgray; border-color: blue;}'
        if self.dim == 1:
            if self.views:
                self.views.set_mode('1D')
            self.button1D.setStyleSheet(pressed)
            self.button2D.setStyleSheet(not_pressed)
            self.button3D.setStyleSheet(not_pressed)
        elif self.dim == 2:
            if self.views:
                self.views.set_mode('2D')
            self.button1D.setStyleSheet(not_pressed)
            self.button2D.setStyleSheet(pressed)
            self.button3D.setStyleSheet(not_pressed)
        elif self.dim == 3:
            if self.views:
                self.views.set_mode(self.views.get_mode_3d())
            self.button1D.setStyleSheet(not_pressed)
            self.button2D.setStyleSheet(not_pressed)
            self.button3D.setStyleSheet(pressed)
        self._clear_view()

    def set1D(self):
        self.dim = 1
        self._clear_parameters()

    def set2D(self):
        self.dim = 2
        self._clear_parameters()

    def set3D(self):
        self.dim = 3
        self._clear_parameters()

    def setTimeInit(self):
        self.timeWidget.setValue(0)

    def setTimeEnd(self):
        self.timeWidget.setValue(self.maxTime.value())

    def moveNextCycle(self):
        frame = self.timeWidget.value()
        T = self.period.value()
        cycle = frame // T
        frame = (cycle + 1) * T
        if frame < self.maxTime.value():
            self.timeWidget.setValue(frame)
        else:
            self.timeWidget.setValue(self.maxTime.value())

    def movePrevCycle(self):
        frame = self.timeWidget.value()
        T = self.period.value()
        cycle = frame // T
        if frame % T == 0:
            frame = (cycle - 1) * T
        else:
            frame = cycle * T
        if frame > 0:
            self.timeWidget.setValue(frame)
        else:
            self.timeWidget.setValue(0)

    def decrementTime(self):
        t = self.timeWidget.value()
        if t > 0:
            self.timeWidget.setValue(t - 1)

    def incrementTime(self):
        t = self.timeWidget.value()
        if t < self.maxTime.value():
            self.timeWidget.setValue(t + 1)

    def timeChanged(self):
        if self.selected_center:
            self._select_time_changed()
        self.draw_objects()

    def setStatus(self, txt: str):
        print(f'status: {txt}')
        self.statusLabel.setText(str(txt))
        self.statusBar.show()
        app.processEvents(QtCore.QEventLoop.ProcessEventsFlag.ExcludeUserInputEvents)

    def _getDimStr(self):
        dims = ['1D', '2D', '3D']
        return dims[self.dim - 1]

    def saveImage(self, subfolder=''):
        if subfolder == False: subfolder = ''
        frame = int(self.time.value())
        self.saveVideo(
            init_frame=frame, end_frame=frame, subfolder=subfolder, num_frames=1,
            resx=self.config.get('image_resx'),
            resy=self.config.get('image_resy'),
            legend=self.config.get('image_legend')
        )

    def saveVideo(
            self, init_frame=0, end_frame=0, subfolder='', prefix='', suffix='', num_frames=0, fps=1.0, turn_angle=0, 
            clean_images=True, legend=True, num_cpus=8, resx=1920, resy=1080
        ):
        if self.views.mode not in ['1D', '2D', '3D']:
            QtWidgets.QMessageBox.critical(self, 'ERROR', 'Split 3D view is not allowed for videos')
            return
        if end_frame > self.maxTime.value():
            QtWidgets.QMessageBox.critical(self, 'ERROR', 'End Frame cannot be greatest than Max Time')
            return
        self.deselect_all()

        app.setOverrideCursor(QtCore.Qt.WaitCursor)
        image_path = self.config.get('image_path')
        frame_rate = fps
        single_image = False
        if num_frames == 1:
            single_image = True
        if num_frames == 0:
            if end_frame == 0:
                num_frames = int(self.maxTime.value() * frame_rate)
            else:
                num_frames = int((end_frame - init_frame + 1) * frame_rate)
        if end_frame == 0:
            end_frame = int(self.maxTime.value())
        if self._check_accumulate() and turn_angle == 0 and num_frames > 1:
            init_frame = 0
            end_frame = 6
            num_frames = 6

        manager = Manager()
        projection = self.views.views[self.views.mode].view.projection
        navigation = self.views.views[self.views.mode].view.navigation
        shr_projection = manager.Value(type(projection), projection)
        shr_navigation = manager.Value(type(navigation), navigation)
        self.num_video_frames = 0
        self.max_video_frames = deepcopy(num_frames)
        self.shr_num_video_frames = manager.Value(int, self.num_video_frames)

        if self.view_selected_rationals:
            view_cells = vu.spacetime_cuda_getCellsWithRationals(
                self.spacetime, self.selected_rationals, len(self.selected_rationals),
                self.timeWidget.value(), self._check_accumulate()
            )

        selected_rationals = [int(x) for x in self.selected_rationals]

        view_spacetime = spacetime_to_list(
            self.spacetime, selected_rationals, self.view_selected_rationals, self._check_accumulate()
        )

        args = (
            shr_projection,
            shr_navigation,
            image_path,
            init_frame,
            end_frame,
            frame_rate,
            subfolder,
            prefix,
            suffix,
            num_frames,
            turn_angle,
            config,
            self.color,
            self.views.views[self.views.mode].type,
            view_spacetime,
            selected_rationals,
            self.dim,
            self.number.value(),
            self.period.value(),
            self.get_output_factors(self.number.value()),
            self._check_accumulate(),
            self._getDimStr(),
            self.actionViewObjects.isChecked(),
            self.actionViewTime.isChecked(),
            self.actionViewNextNumber.isChecked(),
            int(self.maxTime.value()),
            self.shr_num_video_frames,
            clean_images,
            self.selected_center,
            self.selected_time,
            num_cpus,
            legend,
            resx,
            resy
        )

        self.timer_video_count = 0
        self.timer_video.start(1000)
        self.video_thread = VideoThread(self, _saveImages, args, _create_video, single_image)
        self.video_thread.start()

        app.restoreOverrideCursor()

    def cancelVideo(self):
        self.timer_video.stop()
        if self.video_thread:
            self.video_thread.kill()

    def message_video(self):
        l = ['|', '/', '-', '\\']
        if self.shr_num_video_frames.value < 0:
            self.timer_video.stop()
        elif self.shr_num_video_frames.value == 0:
            self.setStatus('Initializing video creation. Please wait...')
        else:
            e = l[self.timer_video_count % 4]
            self.setStatus(f'{e} Creating video, num frames {self.shr_num_video_frames.value} / {self.max_video_frames}')
            self.timer_video_count += 1

    def _switch_display(self, count, state=None):
        for id in self.cell_ids[count]:
            self.views.switch_display_id(id, state=state)

    def select_rationals(self):
        if not self.selected_rationals:
            return
        self.view_selected_rationals = not self.view_selected_rationals
        if not self.view_selected_rationals:
            self.selected_rationals = []
        if self.histogram:
            self.histogram.set_rationals(self.selected_rationals)
        if self.views:
            self.select_center(0, 0, 0)
            self.draw_objects()
            self.views.update()

    def select_cell(self, cell):
        print(f'Selecting cell {cell.x} {cell.y} {cell.z} at time {self.time.value()}')
        self.selected_rationals = vu.cell_cuda_get_rationals(cell)
        print(f'Selected rationals: {len(self.selected_rationals)}')
        self.view_selected_rationals = True
        if self.views:
            self.draw_objects()
            self.views.update()
        if self.histogram:
            self.histogram.clear()
            self.histogram.set_rationals(self.selected_rationals)

    def select_center(self, x, y=0, z=0):
        self.selected_center = (x, y, z)
        self.selected_time = self.timeWidget.value()
        self._select_time_changed()

    def deselect_center(self):
        self.selected_center = None
        self.selected_time = None

    def _select_time_changed(self):
        if not self.selected_center:
            return
        if self.selected_time == 0:
            self.selected_time = 1
        v = np.array(self.selected_center) / self.selected_time
        p = v * self.timeWidget.value()
        self.views.moveTo(p[0], p[1], p[2])
        self.views.update()
        self.update()

    def select_cells(self, count):
        if not count:
            return
        if count not in self.selected:
            self.selected[count] = self.cell_ids[count]
            self._switch_display(count, True)
        else:
            self._switch_display(count, False)
            del self.selected[count]

    def select_all(self, nope=False):
        for count in self.cell_ids:
            if count not in self.selected:
                self.selected[count] = self.cell_ids[count]
                self._switch_display(count, True)
        self.refresh_selection()

    def deselect_all(self, nope=False):
        if not self.selected:
            return
        for count in self.selected:
            self._switch_display(count, False)
        self.selected = {}
        self.refresh_selection()

    def reselect_cells(self):
        for count in self.cell_ids:
            if count in self.selected:
                self._switch_display(count, True)
        self.refresh_selection()

    def invert_selection(self):
        not_selected = {}
        for count in self.cell_ids:
            if count in self.selected:
                self._switch_display(count, False)
            else:
                not_selected[count] = self.cell_ids[count]
                self._switch_display(count, True)
        self.selected = not_selected    
        self.refresh_selection()

    def refresh_selection(self):
        self.print_selection()
        if self.views:
            self.views.update()
        if self.histogram:
            self.histogram.display_all()
            self.histogram.update()

    def print_selection(self):
        selected_cells, selected_paths = self.get_selected_paths()
        if self._check_accumulate():
            max = self.spacetime.countPaths(int(self.time.value()), True)
        else:
            max = int(self.number.value() + 1)
        if selected_cells == 0:
            self.setStatus('Selected cells: 0')
            return
        percent = 100.0 * float(selected_paths) / float(max)
        text = f'Selected cells: {selected_cells}, num paths: {selected_paths} / {max}, percent: {percent:.2f}%'
        self.setStatus(text)
        
    
    def is_selected(self, count):
        if count in self.selected:
            return True
        return False
    
    def get_selected_paths(self):
        num_cells = 0
        total_paths = 0
        for count in self.selected:
            num_cells += len(self.selected[count])
            total_paths += count * len(self.selected[count])
        return num_cells, total_paths

    @timing
    def compute(self, nada=False):
        result = 1
        while result:
            result = collect()

        if not int(self.number.value()):
            return
        
        if self.selected_rationals:
            del self.selected_rationals
            self.selected_rationals = None

        if self.selected_center:
            self.select_center(0, 0, 0)
            self.deselect_center()

        self.view_selected_rationals = False
        self.deselect_all()

        if not self.need_compute:
            self.draw_objects()
            self.period_changed = False
            return

        app.setOverrideCursor(QtCore.Qt.WaitCursor)
        time1 = time()

        n = int(self.number.value())
        num = 2**(self.dim*int(self.period.value())) - 1

        print('resetting spacetime...')
        vu.spacetime_cuda_reset(self.spacetime, self.period.value(), num, self.maxTime.value(), self.dim)

        print('setting and adding rational set...')
        vu.spacetime_cuda_setRationalSet(self.spacetime, n, self.is_special)
        vu.spacetime_cuda_addRationalSet(self.spacetime, 0, 0, 0, 0)
    
        self.timeWidget.setValue(self.maxTime.value() if self.period_changed else self.time.value())
        self.timeWidget.setFocus()

        if self.time.value() != self.maxTime.value():
            self.time.setValue(self.maxTime.value())
        self.draw_objects()

        result = 1
        while result:
            result = collect()
        
        time2 = time()
        self.setStatus(f'Rationals set for number {n:,.0f} computed in {time2-time1:,.2f} secs')

        app.restoreOverrideCursor()

    @timing
    def draw_objects(self, frame=0):
        frame = self.timeWidget.value()
        if self.view_selected_rationals:
            view_cells = vu.spacetime_cuda_getCellsWithRationals(
                self.spacetime, self.selected_rationals, len(self.selected_rationals), frame, self._check_accumulate())
        else:
            view_cells = vu.spacetime_cuda_getCells(self.spacetime, frame, self._check_accumulate())

        out_cells = cells_to_list(view_cells)

        objs, count_cells, self.cell_ids = get_objects(
            out_cells,
            self.number.value(),
            self.dim,
            self._check_accumulate(),
            self.selected_rationals or [],
            self.config,
            self.color,
            self.view_objects,
            self.view_time,
            self.view_next_number, 
            self.maxTime.value(),
            frame,
            self.maxTime.value()
        )
        self.make_view(objs, count_cells)
        del objs
        result = 1
        while result:
            result = collect()

    @timing
    def make_objects(self, frame):
        rationals = []
        if self.view_selected_rationals:
            rationals = [int(x) for x in self.selected_rationals]
        view_cells = vu.spacetime_cuda_getCells(self.spacetime, frame, self._check_accumulate())
        objs, _, _ = get_objects(
            view_cells,
            self.number.value(),
            self.dim,
            self._check_accumulate(),
            rationals,
            self.config,
            self.color,
            self.view_objects,
            self.view_time,
            self.view_next_number, 
            self.maxTime.value(),
            frame,
            vu.spacetime_cuda_getMaxTime(self.spacetime, self._check_accumulate())
        )
        return objs

    def make_view(self, objs=None, count_cells=0):
        objs = objs or {}
        if not self.views:
            # print("view doesn't exists...")
            self.views = Views(self, parent=self)
            self.viewLayout.addWidget(self.views)
            
        elif not self.first_number_set:
            # print('setting first number...')
            self.first_number_set = True
            self.views.initialize(objs)
            if not self.histogram: 
                self.histogram = Histogram(self, self.spacetime)
            self.histogram.set_number(int(self.number.value()))
            if self.selected_rationals:
                self.histogram.set_rationals(self.selected_rationals)
            if self.view_histogram:
                self.histogram.set_time(self._check_accumulate())
                self.histogram.show()
        else:
            # print('continue setting number...')
            self.views.reset(objs)
            self.histogram.set_number(int(self.number.value()))
            self.histogram.set_rationals(self.selected_rationals or [])
            if self.view_histogram:
                self.histogram.set_time(self._check_accumulate())
                self.histogram.show()
        
        self.setStatus(f'{count_cells} cells created at time {self.timeWidget.value()} for number {int(self.number.value())}...')

    def fit_histogram(self):
        if not self.histogram or not self.view_histogram:
            return
        self.histogram.scene.fit()
        self.histogram.reset()
        self.histogram.update()

    def set_view_histogram(self):
        self.view_histogram = not self.view_histogram
        if not self.histogram:
            return
        if not self.view_histogram:
            self.histogram.hide()
        else:
            self.histogram.show()
            self.histogram.update()

    def center_view(self):
        if not self.views:
            return
        self.views.center()

    def swap_3d_view(self):
        if not self.views:
            return
        names = ['3D', '3DSPLIT']
        if not self.views.get_mode() in names:
            return
        new_mode = names[(names.index(self.views.mode) + 1) % 2]
        self.views.set_mode(new_mode)
        frame = self.time.value()
        objs = self.make_objects(frame)
        self.views.reinit(objs)
        self.reselect_cells()
        self.views.update()
        self.views.setFocus()
        collect()

    def turntable(self):
        if self.views.mode not in ['3D', '3DSPLIT']:
            return
        if self.timer.isActive():
            self.timer.stop()
            return
        self.timer.start(40)

    def rotate3DView(self):
        if self.views.mode not in ['3D', '3DSPLIT']:
            return
        self.views.rotate3DView(self.turntable_angle)
        self.update()

    def turntableFaster(self):
        self.turntable_angle *= 1.02

    def turntableSlower(self):
        self.turntable_angle /= 1.02

    def get_factors(self, number):
        factors = self.numbers[number]['factors']
        labels = []
        for factor in factors.keys():
            if factors[factor] == 0:
                continue
            elif factors[factor] == 1:
                labels.append(str(factor))
            else:
                labels.append(str(factor) + '^' + str(factors[factor]))

        if not labels:
            labels = ['1']

        label = ', '.join(labels)
        return label

    def get_output_factors(self, number):
        factors = self.numbers[number]['factors']
        labels = []
        for factor in factors.keys():
            if factors[factor] == 0:
                continue
            elif factors[factor] == 1:
                labels.append(str(factor))
            else:
                labels.append(str(factor) + '^' + str(factors[factor]))
        label = '_'.join(labels)
        return label

    def get_period_factors(self):
        self.setStatus('Computing divisors...')
        self.need_compute = True
        T = int(self.period.value())
        own_divisors, num_divisors = self.fillDivisors(T)
        label = self.get_factors(list(self.numbers.keys())[-1])
        self.factorsLabel.setText(label)
        self.label_num_divisors.setText(f'{own_divisors} / {num_divisors}')
        self.cycles = (4 if T < 8 else (3 if T < 17 else 2))
        self.timeWidget.valueChanged.disconnect(self.timeChanged)
        self.maxTime.setValue(T * self.cycles)
        self.maxTime.setSingleStep(T)
        self.timeWidget.valueChanged.connect(self.timeChanged)
        self.setStatus('Divisors computed. Select now a number from the list and press the Compute button')

    def _to_qt_list_color(self, color_name):
        return QtGui.QColor(*[int(255 * x) for x in _convert_color(self.config.get(color_name))])

    def fillDivisors(self, T: int) -> int:
        not_period = self._to_qt_list_color('list_color_not_period')
        not_period_prime = self._to_qt_list_color('list_color_not_period_prime')
        period_special = self._to_qt_list_color('list_color_period_special')
        period_not_special = self._to_qt_list_color('list_color_period_not_special')

        own_divisors = 0

        a = int(2 ** self.dim)
        b = int(T)
        c = int(2)
        self.numbers = getDivisorsAndFactors(a**b - 1, a)
        self.divisors.clear()
        is_even: bool = True if T % 2 == 0 else False
        specials = []
        if is_even:
            d = int(T // 2)
            specials = divisors(a**d + 1)
        else:
            specials = [c**b - 1]
        for record in self.numbers.values():
            x: int = record['number']
            factors: dict = record['factors']
            period: int = record['period']
            if period == T:
                own_divisors += 1
            item = QtWidgets.QListWidgetItem(f'{x} ({period}) = {self.get_factors(x)}')
            is_prime: bool = True if x in factors.keys() and factors[x] == 1 else False
            is_special: bool = False
            if period != T:
                if is_prime:
                    item.setForeground(not_period_prime)
                else:
                    item.setForeground(not_period)
            else:
                if x in specials:
                    item.setForeground(period_special)
                    is_special = True
                elif is_prime:
                    item.setForeground(period_not_special)
            item.setData(Qt.UserRole, is_special)
            self.divisors.addItem(item)

        return own_divisors, len(self.numbers)
                
    def setNumber(self, index):
        self.need_compute = True
        item = self.divisors.item(index.row())
        self.is_special = item.data(Qt.UserRole)
        self.number.setValue(int(item.text().split(' ', 1)[0]))

    def maxTimeChanged(self):
        self.changed_spacetime = True
        self.need_compute = True

    def update_view_objects(self):
        if self.view_objects:
            self.view_objects = False
        else:
            self.view_objects = True
        self.view_time = False
        self.actionViewObjects.setChecked(self.view_objects)
        self.actionViewTime.setChecked(self.view_time)
        self.draw_objects()

    def update_view_time(self):
        if self.view_time:
            self.view_time = False
        else:
            self.view_time = True
        self.view_objects = False
        self.actionViewObjects.setChecked(self.view_objects)
        self.actionViewTime.setChecked(self.view_time)
        self.draw_objects()

    def update_view_next_number(self):
        self.view_next_number = not self.view_next_number
        self.draw_objects()

    def saveSpecials(self):
        widget = SaveSpecialsWidget(self, self.period.value(), 61)
        widget.show()

    def saveSpecialNumbers(self, init_period, end_period, subfolder):
        self.accumulate.setChecked(True)
        for period in range(init_period, end_period + 1, 2):
            if 46 <= period <= 48 and self.dim == 3:
                continue
            self.period.setValue(period)
            self.changed_spacetime = True
            for row in range(len(self.divisors)):
                self.need_compute = True
                item = self.divisors.item(row)
                is_special = item.data(Qt.UserRole)
                if not is_special:
                    continue
                number = int(item.text().split(' ', 1)[0])
                if number > 1650000:
                    continue
                print(f'------ saving number {number}')
                self.is_special = is_special
                self.number.setValue(number)
                self.update()
                self.compute()
                self.saveImage(subfolder=subfolder)
                print(f'------ number {number} saved')
        self.changed_spacetime = True

    def callSaveVideo(self):
        print(f'Video: ({self.config.get("image_resx")}, {self.config.get("image_resy")})')
        widget = SaveVideoWidget(
            self, self.timeWidget.value(), self.maxTime.value(), self.views.mode, 
            self.config.get('image_resx'), self.config.get('image_resy'), self.saveVideo
        )
        widget.show()

    def save(self):
        number = int(self.number.value())
        if number == 0:
            QtWidgets.QMessageBox.critical(self, 'Error', 'Please, compute a number first')
            return
        period = self.period.value()
        factors = self.get_output_factors(number)
        files_path = self.config.get('files_path')
        path  = os.path.join(files_path, self._getDimStr(), f'P{period:02d}')
        if not os.path.exists(path):
            os.makedirs(path)
        file_name = os.path.join(path, f'{self._getDimStr()}_N{number:d}_P{period:02d}_F{factors}.json')
        out_name, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, 'Save number json file', file_name, '*.json'
        )
        if out_name:
            self.setStatus(f'Saving file: {os.path.basename(out_name)}...')
            time1 = time()
            app.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.spacetime.save(out_name)
            self.files_path = os.path.dirname(out_name)
            app.restoreOverrideCursor()
            time2 = time()
            self.setStatus(f'File {os.path.basename(out_name)} saved in {time2 - time1:0.2f} segs')

    def load(self):
        in_file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, 'Open number json file', self.files_path, '*.json'
        )
        if in_file_name:
            time1 = time()
            self.setStatus(f'Loading file {os.path.basename(in_file_name)}...')
            app.setOverrideCursor(QtCore.Qt.WaitCursor)
            self.files_path = os.path.dirname(in_file_name)
            self.spacetime.load(in_file_name)
            T, n, max, dim, is_special = self.spacetime.getParams()
            self.dim = dim
            spacetime = self.spacetime
            self._clear_parameters()
            self.spacetime = spacetime
            self.period.setValue(T)
            self.spacetime = spacetime
            self.number.setValue(n)
            self.is_special = is_special
            self.maxTime.setValue(max)
            self.first_number_set = False
            self.changed_spacetime = False
            self.need_compute = False
            self.time.setValue(max)
            self.views.setFocus()
            app.restoreOverrideCursor()
            time2 = time()
            self.setStatus(f'File {os.path.basename(in_file_name)} loaded in {time2 - time1:0.2f} segs')

    def applyTransform(self):
        transformWidget = TransformWidget(self.spacetime, self.dim, self)
        transformWidget.show()


if __name__=="__main__":
    freeze_support()
    QtWidgets.QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, False)
    app = QtWidgets.QApplication(sys.argv)
    settings.load(settings_file)
    mw = MainWindow()
    mw.show()
    sys.exit(app.exec())

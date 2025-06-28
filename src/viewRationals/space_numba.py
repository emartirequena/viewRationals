from numba import int32, float64
from numba.experimental import jitclass
from numba import types
from numba.typed import List
from numba.types import ListType
import numpy as np

from cell_numba import Cell
from rationals_numba import c

# Obtenemos el tipo de Cell FUERA del código compilado
cell_type = Cell.class_type.instance_type

# Especificación para la clase Space
space_spec = [
    ('t', float64),
    ('T', int32), 
    ('n', int32),
    ('dim', int32),
    ('base', int32),
    ('indexes', int32[:]),  # Array NumPy en lugar de lista Python
    ('cells', ListType(cell_type)),  # Lista tipada de Cells
    ('num_cells', int32),  # Contador de celdas para optimización
]

@jitclass(space_spec)
class Space:
    def __init__(self, t, dim, T, n):
        self.t = t
        self.T = T
        self.n = n
        self.dim = dim
        self.base = 2**dim
        
        # Calcular el número de elementos necesarios
        num = int((t + 1))**self.dim
        self.indexes = np.full(num, -1, dtype=np.int32)  # Inicializar con -1
        self.cells = List.empty_list(cell_type)
        self.num_cells = 0

    def getCell(self, x, y, z):
        nx = c * self.t - x
        ny = (c * self.t - y) if self.dim > 1 else 0.0
        nz = (c * self.t - z) if self.dim > 2 else 0.0
        n = int(nx + (self.t + 1) * (ny + (self.t + 1) * nz))
        
        if n < 0 or n >= len(self.indexes):
            return None
            
        if self.indexes[n] < 0:
            self.indexes[n] = self.num_cells
            new_cell = Cell(self.dim, self.T, self.n, x, y, z)
            self.cells.append(new_cell)
            self.num_cells += 1
            
        return self.cells[self.indexes[n]]
    
    def getRationals(self, x, y, z):
        cell = self.getCell(x, y, z)
        if cell is not None:
            return cell.get_rationals()
        return List.empty_list(int32)
    
    def countCells(self):
        return self.num_cells

    def getCells(self):
        """ Obtener una lista de celdas con sus datos."""
        return self.cells

    def countPaths(self):
        num_paths = 0
        for i in range(self.num_cells):
            num_paths += self.cells[i].get_count()
        return num_paths

    def add(self, count, time, m, next_digit, x, y, z):
        cell: Cell = self.getCell(x, y, z)
        if cell is not None:
            cell.add(count, time, m, next_digit)

    def clear(self):
        # Crear nuevas estructuras en lugar de usar del
        self.cells = List.empty_list(cell_type)
        self.indexes.fill(-1)  # Reiniciar todos los índices a -1
        self.num_cells = 0

    def getMaxTime(self):
        max_time = -1.0
        for i in range(self.num_cells):
            cell_time = self.cells[i].get_time()
            if cell_time > max_time:
                max_time = cell_time
        return max_time
    
    def get_cell_at_index(self, index):
        # Método auxiliar para acceder a celdas por índice
        if 0 <= index < self.num_cells:
            return self.cells[index]
        return None

# Funciones auxiliares para operaciones con diccionarios (fuera de @jitclass)
def save_space(space):
    """Función externa para guardar el estado del espacio como lista de diccionarios"""
    out_cells = []
    for i in range(space.num_cells):
        cell = space.cells[i]
        cell_dict = {
            'pos': (cell.x, cell.y, cell.z)[:space.dim],
            'count': cell.get_count(),
            'time': cell.time,
            'next_digits': cell.get_next_digits(),
            'rationals': list(cell.get_rationals())
        }
        out_cells.append(cell_dict)
    return out_cells

def load_space(space, input_cells):
    """Función externa para cargar el estado del espacio desde lista de diccionarios"""
    space.clear()
    for in_cell in input_cells:
        pos = in_cell['pos']
        x = pos[0] if len(pos) > 0 else 0.0
        y = pos[1] if len(pos) > 1 else 0.0
        z = pos[2] if len(pos) > 2 else 0.0
        
        cell = space.getCell(x, y, z)
        if cell is not None:
            # Convertir next_digits de dict a array si es necesario
            next_digits_data = in_cell['next_digits']
            if isinstance(next_digits_data, dict):
                next_digits_array = np.zeros(len(next_digits_data), dtype=np.int32)
                for k, v in next_digits_data.items():
                    next_digits_array[int(k)] = v
            else:
                next_digits_array = np.array(next_digits_data, dtype=np.int32)
            
            rationals_array = np.array(in_cell['rationals'], dtype=np.int32)
            cell.set(in_cell['count'], in_cell['time'], next_digits_array, rationals_array)


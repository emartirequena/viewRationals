from numba import int32, float64
from numba.experimental import jitclass
from numba.typed import List
import numpy as np

from hashrationals_numba import HashRationals, hash_rationals_item_type

# obtiene el diccionario de la celda
def get_cell_dict(cell):
    # Convertimos el array de next_digits a un diccionario
    return {
        "pos": cell.get_pos()[:cell.dim],
        "count": cell.get_count(),
        "time": cell.get_time(),
        "next_digits": {i: cell.next_digits[i] for i in range(len(cell.next_digits))},
        "rationals": list(cell.get_rationals())
    }

# Obtenemos el tipo de HashRationals FUERA del código compilado
hash_rationals_type = HashRationals.class_type.instance_type

# Especificación para la clase Cell
cell_spec = [
    ('dim', int32),
    ('T', int32),
    ('n', int32),
    ('x', float64),
    ('y', float64),
    ('z', float64),
    ('count', int32),
    ('time', float64),
    ('next_digits', int32[:]),  # Array para reemplazar el diccionario
    ('rationals', hash_rationals_type),  # Usar el tipo pre-definido
]

@jitclass(cell_spec)
class Cell:
    def __init__(self, dim, T, n, x, y=0.0, z=0.0):
        self.dim = dim
        self.T = T
        self.n = n
        self.x = x
        self.y = y
        self.z = z
        self.count = 0
        self.time = 0.0
        self.next_digits = np.zeros(2**self.dim, dtype=np.int32)  # Reemplaza el dict
        self.rationals = HashRationals(self.n, 100000)  # Instancia de HashRationals

    def add(self, count, time, m, next_digit):
        self.count += count
        self.time += time
        self.next_digits[next_digit] += count
        self.rationals.add(m, time)  # Usa el método de HashRationals (3 parámetros)

    def clear(self):
        self.count = 0
        self.time = 0.0
        self.next_digits.fill(0)  # Reinicia el array
        self.rationals = HashRationals(self.n, 100000)  # Reinicia la instancia de HashRationals

    def get_pos(self):
        return (self.x, self.y, self.z)
    
    def get_count(self):
        return self.count
    
    def get_time(self):
        return self.time
    
    def get_next_digits(self):
        return self.next_digits.copy()
    
    def get_rationals(self):
        return self.rationals.get_rationals()

    def set(self, count, time, next_digits_array):
        self.count = count
        self.time = time
        # Copiar solo los elementos válidos del array
        min_len = min(len(self.next_digits), len(next_digits_array))
        for i in range(min_len):
            self.next_digits[i] = next_digits_array[i]

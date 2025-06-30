from numba.typed import List
from numba import int32
from numba.experimental import jitclass
from numba.types import ListType
import numpy as np

hash_size = 1000  # Tamaño por defecto para HashRationalsItem

# Especificación para HashRationalsItem
hash_rationals_item_spec = [
    ('min', int32),
    ('max', int32),
    ('rationals', int32[:, :]),  # Matriz para almacenar los datos de los racionales
    ('indexes', int32[:]),      # Array para índices
    ('count', int32),           # Contador de elementos en rationals
]

@jitclass(hash_rationals_item_spec)
class HashRationalsItem:
    def __init__(self, min, max):
        self.min = min
        self.max = max
        self.rationals = np.zeros((hash_size, 3), dtype=np.int32)  # [m, count, time]
        self.indexes = np.full(hash_size, -1, dtype=np.int32)      # Inicializa índices con -1
        self.count = 0
        
    def add(self, m, time):
        if not (self.min <= m <= self.max):
            return False

        # Busca si el valor ya está en los índices
        for i in range(self.count):
            if self.rationals[i, 0] == m:
                self.rationals[i, 1] += 1  # Incrementa el contador
                return True

        # Si no está, añade un nuevo racional
        if self.count < len(self.rationals):
            self.rationals[self.count, 0] = m
            self.rationals[self.count, 1] = 1
            self.rationals[self.count, 2] = time
            self.count += 1
            return True

        return False


# Obtenemos el tipo ANTES de usarlo en cualquier código compilado
hash_rationals_item_type = HashRationalsItem.class_type.instance_type

# Especificación para HashRationals
hash_rationals_spec = [
    ('hash_list', ListType(hash_rationals_item_type)),
    ('num', int32),
    ('size', int32),
]

@jitclass(hash_rationals_spec)
class HashRationals:
    def __init__(self, num, size=hash_size):
        self.num = num
        self.size = size
        # Crear lista vacía con el tipo correcto (sin usar class_type aquí)
        self.hash_list = List.empty_list(hash_rationals_item_type)

        # calcula el valor de tamaño si no se proporciona
        s = hash_size // num + 1
        
        # Llenar la lista directamente
        old_max = 0
        for i in range(0, s):
            max_val = (i + 1) * num - 1
            self.hash_list.append(HashRationalsItem(old_max, max_val))
            old_max = max_val + 1

    def add(self, m, time):
        for item in self.hash_list:
            if item.add(m, time):
                return True
        return False

    def get_rationals(self):
        rationals = List.empty_list(int32)  # Usar List tipada para compatibilidad con Numba
        for item in self.hash_list:
            for i in range(item.count):
                rationals.append(item.rationals[i, 0])
        rationals.sort()  # Ordenar directamente la lista tipada
        return rationals

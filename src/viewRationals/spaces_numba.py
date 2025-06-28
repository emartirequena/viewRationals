from numba import int32, float64, boolean
from numba.experimental import jitclass
from numba import types
from numba.typed import List
from numba.types import ListType
import numpy as np

from space_numba import Space, save_space, load_space, cell_type
from rationals_numba import c

# Obtenemos el tipo de Space FUERA del código compilado
space_type = Space.class_type.instance_type

# Especificación para la clase Spaces
spaces_spec = [
    ('T', int32),
    ('n', int32),
    ('max', int32),
    ('dim', int32),
    ('spaces', ListType(space_type)),  # Lista tipada de Spaces
    ('accumulates_even', space_type),  # Space para acumulados pares
    ('accumulates_odd', space_type),   # Space para acumulados impares
]

@jitclass(spaces_spec)
class Spaces:
    def __init__(self, T, n, max_val, dim=1):
        self.T = T
        self.n = n
        self.max = max_val
        self.dim = dim
        
        # Crear lista de espacios
        self.spaces = List.empty_list(space_type)
        for t in range(max_val + 1):
            self.spaces.append(Space(t, dim, T, n))
        
        # Crear espacios acumulados
        even_t = max_val if T % 2 == 0 else max_val - 1
        odd_t = max_val if T % 2 == 1 else max_val - 1
        self.accumulates_even = Space(even_t, dim, T, n)
        self.accumulates_odd = Space(odd_t, dim, T, n)

    def add(self, count, is_special, t, m, next_digit, time, cycle, x, y, z):
        """ Agrega un nuevo número racional a los espacios correspondientes.
        Args:
            count: Cantidad de veces que se repite el número (para optimización).
            is_special: Indica si el número es especial.
            t: Tiempo del ciclo actual.
            m: Numerador del número racional.
            next_digit: Índice del siguiente dígito.
            time: Tiempo asociado al número.
            cycle: Ciclo actual (para determinar acumulación).
            x, y, z: Coordenadas del número en el espacio.
        """
        if t < 0 or t > self.max:
            return
        
        self.spaces[t].add(count, time, m, next_digit, x, y, z)
        
        # para los numeros especiales anadimos 
        # solo el ultimo ciclo en los espacios acumulados
        if t < self.max - cycle and is_special:
            return
            
        # No se acumulan en las celdas extremas los numeros especiales
        skip_accumulate = False
        if self.dim == 1:
            if (x == t * c or x == -t * c) and is_special:
                skip_accumulate = True
        elif self.dim == 2:
            if (x == y == t * c or x == y == z == -t * c) and is_special:
                skip_accumulate = True
        else:  # dim == 3
            if (x == y == z == t * c or x == y == z == -t * c) and is_special:
                skip_accumulate = True
                
        if skip_accumulate:
            return
            
        # Agregar a acumulados
        if t % 2 == 0:
            self.accumulates_even.add(count, time, m, next_digit, x, y, z)
        else:
            self.accumulates_odd.add(count, time, m, next_digit, x, y, z)

    def getMaxTime(self, accumulate):
        max_time = -1.0
        if not accumulate:
            for i in range(len(self.spaces)):
                spc_time = self.spaces[i].getMaxTime()
                if spc_time > max_time:
                    max_time = spc_time
            return max_time
        else:
            max_time = self.accumulates_even.getMaxTime()
            odd_max_time = self.accumulates_odd.getMaxTime()
            if odd_max_time > max_time:
                max_time = odd_max_time
        return max_time

    def clear(self):
        for i in range(len(self.spaces)):
            self.spaces[i].clear()
        self.accumulates_even.clear()
        self.accumulates_odd.clear()

    def reset(self, T, n, max_val, dim):
        """Reset the Spaces instance with new parameters."""
        self.T = T
        self.n = n
        self.max = max_val
        self.dim = dim
        
        # Reset spaces
        self.spaces = List.empty_list(space_type)
        for t in range(max_val + 1):
            self.spaces.append(Space(t, dim, T, n))
        
        # Reset accumulates
        even_t = max_val if T % 2 == 0 else max_val - 1
        odd_t = max_val if T % 2 == 1 else max_val - 1
        self.accumulates_even = Space(even_t, dim, T, n)
        self.accumulates_odd = Space(odd_t, dim, T, n)

    def getCell(self, t, x, y=0.0, z=0.0, accumulate=False):
        if not accumulate:
            return self.spaces[t].getCell(x, y, z)
        else:
            if t % 2 == 0:
                return self.accumulates_even.getCell(x, y, z)
            else:
                return self.accumulates_odd.getCell(x, y, z)
            
    def getRationals(self, t, x, y=0.0, z=0.0, accumulate=False):
        cell = self.getCell(t, x, y, z, accumulate=accumulate)
        if cell is not None:
            return cell.get_rationals()
        return List.empty_list(int32)
            
    def getCells(self, t, accumulate=False):
        if not accumulate:
            return self.spaces[t].getCells()
        else:
            if t % 2 == 0:
                return self.accumulates_even.getCells()
            else:
                return self.accumulates_odd.getCells()
            
    def getCellsWithRationals(self, rationals_array, t, accumulate=False):
        cells = self.getCells(t, accumulate=accumulate)
        selected = List.empty_list(cell_type)

        for i in range(len(cells)):
            cell = cells[i]
            cell_rationals = cell.get_rationals()
            
            # Verificar intersección manualmente (sin usar sets)
            has_intersection = False
            for j in range(len(cell_rationals)):
                for k in range(len(rationals_array)):
                    if cell_rationals[j] == rationals_array[k]:
                        has_intersection = True
                        break
                if has_intersection:
                    break
                    
            if has_intersection:
                selected.append(cell)
                
        return selected

    def getSpace(self, t, accumulate=False):
        if not accumulate:
            return self.spaces[t]
        else:
            if t % 2 == 0:
                return self.accumulates_even
            else:
                return self.accumulates_odd

    def countPaths(self, t, accumulate=False):
        if not accumulate:
            return self.spaces[t].countPaths()
        else:
            if t % 2 == 1:  # Corregido: era t%2 sin comparación
                return self.accumulates_odd.countPaths()
            else:
                return self.accumulates_even.countPaths()

# Funciones auxiliares para operaciones con diccionarios (fuera de @jitclass)
def save_spaces(spaces: Spaces):
    """Función externa para guardar el estado de todos los espacios como diccionario"""
    output = {}
    
    # Guardar espacios regulares
    for t in range(spaces.max + 1):
        space = spaces.getSpace(t, accumulate=False)
        out_cells = save_space(space)
        output[str(t)] = out_cells
    
    # Guardar espacios acumulados
    output['accumulates_even'] = save_space(spaces.accumulates_even)
    output['accumulates_odd'] = save_space(spaces.accumulates_odd)
    
    return output

def load_spaces(spaces: Spaces, input_data: dict):
    """Función externa para cargar el estado de todos los espacios desde diccionario"""
    # Cargar espacios regulares
    for t in range(spaces.max + 1):
        space = spaces.getSpace(t)
        if str(t) in input_data:
            load_space(space, input_data[str(t)])
    
    # Cargar espacios acumulados
    if 'accumulates_even' in input_data:
        load_space(spaces.accumulates_even, input_data['accumulates_even'])
    if 'accumulates_odd' in input_data:
        load_space(spaces.accumulates_odd, input_data['accumulates_odd'])

from numba import njit, types
from numba.typed import List, Dict
import numpy as np
import math
from madcad import icosphere, icosahedron, brick, vec3, cylinder, cone, Box, Axis, X, Y, Z
from cell_numba import Cell
from rationals_numba import c   
from utils import get_alpha
from color import _convert_color


@njit
def _get_next_number_dir(dim, cell: Cell):
    next_digits = cell.get_next_digits()
    if dim == 1:
        v1 = np.array([ 1,  0,  0]) * next_digits[0]
        v2 = np.array([-1,  0,  0]) * next_digits[1]
        v = (v1 + v2) / 2.0
    elif dim == 2:
        v1 = np.array([ 1,  0,  1]) * next_digits[0]
        v2 = np.array([-1,  0,  1]) * next_digits[1]
        v3 = np.array([ 1,  0, -1]) * next_digits[2]
        v4 = np.array([-1,  0, -1]) * next_digits[3]
        v = (v1 + v2 + v3 + v4) / 4.0
    else:
        v1 = np.array([ 1,  1,  1]) * next_digits[0]
        v2 = np.array([-1,  1,  1]) * next_digits[1]
        v3 = np.array([ 1,  1, -1]) * next_digits[2]
        v4 = np.array([-1,  1, -1]) * next_digits[3]
        v5 = np.array([ 1, -1,  1]) * next_digits[4]
        v6 = np.array([-1, -1,  1]) * next_digits[5]
        v7 = np.array([ 1, -1, -1]) * next_digits[6]
        v8 = np.array([-1, -1, -1]) * next_digits[7]
        v = (v1 + v2 + v3 + v4 + v5 + v6 + v7 + v8) / 8.0
    return v * cell.count

@njit
def _num_intersect_rationals(rationals, cell_rationals):
    """
    Count the number of rationals that intersect with the cell's rationals.

    Parameters:
    - rationals: The list of rational numbers to check.
    - cell_rationals: The list of rational numbers in the cell.

    Returns:
    - The count of intersecting rationals.
    """
    if not rationals:
        return 0
    if not cell_rationals:
        return 0
    count = 0
    for i in range(len(rationals)):
        has_intersection = False
        for j in range(len(cell_rationals)):
            if rationals[i] == cell_rationals[j]:
                has_intersection = True
                count += 1
                break
        if has_intersection:
            continue
    return count

def get_objects(view_cells, number, dim, accumulate, rationals, config, ccolor, 
                view_objects, view_time, view_next_number, max_time, ptime, max_spaces_time):
    """
    Get objects for the spacetime visualization.

    Parameters:
    - view_cells: The cells to visualize.
    - number: The number of objects to create.
    - dim: The dimension of the spacetime.
    - accumulate: Whether to accumulate the objects.
    - rationals: The list of rational numbers to check.
    - config: The configuration object.
    - ccolor: The color configuration object.
    - view_objects: Whether to view objects.
    - view_time: Whether to view time.
    - view_next_number: Whether to view the next number.
    - max_time: The maximum time value.
    - ptime: The current time value.
    Returns:
    - A dictionary of objects, the count of cells, and a dictionary of cell IDs.
    """
    objs = {}
    cell_ids = {}
    if not view_cells:
        return objs, 0, cell_ids
    if number == 0:
        return objs, 0, cell_ids

    count = len(view_cells)
    if count == 0:
        return objs, 0, cell_ids

    normalize_alpha = config.get('normalize_alpha')
    alpha_pow = config.get('alpha_pow')

    if not accumulate:
        rad_factor = config.get('rad_factor')
        rad_pow = config.get('rad_pow')
    else:
        rad_factor = config.get('rad_factor_accum')
        rad_pow = config.get('rad_pow_accum')
    rad_min = config.get('rad_min')

    max_faces = config.get('max_faces')
    faces_pow = config.get('faces_pow')

    total = 0
    max = -1
    count = 0
    for i in range(len(view_cells)):
        cell: Cell = view_cells[i]
        cell_count = cell.count
        if cell_count > 0:
            if len(rationals) > 0:
                cell_count = _num_intersect_rationals(rationals, cell.get_rationals())
            if cell_count > max:
                max = cell_count
            count += 1
            total += cell_count

    num_id = 0

    if view_objects:
        for cell in view_cells:
            cell_count = cell.count
            if len(rationals) > 0:
                cell_count = _num_intersect_rationals(rationals, cell.get_rationals())
            alpha, rad = get_alpha(cell_count, number, max, normalize_alpha, alpha_pow, rad_factor, rad_pow, rad_min)
            color = ccolor.getColor(alpha)

            pos = (cell.x, cell.y, cell.z)
            if dim == 3:
                obj = icosphere(vec3(pos[0], pos[1], pos[2]), rad, resolution=('div', int(max_faces * math.pow(rad, faces_pow))))
            elif dim == 2:
                base = vec3(pos[0], 0, pos[1])
                top = vec3(pos[0], alpha*10, pos[1])
                obj = cylinder(base, top, rad)
            else:
                height = 14 * float(cell_count) / float(total)
                obj = brick(vec3(pos[0] - c, 0, 0), vec3(pos[0] + c, 1, height))
            obj.option(color=color)
            objs[num_id] = obj
            if cell.count not in cell_ids:
                cell_ids[cell.count] = []
            cell_ids[cell.count].append(num_id)
            num_id += 1

    elif view_time:
        for cell in view_cells:
            if max_time == 0.0:
                continue
            alpha = float(cell.time) / float(max_spaces_time)
            rad = math.pow(alpha / rad_factor, rad_pow)
            if rad == 0:
                continue
            color = ccolor.getColor(alpha)

            pos = (cell.x, cell.y, cell.z)
            if dim == 3:
                f = 4 * rad
                obj = icosahedron(vec3(pos[0], pos[1], pos[2]), f)
            elif dim == 2:
                obj = brick(vec3(pos[0] - c, 0, pos[1] - c), vec3(pos[0] + c, alpha*10, pos[1] + c))
            else:
                height = 14 * alpha
                obj = brick(vec3(pos[0] - c, 0, 0), vec3(pos[0] + c, 1, height))
            obj.option(color=color)
            objs[num_id] = obj
            num = cell['count']
            if num not in cell_ids:
                cell_ids[num] = []
            cell_ids[num].append(num_id)
            num_id += 1

    if view_next_number: 
        length_factor = config.get('next_pos_length')
        rad_factor = config.get('next_pos_rad')
        min_dir = 1000000
        max_dir = -1000000
        for cell in view_cells:
            dir = _get_next_number_dir(dim, cell)
            ndir = np.linalg.norm(dir)
            if ndir < min_dir: min_dir = ndir
            if ndir > max_dir: max_dir = ndir

        for cell in view_cells:
            dir = _get_next_number_dir(dim, cell)
            mod_dir = np.linalg.norm(dir)
            if min_dir < max_dir:
                k = np.power((mod_dir*1.5 - min_dir) / (max_dir*15 - min_dir), 0.75)
                if k <= 1.0e-6:
                    k = 0.2
            else:
                k = 0.2
            if mod_dir < 1.0e-6:
                continue
            dir = dir * k / mod_dir
            mod_dir = k

            pos = (cell.x, cell.y, cell.z)
            base = vec3(pos[0], pos[1], pos[2])
            dir_len = 5.0 * length_factor
            if dim == 1:
                base = vec3(pos[0], 0.0, -1.0)
                dir_len = 3.0 * length_factor
            elif dim == 2:
                base = vec3(pos[0], 0, pos[1])

            color = vec3(0.6, 0.8, 1.0)
            color = vec3(*_convert_color(config.get('next_pos_color')))

            top = base + dir * dir_len * 0.6
            rad = mod_dir * 0.4 * 0.8 * rad_factor
            obj = cylinder(top, base, rad)
            obj.option(color=color)
            objs[num_id] = obj
            num_id += 1

            base = top
            top = base + dir * dir_len * 0.4
            rad = mod_dir * 0.4 * rad_factor
            obj = cone(top, base, rad) 
            obj.option(color=color)
            objs[num_id] = obj
            num_id += 1

    del view_cells

    dirs = [X, Y, Z]
    for dir in dirs:
        axis = Axis(vec3(0), dir)
        objs[num_id] = axis
        num_id += 1

    if ptime > 0 and dim > 1:
        if not accumulate:
            cube = Box(center=vec3(0), width=ptime)
        else:
            t = max_time
            cube = Box(center=vec3(0), width=t if ptime%2 == 0 else t+c)
        objs[num_id] = cube
        num_id += 1

    return objs, count, cell_ids

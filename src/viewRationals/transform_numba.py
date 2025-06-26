from numba import int32, uint8, boolean, njit
from numba.experimental import jitclass
from numba.typed import List
from numba.types import ListType
import numpy as np

from utils_numba import *

@njit
def num_ones(seq):
    """
    Gets the number of ones on each dimension of a sequence of digits.
    Args:
        seq: array of int representing sequence of digits
    Returns:
        tuple of (nx, ny, nz)
    """
    nx = 0
    ny = 0
    nz = 0
    for d in seq:
        nx += d % 2
        ny += (d // 2) % 2
        nz += (d // 4) % 2
    return nx, ny, nz

@njit
def get_digits(m, ndigits, dim):
    """
    Gets the digits of a number in a given base.
    Args:
        m: number to convert
        ndigits: number of digits in the output
        dim: dimension of the base (1, 2, or 3)
    Returns:
        array of digits in the given base
    """
    base = 2**dim
    number = base**ndigits
    if m == 0:
        digits = np.zeros(ndigits, dtype=np.uint8)
        return digits
    
    digits = np.zeros(ndigits, dtype=np.uint8)
    reminder = m
    digit = (reminder * base) // number
    for i in range(ndigits):
        digits[i] = digit
        reminder = (reminder * base) % number
        digit = (reminder * base) // number
    return digits

@njit
def digit_to_char_uint8(n):
    """
    Converts a digit to a uint8 character representation.
    Args:
        n: number to convert
    Returns:
        uint8 character representation of the number
    """
    return np.uint8(n)

@njit
def check_output_arrays_inline(dimtr, tr_array, dimout, out_array):
    """
    Check the output plugin parameters using uint8 arrays.
    Args:
        dimtr: number of transformed dimensions
        tr_array: uint8 array with the transform
        dimout: number of output dimensions
        out_array: uint8 array with the output
    Returns:
        bool: True if the parameters are valid, False otherwise
    """
    # Check dimension constraint
    if dimout >= dimtr:
        return False

    # Check length constraint  
    if len(out_array) != len(tr_array):
        return False
    
    if count_unique_values(out_array) != 2**dimout:
        return False  

    return True

@njit
def check_input_arrays_inline(dimin, input_array, dimtr, tr_array):
    """
    Check the input plugin parameters using uint8 arrays.
    Args:
        dimin: number of input dimensions
        input_array: uint8 array with the input  
        dimtr: number of transformed dimensions
        tr_array: uint8 array with the transform
    Returns:
        bool: True if the parameters are valid, False otherwise
    """
    # Check dimension constraint
    if dimin >= dimtr:
        return False

    # Check length constraint  
    if len(input_array) != len(tr_array):
        return False
    
    if count_unique_values(input_array) != 2**dimin:
        return False
    
    return True

@njit
def create_tr_array(n):
    """
    Create transformation array for given n.
    Args:
        n: number of digits
    Returns:
        uint8 array with character representations of digits 0 to n-1
    """
    result = create_uint8_array(n)
    for i in range(n):
        result[i] = np.uint8(i)
    return result

@njit
def get_output_plugin(i, dim, dimtr, tr_array, nx, ny, nz):
    """
    Get output plugin using uint8 arrays.
    Args:
        i: plugin index
        dim: dimension
        dimtr: transform dimension  
        tr_array: transformation array
        nx, ny, nz: number of ones in each dimension
    Returns:
        tuple (plugin_array, is_valid)
    """
    # Get digits of the sequence
    digits = get_digits(i, dimtr, dim)
    
    # Check if number of ones matches
    ones = num_ones(digits)
    if ones[0] == nx and ones[1] == ny and ones[2] == nz:
        if check_output_arrays_inline(dimtr, tr_array, dim, digits):
            return digits, True
    
    return create_uint8_array(0), False

@njit
def get_input_plugin(i, dim, strdigits_array, n):
    """
    Get input plugin using uint8 arrays.
    Args:
        i: plugin index
        dim: dimension
        strdigits_array: string digits as uint8 array
        n: number of digits
    Returns:
        tuple (plugin_array, is_valid)
    """
    # Get digits of the sequence
    digits = get_digits(i, len(strdigits_array), dim)
    
    # Convert digits to uint8 array
    sindigits = digits_to_uint8_array(digits)
    
    # Check if valid input plugin
    if check_input_arrays_inline(dim, sindigits, n, strdigits_array):
        return sindigits, True
    
    return create_uint8_array(0), False


@njit
def transform_input_arrays(path_array, input_array, tr_array, level=-1):
    """
    Get all the transformed paths for the input plugin using uint8 arrays.
    This is a Numba-compatible implementation of the stack-based transformation logic.
    Args:
        path_array: uint8 array representing the path
        input_array: uint8 array representing the input plugin
        tr_array: uint8 array representing the transform
        level: transformation level (-1 for full path length)
    Returns:
        List of uint8 arrays representing transformed paths
    """
    if level < 0:
        level = len(path_array)
    if len(path_array) == 0:
        return List.empty_list(uint8[:])

    # Initialize the output list
    outpaths = List.empty_list(uint8[:])

    # Initialize the stacks for iterative processing
    path_stack = List.empty_list(uint8[:])
    path_stack.append(path_array)
    
    level_stack = List.empty_list(int32)
    level_stack.append(level)

    transformation_stack = List.empty_list(uint8[:])
    transformation_stack.append(create_uint8_array(0))

    while len(path_stack) > 0:
        current_path = path_stack.pop()
        current_level = level_stack.pop()
        current_transformation = transformation_stack.pop()

        if current_level == 0:
            continue

        for i in range(len(current_path)):
            c = current_path[i]
            for j in range(len(input_array)):
                if c == input_array[j]:
                    # Found a match. Create new transformation.
                    new_transformation = np.empty(len(current_transformation) + 1, dtype=np.uint8)
                    if len(current_transformation) > 0:
                        new_transformation[:-1] = current_transformation
                    new_transformation[-1] = tr_array[j]

                    if current_level == 1:
                        outpaths.append(new_transformation)
                    else:
                        # Push new state to stacks
                        remaining_path = current_path[i + 1:]
                        path_stack.append(remaining_path)
                        level_stack.append(current_level - 1)
                        transformation_stack.append(new_transformation)
    
    return outpaths

@njit
def transform_output_array(path_array, tr_array, out_array):
    """
    Get the transformed path for the output plugin using uint8 arrays.
    Args:
        path_array: uint8 array with the path to transform.
        tr_array: uint8 array with the transformation characters.
        out_array: uint8 array with the output plugin characters.
    Returns:
        uint8 array with the transformed path.
    """
    if len(path_array) == 0:
        return create_uint8_array(0)

    output_array = np.empty(len(path_array), dtype=np.uint8)
    for i in range(len(path_array)):
        char_to_find = path_array[i]
        found = False
        for j in range(len(tr_array)):
            if char_to_find == tr_array[j]:
                output_array[i] = out_array[j]
                found = True
                break
        if not found:
            # This case should be handled by a check before calling this function.
            # Returning an empty array to signal an error.
            return create_uint8_array(0)
            
    return output_array


# Transform specification for jitclass
transform_spec = [
    ('n', int32),
    ('mx', int32),
    ('my', int32),
    ('mz', int32),
    ('dim', int32),
    ('dimtr', int32),
    ('tr_array', uint8[:]),
    ('dimin', int32),
    ('inplugins', ListType(uint8[:])),
    ('dimout', int32),
    ('outplugins', ListType(uint8[:])),
    ('idxinput', int32),
    ('idxoutput', int32),
    ('active', boolean),
]

@jitclass(transform_spec)
class Transform:
    """
    Numba-compatible Transform class using uint8 arrays.
    """

    def __init__(self):
        """
        Initialize the Transform class with default values.
        """
        self.n = 0
        self.mx = 0
        self.my = 0
        self.mz = 0
        self.dim = 0
        self.dimtr = 0
        self.tr_array = create_uint8_array(1)
        self.dimin = 0
        self.inplugins = List.empty_list(uint8[:])
        self.dimout = 0
        self.outplugins = List.empty_list(uint8[:])
        self.idxinput = -1
        self.idxoutput = -1
        self.active = False

    def set_velocity(self, dim, n, mx, my=0, mz=0):
        """
        Sets transformation velocity using uint8 arrays.
        Args:
            dim: dimension of the spacetime (1, 2, or 3)
            n: denominator of the transformation
            mx: number of ones in the x dimension
            my: number of ones in the y dimension
            mz: number of ones in the z dimension
        Returns:
            int: 0 if successful, -1 if failed outpùt plugins, -2 if failed input plugins
        """
        # Validate input parameters
        if dim < 1 or dim > 3:
            return False
        
        if mx > n or my > n or mz > n:
            return False
        
        # Set basic parameters
        self.dim = dim
        self.n = n
        self.mx = mx
        self.my = my
        self.mz = mz
        
        # Get the number of digits of the transformation on each dimension
        nx = self.mx
        ny = self.my
        nz = self.mz
        
        # Create transformation array
        self.tr_array = create_tr_array(n)
        self.dimtr = len(self.tr_array)
        base = 2**dim
        
        # Get output plugins
        self.outplugins = List.empty_list(uint8[:])
        for i in range(1, base**self.dimtr):
            plugin_array, is_valid = get_output_plugin(i, self.dim, self.dimtr, self.tr_array, nx, ny, nz)
            if is_valid:
                self.outplugins.append(plugin_array)
        
        if len(self.outplugins) == 0:
            return -1
        
        # Get input plugins
        self.inplugins = List.empty_list(uint8[:])
        for i in range(1, base**self.dimtr):
            plugin_array, is_valid = get_input_plugin(i, dim, self.tr_array, n)
            if is_valid:
                self.inplugins.append(plugin_array)
        
        if len(self.inplugins) == 0:
            return -2
        
        self.active = True
        return 0

    def get_dim(self):
        """Get the dimension of the Transform class."""
        return self.dim

    def get_num_inputs(self):
        """Get the number of input plugins."""
        return len(self.inplugins)
    
    def get_num_outputs(self):
        """Get the number of output plugins."""
        return len(self.outplugins)
    
    def get_input_plugin_idx(self):
        """Get the index of the input plugin."""
        return self.idxinput
    
    def get_output_plugin_idx(self):
        """Get the index of the output plugin."""
        return self.idxoutput
    
    def set_input_plugin(self, i):
        """
        Set the input plugin index.
        Args:
            i: index of the input plugin
        Returns:
            bool: True if successful, False otherwise
        """
        if i < 0 or i >= len(self.inplugins):
            return False
        self.idxinput = i
        return True

    def set_output_plugin(self, i):
        """
        Set the output plugin index.
        Args:
            i: index of the output plugin
        Returns:
            bool: True if successful, False otherwise
        """
        if i < 0 or i >= len(self.outplugins):
            return False
        self.idxoutput = i
        return True

    def clear_plugins(self):
        """Clear the input and output plugin indices."""
        self.idxinput = -1
        self.idxoutput = -1

    def transform_path(self, path_array):
        """
        Transform a path using the current plugins.
        Args:
            path_array: uint8 array representing the path
        Returns:
            List of uint8 arrays representing transformed paths
        """
        result_list = List.empty_list(uint8[:])
        
        # Check if plugins are set and transformation is active
        if self.idxinput == -1 or self.idxoutput == -1 or not self.active:
            result_list.append(copy_uint8_array(path_array))
            return result_list
        
        # Check if path is empty
        if len(path_array) == 0:
            return result_list
        
        # Transform the path using the selected plugins
        intermediate_paths = transform_input_arrays(
            path_array,
            self.inplugins[self.idxinput],
            self.tr_array,
            -1 # full level
        )

        final_paths = List.empty_list(uint8[:])
        for intermediate_path in intermediate_paths:
            final_path = transform_output_array(
                intermediate_path,
                self.tr_array,
                self.outplugins[self.idxoutput]
            )
            final_paths.append(final_path)
            
        return final_paths
    
    def set_active(self, value):
        """Set the active state of the Transform class."""
        self.active = value

    def get_input_plugin_array(self, i):
        """
        Get the input plugin array at index i.
        Args:
            i: index of the input plugin
        Returns:
            uint8 array if valid index, empty array otherwise
        """
        if i < 0 or i >= len(self.inplugins):
            return create_uint8_array(0)
        return copy_uint8_array(self.inplugins[i])

    def get_output_plugin_array(self, i):
        """
        Get the output plugin array at index i.
        Args:
            i: index of the output plugin
        Returns:
            uint8 array if valid index, empty array otherwise
        """
        if i < 0 or i >= len(self.outplugins):
            return create_uint8_array(0)
        return copy_uint8_array(self.outplugins[i])

# Helper functions for string/uint8 conversion (non-Numba for external use)
def create_transform():
    """Factory function to create a Transform instance."""
    return Transform()

def set_transform_velocity_from_params(transform, dim, n, mx, my=0, mz=0):
    """Helper function to set velocity from parameters."""
    result = transform.set_velocity(dim, n, mx, my, mz)
    if result == 0:
        return True
    elif result == -1:
        raise ValueError("No output plugins.")
    elif result == -2:
        raise ValueError("No input plugins.")
    else:
        raise ValueError("Unknown error setting transform velocity.")

def transform_string_path(transform: Transform, path_str):
    """
    Wrapper to transform a string path using the Transform class.
    Args:
        transform: An instance of the Transform class.
        path_str: The path string to transform.
    Returns:
        A list of transformed path strings.
    """
    from utils_numba import string_to_uint8_array, uint8_array_list_to_string_list
    path_array = string_to_uint8_array(path_str)
    transformed_arrays = transform.transform_path(path_array)
    return uint8_array_list_to_string_list(transformed_arrays)

def get_input_plugin_as_string(transform, i):
    """Gets an input plugin as a string."""
    from utils_numba import uint8_array_to_string
    arr = transform.get_input_plugin_array(i)
    return uint8_array_to_string(arr)

def get_output_plugin_as_string(transform, i):
    """Gets an output plugin as a string."""
    from utils_numba import uint8_array_to_string
    arr = transform.get_output_plugin_array(i)
    return uint8_array_to_string(arr)



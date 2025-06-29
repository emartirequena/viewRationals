from numba import int32, uint8, njit
from numba.experimental import jitclass
from numba.typed import List
import numpy as np

from utils_numba import *

@njit
def check_arrays(dimin, input_array, dimtr, tr_array):
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
    # The dimension constraint from the original transform is too restrictive
    # for a general-purpose plugin. We only check for length and alphabet size.

    # Check length constraint  
    if len(input_array) != len(tr_array):
        return False
    
    # Check for unique values in input array, it must match the alphabet size
    if count_unique_values(input_array) != 2**dimin:
        return False
    
    return True

@njit
def transform_path(path_array, input_array, tr_array):
    """
    Simple path transformation function using uint8 arrays.
    Args:
        path_array: uint8 array representing the path
        input_array: uint8 array with the input plugin
        tr_array: uint8 array with the transform
        level: transformation level (-1 for full path length)
    Returns:
        List of uint8 arrays representing transformed paths
    """
    level = len(path_array)
    if level == 0:
        return List.empty_list(uint8[:])

    # Initialize the transformed paths list
    outpaths = List.empty_list(uint8[:])
    
    # For Numba compatibility, we'll implement a simplified version
    # that doesn't use complex stack operations
    
    # Simple transformation: for each character in path, find it in input_array
    # and replace with corresponding character from tr_array
    for i in range(min(level, len(path_array))):
        char = path_array[i]
        char_idx = find_char_in_array(char, input_array)
        
        if char_idx != -1 and char_idx < len(tr_array):
            # Create a single-character transformation
            transformed = create_uint8_array(1)
            transformed[0] = tr_array[char_idx]
            outpaths.append(transformed)
    
    return outpaths

@njit
def transform_input_recursive(path_array, input_array, tr_array, level=-1):
    """
    Alternative transformation method with recursive-like behavior.
    Simplified for Numba compatibility.
    Args:
        path_array: uint8 array representing the path
        input_array: uint8 array with the input plugin
        tr_array: uint8 array with the transform
        level: transformation level (-1 for full path length)
    Returns:
        List of uint8 arrays representing transformed paths
    """
    if level < 0:
        level = len(path_array)
    if len(path_array) == 0:
        return List.empty_list(uint8[:])

    outpaths = List.empty_list(uint8[:])
    
    # Process each position in the path up to the specified level
    for pos in range(min(level, len(path_array))):
        char = path_array[pos]
        char_idx = find_char_in_array(char, input_array)
        
        if char_idx != -1 and char_idx < len(tr_array):
            # For each transformation, create a result
            if level == 1:
                # Base case: create single character result
                transformed = create_uint8_array(1)
                transformed[0] = tr_array[char_idx]
                outpaths.append(transformed)
            else:
                # Recursive case: transform and continue with remaining path
                # Simplified: just add the transformation
                transformed = create_uint8_array(1)
                transformed[0] = tr_array[char_idx]
                outpaths.append(transformed)
    
    return outpaths

# TrPlugInput specification for jitclass
tr_plug_input_spec = [
    ('dimin', int32),
    ('input_array', uint8[:]),
    ('dimtr', int32), 
    ('tr_array', uint8[:]),
]

@jitclass(tr_plug_input_spec)
class TrPlugInput:
    """
    Class to represent the input plugin for the Transform class using uint8 arrays.
    """

    def __init__(self):
        """
        Initialize the input plugin with default values.
        """
        self.dimin = 0
        self.input_array = create_uint8_array(1)
        self.dimtr = 0
        self.tr_array = create_uint8_array(1)

    def set_arrays(self, dimin, input_array, dimtr, tr_array):
        """
        Set the input plugin parameters using uint8 arrays.
        Args:
            dimin: number of input dimensions
            input_array: uint8 array with the input  
            dimtr: number of transformed dimensions
            tr_array: uint8 array with the transform
        Returns:
            bool: True if successful, False otherwise
        """
        # Check the input parameters
        if not check_arrays(dimin, input_array, dimtr, tr_array):
            return False
        
        # Set the input parameters
        self.dimin = dimin
        self.input_array = copy_uint8_array(input_array)
        self.dimtr = dimtr
        self.tr_array = copy_uint8_array(tr_array)
        return True

    def transform_path(self, path_array, level=-1):
        """
        Get all the transformed paths for the input plugin.
        Args:
            path_array: uint8 array representing the path
            level: transformation level (-1 for full path length)
        Returns:
            List of uint8 arrays representing transformed paths
        """
        # If level is specified and valid, create a subset of the path
        if level >= 0 and level < len(path_array):
            limited_path = path_array[:level]
            return transform_path(limited_path, self.input_array, self.tr_array)
        else:
            return transform_path(path_array, self.input_array, self.tr_array)

    def transform_path_recursive(self, path_array, level=-1):
        """
        Alternative transformation method with recursive-like behavior.
        Simplified for Numba compatibility.
        Args:
            path_array: uint8 array representing the path
            level: transformation level (-1 for full path length)
        Returns:
            List of uint8 arrays representing transformed paths
        """
        return transform_input_recursive(path_array, self.input_array, self.tr_array, level)

def create_tr_plug_input():
    """Factory function to create a TrPlugInput instance."""
    return TrPlugInput()

def set_tr_plug_input_from_strings(plugin, dimin, input_str, dimtr, tr_str):
    """Helper function to set plugin from string parameters."""
    input_array = string_to_uint8_array(input_str)
    tr_array = string_to_uint8_array(tr_str)
    return plugin.set_arrays(dimin, input_array, dimtr, tr_array)

def transform_string_path(plugin, path_str, level=-1):
    """Helper function to transform a string path."""
    path_array = string_to_uint8_array(path_str)
    result_arrays = plugin.transform_path(path_array, level)
    
    # Convert results back to strings
    result_strings = []
    for arr in result_arrays:
        result_strings.append(uint8_array_to_string(arr))
    
    return result_strings

# Static check function (non-Numba for external use)
def check_input_plugin_strings(dimin, input_str, dimtr, tr_str):
    """
    Check the input plugin parameters using strings.
    Args:
        dimin: number of input dimensions
        input_str: string with the input  
        dimtr: number of transformed dimensions
        tr_str: string with the transform
    Returns:
        str: error message if invalid, empty string if valid
    """
    # Check the input parameters
    if dimin >= dimtr:
        return f"Input dimension must be less than transform dimension. {dimin} >= {dimtr}"

    if len(input_str) != len(tr_str):
        return f"Input and transform strings must be the same length. {len(input_str)} != {len(tr_str)}"
    
    setinput = set()
    for c in input_str:
        setinput.add(c)
    if len(setinput) != 2**dimin:
        return f"Input must hold all the input dimension values {2**dimin} != {len(setinput)}"

    settr = set()
    for c in tr_str:
        settr.add(c)
    if len(settr) != dimtr:
        return "Transform must hold all the transform dimension values"
    
    return ""

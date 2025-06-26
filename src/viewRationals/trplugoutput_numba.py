from numba import int32, uint8, njit
from numba.experimental import jitclass

from utils_numba import *

@njit
def check_output_arrays(dimtr, tr_array, dimout, out_array):
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
    
    # Check unique values in transform array
    tr_unique_count = count_unique_values(tr_array)
    if tr_unique_count != dimtr:
        return False

    # Check unique values in output array
    out_unique_count = count_unique_values(out_array)
    expected_output_count = 2**dimout
    if out_unique_count != expected_output_count:
        return False
    
    return True

@njit
def transform_output(path_array, tr_array, out_array):
    """
    Transform a path using uint8 arrays.
    Args:
        path_array: uint8 array representing the path to transform
        tr_array: uint8 array with the transform characters
        out_array: uint8 array with the output characters
    Returns:
        uint8 array representing the transformed path
    """
    if len(path_array) == 0:
        return create_uint8_array(0)
    
    # Create output array with same length as input path
    output = create_uint8_array(len(path_array))
    
    for i in range(len(path_array)):
        char = path_array[i]
        char_idx = find_char_in_array(char, tr_array)
        
        if char_idx == -1:
            # Character not found in transform array - return empty array to indicate error
            return create_uint8_array(0)
        
        output[i] = out_array[char_idx]
    
    return output

# TrPlugOutput specification for jitclass
tr_plug_output_spec = [
    ('dimtr', int32),
    ('tr_array', uint8[:]),
    ('dimout', int32), 
    ('out_array', uint8[:]),
]

@jitclass(tr_plug_output_spec)
class TrPlugOutput:
    """
    Class to represent the output plugin for the Transform class using uint8 arrays.
    """

    def __init__(self):
        """
        Initialize the output plugin with default values.
        """
        self.dimtr = 0
        self.tr_array = create_uint8_array(1)
        self.dimout = 0
        self.out_array = create_uint8_array(1)

    def set_arrays(self, dimtr, tr_array, dimout, out_array):
        """
        Set the output plugin parameters using uint8 arrays.
        Args:
            dimtr: number of transformed dimensions
            tr_array: uint8 array with the transform
            dimout: number of output dimensions
            out_array: uint8 array with the output
        Returns:
            bool: True if successful, False otherwise
        """
        # Check the input parameters
        if not check_output_arrays(dimtr, tr_array, dimout, out_array):
            return False

        # Set the output parameters
        self.dimtr = dimtr
        self.tr_array = copy_uint8_array(tr_array)
        self.dimout = dimout
        self.out_array = copy_uint8_array(out_array)
        return True

    def transform_path(self, path_array):
        """
        Transform a path using the output plugin.
        Args:
            path_array: uint8 array representing the path to transform
        Returns:
            uint8 array representing the transformed path (empty if error)
        """
        return transform_output(path_array, self.tr_array, self.out_array)

    def is_valid_char(self, char):
        """
        Check if a character is valid for transformation.
        Args:
            char: uint8 character to check
        Returns:
            bool: True if character is in transform array
        """
        return find_char_in_array(char, self.tr_array) != -1

def create_tr_plug_output():
    """Factory function to create a TrPlugOutput instance."""
    return TrPlugOutput()

def set_tr_plug_output_from_strings(plugin, dimtr, tr_str, dimout, out_str):
    """Helper function to set plugin from string parameters."""
    tr_array = string_to_uint8_array(tr_str)
    out_array = string_to_uint8_array(out_str)
    return plugin.set_arrays(dimtr, tr_array, dimout, out_array)

def transform_string_path_output(plugin, path_str):
    """Helper function to transform a string path."""
    path_array = string_to_uint8_array(path_str)
    result_array = plugin.transform_path(path_array)
    
    # Check if transformation was successful (non-empty result)
    if len(result_array) == 0 and len(path_array) > 0:
        return ""  # Error: empty result indicates transformation failed
    
    return uint8_array_to_string(result_array)

# Static check function (non-Numba for external use)
def check_output_plugin_strings(dimtr, tr_str, dimout, out_str):
    """
    Check the output plugin parameters using strings.
    Args:
        dimtr: number of transformed dimensions
        tr_str: string with the transform
        dimout: number of output dimensions
        out_str: string with the output
    Returns:
        str: error message if invalid, empty string if valid
    """
    # Check the input parameters
    if dimout >= dimtr:
        return f"Output dimension must be less than transform dimension. {dimout} >= {dimtr}"

    if len(out_str) != len(tr_str):
        return f"Output and transform strings must be the same length. {len(out_str)} != {len(tr_str)}"
    
    settr = set()
    for c in tr_str:
        settr.add(c)
    if len(settr) != dimtr:
        return f"Transform must hold all the transform dimension values {dimtr} != {len(settr)}"
    
    setout = set()
    for c in out_str:
        setout.add(c)
    if len(setout) != 2**dimout:
        return f"Output must hold all the output dimension values {2**dimout} != {len(setout)}"
    
    return ""

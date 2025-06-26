from numba import njit, boolean, uint8
import numpy as np


def string_to_uint8_array(s):
    """Convert string to uint8 array for Numba compatibility."""
    return np.array([ord(c)-48 for c in s], dtype=np.uint8)

def uint8_array_to_string(arr):
    """Convert uint8 array back to string."""
    result = ''
    larr = list(arr)
    for i in range(len(larr)):
        result += chr(larr[i]+48)
    return result

def uint8_array_list_to_string_list(arr_list):
    """Convert list of uint8 arrays to list of strings."""
    return [uint8_array_to_string(arr) for arr in arr_list]

@njit
def digits_to_uint8_array(digits_arr):
    """Convert digits array to uint8 array of ASCII characters."""
    result = np.zeros(len(digits_arr), dtype=np.uint8)
    for i in range(len(digits_arr)):
        result[i] = np.uint8(digits_arr[i])
        # result[i] = np.uint8(ord(str(digits_arr[i])))
    return result

@njit
def uint8_array_to_digits(uint8_arr):
    """Convert uint8 array of ASCII characters back to digits array."""
    result = np.zeros(len(uint8_arr), dtype=np.int32)
    for i in range(len(uint8_arr)):
        result[i] = int(chr(uint8_arr[i]))
    return result

@njit
def create_uint8_array(size):
    """Create an empty uint8 array of given size."""
    return np.zeros(size, dtype=np.uint8)

@njit
def copy_uint8_array(arr):
    """Create a copy of uint8 array."""
    return arr.copy()

@njit
def uint8_arrays_equal(arr1, arr2):
    """Check if two uint8 arrays are equal."""
    if len(arr1) != len(arr2):
        return False
    for i in range(len(arr1)):
        if arr1[i] != arr2[i]:
            return False
    return True

@njit
def count_unique_values(arr):
    """Count unique non-zero values in uint8 array."""
    unique_count = 0
    seen = np.zeros(256, dtype=uint8)  # Track seen values
    for i in range(len(arr)):
        if not seen[arr[i]]:
            seen[arr[i]] = 1
            unique_count += 1
    return unique_count

@njit
def find_char_in_array(char, arr):
    """Find the index of a character in uint8 array. Returns -1 if not found."""
    for i in range(len(arr)):
        if arr[i] == char:
            return i
    return -1

@njit
def append_uint8_arrays(arr1, arr2):
    """Concatenate two uint8 arrays."""
    result = create_uint8_array(len(arr1) + len(arr2))
    for i in range(len(arr1)):
        result[i] = arr1[i]
    for i in range(len(arr2)):
        result[len(arr1) + i] = arr2[i]
    return result

@njit
def slice_uint8_array(arr, start, end):
    """Create a slice of uint8 array from start to end."""
    if end > len(arr):
        end = len(arr)
    if start < 0:
        start = 0
    if start >= end:
        return create_uint8_array(0)
    
    result = create_uint8_array(end - start)
    for i in range(start, end):
        result[i - start] = arr[i]
    return result

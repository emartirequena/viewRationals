from numba import njit, int32, float64, int64, uint8, types
from numba.experimental import jitclass
import numpy as np

from utils_numba import *

c = 0.5

@njit
def _digits2rational(digits_uint8, base):
    """Convert uint8 array of digit characters to rational m/n."""
    m = 0
    l = len(digits_uint8)
    for i in range(l):
        d = int64(digits_uint8[l - i - 1])
        m += d * base**i
    n = base**l - 1
    return m, n

@njit
def _get_sequence_digits(m, n, dim):
    """Get sequence of digits as uint8 array."""
    base = int(2**dim)
    if m == 0:
        return np.array([0], dtype=np.uint8)
    elif m == n:
        return np.array([base - 1], dtype=np.uint8)
    
    digits = np.zeros(50, dtype=np.uint8)  # Maximum initial size
    count = 0
    reminder = m
    digit = reminder * base // n
    while True:
        digits[count] = np.uint8(digit)
        count += 1
        reminder = (reminder * base) % n
        digit = reminder * base // n
        if reminder == 0 or reminder == m:
            break

    return digits[:count]  # Trim array to actual size

@njit
def _get_sequence_reminders(m, n, dim):
    """Get sequence of reminders as int32 array."""
    base = int(2**dim)
    if m == 0:
        return np.array([0], dtype=np.int32)
    elif m == n:
        return np.array([m], dtype=np.int32)
    
    reminders = np.zeros(50, dtype=np.int32)  # Maximum initial size
    count = 0
    reminder = m
    while True:
        reminders[count] = reminder
        count += 1
        reminder = (reminder * base) % n
        if reminder == 0 or reminder == m:
            break
    
    return reminders[:count]  # Trim array to actual size

@njit
def _get_period(m, n, dim):
    """Calculate the period of the rational sequence."""
    if n == 1:
        return 1
    base = 2**dim
    p = 1
    reminder = m
    while True:
        reminder = (reminder * base) % n
        if reminder == 0 or reminder == m:
            break
        p += 1
        if p > 100:  # Prevent infinite loops
            break
    return p

@njit
def _get_positions(period, digits, dim, positions):
    """Calculate positions for the rational sequence."""
    x = 0.0
    y = 0.0
    z = 0.0
    for i in range(period + 1):
        positions[i, 0] = x
        positions[i, 1] = y
        positions[i, 2] = z
        if i < period + 1:
            idx = i % period
            digit = int(digits[idx])  # Convert uint8 to int
            dx = (digit % 2)
            x += c - dx
            if dim > 1:
                dy = (digit // 2) % 2
                y += c - dy
            if dim > 2:
                dz = (digit // 4) % 2
                z += c - dz

@njit
def _path_uint8(digits, length=0):
    """Return path as uint8 array instead of string."""
    if length == 0:
        length = len(digits)
    
    result = np.zeros(length, dtype=np.uint8)
    l = len(digits)
    for i in range(length+1):
        result[i] = digits[i % l]
    return result

@njit
def _path_string(digits, length=0):
    """Return path as string (for compatibility)."""
    if length == 0:
        actual_length = len(digits)
    else:
        actual_length = length
    
    result = ''
    l = len(digits)
    for i in range(actual_length):
        digit_val = int(digits[i % l])
        result += str(digit_val)
    return result

@njit
def _reminders_list(reminders):
    """Return reminders list."""
    return reminders

@njit
def _reminder(reminders, t, period):
    """Get reminder at time t."""
    return reminders[t % period]

@njit
def _digit(digits, t, period):
    """Get digit at time t."""
    return digits[t % period]

@njit
def _time(digits, t):
    """Calculate time based on digit changes."""
    T = len(digits)
    time = 0
    for i in range(t):
        if digits[i % T] != digits[(i + 1) % T]:
            time += 1
    return time

@njit
def _position(positions, t, period):
    """Get position at time t."""
    px, py, pz = 0.0, 0.0, 0.0
    nt = t // period
    if nt > 0:
        for _ in range(nt):
            px += positions[period, 0]
            py += positions[period, 1]
            pz += positions[period, 2]
    rt = t % period
    if rt != 0:
        px += positions[rt, 0]
        py += positions[rt, 1]
        pz += positions[rt, 2]
    return px, py, pz

@njit
def _eq(reminders1, reminders2):
    """Check if two reminder sequences are equal."""
    l = len(reminders1)
    for i in range(l):
        eq = True
        for j in range(l):
            if reminders1[(i + j) % l] != reminders2[j]:
                eq = False
                break
        if eq:
            return True
    return False

@njit
def _neq(reminders1, reminders2):
    """Check if two reminder sequences are not equal."""
    return not _eq(reminders1, reminders2)

def _repr_rational(r):
    """String representation of rational."""
    return f'Rational(m={r.m}, n={r.n}, dim={r.dim})'


# Define the Rational class specification for jitclass
spec = [
    ('m', int32),
    ('n', int32),
    ('dim', int32),
    ('period', int32),
    ('digits', uint8[:]),           # Changed from int32 to uint8
    ('reminders', int32[:]),
    ('positions', float64[:, :])
]

@jitclass(spec)
class Rational:
    """Numba-compiled Rational class with uint8 arrays for digits."""
    
    def __init__(self, m=0, n=0, dim=1):
        self.m = m
        self.n = n
        self.dim = dim
        self.period = 0
        self.digits = np.zeros(1, dtype=np.uint8)     # Changed to uint8
        self.reminders = np.zeros(1, dtype=np.int32)
        self.positions = np.zeros((1, 3), dtype=np.float64)
        if self.n != 0:
            self.period = _get_period(self.m, self.n, self.dim)
            self.digits = _get_sequence_digits(self.m, self.n, self.dim)
            self.reminders = _get_sequence_reminders(self.m, self.n, self.dim)
            self.positions = np.zeros((self.period+1, 3), dtype=np.float64)
            _get_positions(self.period, self.digits, self.dim, self.positions)

    def set(self, m, n, dim=1):
        """Set new rational parameters."""
        self.__init__(m, n, dim)

    def from_digits(self, digits_uint8, dim):
        """Create rational from uint8 array of digits."""
        base = 2**dim
        m, n = _digits2rational(digits_uint8, base)
        self.__init__(m, n, dim)

    def position(self, t):
        """Get position at time t."""
        return _position(self.positions, t, self.period)

    def time(self, t):
        """Get time based on digit changes."""
        return _time(self.digits, t)

    def path(self, length=0):
        """Get path as string."""
        return _path_string(self.digits, length)
    
    def path_uint8(self, length=0):
        """Get path as uint8 array."""
        return _path_uint8(self.digits, length)
    
    def digit(self, t):
        """Get digit at time t."""
        # return self.digits[t % self.period]
        return _digit(self.digits, t, self.period)
    
    def reminder(self, t):
        """Get reminder at time t."""
        return _reminder(self.reminders, t, self.period)
    
    def __eq__(self, other):
        """Check equality with another rational."""
        return _eq(self.reminders, other.reminders)


# Factory and utility functions
def create_rational(m, n, dim=1):
    """Factory function to create a Rational instance."""
    return Rational(m, n, dim)

def create_rational_from_string(digits_str, dim=1):
    """Create rational from string digits."""
    digits_uint8 = string_to_uint8_array(digits_str)
    r = Rational()
    r.from_digits(digits_uint8, dim)
    return r

# Non-jitclass utility functions for compatibility
def rational_to_string(r):
    """Convert rational to string representation."""
    return _repr_rational(r)

def compare_rationals(r1, r2):
    """Compare two rationals for equality."""
    return _eq(r1.reminders, r2.reminders)

def get_rational_path_string(r, length=0):
    """Get rational path as string."""
    return _path_string(r.digits, length)

def get_rational_path_uint8(r, length=0):
    """Get rational path as uint8 array."""
    return _path_uint8(r.digits, length)

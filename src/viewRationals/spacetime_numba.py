from numba import int32, int64, boolean, njit, types
from numba.experimental import jitclass
from numba.typed import List, Dict
from numba.types import ListType
import numpy as np
from time import time
from gc import collect

from spaces_numba import Spaces
from space_numba import Space
from rationals_numba import Rational, _digits2rational
from transform_numba import Transform
from utils_numba import *


@njit
def create_rational(m, n, dim):
    """Create a rational number with given parameters."""
    return Rational(m, n, dim)

rational_type = Rational.class_type.instance_type

# SpaceTime specification for jitclass
spacetime_spec = [
    ('T', int32),
    ('max_val', int32),
    ('dim', int32),
    ('n', int32),
    ('is_special', boolean),
    ('spaces', Spaces.class_type.instance_type),
    ('rationalSet', ListType(rational_type)),
    ('changed', boolean),
    ('transform', Transform.class_type.instance_type),
]

@jitclass(spacetime_spec)
class SpaceTime:
    """
    Numba-compiled SpaceTime class for managing rational number transformations.
    """
    
    def __init__(self, T, n, max_val, dim):
        """
        Initialize SpaceTime instance.
        
        Args:
            T: Time parameter
            n: Denominator for rational numbers
            max_val: Maximum value for calculations
            dim: Dimension (1, 2, or 3)
        """
        self.T = T
        self.max_val = max_val
        self.dim = dim
        self.n = n
        self.is_special = False
        self.spaces = Spaces(T, n, max_val, dim)
        self.rationalSet = List.empty_list(rational_type)
        self.changed = False
        self.transform = Transform()

    def getParams(self):
        """Get the main parameters of the SpaceTime instance."""
        return self.T, self.n, self.max_val, self.dim, self.is_special

    def len(self):
        """Get the maximum value."""
        return self.max_val

    def clear(self):
        """Clear the SpaceTime data."""
        self.n = 0
        self.is_special = False
        self.spaces.clear()
        # self.transform.set_active(False)

    def reset(self, T, n, max_val, dim):
        """Reset the SpaceTime instance with new parameters."""
        self.T = T
        self.n = n
        self.max_val = max_val
        self.dim = dim
        self.spaces.reset(T, n, max_val, dim)
        self.rationalSet.clear()
        # self.transform.set_active(False)
        self.changed = False

    def getCell(self, t, x, y=0, z=0, accumulate=False):
        """Get a specific cell from spaces."""
        return self.spaces.getCell(t, x, y, z, accumulate)

    def getCells(self, t, accumulate=False):
        """Get all cells at time t."""
        return self.spaces.getCells(t, accumulate)
    
    def getCellsWithRationals(self, rationals, t, accumulate=False):
        """Get cells with specific rationals at time t."""
        return self.spaces.getCellsWithRationals(rationals, t, accumulate)
    
    def getMaxTime(self, accumulate=False):
        """Get the maximum time from spaces."""
        return self.spaces.getMaxTime(accumulate)
    
    def getSpace(self, t, accumulate=False):
        """Get the space at time t."""
        return self.spaces.getSpace(t, accumulate)
    
    def countPaths(self, t, accumulate=False):
        """Count paths at time t."""
        return self.spaces.countPaths(t, accumulate)
    
    def setRationalSet(self, n, is_special=False):
        """Create a set of rational numbers with denominators from 0 to n."""
        self.n = n
        self.is_special = is_special
        self.rationalSet.clear()
        for m in range(n + 1):
            r = create_rational(m, n, self.dim)
            self.rationalSet.append(r)

    def addRationalSet(self, t, x, y, z):
        """Add a set of rationals to the spaces."""
        T = int32(self.T)
        hash = Dict.empty(key_type=int64, value_type=int64)
        base = 2 ** self.dim
        num_paths = 0
        for r in self.rationalSet:
            paths = self.transform.transform_path(r.path_uint8(T))
            for path in paths:
                num_paths += 1
                m, num = _digits2rational(path, base)
                if self.transform.active == False:
                    m = int(m * self.n / num)
                if m in hash:
                    hash[m] += 1
                else:
                    hash[m] = 1

        print(f"Rational set size: {len(self.rationalSet)}, Hash size: {len(hash)}, Number of paths: {num_paths}")

        for m in hash:
            count = hash[m]
            if self.transform.active == False:
                rat = Rational(m, self.n, self.dim)
            else:
                rat = Rational(m, num, self.dim)
            digits = rat.path_uint8(T)
            for rt in range(self.max_val + 1):
                px, py, pz = rat.position(t+rt)
                px += x
                py += y
                pz += z
                next_digit = digits[(t+rt+1) % T]
                rtime = rat.time(t+rt)
                self.spaces.add(count, self.is_special, t+rt, m, next_digit, rtime, T, px, py, pz)

        self.changed = True

    def get_rational_count(self):
        """Get the number of rationals in the current set."""
        return len(self.rationalSet)

    def get_rational(self, index):
        """Get a specific rational from the set."""
        if 0 <= index < len(self.rationalSet):
            return self.rationalSet[index]
        # Return a default rational if index is out of bounds
        return create_rational(0, 1, self.dim)

    def set_active(self, value):
        """Set the changed flag."""
        self.changed = value

    def is_active(self):
        """Check if the SpaceTime instance has been changed."""
        return self.changed

# Factory function to create SpaceTimeJit instances
def create_spacetime(T, n, max_val, dim=1):
    """Factory function to create a SpaceTime instance."""
    return SpaceTime(T, n, max_val, dim)

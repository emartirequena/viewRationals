import scipy as sc
from sympy import nsimplify
from random import shuffle, seed
from time import time

from rationals import Rational


class Transform:
    def __init__(self, dim, n, nx, ny=0, nz=0):
        self.dim = dim
        self.n = n
        self.base = 2**self.dim
        self.set_velocity(n, nx, ny, nz)

    def _set_plug_input(self):
        ratio = self.n // self.base + 1

        self.plug_input = {}
        p = 0
        for i in range(self.base):
            self.plug_input[str(i)] = []
            for _ in range(ratio):
                if p == self.n:
                    break
                self.plug_input[str(i)].append(str(p))
                p += 1

        # self.m = m
        # self.n = n
        # self.dim = dim
        # self.base = 2**dim

        # self.plug_input = {}
        # i = 0
        # j = 0
        # bucket = self.m
        # ci = 0
        # cj = 0
        # for _ in range(self.base):
        #     self.plug_input[str(i)] = []
        #     while bucket > 0:
        #         self.plug_input[str(i)].append(str(j))
        #         j = (j + 1) % self.n
        #         bucket -= 1
        #         cj += 1
        #     i = (i + 1) % self.base
        #     ci += 1
        #     if self.base - ci <= 1:
        #         bucket = self.n - cj
        #     elif (self.n - cj) // self.m <= 1:
        #         bucket = 1
        #     else:
        #         bucket = self.m

    def set_velocity(self, n, nx, ny=0, nz=0):
        seed(time())
        self.n = n
        self._set_plug_input()

        ones_x = [1 for _ in range(nx)] + [0 for _ in range(n - nx)]
        shuffle(ones_x)
        
        ones_y = [1 for _ in range(ny)] + [0 for _ in range(n - ny)]
        shuffle(ones_y)
        
        ones_z = [1 for _ in range(nz)] + [0 for _ in range(n - nz)]
        shuffle(ones_z)

        while True:
            flag = False
            for offset in range(n):
                self.plug_output = {}
                out = set()
                for i in range(n):
                    pos = (i + offset) % n
                    k = ones_x[pos]
                    if dim > 1:
                        k += ones_y[i] * 2
                    if dim > 2:
                        k += ones_z[i] * 4
                    out.add(k)
                    self.plug_output[str(i)] = [str(k)]
                if len(out) == self.base:
                    flag = True
                    break
            if flag:
                break
            shuffle(ones_x)

    def print(self):
        print(f'{self.plug_input}\n{self.plug_output}')

    def transform(self, digits: str):
        seqs = self._input2mid(digits)
        output = []
        for seq in seqs:
            d = ''
            for i in seq:
                d += self.plug_output[i][0]
            output.append(d)
        return output

    def _input2mid(self, digits: str):
        outputs = []

        if not digits:
            return outputs

        i = digits[0]
        for d in self.plug_input[i]:
            if len(digits) == 1:
                outputs.append(d)
            else:
                seqs = self._input2mid(digits[1:])
                if not seqs:
                    outputs.append(d)
                else:
                    for seq in seqs:
                        outputs.append(d + seq)
        return outputs

def sum(digits):
    total = 0
    for d in digits:
        total += int(d)
    return total


def position(digits, dim):
    c = 0.5
    x = 0.0
    y = 0.0
    z = 0.0
    for d in digits:
        nd = int(d)
        x += c - nd % 2
        if dim > 1:
            y += c - (nd // 2) % 2
        if dim > 2:
            z += c - (nd // 4) % 2
    l = len(digits)
    nx = int(c * l - x)
    ny = int(c * l - y) if dim > 1 else 0
    nz = int(c * l - z) if dim > 2 else 0
    pos = int(nx + (l+1) * (ny + (l+1) * nz))
    return pos


if __name__ == '__main__':
    dim = 2
    base = 2**dim
    n = 7
    nx = 2
    ny = 4

    transform = Transform(dim, n, nx, ny)
    # transform.plug_output = {'0': ['0'], '1': ['0'], '2': ['0'], '3': ['1'], '4': ['2'], '5': ['2'], '6': ['3'], '7': ['3'], '8': ['3'], '9': ['3']}
    transform.print()

    nd = 8
    max = base**nd
    inputs = []
    for n in range(max):
        s = ''
        for _ in range(nd):
            s += str(n % base)
            n //= base
        inputs.append(s)

    outputs = {}
    for input in inputs:
        seqs = transform.transform(input)
        for seq in seqs:
            if seq not in outputs:
                outputs[seq] = 0
            outputs[seq] += 1

    total = 0
    space = {}
    for digits, num in outputs.items():
        pos = position(digits, dim)
        if pos not in space:
            space[pos] = 0
        space[pos] += num
        total += num

    l = 0
    for _ in range(nd+1):
        for x in range(nd+1):
            num = space.get(l, 0)
            weight = num / total
            s = f'{weight:0.6f}'.replace('.', ',')
            print(f'{s}', end='; ' if x < nd else '')
            l += 1
        print('', end='\n')


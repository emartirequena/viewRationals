c = 0.5

def _digits2rational(digits: str, base):
    m = 0
    l = len(digits)
    for i in range(l):
        d = int(digits[l-i-1])
        m += d * base**i
    n = base**l - 1
    return m, n

class Rational():
    def __init__(self, m: int=0, n: int=0, dim=1):
        self.m = m
        self.n = n
        self.dim = dim
        self.period = 0

        self.digits: list = []
        self.reminders: list = []
        if self.n != 0:
            self.period =self.getPeriod()
            self.digits, self.reminders = self.getSequence()
            self.positions = [self.getPosition(t) for t in range(self.period + 1)]

    def __del__(self):
        del self.positions

    def set(self, m, n, dim=1):
        self.__init__(m, n, dim)

    def from_digits(self, digits: str, dim: int):
        m, n = _digits2rational(digits, 2**dim)
        self.__init__(m, n, dim)

    def cleanup(self):
        del self.positions

    def getSequence(self):
        base = int(2**self.dim)
        if self.m == 0:
            reminders = [0]
            digits = [0]
            return (digits, reminders)
        elif self.m == self.n:
            reminders = [self.m]
            digits = [base - 1]
            return (digits, reminders)
        digits = []
        reminders = []
        reminder = self.m
        digit = reminder * base // self.n
        while True:
            digits.append(digit)
            reminders.append(reminder)
            reminder = (reminder * base) % self.n
            digit = reminder * base // self.n
            if reminder == 0 or reminder == self.m:
                break
        return (digits, reminders)

    def getPeriod(self):
        if self.n == 1:
            return 1
        base = 2**self.dim
        p = 1
        reminder = self.m
        while True:
            reminder = (reminder * base) % self.n
            if reminder == 0 or reminder == self.m:
                break
            p = p + 1
        return p

    def getPosition(self, t):
        period = len(self.digits)
        x = 0.0
        y = 0.0
        z = 0.0
        for i in range(t):
            digit = self.digits[i % period]
            dx = (digit % 2)
            x += c - dx
            if self.dim > 1:
                dy = (digit // 2) % 2
                y += c - dy
            if self.dim > 2:
                dz = (digit // 4) % 2
                z += c - dz
        return (x, y, z)

    def path(self, length=0):
        if length == 0:
            return ''.join([str(d) for d in self.digits])
        out = ''
        l = len(self.digits)
        for i in range(length):
            out += str(self.digits[i % l])
        return out

    def reminders_list(self):
        return self.reminders
    
    def reminder(self, t):
        T = len(self.digits)
        return self.reminders[t % T]

    def position(self, t):
        px = 0.0
        py = 0.0
        pz = 0.0
        nt = t // self.period
        for _ in range(nt):
            x, y, z = self.positions[self.period]
            px += x
            py += y
            pz += z
        if t % self.period != 0:
            x, y, z = self.positions[t % self.period]
            px += x
            py += y
            pz += z
        return px, py, pz

    def digit(self, t):
        return self.digits[t % self.period]
    
    def time(self, t):
        T = len(self.digits)
        time = 0
        for i in range(t):
            if self.digits[i % T] != self.digits[(i + 1) % T]:
                time += 1
        return time

    def __str__(self) -> str:
        return f'({self.m} / {self.n})'
    
    def __repr__(self) -> str:
        return f'Rational({self.m}, {self.n}, {self.dim})'
    
    def __eq__(self, r) -> bool:
        l = len(self.reminders)
        for i in range(l):
            eq = True
            for j in range(l):
                if self.reminders[(i + j) % l] != r.reminders[j]:
                    eq = False
                    break
            if eq == True:
                return True
        return False
    
    def __neq__(self, r) -> bool:
        return not self.__eq__(r)

if __name__ == '__main__':
    dim = 1
    T = 6
    n = (2**dim)**T - 1
    n = 7
    r = Rational(1, n, dim=dim)
    print(r, r.digits, r.reminders, sum(r.digits), sum(r.digits) % 7)

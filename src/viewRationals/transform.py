def num_ones(seq: list[int]) -> tuple[int]:
    nx = 0
    ny = 0
    nz = 0
    for d in seq:
        nx += d % 2
        ny += (d // 2) % 2
        nz += (d // 4) % 2
    return nx, ny, nz


def get_digits(m: int, n: int, dim: int):
    base = 2**dim
    digits = []
    rem = m
    digit = rem * base // n
    while True:
        digits.append(digit)
        prod = rem * base
        rem = prod % n
        digit = prod // n
        if rem == m:
            break
    return digits
    

class Transform:
    def __init__(self, dim: int, n: int, nx: float|int, ny: float|int=0, nz: float|int=0):
        print('Transform', dim, n, nx, ny, nz)
        self.dim = dim
        self.base = 2**dim
        self.set_velocity(n, nx, ny, nz)

    def _set_plug_input(self):
        ratio = self.n // self.base

        self.plug_input = {}
        p = 0
        for i in range(self.base):
            self.plug_input[str(i)] = []
            for _ in range(ratio):
                if p == self.n:
                    break
                self.plug_input[str(i)].append(str(p))
                p += 1
        if p < self.n:
            while p < self.n:
                self.plug_input[str(self.base - 1)].append(str(p))
                p += 1

    def set_velocity(self, n: int, vx: float|int, vy: float|int=0, vz: float|int=0):
        self.n = n
        if type(vx) is float or type(vy) is float or type(vz) is float:
            self.vx = vx
            self.vy = vy
            self.vz = vz
            if abs(vx) > 0.5 or abs(vy) > 0.5 or abs(vz) > 0.5:
                raise Exception(f'Error: abs speed exceeds 0.5 ({vx}, {vy}, {vz})')
            self.nx = int((vx+1)*n/2)
            self.ny = int((vy+1)*n/2)
            self.nz = int((vz+1)*n/2)
            print(self.n, self.nx, self.ny, self.nz)
        elif type(vx) is int and type(vy) is int and type (vz) is int:
            self.nx = vx
            self.ny = vy
            self.nz = vz
            self.vx = vx/n - 0.5
            self.vz = vy/n - 0.5
            self.vx = vz/n - 0.5
        else:
            raise Exception(f'Error: incongruent parameters ({self.vx}, {self.vy}, {self.vz})')

        self._set_plug_input()

        self.output_modes = []
        keys = {}
        end = 2**(self.dim*n) - 1
        for m in range(end):

            seq = get_digits(m, end, self.dim)
            mx, my, mz = num_ones(seq) 
            if mx != self.nx or my != self.ny or mz != self.nz:
                continue

            plug_output = {}
            out = set()
            for pos in range(n):
                k = seq[pos%len(seq)]
                out.add(k)
                plug_output[str(pos)] = [str(k)]

            if len(out) == self.base:
                res_mode = {key: val for key, val in sorted(plug_output.items(), key=lambda ele: ele[1][0])}
                res_form = {key: val for key, val in sorted(plug_output.items(), key=lambda ele: ele[0])}
                smode = ''.join([ele[0] for ele in res_mode.values()])
                sform = ''.join([ele[0] for ele in res_form.values()])
                if smode not in keys:
                    keys[smode] = {}
                elif sform not in keys[smode]:
                    keys[smode][sform] = res_form

        for mode in range(len(keys)):
            index_mode = list(keys.keys())[mode]
            forms = list(keys[index_mode].values())
            self.output_modes.append(forms)

        for mode in range(len(self.output_modes)):
            print(mode, len(self.output_modes[mode]))
            
    def print(self):
        print(self.plug_input)
        for mode in range(self.get_num_modes()):
            print(self.output_modes[mode])

    def get_num_modes(self):
        return len(self.output_modes)
    
    def get_num_forms(self, mode):
        return len(self.output_modes[mode])
    
    def get_output_mode(self, mode):
        return self.output_modes[mode]
    
    def get_output_form(self, mode, form):
        return self.output_modes[mode][form]
    
    def get_plug_input(self):
        return self.plug_input
    
    def get_num_seqs(self):
        num = 0
        for elem in self.plug_input.values():
            num += len(elem)
        return num

    def transform(self, digits: str, mode: int=0, form: int=0) -> list[str]:
        seqs = self._input2mid(digits)
        output = []
        for seq in seqs:
            d = ''
            for i in seq:
                d += self.output_modes[mode][form][i][0]
            output.append(d)
        return output

    def _input2mid(self, digits: str, level=0):
        outputs = []

        if not digits:
            return outputs

        i = digits[0]
        for d in self.plug_input[i]:
            if len(digits) == 1:
                outputs.append([d])
            else:
                seqs = self._input2mid(digits[1:], level+1)
                if not seqs:
                    outputs.append([d])
                else:
                    for seq in seqs:
                        outputs.append([d] + seq)
        return outputs


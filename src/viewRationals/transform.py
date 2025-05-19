class Transform:
    """
    Class for getting the transformed paths of a path
    for a given dimension, number and velocity
    
    Attributes:
        dim (int): dimensions of space
        base (int): dual spacetime base
        vx (float): speed in the x dimension of the transform
        vy (float): speed in the y dimension of the transform
        vz (float): speed in the z dimension of the transform
        n (int): dividend of the transform (vx=nx/n, vy=ny/n...), 
                 usually the transform decision space dimension
        nx (int): numerator of the transform in the x dimension 
        ny (int): numerator of the transform in the y dimension 
        nz (int): numerator of the transform in the z dimension 
        plug_input (dict): codification of the transform from the 
                           dual spacetime decision space to the 
                           transform decision space
        output_modes (list): codification of the output modes of the
                             transform decision space back to the dual
                             spacetime decision space

    Args:
        dim (int): number of dimensions of the dual spacetime
        n (int): dividend of the transform (vx=nx/n, vy=ny/n...), 
                 usually the transform decision space dimension
        vx (float|int): if float, speed in the x dimension of the transform
                        else, nuemerator of the transform in the x direction
                        vx=nx/n
        vy (float|int): if float, speed in the y dimension of the transform
                        else, nuemerator of the transform in the y direction
                        vy=ny/n. Defaluts to 0 if dim < 2
        vz (float|int): if float, speed in the z dimension of the transform
                        else, nuemerator of the transform in the z direction
                        vz=nz/n. Defautls to 0 if dim < 3
    """
    dim: int
    base: int
    vx: float
    vy: float
    vz: float
    n: int
    nx: int
    ny: int
    nz: int
    plug_input: dict
    output_modes: list

    def __init__(self, dim: int, n: int, vx: float|int, vy: float|int=0, vz: float|int=0):
        print('Transform', dim, n, vx, vy, vz)
        self.dim = dim
        self.base = 2**dim
        self.set_velocity(n, vx, vy, vz)

    @staticmethod
    def _num_ones(seq: list[int]) -> tuple[int]:
        """
        Gets the number of ones on each dimension of a sequence of digits

        Args:
            seq: (list of int): the input sequence
        
        Returns:
            (tuple of int): the number of ones on each dimension
        """
        nx = 0
        ny = 0
        nz = 0
        for d in seq:
            nx += d % 2
            ny += (d // 2) % 2
            nz += (d // 4) % 2
        return nx, ny, nz

    @staticmethod
    def _get_digits(m: int, n: int, dim: int) -> list[int]:
        """
        Given the rational number m/n, gets the digits of the resulting 
        sequence for a given dimension

        Args:
            m (int): numerator of the rational number
            n (int): denominator of the rational number
            dim (int): dimension of the space (1, 2, 3)

        Returns:
            (list of int): the resulting list of digits
        """
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

    @staticmethod
    def _build_plug_input(n: int, dim: int) -> dict[list[str]]:
        """
        Builds the dictionary with the correspondace between the input decision space
        and the transform decision space.

        Args:
            n (int): denominator for speed
            dim (int): dimension of input decision space

        Returns:
            (dict of list of str): dictionary of input to transform decision space
        """
        
        base = 2**dim
        ratio = n // base
        plug_input = {}
        p = 0
        for i in range(base):
            plug_input[str(i)] = []
            for _ in range(ratio):
                if p == n:
                    break
                plug_input[str(i)].append(str(p))
                p += 1
        if p < n:
            while p < n:
                plug_input[str(base - 1)].append(str(p))
                p += 1
        return plug_input

    def set_velocity(self, n: int, vx: float|int, vy: float|int=0, vz: float|int=0) -> None:
        """
        Sets transformation speed.

        Args:
            n (int): numerator for velocity
            vx (float|int): if float, speed in x in the range [-0.5, 0.5]
                            if int, denominator for speed in x
            vy (float|int): if float, speed in y in the range [-0.5, 0.5]
                            if int, denominator for speed in y
            vz (float|int): if float, speed in z in the range [-0.5, 0.5]
                            if int, denominator for speed in z

        """
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
        elif type(vx) is int and type(vy) is int and type (vz) is int:
            self.nx = vx
            self.ny = vy
            self.nz = vz
            self.vx = vx/n - 0.5
            self.vz = vy/n - 0.5
            self.vx = vz/n - 0.5
        else:
            raise Exception(f'Error: incongruent parameters ({self.vx}, {self.vy}, {self.vz})')

        self.plug_input = self._build_plug_input(self.n, self.dim)

        self.output_modes = []
        keys = {}
        end = 2**(self.dim*n) - 1
        for m in range(end):

            seq = self._get_digits(m, end, self.dim)
            mx, my, mz = self._num_ones(seq) 
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
        """Print transformation"""
        print(self.plug_input)
        for mode in range(self.get_num_modes()):
            print(self.output_modes[mode])

    def get_num_modes(self) -> int:
        """Get number of modes of the transformation"""
        return len(self.output_modes)
    
    def get_num_forms(self, mode) -> int:
        """Get the number of forms of a given mode"""
        return len(self.output_modes[mode])
    
    def get_output_mode(self, mode):
        """Get the dictionary of a given mode, with all its forms"""
        return self.output_modes[mode]
    
    def get_output_form(self, mode, form):
        """Get a form of a given mode"""
        return self.output_modes[mode][form]
    
    def get_plug_input(self):
        """Get the input plug of the transformation"""
        return self.plug_input
    
    def get_num_seqs(self):
        """Get the number of sequences in the input plug of the transformaltion"""
        num = 0
        for elem in self.plug_input.values():
            num += len(elem)
        return num

    def transform(self, digits: str, mode: int=0, form: int=0) -> list[str]:
        """
        Transform a path in the form of a sequence of digits for a given mode
        and a given form.

        Args:
            digits (str): string of path digits
            mode (int): mode for the transform (defaults to 0)
            form (int): form of the mode (defaults to 0)

        Returns:
            (list of str): list of transformed paths

        """
        seqs = self._input2mid(digits)
        output = []
        for seq in seqs:
            d = ''
            for i in seq:
                d += self.output_modes[mode][form][i][0]
            output.append(d)
        return output

    def _input2mid(self, digits: str) -> list[str]:
        """
        Recursive method that construct all the posible variants of a given input path
        in the transform decision space.

        Args:
            digits (str): input path as a string of char

        Returns:
            (list of str): list of all paths in the transform decision space
        """
        outputs = []

        if not digits:
            return outputs

        i = digits[0]
        for d in self.plug_input[i]:
            if len(digits) == 1:
                outputs.append([d])
            else:
                seqs = self._input2mid(digits[1:])
                if not seqs:
                    outputs.append([d])
                else:
                    for seq in seqs:
                        outputs.append([d] + seq)
        return outputs

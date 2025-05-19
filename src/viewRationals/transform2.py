import math

class TrPlugInput(object):
    """
    Class to represent the input plugin for the Transform class.
    """

    def __init__(self):
        """
        Initialize the input plugin with default values.
        """
        self.dimin = 0
        self.input = ""
        self.dimtr = 0
        self.tr = ""

    def set(self, dimin:int, input:str, dimtr: int, tr:str):
        """
        Set the input plugin parameters.
        :param dimin: number of input dimensions
        :param input: string with the input  
        :param dimtr: number of transformed dimensions
        :param tr:    string with the transform
        """

        # check the input parameters
        if dimin >= dimtr:
            raise ValueError(f"Input dimension must be less than transform dimension. {dimin} >= {dimtr}")

        if len(input) != len(tr):
            raise ValueError(f"Input and transform strings must be the same length. {len(input)} != {len(tr)}")
        
        setinput = set()
        for c in input:
            setinput.add(c)
        if len(setinput) != 2**dimin:
            raise ValueError(f"Input must hold all the input dimension values {2**dimin} != {len(setinput)}")

        settr = set()
        for c in tr:
            settr.add(c)
        if len(settr) != dimtr:
            raise ValueError("Transform must hold all the transform dimension values")
                
        # set the input parameters
        self.dimin = dimin
        self.input = input
        self.dimtr = dimtr
        self.tr    = tr

    def transform(self, path: str, level:int=-1) -> list[str]:
        """
        Get all the transformed paths for the input plugin.
        """
        if level < 0:
            level = len(path)
        if not path:
            return []

        # initialize the transformed paths
        outpaths = []

        # for each character in the path...
        for i in range(len(path)):
            c = path[i]
            # for each character in the input...
            for j in range(len(self.input)):
                # if the character in the path matches the character in the input...
                if c == self.input[j]:
                    # if the level is greater than 1, recursively transform the rest of the path
                    if level > 1:
                        trpaths = self.transform(path[i+1:], level-1)
                        for trpath in trpaths:
                            outpaths.append(self.tr[j] + trpath)
                    # if the level is 1, add the transformed character to the output paths
                    elif level == 1:
                        outpaths.append(self.tr[j])
        
        # return the transformed paths
        return outpaths


class TrPlugOutput(object):
    """
    Class to represent the output plugin for the Transform class.
    """

    def __init__(self):
        """
        Initialize the input plugin with default values.
        """
        self.dimtr = 0
        self.tr = ""
        self.dimout = 0
        self.out = ""

    def set(self, dimtr: int, tr:str, dimout:int, out:str):
        """
        Set the input plugin parameters.
        :param dimtr:  number of transformed dimensions
        :param tr:     string with the transform
        :param dimout: number of output dimensions
        :param out:    string with the output

        """
        # check the input parameters
        if dimout >= dimtr:
            raise ValueError(f"Output dimension must be less than transform dimension. {dimout} >= {dimtr}")

        if len(out) != len(tr):
            raise ValueError(f"Output and transform strings must be the same length. {len(out)} != {len(tr)}")
        
        settr = set()
        for c in tr:
            settr.add(c)
        if len(settr) != dimtr:
            raise ValueError(f"Transform must hold all the transform dimension values {dimtr} != {len(settr)}")
        
        setout = set()
        for c in out:
            setout.add(c)
        if len(setout) != 2**dimout:
            raise ValueError(f"Output must hold all the transform dimension values {2**dimout} != {len(setout)}")
                
        # set the input parameters
        self.dimtr  = dimtr
        self.tr     = tr
        self.dimout = dimout
        self.out    = out

    def transform(self, path: str) -> str:
        """
        Get the transformed path for the output plugin.
        :param path: path to transform
        :return: transformed path
        """
        output = ""
        for c in path:
            if c not in self.tr:
                raise ValueError(f"Character {c} not in transform string.")
            for i in range(len(self.tr)):
                if c == self.tr[i]:
                    output += self.out[i]

        return output
    

class Transform(object):
    """
    Class to represent the Transform.
    """

    def __init__(self):
        """
        Initialize the Transform class with default values.
        """
        self.n = 0
        self.mx = 0
        self.my = 0
        self.mz = 0
        self.vx = 0
        self.vy = 0
        self.vz = 0
        self.inplugins = []
        self.outplugins = []
        self.inputplugin = None
        self.outputplugin = None

    @staticmethod
    def _num_ones(seq: list[int]) -> tuple[int]:
        """
        Gets the number of ones on each dimension of a sequence of digits
        Args:
            seq (list of int): sequence of digits
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
    def _get_digits(m: int, ndigits: int, dim: int) -> list[int]:
        """
        Gets the digits of a number in a given base.
        Args:
            m (int): number to convert
            ndigits (int): number of digits in the output
            dim (int): dimension of the base (1, 2, or 3)
        Returns:
            digits (list of int): list of digits in the given base
        """
        base = 2**dim
        number = base**ndigits
        if m == 0:
            digits = [0]*ndigits
            return digits
        digits = []
        reminder = m
        digit = (reminder * base) // number
        while len(digits) < ndigits:
            digits.append(digit)
            reminder = (reminder * base) % number
            digit = (reminder * base) // number
        return digits

    def set_velocity(self, n: int, vx: float|int, vy: float|int=0, vz: float|int=0) -> None:
        """
        Sets transformation speed.
        Args:
            n (int): denominator of the transformation
            vx (float|int): speed in x direction or numerator in x
            vy (float|int): speed in y direction or numerator in y (default is 0)
            vz (float|int): speed in z direction or numerator in z (default is 0)
        """
        print("Setting velocity to:", n, vx, vy, vz)
        self.n = n
        if type(vx) is float or type(vy) is float or type(vz) is float:
            self.vx = vx
            self.vy = vy
            self.vz = vz
            if abs(vx) > 0.5 or abs(vy) > 0.5 or abs(vz) > 0.5:
                raise ValueError(f'abs speed exceeds 0.5 ({vx}, {vy}, {vz})')
            self.mx = int((vx+1)*n/2)
            self.my = int((vy+1)*n/2)
            self.mz = int((vz+1)*n/2)
        elif type(vx) is int and type(vy) is int and type (vz) is int:
            self.mx = vx
            self.my = vy
            self.mz = vz
            self.vx = vx/n - 0.5
            self.vy = vy/n - 0.5
            self.vz = vz/n - 0.5
        else:
            raise ValueError(f'incongruent parameters ({vx}, {vy}, {vz})')
        
        # get the number digits of the transformation on each dimension
        diminput = 1
        nx = self.mx

        ny = self.my
        if self.my != 0:
            diminput += 1

        nz = self.mz
        if self.mz != 0:
            diminput += 1 

        # get the string digits of the transformation
        strdigits = "".join([str(d) for d in range(n)])
        ltrdigits = len(strdigits)
        
        # get the output plugins
        self.outplugins = []
        base = 2**diminput
        for i in range(base**ltrdigits):
            
            # get the digits of the sequence
            digits = self._get_digits(i, ltrdigits, diminput)

            # if the number of ones is equal to the number of ones in the output digits
            if self._num_ones(digits) == (nx, ny, nz):
                
                # get the string digits of the output
                soutdigits = "".join([str(d) for d in digits])

                # get append the output plugin
                self.outplugins.append(TrPlugOutput())
                try:
                    self.outplugins[-1].set(n, strdigits, diminput, soutdigits)
                except ValueError as e:
                    self.outplugins.pop()

        # get the input plugins
        self.inplugins = []
        for i in range(1, base**ltrdigits-1):
            
            # get the digits of the sequence
            digits = self._get_digits(i, ltrdigits, diminput)

            # get the string digits of the input            
            sindigits = "".join([str(d) for d in digits])

            # get append the input plugin
            self.inplugins.append(TrPlugInput())
            try:
                self.inplugins[-1].set(diminput, sindigits, n, strdigits)
            except ValueError as e:
                self.inplugins.pop()

        if not self.inplugins:
            raise ValueError("No input plugins found.")
        
        if not self.outplugins:
            raise ValueError("No output plugins found.")
        
        print("Velocity set to:", n, self.vx, self.vy, self.vz)

    def get_num_inputs(self) -> int:
        """
        Get the number of input plugins.
        :return: number of input plugins
        """
        return len(self.inplugins)
    
    def get_num_outputs(self) -> int:
        """
        Get the number of output plugins.
        :return: number of output plugins
        """
        return len(self.outplugins) 

    def set_input_plugin(self, i: int) -> None:
        """
        Set the input plugin for the Transform class.
        :param i: index of the input plugin
        """
        if i < 0 or i >= len(self.inplugins):
            raise ValueError("Input plugin index out of range.")
        self.inputplugin = self.inplugins[i]

    def set_output_plugin(self, i: int) -> None:
        """
        Set the output plugin for the Transform class.
        :param i: index of the output plugin
        """
        if i < 0 or i >= len(self.outplugins):
            raise ValueError("Output plugin index out of range.")
        self.outputplugin = self.outplugins[i]

    def transform(self, path: str) -> list[str]:
        """
        Get the transformed paths for the Transform class.
        :param path: path to transform
        :return: list of transformed paths
        """
        print("Transforming path:", path)

        # get the transformed paths from the input plugin
        trpaths = self.inputplugin.transform(path)

        # for each transformed path, get the output path from the output plugin
        outpaths = []
        for t in trpaths:
            outpaths.append(self.outputplugin.transform(t))
        
        outpaths.sort()
        return outpaths
    

if __name__ == "__main__":
    # Example usage
    path = "0010"
    transform = Transform()
    transform.set_velocity(9, 3, 3, 2)
    nimputs = transform.get_num_inputs()
    noutputs = transform.get_num_outputs()
    print("Number of input plugins:", nimputs)
    print("Number of output plugins:", noutputs)
    countpatsh = 0
    setpaths = set()
    for i in range(nimputs):
        for j in range(noutputs):
            # print("transform", i, j, transform.inplugins[i].input, transform.outplugins[j].out)
            transform.set_input_plugin(i)
            transform.set_output_plugin(j)
            paths = transform.transform(path)
            countpatsh += len(paths)
            for p in paths:
                setpaths.add(p)
            # print(len(paths), paths)
    print("Total number of transformed paths:", countpatsh)
    print("Unique transformed paths:", len(setpaths))
    paths = list(setpaths)
    paths.sort()
    print(paths)
    
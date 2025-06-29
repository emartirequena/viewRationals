from multiprocessing import Pool, cpu_count, managers
from utils import collect


class TrPlugInput(object):
    """
    Class to represent the input plugin for the Transform class.
    """

    def __init__(self):
        """
        Initialize the input plugin with default values.
        """
        self.dimin:int = 0
        self.input: str = ""
        self.dimtr: int = 0
        self.tr: str = ""

    @staticmethod
    def check(dimin:int, input:str, dimtr: int, tr:str) -> bool:
        """
        Check the input plugin parameters.
        :param dimin: number of input dimensions
        :param input: string with the input  
        :param dimtr: number of transformed dimensions
        :param tr:    string with the transform
        :return: True if the parameters are valid, False otherwise
        """
        # check the input parameters
        if dimin >= dimtr:
            return f"Input dimension must be less than transform dimension. {dimin} >= {dimtr}"

        if len(input) != len(tr):
            return f"Input and transform strings must be the same length. {len(input)} != {len(tr)}"
        
        setinput = set()
        for c in input:
            setinput.add(c)
        if len(setinput) != 2**dimin:
            return f"Input must hold all the input dimension values {2**dimin} != {len(setinput)}"

        settr = set()
        for c in tr:
            settr.add(c)
        if len(settr) != dimtr:
            return "Transform must hold all the transform dimension values"
        
        return ""
                

    def set(self, dimin:int, input:str, dimtr: int, tr:str):
        """
        Set the input plugin parameters.
        :param dimin: number of input dimensions
        :param input: string with the input  
        :param dimtr: number of transformed dimensions
        :param tr:    string with the transform
        """

        # check the input parameters
        resutl = self.check(dimin, input, dimtr, tr)
        if resutl:
            raise ValueError(resutl)

        # set the input parameters
        self.dimin = dimin
        self.input = input
        self.dimtr = dimtr
        self.tr    = tr

    def transform(self, path: str, level: int = -1) -> list[str]:
        """
        Get all the transformed paths for the input plugin.
        """
        if level < 0:
            level = len(path)
        if not path:
            return []

        # Initialize the transformed paths
        outpaths = []
        stack = [(path, level, "")]  # Stack to simulate recursion (path, level, current_transformation)

        while stack:
            current_path, current_level, current_transformation = stack.pop()

            # If the level is 0, skip further processing
            if current_level == 0:
                continue

            # Process each character in the current path
            for i in range(len(current_path)):
                c = current_path[i]
                for j in range(len(self.input)):
                    if c == self.input[j]:
                        # Append the transformed character to the current transformation
                        new_transformation = current_transformation + self.tr[j]

                        # If the level is 1, add the transformation to the output
                        if current_level == 1:
                            outpaths.append(new_transformation)
                        else:
                            # Push the remaining path and updated level onto the stack
                            stack.append((current_path[i + 1:], current_level - 1, new_transformation))

        # Return the transformed paths
        return outpaths


class TrPlugOutput(object):
    """
    Class to represent the output plugin for the Transform class.
    """

    def __init__(self):
        """
        Initialize the input plugin with default values.
        """
        self.dimtr: int = 0
        self.tr: str = ""
        self.dimout: int = 0
        self.out: str = ""

    @staticmethod
    def check(dimtr: int, tr:str, dimout:int, out:str) -> str:
        """
        Check the output plugin parameters.
        :param dimtr:  number of transformed dimensions
        :param tr:     string with the transform
        :param dimout: number of output dimensions
        :param out:    string with the output
        :return: error message if the parameters are invalid, empty string otherwise
        """
        # check the input parameters
        if dimout >= dimtr:
            return f"Output dimension must be less than transform dimension. {dimout} >= {dimtr}"

        if len(out) != len(tr):
            return f"Output and transform strings must be the same length. {len(out)} != {len(tr)}"
        
        settr = set()
        for c in tr:
            settr.add(c)
        if len(settr) != dimtr:
            return f"Transform must hold all the transform dimension values {dimtr} != {len(settr)}"
        
        setout = set()
        for c in out:
            setout.add(c)
        if len(setout) != 2**dimout:
            return f"Output must hold all the transform dimension values {2**dimout} != {len(setout)}"
        
        return ""

    def set(self, dimtr: int, tr:str, dimout:int, out:str):
        """
        Set the input plugin parameters.
        :param dimtr:  number of transformed dimensions
        :param tr:     string with the transform
        :param dimout: number of output dimensions
        :param out:    string with the output

        """
        # check the input parameters
        result = self.check(dimtr, tr, dimout, out)
        if result:
            raise ValueError(result)
                
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


def _get_output(args) -> tuple[str]:
    i, dim, dimtr, tr, nx, ny, nz = args

    # get append the output plugin
    digits = Transform._get_digits(i, dimtr, dim)

    # get the string digits of the output
    soutdigits = "".join([Transform._digit_to_char(d) for d in digits])

    if Transform._num_ones(digits) == (nx, ny, nz):
        if not TrPlugOutput.check(dimtr, tr, dim, soutdigits):
            return (soutdigits, True)
    
    return ("", False)


def _get_input(args) -> tuple[str]:
    i, dim, strdigits, n = args

    # get the digits of the sequence
    digits = Transform._get_digits(i, len(strdigits), dim)

    # get the string digits of the input            
    sindigits = "".join([Transform._digit_to_char(d) for d in digits])

    # get append the input plugin
    if not TrPlugInput.check(dim, sindigits, n, strdigits):
        return (sindigits, True)
    
    return ("", False)


class Transform(object):
    """
    Class to represent the Transform.
    """

    def __init__(self):
        """
        Initialize the Transform class with default values.
        """
        self.n: int = 0
        self.mx: int = 0
        self.my: int = 0
        self.mz: int = 0
        self.vx: int = 0
        self.vy: int = 0
        self.vz: int = 0
        self.dim: int = 0
        self.dimtr: int = 0
        self.tr: str = ""
        self.dimin: int = 0
        self.inplugins: list[TrPlugInput] = []
        self.dimout: int = 0 
        self.outplugins: list[TrPlugOutput] = []
        self.idxinput: int = -1
        self.idxoutput: int = -1
        self.active: bool = False

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
    
    @staticmethod
    def _digit_to_char(n: int) -> str:
        """
        Converts a digit to a character representation.
        Args:
            n (int): number to convert
        Returns:
            s (str): character representation of the number in the given base
        """
        if n < 10:
            return str(n)
        elif n < 36:
            return chr(n + 87)
        return ""

    def set_velocity(self, dim: int, n: int, vx: float|int, vy: float|int=0, vz: float|int=0) -> None:
        """
        Sets transformation speed.
        Args:
            dim (int): dimension of the spacetime (1, 2, or 3)
            n (int): denominator of the transformation
            vx (float|int): speed in x direction or numerator in x
            vy (float|int): speed in y direction or numerator in y (default is 0)
            vz (float|int): speed in z direction or numerator in z (default is 0)
        """
        print("Setting velocity to:", n, vx, vy, vz)
        if dim < 1 or dim > 3:
            raise ValueError(f"Dimension must be between 1 and 3. {dim} not in [1, 3]")
        self.dim = dim
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
        nx = self.mx
        ny = self.my
        nz = self.mz

        # get the string digits of the transformation
        self.tr = "".join([self._digit_to_char(d) for d in range(n)])
        self.dimtr = len(self.tr)
        base = 2**dim
        
        # get the output plugins
        print("Getting output plugins...")

        num_cpus = int(cpu_count() * 0.8)
        chunksize = (base**self.dimtr-1) // num_cpus or 1
        p = Pool(num_cpus)
        params = []
        count = 0
        for i in range(1, base**self.dimtr-1):
            if count % 10000 == 0:
                print(f"{i:9d}"+"\b"*9, end="", flush=True)
            count += 1
            params.append((i, self.dim, self.dimtr, self.tr, nx, ny, nz))
        results = p.imap(func=_get_output, iterable=params, chunksize=chunksize)
        p.close()
        p.join()
        del params
        collect()
        print("")

        self.outplugins = []
        for result in results:
            if result[1]:
                self.outplugins.append(result[0])

        del results
        collect()

        if not self.outplugins:
            raise ValueError("No output plugins found.")
        
        # get the input plugins
        print("Getting input plugins...")

        num_cpus = int(cpu_count() * 0.8)
        chunksize = (base**self.dimtr-1) // num_cpus or 1
        p = Pool(num_cpus)
        params = []
        for i in range(1, base**self.dimtr-1):
            params.append((i, dim, self.tr, n))
        results = p.imap(func=_get_input, iterable=params, chunksize=chunksize)
        p.close()
        p.join()
        del params
        collect()

        self.inplugins = []
        for result in results:
            if result[1]:
                self.inplugins.append(result[0])

        del results
        collect()

        if not self.inplugins:
            raise ValueError("No input plugins found.")
        
        print("Velocity set to:", dim, n, self.vx, self.vy, self.vz)
        self.active = True

    def get_dim(self) -> int:
        """
        Get the dimension of the Transform class.
        :return: dimension of the Transform class
        """
        return self.dim

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
    
    def get_input_plugin(self, i: int) -> TrPlugInput:
        """
        Get the input plugin for the Transform class.
        :param i: index of the input plugin
        :return: input plugin
        """
        if i < 0 or i >= len(self.inplugins):
            raise ValueError("Input plugin index out of range.")
        return self.inplugins[i]
    
    def get_output_plugin(self, i: int) -> TrPlugOutput:
        """
        Get the output plugin for the Transform class.
        :param i: index of the output plugin
        :return: output plugin
        """
        if i < 0 or i >= len(self.outplugins):
            raise ValueError("Output plugin index out of range.")
        return self.outplugins[i]
    
    def get_input_plugin_idx(self) -> int:
        """
        Get the index of the input plugin for the Transform class.
        :return: index of the input plugin
        """
        return self.idxinput
    
    def get_output_plugin_idx(self) -> int:
        """
        Get the index of the output plugin for the Transform class.
        :return: index of the output plugin
        """
        return self.idxoutput
    
    def set_input_plugin(self, i: int) -> None:
        """
        Set the input plugin for the Transform class.
        :param i: index of the input plugin
        """
        if i < 0 or i >= len(self.inplugins):
            raise ValueError("Input plugin index out of range.")
        self.inputplugin = self.inplugins[i]
        self.idxinput = i

    def set_output_plugin(self, i: int) -> None:
        """
        Set the output plugin for the Transform class.
        :param i: index of the output plugin
        """
        if i < 0 or i >= len(self.outplugins):
            raise ValueError("Output plugin index out of range.")
        self.outputplugin = self.outplugins[i]
        self.idxoutput = i

    def clear_plugins(self) -> None:
        """
        Clear the input and output plugins.
        """
        self.inputplugin = None
        self.outputplugin = None
        self.idxinput = -1
        self.idxoutput = -1

    def transform(self, path: str) -> list[str]:
        """
        Get the transformed paths for the Transform class.
        :param path: path to transform
        :return: list of transformed paths
        """
        # check if the input and output plugins are set
        if self.idxinput == -1 or self.idxoutput == -1 or not self.active:
            return [path]
        
        # get the transformed paths from the input plugin
        inputplugin = TrPlugInput()
        inputplugin.set(self.dim, self.inputplugin, self.dimtr, self.tr)
        trpaths = inputplugin.transform(path)

        # for each transformed path, get the output path from the output plugin
        outputplugin = TrPlugOutput()
        outputplugin.set(self.dimtr, self.tr, self.dim, self.outputplugin)   
        outpaths = []
        for t in trpaths:
            outpaths.append(outputplugin.transform(t))
        
        outpaths.sort()
        return outpaths
    
    def set_active(self, value: bool) -> None:
        """
        Set the active state of the Transform class.
        :param value: True to set the Transform class as active, False otherwise
        """
        self.active = value
    

if __name__ == "__main__":
    
    # Example usage
    path = "1000"
    transform = Transform()
    transform.set_velocity(4, 2)
    ninputs = transform.get_num_inputs()
    noutputs = transform.get_num_outputs()
    print("Number of input plugins:", ninputs)
    print("Number of output plugins:", noutputs)
    countpaths = 0
    setpaths = set()
    for i in range(ninputs):
        for j in range(noutputs):
            # print("transform", i, j, transform.inplugins[i].input, transform.outplugins[j].out)
            transform.set_input_plugin(i)
            transform.set_output_plugin(j)
            paths = transform.transform(path)
            countpaths += len(paths)
            for p in paths:
                setpaths.add(p)
            # print(len(paths), paths)
    print("Total number of transformed paths:", countpaths)
    print("Unique transformed paths:", len(setpaths))
    print("Path to transform:", path)
    print("Transformed paths:")
    paths = list(setpaths)
    paths.sort()
    print(len(paths), paths)

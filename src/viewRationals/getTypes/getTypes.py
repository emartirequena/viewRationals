import viewUtils as vu
from gc import collect
from time import time

class TypeInfo:
    def __init__(self, values) -> None:
        self.values: list[int] = []
        self.plugins: list[tuple[str, str]] = []
        self.count = 0
        self.setValues(values)

    def setValues(self, values: list[int]) -> None:
        self.values = values

    def addPlugin(self, input: str, output: str) -> None:
        self.plugins.append((input, output))
        self.count += 1

    def dumpToFile(self, fp, total_outputs: int) -> None:
        fp.write("\n")
        fp.write(f"Type Count: {self.count * total_outputs}\n")
        for input, output in self.plugins:
            fp.write(f"Form: Input {input}, Output {output}\n")
        fp.flush()

    def __eq__(self, other: object) -> bool:
        if len(self.values) != len(other.values):
            return False
        if self.values != other.values:
            return False
        return True

def getTypes(period: int, number: int, dim: int, n:int, mx:int, my:int, mz:int) -> list[TypeInfo]:
    types: list[TypeInfo] = []
    spc = vu.spacetime_cuda_create(period, number, period, dim)
    vu.spacetime_cuda_set_tr_velocity(spc, dim, n, mx, my, mz)
    num_inputs = vu.spacetime_cuda_get_tr_num_inputs(spc)
    num_outputs = vu.spacetime_cuda_get_tr_num_outputs(spc)
    print(f"Created spacetime with period={period}, number={number}, dim={dim}, n={n}, mx={mx}, my={my}, mz={mz}")
    print(f"Number of inputs: {num_inputs}, outputs: {num_outputs} = {num_inputs * num_outputs} combinations")
    for output in range(min(num_outputs, 1)):
        for input in range(num_inputs):
            print(f"input {input:6d} output {output:6d}..." + "\b" * 29, end="", flush=True)

            s_input, _ = vu.spacetime_cuda_get_tr_input_plugin(spc, input)
            s_output, _ = vu.spacetime_cuda_get_tr_output_plugin(spc, output)
            if not s_input or not s_output:
                print(f"Failed to get input/output plugin for input {input}")
                continue

            vu.spacetime_cuda_set_tr_input_plugin_by_string(spc, s_input)
            vu.spacetime_cuda_set_tr_output_plugin_by_string(spc, s_output)
            vu.spacetime_cuda_setRationalSet(spc, number, 1)
            vu.spacetime_cuda_addRationalSet(spc, 0, 0, 0, 0)
            
            values = vu.spacetime_cuda_get_space_as_double_list(spc, period)
            id = 0
            found: bool = False
            for id in range(len(types)):
                if values == types[id].values:
                    types[id].addPlugin(s_input.decode(), s_output.decode())
                    found = True
                    break
            if not found:
                types.append(TypeInfo(values))
                types[-1].addPlugin(s_input.decode(), s_output.decode())
            
            vu.spacetime_cuda_reset(spc, period, number, period, dim)
            vu.spacetime_cuda_set_tr_velocity(spc, dim, n, mx, my, mz)

    print(" "*29, end="\n", flush=True)

    return types, spc, num_inputs, num_outputs

if __name__ == "__main__":
    period = 6
    number = 13
    dim = 2
    n = 8
    mx = 2
    my = 2
    mz = 0

    init_time = time()

    print("Getting types...")
    types, spc, num_inputs, num_outputs = getTypes(period, number, dim, n, mx, my, mz)

    # get total number of types
    total = 0
    for t in types:
        total += t.count

    fp = open(f"../types/Types_{dim}D_{n}_{mx}_{my}_{mz}.txt", "w")
    fp.write(f"Types for {dim}D, n={n}, mx={mx}, my={my}, mz={mz}\n")
    fp.write(f"Number of inputs: {num_inputs}, outputs: {num_outputs}\n")
    fp.write(f"Total number of forms: {num_inputs*num_outputs}\n")
    fp.write(f"Total number of types: {len(types)}\n")
    fp.flush()

    print(f"Found {len(types)} types:")
    total_forms = 0
    for t in types:
        s_input = t.plugins[0][0]
        s_output = t.plugins[0][1]
        print(f"Input: {s_input}, Output: {s_output}, Count: {t.count * num_outputs}")
        t.dumpToFile(fp, num_outputs)
        total_forms += t.count * num_outputs

    print(f"Total number of forms: {total_forms}")
    print(f"Total number of types: {len(types)}")

    end_time = time()
    elapsed_time = end_time - init_time
    seconds = int(elapsed_time)
    minutes = seconds // 60
    print(f"Elapsed time: {minutes}:{seconds % 60} seconds")

    fp.close()

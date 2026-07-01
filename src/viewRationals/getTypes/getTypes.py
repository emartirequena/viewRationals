import viewUtils as vu
from gc import collect

class TypeInfo:
    def __init__(self, input: int, output, values) -> None:
        self.input = input
        self.output = output
        self.values: list[int] = []
        self.setValues(values)
        self.count = 1

    def setValues(self, values: list[int]) -> None:
        self.values = values

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
    print(f"Number of inputs: {num_inputs}, outputs: {num_outputs} = {num_inputs * num_outputs} combinations")
    for output in range(min(num_outputs, 1)):
        for input in range(num_inputs):
            print(f"input {input:4d} output {output:4d}..." + "\b" * 25, end="", flush=True)

            vu.spacetime_cuda_set_tr_input_plugin(spc, input)
            vu.spacetime_cuda_set_tr_output_plugin(spc, output)
            vu.spacetime_cuda_setRationalSet(spc, number, 1)
            vu.spacetime_cuda_addRationalSet(spc, 0, 0, 0, 0)
            
            values = vu.spacetime_cuda_get_space_as_double_list(spc, period)
            id = 0
            found: bool = False
            for id in range(len(types)):
                if values == types[id].values:
                    types[id].count += 1
                    found = True
                    break
            if not found:
                types.append(TypeInfo(input, output, values))
                s_input, _ = vu.spacetime_cuda_get_tr_input_plugin(spc, input)
                s_output, _ = vu.spacetime_cuda_get_tr_output_plugin(spc, output)
                print(f"Input: {s_input.decode()}, Output: {s_output.decode()}")
            
            vu.spacetime_cuda_delete(spc)
            spc = None
            collect()
            spc = vu.spacetime_cuda_create(period, number, period, dim)
            vu.spacetime_cuda_set_tr_velocity(spc, dim, n, mx, my, mz)

    return types, spc

if __name__ == "__main__":
    period = 6
    number = 9
    dim = 1
    n = 14
    mx = 7
    my = 0
    mz = 0

    # print("Creating spacetime...")
    # spc = vu.spacetime_cuda_create(period, number, period, dim)

    # print(f"Setting velocity... ({n}, {mx}, {my}, {mz})")
    # res = vu.spacetime_cuda_set_tr_velocity(spc, dim, n, mx, my, mz)
    # if res:
    #     print("Error setting velocity")
    #     exit(1)

    print("Getting types...")
    types, spc = getTypes(period, number, dim, n, mx, my, mz)

    print(f"Found {len(types)} types:")
    for t in types:
        input, _ = vu.spacetime_cuda_get_tr_input_plugin(spc, t.input)
        output, _ = vu.spacetime_cuda_get_tr_output_plugin(spc, t.output)
        print(f"Input: {str(input.decode())}, Output: {str(output.decode())}, Count: {t.count}")

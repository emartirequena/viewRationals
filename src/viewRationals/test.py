import json
import os
import sys
import viewUtils as vu
from gc import collect


def plugin_and(a, b):
    """
    Returns the logical AND of two plugin strings.
    """
    return ''.join('1' if a[i] == '1' and b[i] == '1' else '0' for i in range(len(a)))

def plugin_or(a, b):
    """
    Returns the logical OR of two plugin strings.
    """
    return ''.join('1' if a[i] == '1' or b[i] == '1' else '0' for i in range(len(a)))

def plugin_xor(a, b):
    """
    Returns the logical XOR of two plugin strings.
    """
    return ''.join('1' if a[i] != b[i] else '0' for i in range(len(a)))

def num_ones(s):
    """
    Returns the number of '1's in a string.
    """
    return sum(1 for char in s if char == '1')

def main1(_dim: 1, _nr=4, _mx=2, _my=0, _mz=0):
    dim = _dim
    T = 6
    max_val = 6
    num = 2**(dim * T)
    n = 9
    is_central_subset = True
    nr = _nr
    mx = _mx
    my = _my
    mz = _mz

    print(f"dim: {dim}, T: {T}, max_val: {max_val}, num: {num}, n: {n}, is_central_subset: {is_central_subset}")
    print('Creating spacetime...')
    spacetime = vu.spacetime_cuda_create(T, num, max_val, dim)

    print(f'Setting velocity to {nr}, {mx}, {my}, {mz}')
    vu.spacetime_cuda_set_tr_velocity(spacetime, dim, nr, mx, my, mz)

    num_inputs = vu.spacetime_cuda_get_tr_num_inputs(spacetime)
    print(f'Number of inputs: {num_inputs}')

    num_outputs = vu.spacetime_cuda_get_tr_num_outputs(spacetime)
    print(f'Number of outputs: {num_outputs}')

    num_forms = num_inputs * num_outputs
    print(f'Total forms: {num_forms}')

    result = {
        'dim': dim,
        'T': T,
        'max_val': max_val,
        'num': num,
        'n': n,
        'is_central_subset': is_central_subset,
        'num_inputs': num_inputs,
        'num_outputs': num_outputs,
        'num_forms': num_forms,
        'velocity': [dim, nr, mx, my, mz],
        'num_types': 0,
        'types': []
    }
    types = result['types']
    spaces = []

    count_forms = 0
    max_forms = 2000
    
    num_paths = vu.spacetime_cuda_countPaths(spacetime, max_val, False)
    
    for i in range(num_outputs):
        if count_forms >= max_forms:
            break
        vu.spacetime_cuda_set_tr_output_plugin(spacetime, i)
        output = str(vu.spacetime_cuda_get_tr_output_plugin(spacetime, i)[0].decode('utf-8'))

        for j in range(num_inputs):
            if count_forms >= max_forms:
                break

            vu.spacetime_cuda_set_tr_input_plugin(spacetime, j)
            input = str(vu.spacetime_cuda_get_tr_input_plugin(spacetime, j)[0].decode('utf-8'))
            
            sand = plugin_and(input, output)
            sor = plugin_or(input, output)
            num_ones_and = num_ones(sand)
            num_ones_or = num_ones(sor)
            final = f'{input} {output} - {sand} {sor} - {num_ones_and} {num_ones_or}'
            print(f'{count_forms:5d}/{num_forms} : {final}')
            ones = f'{num_ones_and} {num_ones_or}'

            vu.spacetime_cuda_reset(spacetime, T, num, max_val, dim)
            vu.spacetime_cuda_setRationalSet(spacetime, n, is_central_subset)
            vu.spacetime_cuda_addRationalSet(spacetime, 0, 0, 0, 0)

            space = vu.spacetime_cuda_get_space_as_double_list(spacetime, max_val)
            found = False
            index = 0
            for mspace in spaces:
                if mspace == space:
                    types[index]['count'] += 1
                    if ones not in types[index]['ones']:
                        types[index]['ones'].append(ones)
                        types[index]['final'].append(final)
                    found = True
                    del space
                    res = 1
                    while res:
                        res = collect()
                    break
                index += 1
            if not found:
                spaces.append(space)
                if dim == 1:
                    type_dict = {
                        'space': space,
                        'num_paths': num_paths,
                        'count': 1,
                        'final': [final],
                        'ones': [ones]
                    }
                else:
                    type_dict = {
                        'num_paths': num_paths,
                        'count': 1,
                        'final': [final],
                        'ones': [ones],
                    }
                types.append(type_dict)
            count_forms += 1

        res = 1
        while res:
            res = collect()
    
    result['num_types'] = len(types)
    if count_forms >= max_forms:
        for type_info in types:
            type_info['count'] = int(0.5 + type_info['count'] * num_forms / count_forms)

    print('Writing found types to types.json')
    fname = f'types_{dim}_{nr}_{mx}_{my}_{mz}.json'
    path = os.path.join(os.path.dirname(__file__), 'types')
    if not os.path.exists(path):
        os.makedirs(path)
    with open(os.path.join(path, fname), 'w') as f:
        json.dump(result, f, indent=4)

    return result

def make_report(result):
    """
    Generates a report from the result dictionary.
    """
    report = f"Dimension: {result['dim']}\n"
    report += f"T: {result['T']}\n"
    report += f"Max Value: {result['max_val']}\n"
    report += f"Number: {result['num']}\n"
    report += f"Velocity: {result['velocity']}\n"
    report += f"Number of Inputs: {result['num_inputs']}\n"
    report += f"Number of Outputs: {result['num_outputs']}\n"
    report += f"Number of Forms: {result['num_forms']}\n"
    report += f"Number of Types: {result['num_types']}\n\n"
    
    for i, type_info in enumerate(result['types']):
        report += f"  Type {i+1}:\n"
        report += f"  Count: {type_info['count']}\n"
        for final in type_info['final']:
            report += f"    Final: {final}\n"
        report += "\n"

    fname = f'report_{result["dim"]}_{result["velocity"][1]}_{result["velocity"][2]}_{result["velocity"][3]}_{result["velocity"][4]}.txt'
    path = os.path.join(os.path.dirname(__file__), 'reports')
    if not os.path.exists(path):
        os.makedirs(path)
    fname = os.path.join(path, fname)

    with open(fname, 'w') as f:
        f.write(report)

    print(f"Report written to {fname}")


def main2():
    """
    Second main function.
    """
    ...

if __name__ == '__main__':
    result = main1(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]), int(sys.argv[5]))
    make_report(result)

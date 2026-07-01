import sys
import os
# from gc import collect
from functools import reduce
from copy import copy
import subprocess
from PIL import Image
from PyQt5 import QtGui
from math import sqrt, pow


def plugin_check_complete(plugin_string: str, dim: int) -> bool:
    """
    Checks if a plugin string is complete for the given dimension.
    :param plugin_string: The plugin string to check.
    :param dim: The dimension of the plugin string (1, 2, or 3).
    :return: True if the plugin string is complete, False otherwise.
    """
    base = 2**dim
    set_of_valid_chars = set(str(i) for i in range(base))
    set_of_plguin_chars = set(plugin_string)
    if set_of_plguin_chars != set_of_valid_chars:
        return False
    return True

def plugin_extract(plugin_string: str, dim: int) -> str:
    """
    Extracts the plugin at the specified dimension from a plugin string.
    :param plugin_string: The plugin string to extract from.
    :param dim: The dimension of the plugin to extract.
    :return: The extracted plugin string.
    """
    if dim == 1:
        return ''.join([str(int(s) % 2) for s in plugin_string])
    elif dim == 2:
        return ''.join([str((int(s)//2) % 2) for s in plugin_string])
    elif dim == 3:
        return ''.join([str((int(s)//4) % 2) for s in plugin_string])
    
def plugin_join(plugin_strings: list[str], dim: int) -> str:
    """
    Joins a list of plugin strings into a single string.
    :param plugin_strings: The list of plugin strings to join, in order x, y, z.
    :param dim: The dimension of the plugin strings (1, 2, or 3).
    :return: The joined plugin string.
    """
    if not plugin_strings:
        return ''
    if dim == 1:
        return plugin_strings[0]
    elif dim == 2:
        return ''.join(
            str(int(s2) * 2 + int(s1)) for s2, s1 in zip(
                plugin_strings[1], plugin_strings[0]
            )
        )
    else:
        return ''.join(
            str(int(s3) * 4 + int(s2) * 2 + int(s1)) for s3, s2, s1 in zip(
                plugin_strings[2], plugin_strings[1], plugin_strings[0]
            )
        )

def plugin_shift(plugin_string: str, steps: int) -> str:
    """
    Shifts a plugin string to remove any '0's at the end.
    :param plugin_string: The plugin string to sift.
    :param steps: The number of steps to shift.
    :return: The sifted plugin string.
    """
    if not plugin_string:
        return ''
    if abs(steps) > len(plugin_string):
        raise ValueError("Steps cannot be greater than the length of the plugin string.")
    out = plugin_string + plugin_string
    l = len(plugin_string)
    return out[steps:steps + l] if steps >= 0 else out[steps + l:steps + 2 * l]

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

def plugin_create(n: int, m: int, plugin_and: int, plugin_or: int) -> tuple[str, str]:
    """
    Creates a plugin string from the number of '1's in the logical AND and OR of two plugin strings.
    :param n: The length of the plugin strings.
    :param m: The number of '1's in the output plugin string.
    :param plugin_and: The number of '1's in the logical AND of the plugin strings.
    :param plugin_or: The number of '1's in the logical OR of the plugin strings.
    :return: The combined plugin input and output strings.
    """
    output = [1 for _ in range(m)] + [0 for _ in range(n-m)]
    input = []
    for i in range(n):
        if output[i] == 1:
            plugin_or -= 1
            if plugin_and > 0:
                input.append(1)
                plugin_and -= 1
            else:
                input.append(0)
        else:
            if plugin_or > 0:
                input.append(1)
                plugin_or -= 1
            else:
                input.append(0)

    input.reverse()
    output.reverse()
    input = ''.join(str(i) for i in input)
    output = ''.join(str(i) for i in output)
    return input, output


def lerp(t, ta, a, tb, b):
    return a + (b-a)*(t-ta)/(tb-ta)


def check_ffmpeg(ffmpeg_path: str) -> bool:
    return os.path.exists(ffmpeg_path)

# def collect(s=''):
#     if s:
#         print(f'------- {max(gc.collect(2), gc.collect(1), gc.collect())} objects cleaned for {s}...')
#     else:
#         gc.collect(2)
#         gc.collect(1)
#         gc.collect()

def pil2pixmap(img): 
    if img.mode == "RGB":
        r, g, b = img.split()
        img = Image.merge("RGB", (b, g, r))
    elif  img.mode == "RGBA":
        r, g, b, a = img.split()
        img = Image.merge("RGBA", (b, g, r, a))
    elif img.mode == "L":
        img = img.convert("RGBA")
    img2 = img.convert("RGBA")
    data = img2.tobytes("raw", "RGBA")
    qimg = QtGui.QImage(data, img.size[0], img.size[1], QtGui.QImage.Format_ARGB32)
    pixmap = QtGui.QPixmap.fromImage(qimg)
    return pixmap


def make_video(
        ffmpeg_path: str, 
        in_sequence_path: str, 
        out_video_path: str, 
        video_codec: str='libx264', 
        video_format: str='mp4', 
        frame_rate: int=25, 
        bit_rate ='20M', 
        image_resx: int=1920, 
        image_resy: int=1080
):
    if not check_ffmpeg(ffmpeg_path):
        print(f'------ ERROR: FFMPEG NOT FOUND, {ffmpeg_path}')
        return False
    options = [
        ffmpeg_path,
        '-y',
        '-r', f'{frame_rate}',
        '-i', in_sequence_path,
        '-c', video_codec,
        '-f', video_format,
        '-b:v', f'{bit_rate}',
        '-s', f'{image_resx}x{image_resy}',
        out_video_path,
    ]
    print(*options)
    subprocess.run(options)
    return True

def get_alpha(count, number, max, normalize_alpha, alpha_pow, rad_factor, rad_pow, rad_min):
    div = number
    if normalize_alpha:
        div = max
    alpha = pow(float(count) / float(div), alpha_pow)
    rad = pow(alpha * rad_factor, rad_pow)
    rad = rad_min if rad < rad_min else rad
    rad = 1.0 if rad > 1.0 else rad
    return alpha, rad


def appendEs2Sequences(sequences, es):
    result=[]
    if not sequences:
        for e in es:
            result.append([e])
    else:
        for e in es:
            result+=[seq+[e] for seq in sequences]
    return result

def cartesianproduct(lists) :
    """
    given a list of lists,
    returns all the possible combinations taking one element from each list
    The list does not have to be of equal length
    """
    return reduce(appendEs2Sequences, lists, [])

def primefactors(n: int) -> list[int]:
    """lists prime factors, from greatest to smallest"""
    i:int = 3
    limit:int = int(sqrt(float(n)))
    while i <= limit:
        if n % i == 0:
            lst: list[int] = primefactors(n // i)
            lst.append(i)
            return lst
        i+=2
    return [n]      # n is prime

def factorGenerator(n: int) -> dict:
    p = primefactors(n)
    factors= dict()
    for p1 in p:
        try:
            factors[p1]+=1
        except KeyError:
            factors[p1]=1
    factors = dict(sorted(factors.items(), key=lambda t:t[0]))
    return factors

def divisors(n: int) -> list[int]:
    factors = factorGenerator(n)
    divisors: list[int] = []
    listexponents: list[int] = [list(map(lambda x:int(k**x),range(0, factors[k]+1))) for k in factors.keys()]
    listfactors: list[int] = cartesianproduct(listexponents)
    for f in listfactors:
        divisors.append(reduce(lambda x, y: int(x*y), f, 1))
    divisors.sort()
    return divisors

def getExponentsFromFactors(factors: dict, exponents: list[int]) -> dict:
    out: dict = copy(factors)
    keys: list = list(factors.keys())
    for index in range(0, len(exponents)):
        e: int = exponents[index]
        if e == 1:
            out[keys[index]] = 0
        else:
            r: int = e
            for factor in range(0, factors[keys[index]] + 1):
                r = r // keys[index]
                if r == 1:
                    break
            out[keys[index]] = factor + 1
    return out

def getDivisorsAndFactors(n: int, base: int) -> dict:
    factors = factorGenerator(n)
    divisors: dict = {}
    listexponents: list[list[int]] = [list(map(lambda x:int(k**x),range(0, factors[k]+1))) for k in factors.keys()]
    listfactors: list[list[int]] = cartesianproduct(listexponents)
    for f in listfactors:
        number: int = reduce(lambda x, y: int(x*y), f, 1)
        record: dict = {
            'number': number,
            'period': getPeriod(number, base),
            'factors': getExponentsFromFactors(factors, listfactors[listfactors.index(f)])
        }
        divisors[number] = record
    divisors = {k: v for k, v in sorted(divisors.items(), key=lambda item: item[1]['number'])}
    return divisors

def getPeriod(n: int, base: int) -> int:
    if n == 1:
        return 1
    reminder = 1
    p = 1
    while True:
        reminder = (reminder * base) % n
        if reminder == 1:
            break
        p = p + 1
    return p

def getDivisorsOfPeriod(n: int, base: int):
    period = getPeriod(n, base)
    divs = divisors(n)
    out = []
    for div in divs:
        if getPeriod(div, base) != period:
            continue
        out.append(div)
    return out

def printDivisors():
    if len(sys.argv) != 3:
        print(f'Syntax: python utils.py <n> <base>')
        return

    n = int(sys.argv[1])
    base = int(sys.argv[2])
    divs = divisors(n)
    for div in divs:
        print(div)
    print(f'num divisors: {len(divs)}')
    print(f'period: {getPeriod(n, base)}')

def gcd(a: int, b: int) -> int:
    """Compute the greatest common divisor of a and b."""
    while b:
        a, b = b, a % b
    return a

def reduce_rational(m:int, n:int) -> tuple[int, int]:
    """Reduce a rational number m/n to its simplest form."""
    if n == 0:
        raise ValueError("Denominator cannot be zero.")
    if m == 0:
        return (0, 1)  # Return 0 as a rational number
    divisor = gcd(abs(m), abs(n))
    return (m // divisor, n // divisor) if n > 0 else (-m // divisor, -n // divisor)


if __name__ == '__main__':
    printDivisors()

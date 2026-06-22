from math import inf, floor
from decimal import Decimal
from typing import Tuple
from mathparse import mathparse

DEFAULT_ITERS = 5000

def estimate_irrational(a: Decimal, end: int, start: int = 1) -> tuple:
    d_best = inf
    digits_best = 0
    
    for k in range(start, end):
        b = k * a
        c = (a * round(b)) / b
        d = abs(c - a)
        digits = num_correct_digits(c, a)
        
        if d < d_best and digits > digits_best:
            num = round(b)
            denom = k
            d_best = d
            digits_best = digits
    
    return (num, denom, digits_best, d_best)

def num_correct_digits(approx: Decimal, num: Decimal) -> int:
    a = approx
    b = num
    digits = 0
    
    while True:
        if floor(a) == floor(b) and a != 0 and b != 0:
            digits += 1
            a = 10 * (a - floor(a))
            b = 10 * (b - floor(b))
        else:
            return digits

def print_fraction(frac: Tuple[int, int, int, Decimal], val: Decimal) -> str:
    try:
        print(f"Value (Decimal):     {val}")
        print(f"Estimate (Fraction): {frac[0]} / {frac[1]}\n")

        print("Number of Correct Digits:", frac[2])
        print("Overall Error:", abs(frac[3]))
    except ValueError:
        print("Invalid fraction!")
        
if __name__ == "__main__":
    num_in = input("Input your number, or a mathematical expression: ").strip()
    iters_in = input("How many iterations would you like to estimate? (Default: 5000) ").strip()
    
    num: Decimal = Decimal(mathparse.parse(num_in, language="ENG"))
    iters: int = int(iters_in) if iters_in.isnumeric() else DEFAULT_ITERS
    res = estimate_irrational(num, iters)
    
    print_fraction(res, num)
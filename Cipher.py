from __future__ import annotations
from typing import Dict, List, Tuple
from sys import argv
import random

"""
GOALS OF THIS PROJECT:
  - Implement a two-way encoding/decoding scheme that reduces all messages to numeric strings
  - Messages can only be decoded if sender and receiver have a shared secret string
  - Messages cannot easily be recovered by brute-forcing secrets
  - Messages encoded with similar secrets do not appear similar
"""

allowed_chars: List[str] = list("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_=+ []:;'\",<.>?/`~")

class Cipher:
    secret_text: str
    secret_numeric: str = ""
    char_lookup_table: Dict[str, int] = {}
    reverse_lookup_table: Dict[int, str] = {}
    modifier: Modifier

    def __init__(self, secret: str):
        self.secret_text = secret
        self.secret_numeric = ""
        self.modifier = Modifier()

        # Set random seed and initialize scrambled char lookup table
        random.seed(secret)
        self.initialize_lookup_tables()

        # Initialize numeric secret
        self.initialize_numeric_secret()

        # Initialize modifier
        self.initialize_modifier()

    def initialize_lookup_tables(self):
        scrambled_chars = allowed_chars.copy()
        random.shuffle(scrambled_chars)
        self.char_lookup_table = {char: i for i, char in enumerate(scrambled_chars)}
        self.reverse_lookup_table = {i: char for i, char in enumerate(scrambled_chars)}

    def initialize_numeric_secret(self):
        for char in self.secret_text:
            num = str(self.char_lookup_table[char])
            self.secret_numeric += num

    def initialize_modifier(self):
        self.modifier.initialize_modifications(self.secret_numeric)

    def get_salt_positions(self, n: int, string_len: int) -> List[int]:
        digits = self.secret_numeric * ((n * 2 // len(self.secret_numeric)) + 1)
        positions = []
        i = 0
        for _ in range(n):
            # Use enough digits to represent string_len
            width = len(str(string_len)) if string_len > 0 else 1
            raw = int(digits[i:i + width])
            positions.append(raw % (string_len + 1))
            i += width
        return positions


class Cipher_Encoder(Cipher):
    input_text: str
    input_numeric: str = ""
    digit_length_salt: List[int] = []

    def __init__(self, input: str, secret: str):
        if len(input) < len(secret):
            raise ValueError("Input must be longer than secret")

        self.input_text = input
        self.input_numeric = ""
        self.digit_length_salt = []

        super().__init__(secret)

        # Initialize numeric string and salt
        self.initialize_numeric_input()

    def initialize_numeric_input(self):
        for char in self.input_text:
            num = str(self.char_lookup_table[char])
            self.input_numeric += num
            self.digit_length_salt.append(len(num))

    def apply_salt(self, encoded: str) -> str:
        chars = list(encoded)
        n = len(self.digit_length_salt)
        positions = self.get_salt_positions(n, len(chars))

        for i in sorted(range(n), key=lambda i: positions[i]):
            chars.insert(positions[i], str(self.digit_length_salt[i]))

        return "".join(chars)

    def encode(self) -> str:
        salted = self.apply_salt(self.input_numeric)
        encoded = self.modifier.apply_modifications(salted)
        last_chars = str(len(self.digit_length_salt))
        return encoded + "_" + last_chars


class Cipher_Decoder(Cipher):
    encoded_numeric: str
    digit_length_salt: List[int] = []
    last_char: str

    def __init__(self, encoded: str, secret: str):
        super().__init__(secret)
        self.initialize_last_char(encoded)
    
    def initialize_last_char(self, encoded: str):
        self.encoded_numeric, self.last_char = encoded.rsplit("_", 1)

    def remove_salt(self, salted: str) -> Tuple[str, List[int]]:
        n = int(self.last_char)
        chars = list(salted)

        # string_len is the length after all salt is removed
        salt_len = n
        string_len = len(chars) - salt_len
        positions = self.get_salt_positions(n, string_len)

        salt = [0] * n
        for i in reversed(sorted(range(n), key=lambda i: positions[i])):
            salt[i] = int(chars.pop(positions[i]))

        unsalted = "".join(chars)
        return unsalted, salt

    def numeric_to_text(self, numeric: str) -> str:
        i = 0
        res = ""
        for d in self.digit_length_salt:
            try:
                num = int(numeric[i:i+d])
                i += d
                res += self.reverse_lookup_table[num]
            except Exception:
                res += "?"
        return res

    def decode(self) -> str:
        # Reverse modifications
        salted = self.modifier.reverse_modifications(self.encoded_numeric)
        
        # Remove salt from encoded text
        unsalted, salt = self.remove_salt(salted)
        self.digit_length_salt = salt
        
        # Numeric
        decoded_text = self.numeric_to_text(unsalted)
        return decoded_text


class Modifier:
    modifications: List[function]
    modification_order: List[int]

    def __init__(self):
        pass

    def initialize_modifications(self, secret_numeric: str):
        # Initialize modifications
        self.modifications = [self.modifier_lookup_table[int(char)] for char in secret_numeric]

        # Initialize modification order
        self.modification_order = list(range(len(secret_numeric)))
        random.shuffle(self.modification_order)

    def apply_modifications(self, str: str) -> str:
        res = str
        for i in self.modification_order:
            modifier = self.modifications[i]
            res = modifier(res, reverse=False)
        return res

    def reverse_modifications(self, str: str) -> str:
        res = str
        for i in self.modification_order[::-1]:
            modifier = self.modifications[i]
            res = modifier(res, reverse=True)
        return res

    def modify_0(s: str, reverse=False) -> str:
        # Reverse the string
        if not reverse:
            return s[::-1]
        else:
            return s[::-1]

    def modify_1(s: str, reverse=False) -> str:
        # Add 1 to each digit (mod 10)
        if not reverse:
            return "".join(str((int(c) + 1) % 10) for c in s)
        else:
            return "".join(str((int(c) - 1) % 10) for c in s)

    def modify_2(s: str, reverse=False) -> str:
        # Swap each adjacent pair of digits (1234 -> 2143)
        chars = list(s)
        for i in range(0, len(chars) - 1, 2):
            chars[i], chars[i+1] = chars[i+1], chars[i]
        if not reverse:
            return "".join(chars)
        else:
            return "".join(chars)

    def modify_3(s: str, reverse=False) -> str:
        # Interleave first and second halves (abcdef -> adbecf)
        n = len(s)
        mid = n // 2
        if not reverse:
            first, second = s[:mid], s[mid:2*mid]
            return "".join(a + b for a, b in zip(first, second)) + s[2*mid:]
        else:
            interleaved, tail = s[:2*mid], s[2*mid:]
            return interleaved[0::2] + interleaved[1::2] + tail

    def modify_4(s: str, reverse=False) -> str:
        # Add each digit's index to itself (mod 10)
        if not reverse:
            return "".join(str((int(c) + i) % 10) for i, c in enumerate(s))
        else:
            return "".join(str((int(c) - i) % 10) for i, c in enumerate(s))

    def modify_5(s: str, reverse=False) -> str:
        # Rotate digits left by len//2
        n = len(s)
        mid = n // 2
        if not reverse:
            return s[mid:] + s[:mid]
        else:
            return s[n - mid:] + s[:n - mid]

    def modify_6(s: str, reverse=False) -> str:
        # Each digit absorbs its left neighbour (mod 10)
        chars = list(s)
        if not reverse:
            for i in range(1, len(chars)):
                chars[i] = str((int(chars[i]) + int(chars[i-1])) % 10)
        else:
            for i in range(len(chars) - 1, 0, -1):
                chars[i] = str((int(chars[i]) - int(chars[i-1])) % 10)
        return "".join(chars)

    def modify_7(s: str, reverse=False) -> str:
        # Complement each digit (d -> 9 - d)
        if not reverse:
            return "".join(str(9 - int(c)) for c in s)
        else:
            return "".join(str(9 - int(c)) for c in s)

    def modify_8(s: str, reverse=False) -> str:
        # Swap first and last quarters
        n = len(s)
        q = n // 4
        if not reverse:
            return s[3*q:4*q] + s[q:3*q] + s[0:q] + s[4*q:]
        else:
            return s[3*q:4*q] + s[q:3*q] + s[0:q] + s[4*q:]

    def modify_9(s: str, reverse=False) -> str:
        # Shift each digit by its distance from the center (mod 10)
        n = len(s)
        mid = n / 2
        if not reverse:
            return "".join(str((int(c) + int(abs(i - mid))) % 10) for i, c in enumerate(s))
        else:
            return "".join(str((int(c) - int(abs(i - mid))) % 10) for i, c in enumerate(s))

    modifier_lookup_table: Dict[int, function] = {
        0: modify_0,
        1: modify_1,
        2: modify_2,
        3: modify_3,
        4: modify_4,
        5: modify_5,
        6: modify_6,
        7: modify_7,
        8: modify_8,
        9: modify_9,
    }


def warn_improper_args(code: int = 1):
    print("Usage: python Cipher.py [encode|decode] [message] [secret]")
    print()
    exit(code)

if __name__ == "__main__":
    if len(argv) != 4:
        warn_improper_args()

    operation = argv[1].lower().strip()
    message = argv[2]
    secret = argv[3]

    if operation not in ["encode", "decode"]:
        warn_improper_args()

    if operation == "encode":
        encoder = Cipher_Encoder(message, secret)
        encoded_text = encoder.encode()
        print(encoded_text)
        exit(0)

    if operation == "decode":
        decoder = Cipher_Decoder(message, secret)
        decoded_text = decoder.decode()
        print(decoded_text)
        exit(0)
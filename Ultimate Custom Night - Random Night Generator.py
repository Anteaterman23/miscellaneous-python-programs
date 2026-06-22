import os
import random
from math import inf

ANIMATRONICS = ["Freddy", "Bonnie", "Chica", "Foxy", "Toy Freddy", "Toy Bonnie", "Toy Chica", "Mangle", "BB", "JJ", "Withered Chica", "Withered Bonnie", "Marionette", "Golden Freddy", "Springtrap", "Phantom Mangle", "Phantom Freddy", "Phantom BB", "Nightmare Freddy", "Nightmare Bonnie", "Nightmare Fredbear", "Nightmare", "Jack-O-Chica", "Nightmare Mangle",
                "Nightmarionette", "Nightmare BB", "Old Man Consequences", "Circus Baby", "Ballora", "Funtime Foxy", "Ennard", "Trash Gang", "Helpy", "Happy Frog", "Mr. Hippo", "Pigpatch", "Nedd Bear", "Orville", "Rockstar Freddy", "Rockstar Bonnie", "Rockstar Chica", "Rockstar Foxy", "Music Man", "El Chip", "Funtime Chica", "Molten Freddy", "Scrap Baby", "Afton", "Lefty", "Phone Guy"]

BOLD = "\033[1m"
UNDERLINE = "\033[4m"
RESET = "\033[0m"

MAX_RETRIES = 100

##############################################


def clear_screen():
    if os.name == 'nt':  # For Windows
        _ = os.system('cls')
    else:  # For macOS and Linux
        _ = os.system('clear')


def input_parameter(param_name: str, min: int, max: int):
    q = f"Input {param_name} between {min} and {max} (Leave blank to randomize): "

    while True:
        clear_screen()
        response = input(q).strip()

        if not response:
            return random.randint(min, max)

        try:
            p = int(response)
            if p < min or p > max:
                raise ValueError
            elif param_name == "Number of Points" and p % 10 != 0:
                raise ValueError
            else:
                break
        except ValueError:
            continue

    return p


def setup_night(points: int, num_animatronics: int, max_difficulty: int, night_num: int):
    # Set all animatronic difficulties to 0 by default
    animatronic_difficulties = {a: 0 for a in ANIMATRONICS}

    # Pick a random collection of animatronics for the night
    active_animatronics = random.sample(ANIMATRONICS, num_animatronics)

    # Iterate through until all difficulty points have been used
    for _ in range(int(points/10)):
        a_diff = float(inf)

        # Ensure that we don't pick an animatronic whose difficulty is too high
        # Timeout and return if too many attempts
        attempts = 0
        should_break = False
        while a_diff >= max_difficulty:
            a = random.choice(active_animatronics)
            a_diff = animatronic_difficulties[a]
            attempts += 1

            if attempts > MAX_RETRIES:
                should_break = True
                break

        if should_break:
            break

        # Once one is picked, increase its difficulty by one
        animatronic_difficulties[a] += 1

    return print_night(animatronic_difficulties, night_num)


def print_night(animatronic_difficulties: dict[str, int], night_num: int):
    # Discard animatronics whose difficulty = 0
    final_animatronics = {k: v for k, v in animatronic_difficulties.items() if v > 0}

    # Add animatronics and difficulties to final string
    res = f"{BOLD}{UNDERLINE}NIGHT {night_num}:{RESET}\n\n"
    for a, a_diff in final_animatronics.items():
        res += f"{a}: {BOLD}{a_diff}{RESET}\n"

    return res

##############################################


if __name__ == "__main__":
    night_number = input_parameter("Night Number", 1, 5)
    points = input_parameter("Number of Points", 0, 10000)
    num_animatronics = input_parameter("Number of Animatronics", 0, 50)
    max_difficulty = input_parameter("Max Difficulty", 0, 20)

    clear_screen()
    print(setup_night(points, num_animatronics, max_difficulty, night_number))

import random

async def attempt():
    random_number = random.randint(0, 10)

    if random_number > 6:
        caught = True
        escaped = False
        return caught, escaped
    else:
        caught = False
        random_number = random.randint(0, 1)
        if random_number == 0:
            escaped = True
        else:
            caught = False
            escaped = False
        return caught, escaped

def calculate_level(thrown, catches, unique_catches):
    total_score = thrown * 5 + (catches - unique_catches) * 10 + unique_catches * 25
    level = total_score // 100

    return level, total_score

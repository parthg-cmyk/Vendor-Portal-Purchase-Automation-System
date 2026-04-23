def rating_stars(rating):
    try:
        rating = int(round(float(rating or 0)))
    except:
        rating = 0

    filled = "★" * rating
    empty = "☆" * (5 - rating)

    return filled + empty
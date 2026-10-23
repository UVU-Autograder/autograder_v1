"""Product Rating Analyzer.

Uses functional programming features in Python: map, filter, reduce, lambda,
and comprehensions to analyze product reviews.
"""

from functools import reduce


def generate_recommendation_flags(ratings):
    """Return a list of Boolean recommendation flags using list comprehension."""
    # List comprehension to generate Boolean flags
    return [rating >= 4 for rating in ratings]


def rating_summary(ratings):
    """Return a dictionary comprehension mapping ratings 1-5 to counts."""
    # Dictionary comprehension counting each rating 1-5
    return {rating: ratings.count(rating) for rating in range(1, 6)}


def main():
    # Review scores (1 to 5)
    ratings = [4, 5, 2, 3, 5, 1, 4, 3, 5, 2, 4]

    # Use map() with a lambda to convert numeric rating to description
    desc_map = {5: "Excellent", 4: "Good", 3: "Average", 2: "Poor", 1: "Terrible"}
    descriptions = list(map(lambda r: desc_map.get(r, "Unknown"), ratings))

    # Use filter() with a lambda to extract positive ratings (4 or 5)
    positive_ratings = list(filter(lambda r: r >= 4, ratings))

    # Use reduce() with a lambda to compute total and average rating
    total = reduce(lambda acc, r: acc + r, ratings, 0)
    avg_rating = total / len(ratings) if ratings else 0.0

    # Call comprehension functions
    flags = generate_recommendation_flags(ratings)
    summary = rating_summary(ratings)

    # Print results
    print(f"Original Ratings: {ratings}")
    print(f"Descriptions: {descriptions}")
    print(f"Positive Ratings: {positive_ratings}")
    print(f"Average Rating: {avg_rating:.2f}")
    print(f"Recommendation Flags: {flags}")
    print(f"Rating Summary: {summary}")


if __name__ == "__main__":
    main()

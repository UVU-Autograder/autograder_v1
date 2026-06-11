def add_numbers(a, b):
    return a + b


def reverse_words(text):
    return " ".join(word[::-1] for word in text.split(" "))


def count_vowels(text):
    vowels = set("aeiou")
    return sum(1 for character in text.lower() if character in vowels)

# Module 2: Lab 3 - Type Hinting and Encapsulation

## Objectives
In this lab, you will:
- Add type hints to a Python class constructor and method
- Apply encapsulation using `_` and `__`, and understand their differences
- Implement getter and setter methods to safely access and modify private attributes

## Starter Code
You’re provided with a basic `YouTubeChannel` class that uses public attributes and a simple `__str__()` method. Your task is to refactor this code to use type hints and encapsulation.

```python
class YouTubeChannel:
    def __init__(self, name="", video_count=0):
        '''
        name: the channel title  
        video_count: number of videos uploaded to this channel  
        '''
        self.name = name
        self.video_count = video_count

    def __str__(self):
        return f"Channel: {self.name}, Videos: {self.video_count}"
```

## Part 1 – Add Type Hints (20 points)
Update the following with appropriate type hints:

1. **The constructor:**
   - `name: str`
   - `video_count: int`
2. **The `__str__` method:**
   - Indicate the return type is a `str`
3. Run `mypy` on your code to ensure no type errors.

## Part 2 – Apply Encapsulation (40 points)
Refactor the class to use encapsulation:
1. **(10 points)** Make `name` private using a single underscore (`_name`).
2. **(10 points)** Make `video_count` private using double underscore (`__video_count`).
3. **(10 points)** Update the `__str__` method to access the private attributes correctly.
4. **(20 points)** Add getter and setter methods for both attributes:
   - For `video_count`, the setter should ignore negative values.

## Part 3 – Reflection and Main Method Testing (40 points)

### 3.1 Main Method: Test Your Setters and Getters (10 points)
Use the following starter code to test your class:

```python
def main():
    channel = YouTubeChannel("UVUCS1410", 150)
    print(channel)

if __name__ == "__main__":
    main()
```

Expected Output:
```text
Channel: UVUCS1410, Videos: 150
```

Now expand `main()` function to:
- Use getter methods to print `_name` and `__video_count`.
- Use setter methods to modify them and print the updated values.

### 3.2 Reflection Questions (30 points)
Answer the following questions and verify your answers by modifying the `main()` function.

Each question is worth 10 points:
- 5 points for your written answer (in a markdown or PDF file)
- 5 points for verifying your answer in code

1. Can you access `_name` directly using `channel._name` outside the class? Add code in `main()` to check this behavior.
2. Can you access `__video_count` directly using `channel.__video_count`? What exception (if any) is raised?
3. How can you access it using name mangling? Show the syntax and test it in `main()`.

## What to Submit
Submit the following files to Canvas:
- `youtube_channel.py`: your refactored class and updated `main()` method
- `Lab3_reflection.md` or `Lab3_reflection.pdf`: your responses to the reflection questions

Module 2: Lab 3 - Type Hinting and Encapsulation
 
Objectives
In this lab, you will:

Add type hints to a Python class constructor and method

Apply encapsulation using _ and __, and understand their differences

Implement getter and setter methods to safely access and modify private attributes

Starter Code
You’re provided with a basic YouTubeChannel class that uses public attributes and a simple __str__() method. Your task is to refactor this code to use type hints and encapsulation.

class YouTubeChannel:
    def __init__(self, name="", video_count=0):
        '''
        name: the channel title  
        video_count: number of videos uploaded to this channel  
        '''
        self.name = name
        self.video_count = video_count
​
    def __str__(self):
        return f"Channel: {self.name}, Videos: {self.video_count}"
Download youtube_channel.pyDownload Download youtube_channel.py

Part 1 – Add Type Hints (20 points)
Update the following with appropriate type hints:

The constructor:

name: str

video_count: int

The __str__ method:

Indicate the return type is a str

Run mypy on your code to ensure no type errors.

Part 2 – Apply Encapsulation (40 points)
Refactor the class to use encapsulation: (10 points)

Make name private using a single underscore

Make video_count private using double underscore

Update the __str__ method to access the private attributes correctly. (10 points)

Add getter and setter methods for both attributes: (20 points)

For video_count, the setter should ignore negative values

Part 3 – Reflection and Main Method Testing (40 points)
3.1 Main Method: Test Your setters and getters (10 points)
Use the following starter code to test your class:

```def main():
    channel = YouTubeChannel("UVUCS1410", 150)
    print(channel)
​
if __name__ == "__main__":
    main()```
Expected Output:

`Channel: UVUCS1410, Videos: 150`
Now expand main() function to:

Use getter methods to print _name and __video_count

Use setter methods to modify them and print the updated values

3.2 Reflection Questions (30 points)
Answer the following questions and verify your answers by modifying the main() function:

Each question is worth 10 points:

5 points for your written answer (in a markdown or PDF file)

5 points for verifying your answer in code

Can you access _name directly using channel._name outside the class?

Add code in main() to check this behavior.

Can you access __video_count directly using channel.__video_count?

What exception (if any) is raised?

How can you access it using name mangling? Show the syntax and test it in main().

What to Submit
Submit the following files to Canvas:

youtube_channel.py: your refactored class and updated main() method

Lab3_reflection.md or Lab3_reflection.pdf: your responses to the reflection questions
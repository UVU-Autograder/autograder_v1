# Lab 3 Reflection Responses

1. Can you access `_name` directly using `channel._name` outside the class?
   - Yes, single underscore `_name` is a convention indicating protected status, but Python does not strictly enforce private access on `_` attributes.

2. Can you access `__video_count` directly using `channel.__video_count`?
   - No, accessing `channel.__video_count` directly raises an `AttributeError` due to Python's name mangling.

3. How can you access it using name mangling?
   - It can be accessed via `channel._YouTubeChannel__video_count`.

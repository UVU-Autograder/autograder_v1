"""YouTubeChannel Class - Lab 3 Model Solution."""


class YouTubeChannel:
    """Represents a YouTube channel with type hints and encapsulated attributes."""

    def __init__(self, name: str = "", video_count: int = 0) -> None:
        """Initialize channel name and video count."""
        self._name: str = name
        self.__video_count: int = max(0, video_count)

    def __str__(self) -> str:
        """Return formatted string representation of channel."""
        return f"Channel: {self._name}, Videos: {self.__video_count}"

    def get_name(self) -> str:
        """Return the protected channel name."""
        return self._name

    def set_name(self, name: str) -> None:
        """Update channel name."""
        self._name = name

    def get_video_count(self) -> int:
        """Return private video count."""
        return self.__video_count

    def set_video_count(self, count: int) -> None:
        """Update video count, ignoring negative values."""
        if count >= 0:
            self.__video_count = count


def main() -> None:
    """Main testing entrypoint."""
    channel = YouTubeChannel("UVUCS1410", 150)
    print(channel)
    print(f"Name: {channel.get_name()}, Videos: {channel.get_video_count()}")
    channel.set_name("UVU CS Department")
    channel.set_video_count(200)
    print(channel)


if __name__ == "__main__":
    main()

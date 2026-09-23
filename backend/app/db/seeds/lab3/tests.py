"""Autograding test suite for Lab 3: Type Hinting and Encapsulation."""

import inspect

import pytest
from python_autograder_helpers import import_student_modules


@pytest.mark.ag_encapsulation
def test_encapsulation() -> None:
    """Verify _name protected attribute and __video_count private attribute encapsulation."""
    (yt_mod,) = import_student_modules("youtube_channel")
    YouTubeChannel = yt_mod.YouTubeChannel
    ch = YouTubeChannel("Test", 10)

    assert hasattr(ch, "_name"), "YouTubeChannel must have _name attribute"
    assert hasattr(ch, "_YouTubeChannel__video_count") or hasattr(ch, "__video_count"), "YouTubeChannel must have __video_count private attribute"

    # Constructor should not accept negative video count
    ch_neg = YouTubeChannel("Neg", -5)
    priv_count = getattr(ch_neg, "_YouTubeChannel__video_count", getattr(ch_neg, "__video_count", None))
    assert priv_count == 0, "Constructor must not store a negative video count"


@pytest.mark.ag_getters_setters
def test_getters_setters() -> None:
    """Verify getter and setter methods and negative guard for video count."""
    (yt_mod,) = import_student_modules("youtube_channel")
    YouTubeChannel = yt_mod.YouTubeChannel
    ch = YouTubeChannel("Initial", 5)

    assert hasattr(ch, "get_name"), "Missing get_name method"
    assert hasattr(ch, "set_name"), "Missing set_name method"
    assert hasattr(ch, "get_video_count"), "Missing get_video_count method"
    assert hasattr(ch, "set_video_count"), "Missing set_video_count method"

    assert ch.get_name() == "Initial"
    ch.set_name("Updated")
    assert ch.get_name() == "Updated"

    assert ch.get_video_count() == 5
    ch.set_video_count(20)
    assert ch.get_video_count() == 20

    # Negative guard test
    ch.set_video_count(-10)
    assert ch.get_video_count() == 20, "set_video_count should ignore negative values"

    # Zero count test (0 is not negative)
    ch.set_video_count(0)
    assert ch.get_video_count() == 0, "set_video_count(0) should be accepted (0 is not negative)"


@pytest.mark.ag_type_hints
def test_type_hints() -> None:
    """Verify type hint annotations on constructor and __str__ method."""
    (yt_mod,) = import_student_modules("youtube_channel")
    YouTubeChannel = yt_mod.YouTubeChannel

    sig_init = inspect.signature(YouTubeChannel.__init__)
    params = sig_init.parameters
    assert "name" in params and params["name"].annotation != inspect.Parameter.empty, "__init__ name parameter missing type hint"
    assert "video_count" in params and params["video_count"].annotation != inspect.Parameter.empty, "__init__ video_count parameter missing type hint"

    sig_str = inspect.signature(YouTubeChannel.__str__)
    assert sig_str.return_annotation != inspect.Signature.empty, "__str__ missing return type hint"

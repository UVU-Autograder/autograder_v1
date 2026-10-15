"""FERPA scrubbing applied to everything that goes into a model prompt.

Lives in the shared prompt package so training data, eval inputs, and live
sandbox prompts are scrubbed identically -- a model trained on unscrubbed text
and served scrubbed text sees two different distributions.
"""

from app.core.sanitizer import sanitize_code_and_text

__all__ = ["sanitize_code_and_text"]

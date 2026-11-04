import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import MarkdownRenderer, { normalizeMarkdownContent } from "../markdown-renderer";

describe("normalizeMarkdownContent", () => {
  it("removes invisible zero-width spaces and BOMs", () => {
    const input = "Hello\u200BWorld\uFEFF!";
    expect(normalizeMarkdownContent(input)).toBe("HelloWorld!");
  });

  it("removes scraped Canvas download button text", () => {
    const input =
      "Starter code:\nDownload youtube_channel.pyDownload Download youtube_channel.py\nNext section";
    const cleaned = normalizeMarkdownContent(input);
    expect(cleaned).not.toContain("Download youtube_channel.py");
    expect(cleaned).toContain("Starter code:\n\nNext section");
  });

  it("fixes opening code fences with code glued to backticks", () => {
    const input = "```def main():\n    print('hello')\n```";
    const expected = "```python\ndef main():\n    print('hello')\n```";
    expect(normalizeMarkdownContent(input)).toBe(expected);
  });

  it("preserves standard valid language fence tags", () => {
    const input = "```python\ndef main():\n    pass\n```\n```json\n{\"k\": 1}\n```";
    expect(normalizeMarkdownContent(input)).toBe(input);
  });

  it("fixes closing code fences glued to code", () => {
    const input = "```python\ndef main():\n    main()```";
    const expected = "```python\ndef main():\n    main()\n```";
    expect(normalizeMarkdownContent(input)).toBe(expected);
  });
});

describe("MarkdownRenderer Component", () => {
  it("renders headers and paragraphs", () => {
    render(<MarkdownRenderer content={"# Title\n\nParagraph text."} />);
    expect(screen.getByRole("heading", { level: 4, name: "Title" })).toBeDefined();
    expect(screen.getByText("Paragraph text.")).toBeDefined();
  });

  it("recovers and renders glued code fence properly inside a code block", () => {
    const malformed = "```def main():\n    print(123)\n    main()```";
    render(<MarkdownRenderer content={malformed} />);
    // def main(): should be rendered in code, not discarded
    expect(screen.getByText(/def main\(\):/)).toBeDefined();
    expect(screen.getByText(/print\(123\)/)).toBeDefined();
  });
});

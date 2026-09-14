import { describe, it, expect } from "vitest";
import { slugifyKey, slugifySlug, makeUniqueKey } from "../slugify";

describe("slugify utilities", () => {
  describe("slugifyKey", () => {
    it("preserves up to 5 words to prevent unwieldy keys while keeping sufficient context", () => {
      expect(slugifyKey("Part 1: Question 1")).toBe("part_1_question_1");
      expect(slugifyKey("Part 1: Question 2")).toBe("part_1_question_2");
      expect(
        slugifyKey("Code formatting, docstrings, type annotations, and flake8 compliance")
      ).toBe("code_formatting_docstrings_type_annotations");
    });

    it("handles leading numbers by prefixing item_ for backend schema validity", () => {
      expect(slugifyKey("1. Code Formatting")).toBe("item_1_code_formatting");
      expect(slugifyKey("42 Questions")).toBe("item_42_questions");
    });

    it("normalizes unicode characters with accents", () => {
      expect(slugifyKey("Café Documentation")).toBe("cafe_documentation");
    });

    it("handles special characters and extra spaces", () => {
      expect(slugifyKey("  @Special #1 -- Item!!  ")).toBe("special_1_item");
    });

    it("falls back to item for empty inputs", () => {
      expect(slugifyKey("")).toBe("item");
      expect(slugifyKey("   ")).toBe("item");
      expect(slugifyKey("!@#$%^")).toBe("item");
    });

    it("truncates extremely long text at maxChars boundary cleanly", () => {
      const veryLongWord = "supercalifragilisticexpialidociousunbelievablylongword";
      const key = slugifyKey(veryLongWord, 5, 30);
      expect(key.length).toBeLessThanOrEqual(30);
      expect(key.endsWith("_")).toBe(false);
    });
  });

  describe("makeUniqueKey", () => {
    it("returns base key if not in existing keys", () => {
      expect(makeUniqueKey("question", ["item_1", "item_2"])).toBe("question");
    });

    it("appends incrementing suffixes on collisions (e.g. truncated identical prefixes)", () => {
      const existing = ["code_formatting", "code_formatting_2"];
      expect(makeUniqueKey("code_formatting", existing)).toBe("code_formatting_3");
    });

    it("ignores currentKey when updating an existing item", () => {
      const existing = ["question", "part_1"];
      expect(makeUniqueKey("question", existing, "question")).toBe("question");
    });
  });

  describe("slugifySlug", () => {
    it("creates kebab-case URLs with sensible word truncation", () => {
      expect(slugifySlug("Lab 2: Loops and Conditionals")).toBe(
        "lab-2-loops-and-conditionals"
      );
      expect(
        slugifySlug(
          "Assignment 4: Advanced Object Oriented Programming Patterns in Python"
        )
      ).toBe("assignment-4-advanced-object-oriented");
    });
  });
});

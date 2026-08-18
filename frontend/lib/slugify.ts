/**
 * Convert human readable labels into clean, snake_case keys for autograder configs & pytest markers.
 * Truncates to a sensible maximum length (5 words or 48 chars) and ensures a leading alphabetic character
 * conforming to backend validation regex (^[a-z][a-z0-9_]*$).
 * Example: "Main Entrypoint Script!" -> "main_entrypoint_script"
 * Example: "1. Code Style" -> "item_1_code_style"
 */
export function slugifyKey(
  text: string,
  maxWords: number = 5,
  maxChars: number = 48
): string {
  const normalized = text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s_-]/g, "");

  const words = normalized.split(/[\s_-]+/).filter(Boolean);

  if (words.length === 0) return "item";

  const truncatedWords = words.slice(0, maxWords);
  let base = truncatedWords.join("_");

  if (base.length > maxChars) {
    base = base.slice(0, maxChars).replace(/_+$/, "");
  }

  // Ensure key starts with an ASCII letter [a-z] to satisfy backend schema constraints
  if (/^[0-9]/.test(base)) {
    base = `item_${base}`;
    if (base.length > maxChars) {
      base = base.slice(0, maxChars).replace(/_+$/, "");
    }
  }

  return base || "item";
}

/**
 * Ensures a key is unique among existing keys by appending an incrementing suffix (_2, _3, ...) if needed.
 */
export function makeUniqueKey(
  base: string,
  existingKeys: string[],
  currentKey?: string
): string {
  const otherKeys = new Set(existingKeys.filter((k) => k !== currentKey));
  const candidate = base || "item";
  if (!otherKeys.has(candidate)) {
    return candidate;
  }
  let counter = 2;
  while (otherKeys.has(`${candidate}_${counter}`)) {
    counter++;
  }
  return `${candidate}_${counter}`;
}

/**
 * Convert human readable titles into clean, kebab-case slugs for assignment & course URLs.
 * Truncates to a sensible maximum length (5 words or 48 chars) to prevent unwieldy URLs.
 * Example: "Dessert Shop 2!" -> "dessert-shop-2"
 */
export function slugifySlug(
  text: string,
  maxWords: number = 5,
  maxChars: number = 48
): string {
  const normalized = text
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9\s_-]/g, "");

  const words = normalized.split(/[\s_-]+/).filter(Boolean);

  if (words.length === 0) return "assignment";

  const truncatedWords = words.slice(0, maxWords);
  let base = truncatedWords.join("-");

  if (base.length > maxChars) {
    base = base.slice(0, maxChars).replace(/-+$/, "");
  }

  return base || "assignment";
}

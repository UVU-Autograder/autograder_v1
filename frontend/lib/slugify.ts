/**
 * Convert human readable labels into clean, snake_case keys for autograder configs & pytest markers.
 * Example: "Main Entrypoint Script!" -> "main_entrypoint_script"
 */
export function slugifyKey(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[\s-]+/g, "_")
    .replace(/[^a-z0-9_]/g, "")
    .replace(/_+/g, "_")
    .replace(/^_+|_+$/g, "");
}

/**
 * Convert human readable titles into clean, kebab-case slugs for assignment & course URLs.
 * Example: "Dessert Shop 2!" -> "dessert-shop-2"
 */
export function slugifySlug(text: string): string {
  return text
    .toLowerCase()
    .trim()
    .replace(/[\s_]+/g, "-")
    .replace(/[^a-z0-9-]/g, "")
    .replace(/-+/g, "-")
    .replace(/^-+|-+$/g, "");
}

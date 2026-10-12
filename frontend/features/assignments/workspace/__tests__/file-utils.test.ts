import { describe, expect, it } from "vitest";
import JSZip from "jszip";
import {
  checkBundleRequirements,
  createSubmissionBundle,
  dataUrlToBytes,
  isImageFilename,
  languageFromFilename,
  sanitizeFilename,
  validateFilename,
} from "../file-utils";
import type { OpenFile } from "../editor-layout";
import type { Assignment } from "@/features/assignments/types";

describe("sandbox image file helpers", () => {
  it("detects image filenames and languages", () => {
    expect(isImageFilename("sprite.png")).toBe(true);
    expect(isImageFilename("notes.py")).toBe(false);
    expect(languageFromFilename("photo.webp")).toBe("image");
    expect(languageFromFilename("main.py")).toBe("python");
  });

  it("round-trips image bytes through zip bundles", async () => {
    const pngBytes = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
    let binary = "";
    for (const byte of pngBytes) {
      binary += String.fromCharCode(byte);
    }
    const dataUrl = `data:image/png;base64,${btoa(binary)}`;

    const files: Record<string, OpenFile> = {
      "diagram.png": {
        filename: "diagram.png",
        content: dataUrl,
        language: "image",
        category: "workspace",
        kind: "image",
      },
      "main.py": {
        filename: "main.py",
        content: "print('hi')\n",
        language: "python",
        category: "workspace",
        kind: "text",
      },
    };

    const blob = await createSubmissionBundle(files);
    const zip = await JSZip.loadAsync(blob);
    const recovered = await zip.file("diagram.png")?.async("uint8array");
    expect(recovered).toBeTruthy();
    expect(Array.from(recovered!)).toEqual(Array.from(pngBytes));
    expect(await zip.file("main.py")?.async("string")).toBe("print('hi')\n");
  });

  it("decodes data URLs to bytes", () => {
    const bytes = dataUrlToBytes("data:image/png;base64,AQID");
    expect(Array.from(bytes)).toEqual([1, 2, 3]);
  });
});

describe("filename validation and sanitization helpers", () => {
  it("sanitizes filenames stripping traversal prefixes", () => {
    expect(sanitizeFilename("../../solution.py")).toBe("solution.py");
    expect(sanitizeFilename("dir/sub\\file.py")).toBe("dir_sub_file.py");
  });

  it("validates valid filenames", () => {
    const result = validateFilename("solution.py", ["main.py"]);
    expect(result.valid).toBe(true);
    expect(result.error).toBeUndefined();
  });

  it("rejects empty or whitespace-only filenames", () => {
    expect(validateFilename("", []).valid).toBe(false);
    expect(validateFilename("   ", []).valid).toBe(false);
  });

  it("rejects illegal characters and traversal paths", () => {
    expect(validateFilename("bad/name.py", []).valid).toBe(false);
    expect(validateFilename("bad\\name.py", []).valid).toBe(false);
    expect(validateFilename("bad:name.py", []).valid).toBe(false);
    expect(validateFilename("bad*name.py", []).valid).toBe(false);
    expect(validateFilename("..", []).valid).toBe(false);
    expect(validateFilename(".", []).valid).toBe(false);
    expect(validateFilename("../test.py", []).valid).toBe(false);
  });

  it("detects case-insensitive collisions with existing files", () => {
    const existing = ["Main.py", "utils.py"];
    expect(validateFilename("main.py", existing).valid).toBe(false);
    expect(validateFilename("MAIN.PY", existing).valid).toBe(false);
    expect(validateFilename("utils.py", existing).valid).toBe(false);

    // Permitted if renaming to its current name
    expect(validateFilename("Main.py", existing, "Main.py").valid).toBe(true);
    // Unrelated name is permitted
    expect(validateFilename("helper.py", existing).valid).toBe(true);
  });
});

describe("checkBundleRequirements helper", () => {
  const dummyAssignment: Assignment = {
    id: "1",
    course_id: "1",
    title: "Test Assignment",
    sandbox_enabled: true,
    language: "python",
    max_score: 100,
    upload_quota: {
      limit: 10,
      window_seconds: 3600,
      remaining: 10,
      reset_at: "2026-10-06T00:00:00Z",
    },
    description: "Test assignment description",
    accepted_bundle_types: ["zip"],
    max_upload_bytes: 1024 * 1024,
    constraints: [],
    rubric: [],
    rubric_groups: [],
    completion_requirements: [],
    config: {
      bundle: {
        entrypoint: "main.py",
        file_requirements: [
          { label: "Helper Module", paths: ["helper.py"] },
        ],
      },
      scoring_items: [],
    },
  };

  it("flags missing entrypoint and required files", () => {
    const files: Record<string, OpenFile> = {
      "random.py": {
        filename: "random.py",
        content: "pass",
        language: "python",
        category: "workspace",
      },
    };

    const status = checkBundleRequirements(files, dummyAssignment);
    expect(status.hasRequiredEntrypoint).toBe(false);
    expect(status.expectedEntrypoint).toBe("main.py");
    expect(status.missingRequiredFiles).toEqual(["helper.py"]);
  });

  it("detects when all bundle requirements are satisfied", () => {
    const files: Record<string, OpenFile> = {
      "main.py": {
        filename: "main.py",
        content: "print('main')",
        language: "python",
        category: "workspace",
      },
      "helper.py": {
        filename: "helper.py",
        content: "def help(): pass",
        language: "python",
        category: "workspace",
      },
    };

    const status = checkBundleRequirements(files, dummyAssignment);
    expect(status.hasRequiredEntrypoint).toBe(true);
    expect(status.missingRequiredFiles).toEqual([]);
  });

  it("packages renamed files in submission bundle without stale names", async () => {
    // Simulate files state after rename from "draft.py" to "solution.py"
    const files: Record<string, OpenFile> = {
      "solution.py": {
        filename: "solution.py",
        content: "print('renamed')",
        language: "python",
        category: "workspace",
        kind: "text",
      },
    };

    const blob = await createSubmissionBundle(files);
    const zip = await JSZip.loadAsync(blob);
    expect(zip.file("draft.py")).toBeNull();
    const solutionContent = await zip.file("solution.py")?.async("string");
    expect(solutionContent).toBe("print('renamed')");
  });
});


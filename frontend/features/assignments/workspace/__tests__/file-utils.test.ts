import { describe, expect, it } from "vitest";
import JSZip from "jszip";
import {
  createSubmissionBundle,
  dataUrlToBytes,
  isImageFilename,
  languageFromFilename,
} from "../file-utils";
import type { OpenFile } from "../editor-layout";

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

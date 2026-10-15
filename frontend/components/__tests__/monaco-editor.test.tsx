import React from "react";
import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

const loaderMock = vi.hoisted(() => ({ config: vi.fn(), init: vi.fn() }));

vi.mock("@monaco-editor/react", () => ({
  Editor: () => <div data-testid="monaco" />,
  loader: loaderMock,
}));

import MonacoEditor from "../monaco-editor";

describe("MonacoEditor", () => {
  beforeEach(() => {
    loaderMock.init.mockReset();
  });

  it("loads Monaco from this app instead of the CDN", () => {
    expect(loaderMock.config).toHaveBeenCalledWith({ paths: { vs: "/monaco/vs" } });
  });

  it("uses Monaco when it loads", async () => {
    loaderMock.init.mockReturnValue(Promise.resolve({}));
    render(<MonacoEditor defaultValue="print('hi')" />);
    expect(await screen.findByTestId("monaco")).toBeTruthy();
    expect(screen.queryByTestId("editor-fallback")).toBeNull();
  });

  it("falls back to a plain editor that still edits when Monaco cannot load", async () => {
    loaderMock.init.mockReturnValue(Promise.reject(new Error("blocked by network")));
    const onChange = vi.fn();
    render(<MonacoEditor defaultValue="print('hi')" onChange={onChange} />);
    const fallback = (await screen.findByTestId("editor-fallback")) as HTMLTextAreaElement;
    expect(fallback.value).toBe("print('hi')");
    fireEvent.change(fallback, { target: { value: "print('bye')" } });
    expect(onChange).toHaveBeenCalledWith("print('bye')");
  });

  it("keeps read-only files read-only in the fallback", async () => {
    loaderMock.init.mockReturnValue(Promise.reject(new Error("blocked")));
    render(<MonacoEditor defaultValue="tests" options={{ readOnly: true }} />);
    expect(((await screen.findByTestId("editor-fallback")) as HTMLTextAreaElement).readOnly).toBe(true);
  });
});

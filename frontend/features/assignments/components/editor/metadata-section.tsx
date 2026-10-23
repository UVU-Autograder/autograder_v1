"use client";

import React from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { PlusCircleIcon, Trash2Icon, PlusIcon, XIcon } from "lucide-react";
import { useAssignmentEditor } from "./assignment-editor-context";

export function MetadataSection() {
  const {
    title,
    setTitle,
    description,
    setDescription,
    moduleId,
    setModuleId,
    sandboxEnabled,
    setSandboxEnabled,
    language,
    setLanguage,
    courseModules,
    entrypoint,
    setEntrypoint,
    fileRequirements,
    addFileRequirement,
    removeFileRequirement,
    updateFileRequirement,
    updateFileRequirementPath,
    addFileRequirementPath,
    removeFileRequirementPath,
    toggleFileRequirementGlob,
    markDirty,
  } = useAssignmentEditor();

  return (
    <div className="space-y-6">
      {/* Basic General Metadata Card */}
      <Card size="sm" className="gap-1.5 py-3">
        <CardHeader className="px-4 py-0">
          <CardTitle>General Metadata</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4 px-4 py-0">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="space-y-2">
              <Label>Assignment Title *</Label>
              <Input
                value={title}
                onChange={(e) => {
                  setTitle(e.target.value);
                  markDirty();
                }}
                placeholder="e.g. Lab 1: Functions & Control Flow"
              />
            </div>

            <div className="space-y-2">
              <Label>Module</Label>
              <Select
                value={moduleId !== null ? String(moduleId) : "none"}
                onValueChange={(val) => {
                  setModuleId(val === "none" ? null : parseInt(val, 10));
                  markDirty();
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="No Module" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No Module</SelectItem>
                  {courseModules.map((m) => (
                    <SelectItem key={m.id} value={String(m.id)}>
                      {m.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Programming Language</Label>
              <Select
                value={language}
                onValueChange={(val) => {
                  setLanguage(val);
                  markDirty();
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Select language" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="python">Python</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="space-y-2 pt-2 border-t border-border">
            <div className="flex items-center justify-between">
              <Label htmlFor="assignment-description">
                Assignment Description / Instructions (Markdown)
              </Label>
            </div>
            <Textarea
              id="assignment-description"
              value={description}
              onChange={(e) => {
                setDescription(e.target.value);
                markDirty();
              }}
              rows={8}
              placeholder="Enter markdown instructions for the assignment (e.g. ## Overview, specifications, functions to implement)..."
              className="font-mono text-xs"
            />
          </div>

          <div className="flex items-center space-x-2 pt-4 border-t border-border">
            <input
              type="checkbox"
              id="sandbox"
              checked={sandboxEnabled}
              onChange={(e) => {
                setSandboxEnabled(e.target.checked);
                markDirty();
              }}
              className="w-4 h-4 rounded border-input text-primary focus:ring-ring"
            />
            <Label htmlFor="sandbox" className="cursor-pointer pl-0">
              Enable Student Sandbox Access
            </Label>
          </div>
        </CardContent>
      </Card>

      {/* File Requirements Card */}
      <Card size="sm" className="gap-1.5 py-3">
        <CardHeader className="flex flex-row items-center justify-between gap-3 px-4 py-0">
          <CardTitle>File Requirements</CardTitle>
          <Button
            type="button"
            onClick={addFileRequirement}
            variant="outline"
            size="sm"
          >
            <PlusCircleIcon className="w-4 h-4 mr-1.5" /> Add Required File
          </Button>
        </CardHeader>
        <CardContent className="space-y-4 px-4 py-0">
          <div className="space-y-4">
            {fileRequirements.map((req, idx) => {
              const isEntrypoint = Boolean(
                (req.paths && req.paths.includes(entrypoint)) ||
                req.pattern === entrypoint,
              );

              return (
                <div
                  key={idx}
                  className={`relative rounded-lg border p-4 shadow-xs space-y-4 transition-colors ${
                    isEntrypoint
                      ? "border-primary bg-primary/5 dark:bg-primary/10"
                      : "border-border bg-card text-card-foreground"
                  }`}
                >
                  <div className="flex items-center justify-between border-b border-border pb-3">
                    <label className="flex items-center gap-2 cursor-pointer font-semibold text-xs text-foreground">
                      <input
                        type="radio"
                        name="entrypoint_selection"
                        checked={isEntrypoint}
                        onChange={() => {
                          const targetPath =
                            req.paths?.[0] || req.pattern || "";
                          if (targetPath) {
                            setEntrypoint(targetPath);
                            markDirty();
                          }
                        }}
                        className="w-4 h-4 text-primary focus:ring-ring"
                      />
                      <span>Primary Entrypoint</span>
                    </label>
                    <button
                      type="button"
                      aria-label="Remove file requirement"
                      onClick={() => removeFileRequirement(idx)}
                      className="text-muted-foreground hover:text-destructive transition-colors p-1 cursor-pointer"
                    >
                      <Trash2Icon className="w-4 h-4" />
                    </button>
                  </div>

                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <Label className="text-xs text-muted-foreground uppercase">
                        {req.pattern !== undefined && req.pattern !== null
                          ? "Glob Pattern"
                          : "Allowed File Name(s)"}
                      </Label>
                      <label className="flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer select-none">
                        <input
                          type="checkbox"
                          checked={
                            req.pattern !== undefined && req.pattern !== null
                          }
                          onChange={(e) =>
                            toggleFileRequirementGlob(idx, e.target.checked)
                          }
                          className="w-3.5 h-3.5 rounded border-input text-primary focus:ring-ring"
                        />
                        <span>Treat as glob pattern (e.g. *.py, lab?.txt)</span>
                      </label>
                    </div>

                    {req.pattern !== undefined && req.pattern !== null ? (
                      <div className="space-y-1">
                        <Input
                          value={req.pattern}
                          onChange={(e) => {
                            updateFileRequirement(
                              idx,
                              "pattern",
                              e.target.value,
                            );
                            if (isEntrypoint) {
                              setEntrypoint(e.target.value);
                            }
                          }}
                          placeholder="e.g. *.py or **/*.py"
                          className="max-w-md font-mono text-xs"
                        />
                      </div>
                    ) : (
                      <div className="space-y-2">
                        {(req.paths || [""]).map((path, pathIdx) => (
                          <div
                            key={pathIdx}
                            className="flex gap-2 items-center"
                          >
                            <Input
                              value={path}
                              onChange={(e) => {
                                updateFileRequirementPath(
                                  idx,
                                  pathIdx,
                                  e.target.value,
                                );
                                if (isEntrypoint && pathIdx === 0) {
                                  setEntrypoint(e.target.value);
                                }
                              }}
                              placeholder={
                                pathIdx === 0
                                  ? "e.g. main.py"
                                  : "e.g. solution.py"
                              }
                              className="font-mono text-xs max-w-md"
                            />
                            {(req.paths?.length || 0) > 1 && (
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                onClick={() =>
                                  removeFileRequirementPath(idx, pathIdx)
                                }
                              >
                                <XIcon className="w-3.5 h-3.5 text-muted-foreground hover:text-destructive" />
                              </Button>
                            )}
                          </div>
                        ))}

                        <div className="flex flex-wrap items-center gap-4 pt-1">
                          <Button
                            type="button"
                            onClick={() => addFileRequirementPath(idx)}
                            variant="outline"
                            size="sm"
                            className="h-7 text-xs"
                          >
                            <PlusIcon className="w-3 h-3 mr-1" /> Add Alternate
                            File Name
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {fileRequirements.length === 0 && (
              <p className="rounded-lg border border-dashed border-border px-3 py-3 text-center text-xs text-muted-foreground">
                No file requirements yet.
              </p>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

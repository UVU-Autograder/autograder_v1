'use client';

import { useState, useEffect } from "react";
import Link from "next/link";
import { ArrowLeftIcon, TerminalSquareIcon, BookOpenIcon } from "lucide-react"
import { Button } from "@/components/ui/button";
import { AppSidebar } from "@/components/app-sidebar"
import { Assignment, ConceptMetadata } from "@/features/assignments/types";
import { useAssignmentFile } from "./assignment-file-context";
import { FileUploadButton } from "./file-upload-button";
import { useBasePath } from "@/lib/view-context";
import { getConceptsMetadata } from "@/features/assignments/api";

function detailsFileContent(assignment: Assignment, conceptMeta: Record<string, ConceptMetadata>) {
    const constraintsList = (assignment.constraints || [])
        .map((c) => `- ${c.label}: ${c.value}`)
        .join("\n") || "None";

    const conceptsList = (assignment.allowed_concepts || []).map(c => {
        const item = conceptMeta[c];
        if (!item) return `- ${c}`;
        const title = item.title;
        const patterns = (item.syntax_patterns || []).map(p => `  - ${p}`).join("\n");
        return `${title}:\n${patterns}`;
    }).join("\n\n") || "No concepts whitelist configured (all concepts allowed).";

    return `Assignment Details: ${assignment.title}
==================================================

Max Score: ${assignment.max_score} points

Submission Rules & Constraints:
${constraintsList}

Allowed Concepts:
-----------------
${conceptsList}
`;
}

export function AssignmentSidebar({
    assignment,
    courseId,
    className
}: {
    assignment: Assignment;
    courseId: string;
    className: string
}) {
    const basePath = useBasePath();
    const { files, openFileByName, uploadFiles, deleteFile } = useAssignmentFile();
    const [conceptMeta, setConceptMeta] = useState<Record<string, ConceptMetadata>>({});

    useEffect(() => {
        getConceptsMetadata().then(setConceptMeta).catch(console.error);
    }, []);

    const workspaceFiles = Object.values(files)
        .filter((file) => file.category === 'workspace')
        .map((file) => file.filename)
        .sort((a, b) => a.localeCompare(b));

    const data = {
        header: (
            <Button variant="ghost" size="sm" className="w-full justify-start" asChild>
                <Link href={basePath === "/sandbox" ? `/sandbox/${courseId}/assignments` : `/staff/courses/${courseId}/assignments`}>
                    <ArrowLeftIcon />
                    Back to assignments
                </Link>
            </Button>
        ),
        navMain: [
            {
                title: "Details",
                url: "#",
                icon: (
                <TerminalSquareIcon
                />
                ),
                isActive: true,
                items: [
                    {
                        title: "details.txt",
                        onClick: () =>
                            openFileByName("details.txt", {
                                content: detailsFileContent(assignment, conceptMeta),
                                language: 'plaintext',
                                category: 'constraint',
                            }),
                    }
                ]
            },
            {
                title: "Files",
                url: "#",
                isActive: true,
                icon: (
                <BookOpenIcon
                />
                ),
                items: workspaceFiles.map((filename) => ({
                    title: filename,
                    onClick: () => openFileByName(filename),
                    onDelete: () => deleteFile(filename),
                })),
                actions: (
                    <FileUploadButton
                        className="w-full"
                        onFilesSelected={uploadFiles}
                    />
                ),
            },
        ]
    }

    return (
        <AppSidebar data={data} className={className} />
    )
}

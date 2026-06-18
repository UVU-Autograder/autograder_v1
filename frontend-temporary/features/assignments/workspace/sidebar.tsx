'use client';

import { TerminalSquareIcon, BotIcon, BookOpenIcon, Settings2Icon } from "lucide-react"
import { AppSidebar } from "@/components/app-sidebar"
import { Assignment, Constraint } from "@/features/assignments/types";
import { useAssignmentFile } from "./assingment-file-context";

function constraintFilename(label: string) {
    return `${label.toLowerCase().replace(/\s+/g, '_').replace(/[^\w.-]/g, '')}.txt`;
}

function constraintFileContent(constraint: Constraint) {
    return `${constraint.label}\n${'='.repeat(constraint.label.length)}\n\n${constraint.value}`;
}

export function AssignmentSidebar({ assignment }: { assignment: Assignment }) {
    const { openFileByName } = useAssignmentFile();

    const data = {
        navMain: [
            {
                title: "Details",
                url: "#",
                icon: (
                <TerminalSquareIcon
                />
                ),
                isActive: true,
            },
            {
                title: "Test Cases",
                url: "#",
                icon: (
                <BotIcon
                />
                ),
                items: [
                {
                    title: "Test Case 1",
                    onClick: () => openFileByName("test_case_1.txt"),
                },
                {
                    title: "Test Case 2",
                    url: "#",
                }
                ],
            },
            {
                title: "Files",
                url: "#",
                isActive: true,
                icon: (
                <BookOpenIcon
                />
                ),
                items: [
                {
                    title: "main.py",
                    onClick: () => openFileByName("main.py"),
                },
                {
                    title: "test_main.py",
                    onClick: () => openFileByName("test_main.py"),
                },
                {
                    title: "test_main1.py",
                    onClick: () => openFileByName("test_main1.py"),
                },
                {
                    title: "test_main2.py",
                    onClick: () => openFileByName("test_main2.py"),
                }
                ],
            },
            {
                title: "Constraints",
                url: "#",
                icon: (
                <Settings2Icon
                />
                ),
                items: assignment.constraints.map((constraint) => ({
                    title: constraint.label,
                    onClick: () =>
                        openFileByName(constraintFilename(constraint.label), {
                            content: constraintFileContent(constraint),
                            language: 'plaintext',
                        }),
                })),
            },
        ]
    }

    return (
        <AppSidebar data={data} />
    )
}
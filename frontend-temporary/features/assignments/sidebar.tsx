'use client';

import { TerminalSquareIcon, BotIcon, BookOpenIcon, Settings2Icon } from "lucide-react"
import { AppSidebar } from "@/components/app-sidebar"
import { useAssignmentFile } from "./assingment-file-context";

export function AssignmentsSidebar() {
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
                    url: "#",
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
                items: [
                {
                    title: "No Bubble Sort",
                    url: "#",
                },
                ],
            },
        ]
    }

    return (
        <AppSidebar data={data} />
    )
}
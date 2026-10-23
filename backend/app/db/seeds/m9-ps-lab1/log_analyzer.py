"""Module 9 Problem Solving Lab 1: Log Line Analyzer."""


def analyze_logs(input_filename: str = "server_logs.txt", output_filename: str = "log_summary.txt") -> None:
    """Read server logs, count severity levels, find longest message, and write summary."""
    counts = {}
    longest_message = ""

    with open(input_filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or "|" not in line:
                continue
            parts = line.split("|")
            severity = parts[0].strip()
            message = parts[1].strip()

            counts[severity] = counts.get(severity, 0) + 1

            if len(message) > len(longest_message):
                longest_message = message

    with open(output_filename, "w", encoding="utf-8") as out:
        out.write("Log Summary\n")
        for sev, count in counts.items():
            out.write(f"{sev}: {count}\n")
        out.write(f"\nLongest message: {longest_message}\n")


def main() -> None:
    analyze_logs()
    print("Log analysis complete. Results saved to log_summary.txt.")


if __name__ == "__main__":
    main()

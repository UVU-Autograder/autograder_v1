export function getFile(filename: string) {
    const mockPythonFiles: Record<string, string> = {
      "main.py": `def main():
    print("Hello from main.py!")

if __name__ == "__main__":
    main()
        `,
      "test_main.py":`def say_hello():
    print("Hello, World!")
      
if __name__ == "__main__":
    say_hello()
              `,
      "test_case_1.txt": `Expected input:
    1 2 
Expected output:
    3
      `
    };
    const code = mockPythonFiles[filename] ?? `# ${filename}\n...`;
    return Promise.resolve({ text: () => Promise.resolve(code) });
}
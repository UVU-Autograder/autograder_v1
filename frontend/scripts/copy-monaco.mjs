// Copies Monaco's prebuilt AMD bundle into public/monaco/vs so the editor loads
// from this app instead of cdn.jsdelivr.net. Some networks (campus VPN, strict
// browsers) block the CDN, which left every editor stuck on "Loading...".
// Runs on postinstall and prebuild; public/monaco is gitignored.
import { cpSync, existsSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");

// monaco-editor's "exports" hide package.json from require.resolve, so walk up
// node_modules folders the way Node does.
function findPackageDir(name, start) {
  for (let dir = start; ; dir = dirname(dir)) {
    const candidate = join(dir, "node_modules", name);
    if (existsSync(join(candidate, "package.json"))) return candidate;
    if (dirname(dir) === dir) return null;
  }
}

const pkgDir = findPackageDir("monaco-editor", root);
if (!pkgDir) {
  console.error("copy-monaco: monaco-editor is not installed (npm install)");
  process.exit(1);
}
const { version } = JSON.parse(readFileSync(join(pkgDir, "package.json"), "utf8"));
const source = join(pkgDir, "min", "vs");
const target = join(root, "public", "monaco", "vs");
const stamp = join(root, "public", "monaco", "VERSION");

if (!existsSync(join(source, "loader.js"))) {
  console.error(`copy-monaco: ${source}/loader.js not found; monaco-editor ${version} has no AMD build`);
  process.exit(1);
}
if (existsSync(stamp) && readFileSync(stamp, "utf8").trim() === version && existsSync(join(target, "loader.js"))) {
  process.exit(0);
}
rmSync(join(root, "public", "monaco"), { recursive: true, force: true });
cpSync(source, target, { recursive: true });
writeFileSync(stamp, `${version}\n`);
console.log(`copy-monaco: monaco-editor ${version} -> public/monaco/vs`);

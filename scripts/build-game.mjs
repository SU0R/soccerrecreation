import { cp, mkdir, rm } from "node:fs/promises";
import { existsSync } from "node:fs";
import { spawn } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const root = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const gameBuild = path.join(root, "src", "build", "web");
const dist = path.join(root, "dist");

function run(command, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(command, args, {
      cwd: root,
      stdio: "inherit",
    });
    child.on("exit", (code) => {
      if (code === 0) resolve();
      else reject(new Error(`${command} ${args.join(" ")} exited with ${code}`));
    });
  });
}

await rm(path.join(root, "build"), { recursive: true, force: true });
await rm(path.join(root, "src", "build"), { recursive: true, force: true });
await rm(dist, { recursive: true, force: true });
await run("python", ["-m", "pygbag", "--build", "src/main.py"]);

await mkdir(path.join(dist, "game"), { recursive: true });
await cp(path.join(root, "public"), dist, { recursive: true });

if (!existsSync(gameBuild)) {
  throw new Error(`Expected pygbag output at ${gameBuild}`);
}

await cp(gameBuild, path.join(dist, "game"), { recursive: true });
console.log("Built dist/ for Vercel.");

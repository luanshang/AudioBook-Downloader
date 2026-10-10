// 一键产出三件套：便携版 ZIP + 自定义 EXE 安装器 + MSI 安装包
// 用法：node build/scripts/build-installer.mjs
import { cpSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import { basename, dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

// 本脚本位于 build/scripts/，项目根在其上两级
const root = join(dirname(dirname(fileURLToPath(import.meta.url))), "..");
const pyproject = readFileSync(join(root, "pyproject.toml"), "utf8");
const versionMatch = pyproject.match(/^version\s*=\s*"([^"]+)"/m);
const version = versionMatch?.[1] ?? "0.0.1";
console.log(`版本：${version}`);

const portableDir = join(root, "build", "output", "有声书下载器_便携版");
const portableExe = join(portableDir, "有声书下载器.exe");
const payload = join(root, "build", "installer", "payload.exe");
const issFile = join(root, "build", "packaging", "installer-payload.iss");
const hostRoot = join(root, "build", "installer-host");
const hostManifest = join(hostRoot, "Cargo.toml");
const outputDir = join(root, "build", "output");
const output = join(outputDir, `AudioBook Downloader-v${version}-setup.exe`);
const python = join(root, ".venv", "Scripts", "python.exe");

function run(command, args, cwd = root) {
  console.log(`\n> ${command} ${args.join(" ")}`);
  execFileSync(command, args, { cwd, stdio: "inherit" });
}

// 0) 便携版 + MSI：复用 build_all.py（跳过旧 Inno EXE；便携版缺失时自动生成）
if (!existsSync(python)) {
  console.error(`未找到项目虚拟环境 Python：${python}`);
  process.exit(1);
}
run(python, ["build/packaging/build_all.py", "--skip-exe"]);

// 1) Inno Setup 静默载荷（自定义 EXE 的内核）
if (!existsSync(portableExe)) {
  console.error(
    `便携版不存在：${portableDir}\n请先运行：uv run python build\\scripts\\build_release.py`
  );
  process.exit(1);
}
const isccCandidates = [
  "C:\\Program Files\\Inno Setup 7\\ISCC.exe",
  "C:\\Program Files (x86)\\Inno Setup 7\\ISCC.exe",
  "C:\\Program Files\\Inno Setup 6\\ISCC.exe",
  "C:\\Program Files (x86)\\Inno Setup 6\\ISCC.exe",
];
const iscc = isccCandidates.find((c) => existsSync(c));
if (!iscc) {
  console.error("未找到 ISCC.exe，请安装 Inno Setup: https://jrsoftware.org/isdl.php");
  process.exit(1);
}
run(iscc, [`-DMyAppVersion=${version}`, issFile]);

if (!existsSync(payload)) throw new Error(`载荷未生成：${payload}`);

// 2) Tauri 引导器（嵌入 payload）。cargo 可能不在后台 shell 的 PATH 中。
const cargo = (() => {
  const candidates = ["cargo", join(process.env.HOME || "", ".cargo", "bin", "cargo.exe")];
  for (const c of candidates) {
    try {
      execFileSync(c, ["--version"], { stdio: "ignore" });
      return c;
    } catch {
      /* try next */
    }
  }
  throw new Error("未找到 cargo，请安装 Rust: https://rustup.rs");
})();
mkdirSync(join(hostRoot, "icons"), { recursive: true });
// 图标已由 `npx tauri icon build/installer/icon-source.png --output build/installer-host/icons` 预生成
const hostIcon = join(hostRoot, "icons", "icon.ico");
if (!existsSync(hostIcon)) throw new Error(`引导器图标缺失：${hostIcon}`);
run(cargo, ["build", "--release", "--manifest-path", hostManifest]);
const hostExe = join(hostRoot, "target", "release", "abk-installer.exe");
if (!existsSync(hostExe)) throw new Error(`引导器未生成：${hostExe}`);

mkdirSync(outputDir, { recursive: true });
cpSync(hostExe, output, { force: true });
console.log(`\n自定义安装器已生成：${output}`);

// 重新生成 setup.exe 的 sha256（build_all.py 阶段算的是旧文件）
const digest = createHash("sha256").update(readFileSync(output)).digest("hex");
const sidecar = `${output}.sha256`;
writeFileSync(sidecar, `${digest}  ${basename(output)}\n`, "ascii");
console.log(`校验文件已更新：${sidecar}`);

import { createReadStream, existsSync, statSync } from "node:fs";
import { createServer } from "node:http";
import { extname, join, normalize, resolve } from "node:path";

const root = resolve("dist");
const port = Number(process.env.PORT || 4174);

const mime = {
  ".apk": "application/vnd.android.package-archive",
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".png": "image/png",
  ".svg": "image/svg+xml",
};

function sendHeaders(res, file) {
  res.setHeader("Cross-Origin-Opener-Policy", "same-origin");
  res.setHeader("Cross-Origin-Embedder-Policy", "credentialless");
  res.setHeader("Cross-Origin-Resource-Policy", "cross-origin");
  res.setHeader("Origin-Agent-Cluster", "?1");
  res.setHeader("Access-Control-Allow-Origin", "*");
  res.setHeader("Content-Type", mime[extname(file)] || "application/octet-stream");
}

createServer((req, res) => {
  const url = new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);
  let pathname = decodeURIComponent(url.pathname);
  if (pathname.endsWith("/")) pathname += "index.html";
  let file = normalize(join(root, pathname));

  if (!file.startsWith(root)) {
    res.writeHead(403).end("Forbidden");
    return;
  }

  if (!existsSync(file) && !extname(file)) {
    const cleanUrlFile = `${file}.html`;
    if (existsSync(cleanUrlFile)) file = cleanUrlFile;
  }

  if (!existsSync(file) || !statSync(file).isFile()) {
    res.writeHead(404).end("Not found");
    return;
  }

  sendHeaders(res, file);
  res.setHeader("Content-Length", statSync(file).size);
  res.writeHead(200);
  createReadStream(file).pipe(res);
}).listen(port, () => {
  console.log(`Serving ${root} at http://localhost:${port}`);
});

/*
 * Zero-dependency static file server for the built SPA.
 *
 * Why this exists: the serverless runtime has no reliable npm egress at cold
 * start, so `npx serve` (which downloads the `serve` package on demand) fails
 * and the instance never becomes healthy. This server uses only Node built-ins,
 * is bundled into the deployment artifact, and needs no network at runtime.
 *
 * It serves files from its own directory (the built `dist/`) with SPA fallback
 * to index.html, and listens on the platform-injected port.
 */
const http = require('http');
const fs = require('fs');
const path = require('path');

const ROOT = __dirname;
const PORT =
  process.env._BYTEFAAS_RUNTIME_PORT ||
  process.env.PORT ||
  process.env.BYTEFAAS_FUNC_PORT ||
  8000;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.ico': 'image/x-icon',
  '.woff': 'font/woff',
  '.woff2': 'font/woff2',
  '.ttf': 'font/ttf',
  '.map': 'application/json; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.webp': 'image/webp',
};

function send(res, status, body, headers) {
  res.writeHead(status, headers || {});
  res.end(body);
}

function serveFile(res, filePath) {
  const ext = path.extname(filePath).toLowerCase();
  const type = MIME[ext] || 'application/octet-stream';
  const stream = fs.createReadStream(filePath);
  stream.on('open', () => {
    res.writeHead(200, { 'Content-Type': type });
    stream.pipe(res);
  });
  stream.on('error', () => send(res, 500, 'Internal Server Error'));
}

const server = http.createServer((req, res) => {
  try {
    // Lightweight health endpoint (some platforms probe "/").
    let urlPath = decodeURIComponent((req.url || '/').split('?')[0]);
    if (urlPath.includes('..')) {
      return send(res, 400, 'Bad Request');
    }
    if (urlPath === '/') urlPath = '/index.html';

    let filePath = path.join(ROOT, urlPath);

    fs.stat(filePath, (err, stat) => {
      if (!err && stat.isFile()) {
        return serveFile(res, filePath);
      }
      if (!err && stat.isDirectory()) {
        const indexPath = path.join(filePath, 'index.html');
        if (fs.existsSync(indexPath)) return serveFile(res, indexPath);
      }
      // SPA fallback: serve index.html for client-side routes.
      const indexHtml = path.join(ROOT, 'index.html');
      if (fs.existsSync(indexHtml)) return serveFile(res, indexHtml);
      return send(res, 404, 'Not Found');
    });
  } catch (e) {
    send(res, 500, 'Internal Server Error');
  }
});

server.listen(PORT, '0.0.0.0', () => {
  // eslint-disable-next-line no-console
  console.log(`[static-server] serving ${ROOT} on 0.0.0.0:${PORT}`);
});

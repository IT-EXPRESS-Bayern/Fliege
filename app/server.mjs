import { createServer } from 'node:http';
import { createReadStream } from 'node:fs';
import { stat } from 'node:fs/promises';
import { dirname, extname, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';
import { GRAPH_FILES, inspectBrainCandidates, inspectBrainGraph } from './status.mjs';

const root = dirname(fileURLToPath(import.meta.url));
const brainRoot = resolve(root, '../brain');
const graphRoot = resolve(brainRoot, 'graph-original-v783');
const port = Number(process.env.PORT || 4173);
let cachedCandidates = null;
const mime = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.txt': 'text/plain; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.md': 'text/markdown; charset=utf-8',
};

function json(response, status, value) {
  const body = JSON.stringify(value);
  response.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(body),
    'Cache-Control': 'no-store',
  }).end(body);
}

const server = createServer(async (request, response) => {
  if (request.method !== 'GET' && request.method !== 'HEAD') {
    response.writeHead(405).end();
    return;
  }
  let pathname;
  try {
    pathname = decodeURIComponent(new URL(request.url, 'http://localhost').pathname);
  } catch {
    response.writeHead(400).end();
    return;
  }
  if (pathname === '/api/brain-status') {
    json(response, 200, await inspectBrainGraph(graphRoot));
    return;
  }
  if (pathname === '/api/brain-candidates') {
    const status = await inspectBrainGraph(graphRoot);
    if (status.state !== 'ready') {
      json(response, 503, { reason: 'Graph noch nicht bereit' });
      return;
    }
    try {
      cachedCandidates ||= await inspectBrainCandidates(graphRoot);
      json(response, 200, { dataset: status.dataset, ...cachedCandidates });
    } catch {
      json(response, 500, { reason: 'Annotationen nicht lesbar' });
    }
    return;
  }
  if (pathname === '/api/data-status') {
    try {
      const upstream = await fetch('http://127.0.0.1:8765/api/status', {
        cache: 'no-store', signal: AbortSignal.timeout(2000),
      });
      if (!upstream.ok) throw new Error(`HTTP ${upstream.status}`);
      json(response, 200, await upstream.json());
    } catch {
      json(response, 503, { available: false, reason: 'Downloadanzeige nicht erreichbar' });
    }
    return;
  }
  let path;
  if (pathname === '/analysis/report.md') {
    path = resolve(root, '../analysis/report.md');
  } else if (pathname.startsWith('/analysis/')) {
    response.writeHead(404).end('Not found');
    return;
  } else if (['/brain/web.mjs', '/brain/engine.mjs', '/brain/worker.mjs'].includes(pathname)) {
    path = resolve(brainRoot, pathname.slice('/brain/'.length));
  } else {
    const graphMatch = /^\/brain\/graph-original-v783\/([^/]+)$/.exec(pathname);
    if (graphMatch && (GRAPH_FILES.includes(graphMatch[1]) || graphMatch[1] === 'manifest.json')) {
      path = resolve(graphRoot, graphMatch[1]);
    } else if (pathname.startsWith('/brain/')) {
      response.writeHead(404).end('Not found');
      return;
    } else {
      path = resolve(root, `.${pathname === '/' ? '/index.html' : pathname}`);
      if (path !== root && !path.startsWith(root + sep)) {
        response.writeHead(403).end();
        return;
      }
    }
  }
  try {
    const details = await stat(path);
    if (!details.isFile()) throw new Error('not a file');
    response.writeHead(200, {
      'Content-Type': mime[extname(path)] || 'application/octet-stream',
      'Content-Length': details.size,
      'Cache-Control': 'no-cache',
      'X-Content-Type-Options': 'nosniff',
    });
    if (request.method === 'HEAD') response.end();
    else createReadStream(path).pipe(response);
  } catch {
    response.writeHead(404).end('Not found');
  }
});

server.listen(port, '127.0.0.1', () => {
  console.log(`Fliegen-Demonstrator: http://127.0.0.1:${port}`);
});

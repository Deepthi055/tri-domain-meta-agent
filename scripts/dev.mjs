#!/usr/bin/env node
import { spawn } from 'node:child_process';
import http from 'node:http';
import { setTimeout as delay } from 'node:timers/promises';

const backendUrl = process.env.BACKEND_URL || 'http://127.0.0.1:8000/api-status';
const pythonCmd = process.platform === 'win32' ? '.venv\\Scripts\\python.exe' : '.venv/bin/python';
const viteCmd = process.platform === 'win32' ? 'npm.cmd' : 'npm';

let backendChild = null;
let viteChild = null;
let shuttingDown = false;

function stopChildren(signal = 'SIGTERM') {
  if (shuttingDown) return;
  shuttingDown = true;

  if (viteChild && !viteChild.killed) {
    viteChild.kill(signal);
  }

  if (backendChild && !backendChild.killed) {
    backendChild.kill(signal);
  }
}

process.on('SIGINT', () => {
  stopChildren('SIGINT');
  process.exit(0);
});

process.on('SIGTERM', () => {
  stopChildren('SIGTERM');
  process.exit(0);
});

async function isBackendUp() {
  return await new Promise((resolve) => {
    const req = http.get(backendUrl, (res) => {
      res.resume();
      resolve(res.statusCode === 200);
    });

    req.on('error', () => resolve(false));
    req.setTimeout(1000, () => {
      req.destroy();
      resolve(false);
    });
  });
}

async function ensureBackend() {
  for (let attempt = 1; attempt <= 10; attempt += 1) {
    if (await isBackendUp()) {
      console.log('[dev] Backend already available at http://127.0.0.1:8000');
      return null;
    }

    if (attempt === 10) {
      break;
    }

    await delay(1000);
  }

  console.log('[dev] Starting backend on port 8000...');
  backendChild = spawn(
    pythonCmd,
    ['-m', 'uvicorn', 'main:app', '--host', '127.0.0.1', '--port', '8000'],
    {
      cwd: process.cwd(),
      stdio: 'inherit',
      env: { ...process.env, PYTHONUNBUFFERED: '1' },
    },
  );

  backendChild.on('exit', (code) => {
    if (!shuttingDown) {
      console.error(`[dev] Backend exited with code ${code}`);
      process.exit(code ?? 1);
    }
  });

  for (let attempt = 1; attempt <= 20; attempt += 1) {
    if (await isBackendUp()) {
      console.log('[dev] Backend is ready');
      return backendChild;
    }

    await delay(1000);
  }

  throw new Error('Backend did not become ready on port 8000');
}

async function main() {
  try {
    await ensureBackend();
    console.log('[dev] Starting Vite dev server...');
    viteChild = spawn(viteCmd, ['run', 'dev:frontend'], {
      cwd: process.cwd(),
      stdio: 'inherit',
      env: process.env,
      shell: process.platform === 'win32',
    });

    viteChild.on('exit', (code) => {
      stopChildren();
      process.exit(code ?? 0);
    });
  } catch (error) {
    console.error(`[dev] ${error.message}`);
    stopChildren();
    process.exit(1);
  }
}

main();

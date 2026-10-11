import { spawn } from 'node:child_process'
import { existsSync } from 'node:fs'
import { resolve } from 'node:path'

const backendDirectory = resolve('backend')
const pythonPath = process.platform === 'win32'
  ? resolve(backendDirectory, '.venv', 'Scripts', 'python.exe')
  : resolve(backendDirectory, '.venv', 'bin', 'python')

if (!existsSync(pythonPath)) {
  console.error(`Python virtual environment not found at ${pythonPath}`)
  console.error('Create it with: cd backend; python -m venv .venv; pip install -r requirements.txt')
  process.exit(1)
}

const api = spawn(pythonPath, ['manage.py', 'runserver', '127.0.0.1:5001', '--noreload'], {
  cwd: backendDirectory,
  stdio: 'inherit',
})
const vite = spawn(process.execPath, [resolve('node_modules', 'vite', 'bin', 'vite.js')], {
  stdio: 'inherit',
})

let stopping = false
const stop = (code = 0) => {
  if (stopping) return
  stopping = true
  api.kill()
  vite.kill()
  process.exit(code)
}

api.on('exit', (code) => stop(code ?? 1))
vite.on('exit', (code) => stop(code ?? 0))
process.on('SIGINT', () => stop())
process.on('SIGTERM', () => stop())

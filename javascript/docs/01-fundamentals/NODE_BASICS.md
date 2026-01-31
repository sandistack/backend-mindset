# 🟢 NODE.JS BASICS - Fundamental Node.js (Junior → Mid)

Dokumentasi singkat tentang fundamental Node.js yang perlu dipahami sebelum masuk ke Express.

---

## 🎯 Apa itu Node.js?

```
Node.js = JavaScript runtime di server
Bukan framework, bukan bahasa baru

Built on: V8 JavaScript Engine (Chrome)
Package Manager: npm / yarn / pnpm
```

---

## 1️⃣ JUNIOR LEVEL - Setup & Basics

### Install Node.js

```bash
# Via nvm (recommended)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
nvm install --lts
nvm use --lts

# Verify
node --version
npm --version
```

### Initialize Project

```bash
mkdir my-project
cd my-project
npm init -y

# package.json created
```

### Menjalankan File

```bash
# Buat file
echo "console.log('Hello Node.js')" > index.js

# Jalankan
node index.js
```

---

## 2️⃣ Modules System

### CommonJS (Default Node.js)

```javascript
// math.js - Export
const add = (a, b) => a + b;
const subtract = (a, b) => a - b;

module.exports = { add, subtract };
// atau
module.exports.multiply = (a, b) => a * b;

// app.js - Import
const { add, subtract } = require('./math');
const math = require('./math');

console.log(add(2, 3));         // 5
console.log(math.multiply(2, 3)); // 6
```

### ES Modules (Modern Way)

```json
// package.json - tambahkan type
{
  "name": "my-project",
  "type": "module"
}
```

```javascript
// math.js - Export
export const add = (a, b) => a + b;
export const subtract = (a, b) => a - b;
export default { add, subtract };

// app.js - Import
import { add, subtract } from './math.js';
import math from './math.js';

console.log(add(2, 3));
```

### Built-in Modules

```javascript
// File System
const fs = require('fs');
const fsPromises = require('fs').promises;

// Path
const path = require('path');

// HTTP
const http = require('http');

// OS
const os = require('os');

// Events
const EventEmitter = require('events');
```

---

## 3️⃣ Async/Await & Promises

### Callbacks (Old Way)

```javascript
const fs = require('fs');

// ❌ Callback Hell
fs.readFile('file1.txt', (err, data1) => {
  if (err) throw err;
  fs.readFile('file2.txt', (err, data2) => {
    if (err) throw err;
    console.log(data1, data2);
  });
});
```

### Promises

```javascript
const fs = require('fs').promises;

// ✅ Promise Chain
fs.readFile('file1.txt')
  .then(data1 => {
    console.log(data1.toString());
    return fs.readFile('file2.txt');
  })
  .then(data2 => {
    console.log(data2.toString());
  })
  .catch(err => console.error(err));

// Create Promise
const delay = (ms) => new Promise(resolve => setTimeout(resolve, ms));

delay(1000).then(() => console.log('1 second later'));
```

### Async/Await (Modern Way)

```javascript
const fs = require('fs').promises;

// ✅ Async/Await - Clean & Readable
async function readFiles() {
  try {
    const data1 = await fs.readFile('file1.txt');
    const data2 = await fs.readFile('file2.txt');
    console.log(data1.toString(), data2.toString());
  } catch (err) {
    console.error('Error:', err.message);
  }
}

readFiles();

// Parallel execution
async function readFilesParallel() {
  const [data1, data2] = await Promise.all([
    fs.readFile('file1.txt'),
    fs.readFile('file2.txt')
  ]);
  console.log(data1.toString(), data2.toString());
}
```

### Error Handling

```javascript
// Wrapper function
const asyncHandler = (fn) => (req, res, next) => {
  Promise.resolve(fn(req, res, next)).catch(next);
};

// Custom async function with error
async function fetchData(url) {
  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Fetch failed:', error.message);
    throw error; // Re-throw for caller to handle
  }
}
```

---

## 4️⃣ Event Loop (Penting!)

### Konsep Event Loop

```
   ┌───────────────────────────┐
┌─>│         timers            │  setTimeout, setInterval
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │     pending callbacks     │  I/O callbacks
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │       idle, prepare       │  internal use
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │           poll            │  retrieve new I/O events
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
│  │           check           │  setImmediate
│  └─────────────┬─────────────┘
│  ┌─────────────┴─────────────┐
└──┤      close callbacks      │  socket.on('close')
   └───────────────────────────┘
```

### Execution Order

```javascript
console.log('1: Script start');

setTimeout(() => {
  console.log('4: setTimeout');
}, 0);

Promise.resolve().then(() => {
  console.log('3: Promise');
});

console.log('2: Script end');

// Output:
// 1: Script start
// 2: Script end
// 3: Promise (microtask)
// 4: setTimeout (macrotask)
```

### process.nextTick vs setImmediate

```javascript
setImmediate(() => {
  console.log('3: setImmediate');
});

process.nextTick(() => {
  console.log('2: nextTick');
});

console.log('1: sync');

// Output:
// 1: sync
// 2: nextTick (before event loop continues)
// 3: setImmediate (check phase)
```

---

## 5️⃣ Environment Variables

### Using dotenv

```bash
npm install dotenv
```

```javascript
// .env
DATABASE_URL=postgres://localhost:5432/mydb
JWT_SECRET=mysecretkey
PORT=3000
```

```javascript
// config.js
require('dotenv').config();

const config = {
  port: process.env.PORT || 3000,
  dbUrl: process.env.DATABASE_URL,
  jwtSecret: process.env.JWT_SECRET,
  nodeEnv: process.env.NODE_ENV || 'development',
  isDev: process.env.NODE_ENV !== 'production'
};

module.exports = config;
```

```javascript
// app.js
const config = require('./config');

console.log(`Running on port ${config.port}`);
console.log(`Environment: ${config.nodeEnv}`);
```

---

## 6️⃣ File System Operations

### Reading Files

```javascript
const fs = require('fs').promises;
const path = require('path');

// Read file
async function readFile() {
  const filePath = path.join(__dirname, 'data.txt');
  const content = await fs.readFile(filePath, 'utf-8');
  return content;
}

// Read JSON
async function readJSON() {
  const content = await fs.readFile('config.json', 'utf-8');
  return JSON.parse(content);
}

// Read directory
async function listFiles() {
  const files = await fs.readdir('./src');
  return files;
}
```

### Writing Files

```javascript
const fs = require('fs').promises;

// Write file
async function writeFile(filename, content) {
  await fs.writeFile(filename, content, 'utf-8');
}

// Append to file
async function appendToFile(filename, content) {
  await fs.appendFile(filename, content + '\n', 'utf-8');
}

// Write JSON
async function writeJSON(filename, data) {
  await fs.writeFile(filename, JSON.stringify(data, null, 2));
}
```

---

## 7️⃣ Process & Arguments

### Command Line Arguments

```javascript
// node app.js --name=John --age=25

// Basic
console.log(process.argv);
// ['/usr/bin/node', '/path/app.js', '--name=John', '--age=25']

// Parse manually
const args = process.argv.slice(2);
const params = {};
args.forEach(arg => {
  const [key, value] = arg.replace('--', '').split('=');
  params[key] = value;
});
console.log(params); // { name: 'John', age: '25' }
```

### Process Info

```javascript
console.log('PID:', process.pid);
console.log('CWD:', process.cwd());
console.log('Platform:', process.platform);
console.log('Node Version:', process.version);
console.log('Memory:', process.memoryUsage());
```

### Graceful Shutdown

```javascript
// Handle shutdown signals
process.on('SIGINT', () => {
  console.log('Received SIGINT. Shutting down...');
  // Cleanup
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('Received SIGTERM. Shutting down...');
  // Cleanup
  process.exit(0);
});

// Uncaught exception
process.on('uncaughtException', (err) => {
  console.error('Uncaught Exception:', err);
  process.exit(1);
});

// Unhandled rejection
process.on('unhandledRejection', (reason, promise) => {
  console.error('Unhandled Rejection:', reason);
});
```

---

## 📊 Quick Reference

### Module Types

| Type | Extension | Import Syntax |
|------|-----------|---------------|
| CommonJS | .js | `require()` |
| ES Modules | .mjs atau "type": "module" | `import/export` |

### Async Patterns

| Pattern | Use Case |
|---------|----------|
| Callbacks | Legacy, events |
| Promises | Chainable async |
| Async/Await | Modern, readable |

### Common Built-in Modules

| Module | Purpose |
|--------|---------|
| `fs` | File system |
| `path` | File paths |
| `http` | HTTP server |
| `events` | Event emitter |
| `crypto` | Encryption |
| `util` | Utilities |

---

## 💡 Summary

**Yang Perlu Dipahami:**
- ✅ ES Modules (import/export)
- ✅ Async/Await pattern
- ✅ Event Loop basics
- ✅ Environment variables
- ✅ Graceful shutdown

**Selanjutnya:**
→ Express.js untuk web framework (fokus utama)
→ Database dengan Prisma
→ Authentication dengan JWT

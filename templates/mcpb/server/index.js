#!/usr/bin/env node
// Zero-dependency MCP server — NDJSON over stdio (matches SDK wire format).
'use strict';

const { readFileSync } = require('fs');
const { join } = require('path');
const { createInterface } = require('readline');

const config = JSON.parse(readFileSync(join(__dirname, 'config.json'), 'utf-8'));
const instructions = readFileSync(join(__dirname, 'instructions.md'), 'utf-8');
const toolDescription = readFileSync(join(__dirname, 'tool-description.md'), 'utf-8');

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + '\n');
}

async function handleGetJson(id, params) {
  const path = params?.arguments?.path;
  if (!path) {
    send({ jsonrpc: '2.0', id, result: {
      content: [{ type: 'text', text: 'Error: path argument is required' }],
      isError: true,
    }});
    return;
  }
  const url = `${config.base_url}actions/${path}`;
  try {
    const res = await fetch(url);
    if (!res.ok) {
      send({ jsonrpc: '2.0', id, result: {
        content: [{ type: 'text', text: `Error: ${res.status} ${res.statusText} for ${url}` }],
        isError: true,
      }});
      return;
    }
    const data = await res.json();
    send({ jsonrpc: '2.0', id, result: {
      content: [{ type: 'text', text: JSON.stringify(data, null, 2) }],
    }});
  } catch (err) {
    send({ jsonrpc: '2.0', id, result: {
      content: [{ type: 'text', text: `Error fetching ${url}: ${err.message}` }],
      isError: true,
    }});
  }
}

function handleMessage(msg) {
  if (!('id' in msg)) return;

  switch (msg.method) {
    case 'initialize':
      send({ jsonrpc: '2.0', id: msg.id, result: {
        protocolVersion: '2024-11-05',
        capabilities: { tools: {} },
        serverInfo: { name: 'legal-ed-skills-hub', version: '1.0.0' },
        instructions,
      }});
      break;

    case 'ping':
      send({ jsonrpc: '2.0', id: msg.id, result: {} });
      break;

    case 'tools/list':
      send({ jsonrpc: '2.0', id: msg.id, result: { tools: [{
        name: 'getJson',
        description: toolDescription,
        inputSchema: {
          type: 'object',
          properties: {
            path: {
              type: 'string',
              description: "Path relative to the actions root, e.g. 'personas/student.json'",
            },
          },
          required: ['path'],
        },
      }]}});
      break;

    case 'tools/call':
      if (msg.params?.name === 'getJson') {
        handleGetJson(msg.id, msg.params);
      } else {
        send({ jsonrpc: '2.0', id: msg.id, error: {
          code: -32601, message: `Unknown tool: ${msg.params?.name}`,
        }});
      }
      break;

    default:
      send({ jsonrpc: '2.0', id: msg.id, error: {
        code: -32601, message: 'Method not found',
      }});
      break;
  }
}

const rl = createInterface({ input: process.stdin, terminal: false });
rl.on('line', (line) => {
  if (!line.trim()) return;
  try {
    handleMessage(JSON.parse(line));
  } catch (err) {
    process.stderr.write(`Parse error: ${err.message}\n`);
  }
});

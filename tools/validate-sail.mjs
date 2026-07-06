#!/usr/bin/env node
/**
 * validate-sail.mjs
 *
 * Simple Node.js CLI validator for Xebec/SAIL .sail files using JSON Schema.
 *
 * Install:
 *   npm install
 *
 * Usage:
 *   node validate-sail.mjs path/to/model.sail
 *   node validate-sail.mjs path/to/model.sail --schema path/to/sail-architecture.schema.json
 *   node validate-sail.mjs path/to/model.sail --json
 */

import fs from "node:fs";
import path from "node:path";
import process from "node:process";
import Ajv2020 from "ajv/dist/2020.js";

function parseArgs(argv) {
  const args = {
    sailFile: null,
    schemaFile: path.join(path.dirname(new URL(import.meta.url).pathname), "sail-architecture.schema.json"),
    json: false,
  };

  for (let i = 2; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--schema") {
      args.schemaFile = argv[++i];
    } else if (arg === "--json") {
      args.json = true;
    } else if (!args.sailFile) {
      args.sailFile = arg;
    } else {
      throw new Error(`Unexpected argument: ${arg}`);
    }
  }

  if (!args.sailFile) {
    throw new Error("Missing required argument: path to .sail file");
  }
  return args;
}

function loadJson(filePath) {
  try {
    const text = fs.readFileSync(filePath, "utf8").replace(/^\uFEFF/, "");
    return JSON.parse(text);
  } catch (err) {
    throw new Error(`Could not read or parse JSON file ${filePath}: ${err.message}`);
  }
}

function printUsage() {
  console.error(`Usage:
  node validate-sail.mjs path/to/model.sail
  node validate-sail.mjs path/to/model.sail --schema path/to/sail-architecture.schema.json
  node validate-sail.mjs path/to/model.sail --json`);
}

try {
  const args = parseArgs(process.argv);
  const schema = loadJson(args.schemaFile);
  const sailDoc = loadJson(args.sailFile);

  const ajv = new Ajv2020({
    allErrors: true,
    strict: false,
    allowUnionTypes: true,
  });

  const validate = ajv.compile(schema);
  const valid = validate(sailDoc);

  if (valid) {
    const result = {
      valid: true,
      sailFile: args.sailFile,
      schemaFile: args.schemaFile,
      errorCount: 0,
    };
    console.log(args.json ? JSON.stringify(result, null, 2) : `VALID: ${args.sailFile}`);
    process.exit(0);
  }

  const errors = (validate.errors || []).map((e) => ({
    path: e.instancePath || "$",
    message: e.message,
    keyword: e.keyword,
    schemaPath: e.schemaPath,
    params: e.params,
  }));

  const result = {
    valid: false,
    sailFile: args.sailFile,
    schemaFile: args.schemaFile,
    errorCount: errors.length,
    errors,
  };

  if (args.json) {
    console.log(JSON.stringify(result, null, 2));
  } else {
    console.log(`INVALID: ${args.sailFile}`);
    console.log(`${errors.length} schema validation error(s):`);
    errors.slice(0, 50).forEach((err, idx) => {
      console.log(`\n${idx + 1}. ${err.path}`);
      console.log(`   ${err.message}`);
      console.log(`   keyword: ${err.keyword}`);
    });
  }
  process.exit(1);
} catch (err) {
  printUsage();
  console.error(`\nError: ${err.message}`);
  process.exit(2);
}

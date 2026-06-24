#!/usr/bin/env bun
/**
 * SecurityValidatorHook — IPEA_HUB
 * Intercepta comandos peligrosos antes de ejecutarse.
 * Se registra como PreToolUse hook en Claude Code settings.json.
 */

import { readFileSync } from "fs";
import { join } from "path";

interface HookInput {
  tool_name: string;
  tool_input: Record<string, unknown>;
}

const DANGEROUS_PATTERNS = [
  /rm\s+-rf/,
  /rm\s+-r\s+\//,
  /sudo\s+rm/,
  /chmod\s+777/,
  /chown\s+root/,
  /:\s*>\s*\/etc/,
  /dd\s+if=/,
  /mkfs/,
  /format\s+[cC]:/,
  /deltree/,
  /rd\s+\/s\s+\/q/,
];

const PROTECTED_PATHS = [
  process.env.PAI_DIR ?? `${process.env.HOME}/.pai-engineering`,
  `${process.env.HOME}/.claude`,
  `${process.env.HOME}/.ssh`,
  `${process.env.HOME}/.env`,
  "/etc",
  "/usr",
  "/bin",
  "/sbin",
];

function logSecurityEvent(
  level: "WARN" | "BLOCK",
  tool: string,
  reason: string,
  input: unknown
): void {
  const logDir = `${process.env.PAI_DIR ?? process.env.HOME + "/.pai-engineering"}/logs`;
  const timestamp = new Date().toISOString();
  const entry = JSON.stringify({
    timestamp,
    level,
    tool,
    reason,
    input,
  });

  try {
    const { appendFileSync, mkdirSync } = require("fs");
    mkdirSync(logDir, { recursive: true });
    appendFileSync(`${logDir}/security.log`, entry + "\n");
  } catch {
    // silently ignore log failures
  }
}

function isCommandDangerous(command: string): string | null {
  for (const pattern of DANGEROUS_PATTERNS) {
    if (pattern.test(command)) {
      return `Patrón peligroso detectado: ${pattern.source}`;
    }
  }
  return null;
}

function isPathProtected(path: string): string | null {
  for (const protectedPath of PROTECTED_PATHS) {
    if (path.startsWith(protectedPath) && path !== protectedPath) {
      const paiDir = process.env.PAI_DIR ?? `${process.env.HOME}/.pai-engineering`;
      if (path.startsWith(paiDir)) {
        return null;
      }
      return `Ruta protegida: ${protectedPath}`;
    }
  }
  return null;
}

function validate(input: HookInput): { block: boolean; reason?: string } {
  const { tool_name, tool_input } = input;

  if (tool_name === "Bash") {
    const command = String(tool_input.command ?? "");
    const danger = isCommandDangerous(command);
    if (danger) {
      return { block: true, reason: danger };
    }
  }

  if (tool_name === "Write" || tool_name === "Edit") {
    const filePath = String(tool_input.file_path ?? "");
    const protectedReason = isPathProtected(filePath);
    if (protectedReason) {
      return { block: true, reason: protectedReason };
    }
  }

  if (tool_name === "Bash") {
    const command = String(tool_input.command ?? "");
    for (const protectedPath of PROTECTED_PATHS) {
      const paiDir = process.env.PAI_DIR ?? `${process.env.HOME}/.pai-engineering`;
      if (command.includes(protectedPath) && !command.includes(paiDir)) {
        const hasWrite =
          command.includes(">") ||
          command.includes(">>") ||
          command.includes("tee ") ||
          command.includes("cp ") ||
          command.includes("mv ") ||
          command.includes("rm ");
        if (hasWrite) {
          logSecurityEvent(
            "WARN",
            tool_name,
            `Escritura en ruta crítica: ${protectedPath}`,
            { command }
          );
        }
      }
    }
  }

  return { block: false };
}

async function main(): Promise<void> {
  try {
    const raw = readFileSync("/dev/stdin", "utf8");
    const input: HookInput = JSON.parse(raw);
    const result = validate(input);

    if (result.block) {
      logSecurityEvent("BLOCK", input.tool_name, result.reason!, input.tool_input);
      console.error(`[IPEA Security] BLOQUEADO: ${result.reason}`);
      console.error(`[IPEA Security] Herramienta: ${input.tool_name}`);
      console.error(`[IPEA Security] Revisa los logs en $PAI_DIR/logs/security.log`);
      process.exit(1);
    }

    process.exit(0);
  } catch (err) {
    process.exit(0);
  }
}

main();

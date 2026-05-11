#!/usr/bin/env bun
/**
 * HistorySystemHook — IPEA_HUB
 * Registra sesiones técnicas, cálculos y decisiones en el sistema de historial.
 * Se ejecuta como PostToolUse hook en Claude Code.
 */

import { appendFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from "fs";
import { join } from "path";

const PAI_DIR = process.env.PAI_DIR ?? `${process.env.HOME}/.pai-engineering`;

interface ToolEvent {
  tool_name: string;
  tool_input: Record<string, unknown>;
  tool_response?: unknown;
}

interface HistoryEntry {
  timestamp: string;
  session_id: string;
  tool: string;
  category: "calculation" | "decision" | "document" | "qa" | "general";
  summary: string;
  metadata: Record<string, unknown>;
}

const SESSION_ID = `session_${Date.now()}`;

function ensureDirs(): void {
  const dirs = [
    join(PAI_DIR, "history", "projects"),
    join(PAI_DIR, "history", "calculations"),
    join(PAI_DIR, "history", "decisions"),
    join(PAI_DIR, "history", "learnings"),
    join(PAI_DIR, "logs"),
  ];
  for (const dir of dirs) {
    if (!existsSync(dir)) {
      mkdirSync(dir, { recursive: true });
    }
  }
}

function categorizeEvent(event: ToolEvent): "calculation" | "decision" | "document" | "qa" | "general" {
  const { tool_name, tool_input } = event;
  const input = JSON.stringify(tool_input).toLowerCase();

  if (
    input.includes("cálculo") ||
    input.includes("calculo") ||
    input.includes("voltage") ||
    input.includes("hvac") ||
    input.includes("caída") ||
    input.includes("corriente") ||
    input.includes("dimensionamiento") ||
    input.includes("sizing")
  ) {
    return "calculation";
  }

  if (
    input.includes("memoria") ||
    input.includes("reporte") ||
    input.includes("documento") ||
    input.includes(".docx") ||
    input.includes(".pdf") ||
    input.includes(".xlsx")
  ) {
    return "document";
  }

  if (
    input.includes("qa") ||
    input.includes("qc") ||
    input.includes("revisión") ||
    input.includes("revision") ||
    input.includes("validar") ||
    input.includes("nom-001")
  ) {
    return "qa";
  }

  if (tool_name === "Write" || tool_name === "Edit") {
    return "decision";
  }

  return "general";
}

function buildSummary(event: ToolEvent): string {
  const { tool_name, tool_input } = event;

  if (tool_name === "Bash") {
    const cmd = String(tool_input.command ?? "").slice(0, 120);
    return `CMD: ${cmd}`;
  }
  if (tool_name === "Write") {
    return `Archivo escrito: ${tool_input.file_path ?? ""}`;
  }
  if (tool_name === "Edit") {
    return `Archivo editado: ${tool_input.file_path ?? ""}`;
  }
  if (tool_name === "Read") {
    return `Archivo leído: ${tool_input.file_path ?? ""}`;
  }
  return `${tool_name} ejecutado`;
}

function logEntry(entry: HistoryEntry): void {
  const logFile = join(PAI_DIR, "logs", "history.jsonl");
  try {
    appendFileSync(logFile, JSON.stringify(entry) + "\n");
  } catch {
    // ignore
  }

  if (entry.category === "calculation") {
    const calcLog = join(PAI_DIR, "history", "calculations", `${entry.timestamp.slice(0, 10)}.jsonl`);
    try {
      appendFileSync(calcLog, JSON.stringify(entry) + "\n");
    } catch {
      // ignore
    }
  }
}

function updateIndex(): void {
  const indexPath = join(PAI_DIR, "history", "HISTORY_INDEX.md");
  const today = new Date().toLocaleDateString("es-MX", {
    timeZone: process.env.TIME_ZONE ?? "America/Cancun",
  });

  const sessionLine = `- ${today} — Sesión ${SESSION_ID}\n`;

  try {
    if (!existsSync(indexPath)) {
      writeFileSync(
        indexPath,
        `# IPEA_HUB — Índice de Historial Técnico\n\n## Sesiones\n${sessionLine}`
      );
    } else {
      const content = readFileSync(indexPath, "utf8");
      if (!content.includes(SESSION_ID)) {
        appendFileSync(indexPath, sessionLine);
      }
    }
  } catch {
    // ignore
  }
}

async function main(): Promise<void> {
  try {
    ensureDirs();
    updateIndex();

    const raw = readFileSync("/dev/stdin", "utf8");
    const event: ToolEvent = JSON.parse(raw);

    const entry: HistoryEntry = {
      timestamp: new Date().toISOString(),
      session_id: SESSION_ID,
      tool: event.tool_name,
      category: categorizeEvent(event),
      summary: buildSummary(event),
      metadata: {
        tool_input_keys: Object.keys(event.tool_input ?? {}),
      },
    };

    logEntry(entry);
    process.exit(0);
  } catch {
    process.exit(0);
  }
}

main();

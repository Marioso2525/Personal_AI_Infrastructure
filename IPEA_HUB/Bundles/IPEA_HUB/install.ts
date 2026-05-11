#!/usr/bin/env bun
/**
 * install.ts — IPEA_HUB Bundle Installer
 * Instala todos los packs del sistema IPEA_HUB en orden de dependencia.
 */

import { cpSync, existsSync, mkdirSync, readFileSync, writeFileSync, appendFileSync } from "fs";
import { join, dirname } from "path";
import { execSync } from "child_process";

const PAI_DIR = process.env.PAI_DIR ?? `${process.env.HOME}/.pai-engineering`;
const PACKS_DIR = join(dirname(import.meta.dir), "..", "Packs");

const PACK_INSTALL_ORDER = [
  "ipea-core",
  "ipea-electrical",
  "ipea-hvac",
  "ipea-hydrosanitary",
  "ipea-gas",
  "ipea-cad-qa",
  "ipea-revit-qa",
  "ipea-documentation",
];

const REQUIRED_DIRS = [
  "hooks",
  "skills/electrical",
  "skills/hvac",
  "skills/hydrosanitary",
  "skills/gas",
  "skills/cad-qa",
  "skills/revit-qa",
  "skills/documentation",
  "standards/nom-001-sede-2012",
  "scripts/python",
  "templates/word",
  "templates/excel",
  "templates/reports",
  "history/projects",
  "history/calculations",
  "history/decisions",
  "history/learnings",
  "logs",
  "config",
  "datasets",
];

const PYTHON_DEPS = [
  "python-docx",
  "reportlab",
  "openpyxl",
  "pandas",
  "numpy",
  "scipy",
  "pydantic",
  "matplotlib",
];

function log(msg: string, level: "INFO" | "OK" | "WARN" | "ERROR" = "INFO"): void {
  const prefix: Record<string, string> = {
    INFO: "  ℹ",
    OK: "  ✅",
    WARN: "  ⚠",
    ERROR: "  ❌",
  };
  console.log(`${prefix[level] ?? "  •"} ${msg}`);
}

function createDirectories(): void {
  console.log("\n[1/5] Creando estructura de directorios...");
  for (const dir of REQUIRED_DIRS) {
    const fullPath = join(PAI_DIR, dir);
    if (!existsSync(fullPath)) {
      mkdirSync(fullPath, { recursive: true });
      log(`Creado: ${fullPath}`, "OK");
    } else {
      log(`Ya existe: ${dir}`, "INFO");
    }
  }
}

function installPacks(): void {
  console.log("\n[2/5] Instalando packs...");
  for (const pack of PACK_INSTALL_ORDER) {
    const packSrcDir = join(PACKS_DIR, pack, "src");
    if (!existsSync(packSrcDir)) {
      log(`Pack no encontrado: ${pack} — omitiendo`, "WARN");
      continue;
    }

    try {
      cpSync(packSrcDir, PAI_DIR, { recursive: true });
      log(`Instalado: ${pack}`, "OK");
    } catch (err) {
      log(`Error instalando ${pack}: ${(err as Error).message}`, "ERROR");
    }
  }
}

function installPythonDeps(): void {
  console.log("\n[3/5] Instalando dependencias Python...");
  try {
    execSync(`pip install ${PYTHON_DEPS.join(" ")} --quiet`, { stdio: "pipe" });
    log(`Dependencias Python instaladas: ${PYTHON_DEPS.join(", ")}`, "OK");
  } catch {
    log("pip no disponible o error instalando dependencias. Instalar manualmente:", "WARN");
    log(`pip install ${PYTHON_DEPS.join(" ")}`, "INFO");
  }
}

function configureClaudeCode(): void {
  console.log("\n[4/5] Configurando Claude Code...");
  const claudeDir = `${process.env.HOME}/.claude`;
  const settingsPath = join(claudeDir, "settings.json");

  if (!existsSync(claudeDir)) {
    mkdirSync(claudeDir, { recursive: true });
  }

  const ipeaSettings = {
    env: {
      PAI_DIR,
      DA: process.env.DA ?? "EngineeringAI",
      TIME_ZONE: process.env.TIME_ZONE ?? "America/Cancun",
    },
    hooks: {
      PreToolUse: [
        {
          matcher: ".*",
          hooks: [
            {
              type: "command",
              command: `bun ${PAI_DIR}/hooks/SecurityValidatorHook.ts`,
            },
          ],
        },
      ],
      PostToolUse: [
        {
          matcher: ".*",
          hooks: [
            {
              type: "command",
              command: `bun ${PAI_DIR}/hooks/HistorySystemHook.ts`,
            },
          ],
        },
      ],
      SessionStart: [
        {
          hooks: [
            {
              type: "command",
              command: `bun ${PAI_DIR}/hooks/EngineeringContextLoader.ts`,
            },
            {
              type: "command",
              command: `bun ${PAI_DIR}/hooks/ProjectContextHook.ts`,
            },
          ],
        },
      ],
    },
  };

  if (existsSync(settingsPath)) {
    try {
      const existing = JSON.parse(readFileSync(settingsPath, "utf8"));
      const merged = { ...existing, ...ipeaSettings };
      merged.env = { ...(existing.env ?? {}), ...ipeaSettings.env };
      writeFileSync(settingsPath, JSON.stringify(merged, null, 2));
      log("settings.json actualizado (fusionado con existente)", "OK");
    } catch {
      const backupPath = settingsPath + ".backup";
      cpSync(settingsPath, backupPath);
      writeFileSync(settingsPath, JSON.stringify(ipeaSettings, null, 2));
      log(`settings.json reemplazado (backup en ${backupPath})`, "OK");
    }
  } else {
    writeFileSync(settingsPath, JSON.stringify(ipeaSettings, null, 2));
    log("settings.json creado", "OK");
  }
}

function initializeHistory(): void {
  console.log("\n[5/5] Inicializando sistema de historial...");
  const indexPath = join(PAI_DIR, "history", "HISTORY_INDEX.md");

  if (!existsSync(indexPath)) {
    const content = [
      "# IPEA_HUB — Índice de Historial Técnico",
      "",
      `Instalado: ${new Date().toLocaleString("es-MX", { timeZone: process.env.TIME_ZONE ?? "America/Cancun" })}`,
      `PAI_DIR: ${PAI_DIR}`,
      "",
      "## Proyectos",
      "",
      "## Cálculos",
      "",
      "## Decisiones Técnicas",
      "",
      "## Aprendizajes",
      "",
    ].join("\n");
    writeFileSync(indexPath, content);
    log("HISTORY_INDEX.md creado", "OK");
  }

  const envPath = join(PAI_DIR, ".env");
  if (!existsSync(envPath)) {
    const envContent = [
      `DA=${process.env.DA ?? "EngineeringAI"}`,
      `TIME_ZONE=${process.env.TIME_ZONE ?? "America/Cancun"}`,
      "ANTHROPIC_API_KEY=",
      "OPENAI_API_KEY=",
      "ELEVENLABS_API_KEY=",
    ].join("\n");
    writeFileSync(envPath, envContent);
    log(".env creado (completar con API keys)", "OK");
  }
}

function printSummary(): void {
  console.log("\n" + "=".repeat(60));
  console.log("  IPEA_HUB — Instalación Completada");
  console.log("=".repeat(60));
  console.log(`  PAI_DIR: ${PAI_DIR}`);
  console.log(`  Packs instalados: ${PACK_INSTALL_ORDER.length}`);
  console.log(`  Skills disponibles: electrical, hvac, hydrosanitary,`);
  console.log(`                      gas, cad-qa, revit-qa, documentation`);
  console.log();
  console.log("  Próximos pasos:");
  console.log("  1. Agregar API keys en: $PAI_DIR/.env");
  console.log("  2. Reiniciar Claude Code para activar hooks");
  console.log("  3. Probar: python $PAI_DIR/scripts/python/voltage_drop.py");
  console.log();
  console.log("  Documentación: IPEA_HUB/README.md");
  console.log("=".repeat(60));
}

async function main(): Promise<void> {
  console.log("=".repeat(60));
  console.log("  IPEA_HUB — Bundle Installer v1.0");
  console.log("  Sistema Operativo de Ingeniería AI");
  console.log("=".repeat(60));
  console.log(`  Destino: ${PAI_DIR}`);
  console.log(`  Packs: ${PACK_INSTALL_ORDER.join(", ")}`);

  try {
    createDirectories();
    installPacks();
    installPythonDeps();
    configureClaudeCode();
    initializeHistory();
    printSummary();
  } catch (err) {
    console.error(`\n❌ Error durante instalación: ${(err as Error).message}`);
    process.exit(1);
  }
}

main();

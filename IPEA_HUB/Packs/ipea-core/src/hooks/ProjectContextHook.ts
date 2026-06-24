#!/usr/bin/env bun
/**
 * ProjectContextHook — IPEA_HUB
 * Detecta la disciplina del proyecto activo y carga la memoria previa correspondiente.
 * Se ejecuta como SessionStart hook.
 */

import { existsSync, readdirSync, readFileSync, statSync, writeFileSync, mkdirSync } from "fs";
import { join, basename, extname } from "path";

const PAI_DIR = process.env.PAI_DIR ?? `${process.env.HOME}/.pai-engineering`;
const CWD = process.cwd();

type Discipline = "electrical" | "hvac" | "hydrosanitary" | "gas" | "cad" | "revit" | "general";

interface ProjectMemory {
  name: string;
  discipline: Discipline;
  lastOpened: string;
  calculations: string[];
  decisions: string[];
  standards: string[];
  notes: string;
}

const DISCIPLINE_SIGNALS: Record<Discipline, RegExp[]> = {
  electrical: [
    /electr/i,
    /\.dwg$/i,
    /tablero/i,
    /circuito/i,
    /alimentador/i,
    /nom.001/i,
    /panel/i,
    /voltage/i,
  ],
  hvac: [/hvac/i, /clima/i, /aire.acondicionado/i, /duct/i, /ashrae/i, /refriger/i, /ventilacion/i],
  hydrosanitary: [/hidro/i, /sanitari/i, /plomeria/i, /agua/i, /drenaje/i, /pipes/i, /tuber/i],
  gas: [/gas/i, /lp$/i, /natural.gas/i, /combustible/i, /gasoducto/i],
  cad: [/\.dwg$/i, /autocad/i, /lisp/i, /cad.qa/i, /planos/i],
  revit: [/\.rvt$/i, /revit/i, /bim/i, /dynamo/i, /familia/i, /schedule/i],
  general: [],
};

function detectDiscipline(cwdPath: string): Discipline {
  try {
    const files = readdirSync(cwdPath);
    const allNames = files.join(" ").toLowerCase() + " " + cwdPath.toLowerCase();

    for (const [discipline, patterns] of Object.entries(DISCIPLINE_SIGNALS)) {
      if (discipline === "general") continue;
      for (const pattern of patterns) {
        if (pattern.test(allNames)) {
          return discipline as Discipline;
        }
      }
    }
  } catch {
    // ignore
  }
  return "general";
}

function loadProjectMemory(projectName: string): ProjectMemory | null {
  const memPath = join(PAI_DIR, "history", "projects", `${projectName}.json`);
  if (!existsSync(memPath)) return null;

  try {
    return JSON.parse(readFileSync(memPath, "utf8"));
  } catch {
    return null;
  }
}

function saveProjectMemory(memory: ProjectMemory): void {
  const dir = join(PAI_DIR, "history", "projects");
  if (!existsSync(dir)) {
    mkdirSync(dir, { recursive: true });
  }

  const sanitized = memory.name.replace(/[^a-z0-9_-]/gi, "_");
  const memPath = join(dir, `${sanitized}.json`);
  writeFileSync(memPath, JSON.stringify(memory, null, 2));
}

function loadDisciplineStandards(discipline: Discipline): string[] {
  const standardsDir = join(PAI_DIR, "standards");
  if (!existsSync(standardsDir)) return [];

  const disciplineStandards: Record<Discipline, string[]> = {
    electrical: ["NOM-001-SEDE-2012", "NOM-008-ENER", "NFPA-70"],
    hvac: ["ASHRAE-62.1", "ASHRAE-90.1", "SMACNA"],
    hydrosanitary: ["NOM-004-CNA", "NOM-006-CNA", "IPC"],
    gas: ["NOM-004-SEDG", "NOM-002-SECRE", "NFPA-54"],
    cad: ["Estándares CAD internos"],
    revit: ["BIM Level 2", "ISO 19650"],
    general: [],
  };

  return disciplineStandards[discipline] ?? [];
}

function buildContextOutput(discipline: Discipline, memory: ProjectMemory | null, projectName: string): string {
  const lines: string[] = [
    "## Contexto de Proyecto Detectado",
    "",
    `**Directorio:** ${CWD}`,
    `**Disciplina detectada:** ${discipline.toUpperCase()}`,
    `**Proyecto:** ${projectName}`,
    "",
  ];

  const standards = loadDisciplineStandards(discipline);
  if (standards.length > 0) {
    lines.push("### Normas Aplicables");
    for (const s of standards) {
      lines.push(`- ${s}`);
    }
    lines.push("");
  }

  if (memory) {
    lines.push("### Memoria del Proyecto Cargada");
    lines.push(`- Última apertura: ${memory.lastOpened}`);

    if (memory.calculations.length > 0) {
      lines.push("- Cálculos previos:");
      for (const c of memory.calculations.slice(-3)) {
        lines.push(`  - ${c}`);
      }
    }

    if (memory.decisions.length > 0) {
      lines.push("- Decisiones previas:");
      for (const d of memory.decisions.slice(-3)) {
        lines.push(`  - ${d}`);
      }
    }

    if (memory.notes) {
      lines.push(`- Notas: ${memory.notes}`);
    }

    lines.push("");
  } else {
    lines.push("### Proyecto Nuevo");
    lines.push("- No se encontró memoria previa para este proyecto.");
    lines.push("- Se creará registro automáticamente al finalizar la sesión.");
    lines.push("");
  }

  const skillHints: Record<Discipline, string> = {
    electrical: "Usa: `calcular caída de tensión`, `dimensionar conductor`, `validar NOM-001`",
    hvac: "Usa: `calcular carga térmica`, `dimensionar ducto`, `seleccionar equipo HVAC`",
    hydrosanitary: "Usa: `calcular gasto probable`, `dimensionar tubería`, `calcular presión`",
    gas: "Usa: `dimensionar tubería gas`, `calcular caída de presión`, `validar caudal`",
    cad: "Usa: `revisar layers CAD`, `validar escala`, `limpiar drawing`",
    revit: "Usa: `validar parámetros BIM`, `revisar clashes`, `generar schedule`",
    general: "Skills disponibles en $PAI_DIR/skills/",
  };

  lines.push(`**Tip:** ${skillHints[discipline]}`);

  return lines.join("\n");
}

async function main(): Promise<void> {
  try {
    const discipline = detectDiscipline(CWD);
    const projectName = basename(CWD);
    const memory = loadProjectMemory(projectName);

    if (!memory) {
      const newMemory: ProjectMemory = {
        name: projectName,
        discipline,
        lastOpened: new Date().toISOString(),
        calculations: [],
        decisions: [],
        standards: loadDisciplineStandards(discipline),
        notes: "",
      };
      saveProjectMemory(newMemory);
    } else {
      memory.lastOpened = new Date().toISOString();
      saveProjectMemory(memory);
    }

    const output = buildContextOutput(discipline, memory, projectName);
    console.log(output);
    process.exit(0);
  } catch {
    process.exit(0);
  }
}

main();

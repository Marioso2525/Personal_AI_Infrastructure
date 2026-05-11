#!/usr/bin/env bun
/**
 * EngineeringContextLoader — IPEA_HUB
 * Se ejecuta al inicio de cada sesión (SessionStart hook).
 * Carga el contexto técnico: normas activas, proyectos recientes, preferencias.
 */

import { existsSync, readFileSync, readdirSync, statSync } from "fs";
import { join } from "path";

const PAI_DIR = process.env.PAI_DIR ?? `${process.env.HOME}/.pai-engineering`;

interface ProjectContext {
  name: string;
  discipline: string;
  lastModified: Date;
  path: string;
}

interface EngineeringContext {
  activeStandards: string[];
  recentProjects: ProjectContext[];
  availableSkills: string[];
  systemStatus: Record<string, boolean>;
}

function loadActiveStandards(): string[] {
  const standardsDir = join(PAI_DIR, "standards");
  if (!existsSync(standardsDir)) return [];

  const standards: string[] = [];
  try {
    const dirs = readdirSync(standardsDir);
    for (const dir of dirs) {
      const indexPath = join(standardsDir, dir, "index.json");
      if (existsSync(indexPath)) {
        const meta = JSON.parse(readFileSync(indexPath, "utf8"));
        standards.push(`${meta.code} (${meta.version})`);
      } else {
        standards.push(dir.toUpperCase());
      }
    }
  } catch {
    // ignore
  }
  return standards;
}

function loadRecentProjects(limit = 5): ProjectContext[] {
  const projectsDir = join(PAI_DIR, "history", "projects");
  if (!existsSync(projectsDir)) return [];

  const projects: ProjectContext[] = [];
  try {
    const files = readdirSync(projectsDir)
      .filter((f) => f.endsWith(".json"))
      .map((f) => ({
        name: f,
        path: join(projectsDir, f),
        mtime: statSync(join(projectsDir, f)).mtime,
      }))
      .sort((a, b) => b.mtime.getTime() - a.mtime.getTime())
      .slice(0, limit);

    for (const file of files) {
      try {
        const data = JSON.parse(readFileSync(file.path, "utf8"));
        projects.push({
          name: data.name ?? file.name.replace(".json", ""),
          discipline: data.discipline ?? "general",
          lastModified: file.mtime,
          path: file.path,
        });
      } catch {
        // ignore malformed files
      }
    }
  } catch {
    // ignore
  }
  return projects;
}

function loadAvailableSkills(): string[] {
  const skillsDir = join(PAI_DIR, "skills");
  if (!existsSync(skillsDir)) return [];

  const skills: string[] = [];
  try {
    const disciplineDirs = readdirSync(skillsDir);
    for (const dir of disciplineDirs) {
      const skillPath = join(skillsDir, dir);
      if (statSync(skillPath).isDirectory()) {
        const skillFiles = readdirSync(skillPath).filter((f) => f.endsWith(".md"));
        for (const sf of skillFiles) {
          skills.push(`${dir}/${sf.replace(".md", "")}`);
        }
      }
    }
  } catch {
    // ignore
  }
  return skills;
}

function checkSystemStatus(): Record<string, boolean> {
  return {
    paiDirExists: existsSync(PAI_DIR),
    hooksInstalled: existsSync(join(PAI_DIR, "hooks")),
    historySystem: existsSync(join(PAI_DIR, "history")),
    standardsLoaded: existsSync(join(PAI_DIR, "standards")),
    templatesReady: existsSync(join(PAI_DIR, "templates")),
    scriptsReady: existsSync(join(PAI_DIR, "scripts", "python")),
  };
}

function buildContextMessage(ctx: EngineeringContext): string {
  const now = new Date().toLocaleString("es-MX", {
    timeZone: process.env.TIME_ZONE ?? "America/Cancun",
  });

  const lines: string[] = [
    `## IPEA_HUB — Contexto de Ingeniería Cargado`,
    `**Sesión iniciada:** ${now}`,
    `**Asistente:** ${process.env.DA ?? "EngineeringAI"}`,
    `**PAI_DIR:** ${PAI_DIR}`,
    "",
    "### Normas Técnicas Disponibles",
    ctx.activeStandards.length > 0
      ? ctx.activeStandards.map((s) => `- ${s}`).join("\n")
      : "- No hay normas cargadas (ejecutar ipea-electrical para NOM-001-SEDE-2012)",
    "",
    "### Skills Disponibles",
    ctx.availableSkills.length > 0
      ? ctx.availableSkills.map((s) => `- ${s}`).join("\n")
      : "- No hay skills instalados",
    "",
    "### Proyectos Recientes",
    ctx.recentProjects.length > 0
      ? ctx.recentProjects
          .map(
            (p) =>
              `- **${p.name}** (${p.discipline}) — ${p.lastModified.toLocaleDateString("es-MX")}`
          )
          .join("\n")
      : "- Sin proyectos registrados",
    "",
    "### Estado del Sistema",
    ...Object.entries(ctx.systemStatus).map(
      ([key, ok]) => `- ${ok ? "✅" : "❌"} ${key}`
    ),
    "",
    "---",
    "Puedes usar cualquiera de los skills disponibles. Ejemplo: `usar skill electrical para calcular caída de tensión`",
  ];

  return lines.join("\n");
}

async function main(): Promise<void> {
  try {
    const ctx: EngineeringContext = {
      activeStandards: loadActiveStandards(),
      recentProjects: loadRecentProjects(),
      availableSkills: loadAvailableSkills(),
      systemStatus: checkSystemStatus(),
    };

    const message = buildContextMessage(ctx);
    console.log(message);
    process.exit(0);
  } catch (err) {
    // Non-critical — context loading failure should not block the session
    process.exit(0);
  }
}

main();

# ipea-core — Core Infrastructure Pack

Pack fundacional del sistema IPEA_HUB. Instala los hooks de seguridad, el sistema de historial técnico y el cargador de contexto de ingeniería. Todos los demás packs dependen de este.

---

## Problema que Resuelve

Sin ipea-core:
- No hay protección contra operaciones destructivas
- No hay memoria persistente entre sesiones
- No hay carga automática de contexto técnico
- No hay registro de decisiones de diseño

Con ipea-core:
- Protección automática de archivos críticos
- Historial persistente de cálculos y decisiones
- Carga automática de normas y plantillas al iniciar sesión
- Registro completo de cambios para trazabilidad

---

## Componentes

| Componente                  | Archivo                          | Función |
|-----------------------------|----------------------------------|---------|
| Security Validator Hook     | `hooks/SecurityValidatorHook.ts` | Bloquea operaciones peligrosas |
| Engineering Context Loader  | `hooks/EngineeringContextLoader.ts` | Carga contexto técnico al inicio |
| History System Hook         | `hooks/HistorySystemHook.ts`     | Registra sesiones y decisiones |
| Project Context Hook        | `hooks/ProjectContextHook.ts`    | Detecta disciplina y carga memoria |
| Settings Configuration      | `config/settings.json`           | Configura hooks en Claude Code |

---

## Dependencias

- Claude Code >= 1.0
- Bun >= 1.0
- Node.js >= 18

---

## Variables de Entorno Requeridas

```env
PAI_DIR=$HOME/.pai-engineering
DA=EngineeringAI
TIME_ZONE=America/Cancun
```

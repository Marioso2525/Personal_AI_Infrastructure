# INSTALL — ipea-core

## Paso 1: Crear Estructura de Directorios

```bash
mkdir -p $HOME/.pai-engineering/{hooks,skills,standards,scripts/python,templates/{word,excel,reports},history/{projects,calculations,decisions,learnings},logs,config,datasets}
```

## Paso 2: Copiar Hooks

```bash
cp src/hooks/SecurityValidatorHook.ts $HOME/.pai-engineering/hooks/
cp src/hooks/EngineeringContextLoader.ts $HOME/.pai-engineering/hooks/
cp src/hooks/HistorySystemHook.ts $HOME/.pai-engineering/hooks/
cp src/hooks/ProjectContextHook.ts $HOME/.pai-engineering/hooks/
```

## Paso 3: Configurar Variables de Entorno

Agregar a `~/.bashrc` o `~/.zshrc`:

```bash
export PAI_DIR="$HOME/.pai-engineering"
export DA="EngineeringAI"
export TIME_ZONE="America/Cancun"
```

## Paso 4: Crear Archivo .env

```bash
cat > $HOME/.pai-engineering/.env << 'EOF'
DA=EngineeringAI
TIME_ZONE=America/Cancun
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
ELEVENLABS_API_KEY=
EOF
```

## Paso 5: Aplicar Configuración de Claude Code

```bash
# Copiar o fusionar con ~/.claude/settings.json
cp src/config/settings.json $HOME/.claude/settings.json
```

Si ya tienes un settings.json, fusiona manualmente la sección `hooks`.

## Paso 6: Inicializar Sistema de Historia

```bash
cat > $HOME/.pai-engineering/history/HISTORY_INDEX.md << 'EOF'
# IPEA_HUB — Índice de Historial Técnico

## Proyectos
## Cálculos
## Decisiones
## Aprendizajes
EOF
```

## Paso 7: Verificar Instalación

Ejecutar VERIFY.md para confirmar que todo funciona.

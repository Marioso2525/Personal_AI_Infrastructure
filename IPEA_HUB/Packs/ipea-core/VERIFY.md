# VERIFY — ipea-core

Ejecutar este checklist después de instalar. Todos los puntos deben pasar.

---

## Checklist de Verificación

### Estructura de Directorios

```bash
[ ] ls $HOME/.pai-engineering/hooks/          # debe mostrar los 4 hooks .ts
[ ] ls $HOME/.pai-engineering/history/        # debe mostrar projects/ calculations/ decisions/
[ ] ls $HOME/.pai-engineering/templates/      # debe mostrar word/ excel/ reports/
[ ] ls $HOME/.pai-engineering/standards/      # directorio existe
[ ] ls $HOME/.pai-engineering/scripts/python/ # directorio existe
[ ] ls $HOME/.pai-engineering/logs/           # directorio existe
```

### Variables de Entorno

```bash
[ ] echo $PAI_DIR    # debe mostrar $HOME/.pai-engineering
[ ] echo $DA         # debe mostrar EngineeringAI
[ ] echo $TIME_ZONE  # debe mostrar America/Cancun
```

### Hooks Instalados

```bash
[ ] ls $HOME/.pai-engineering/hooks/SecurityValidatorHook.ts
[ ] ls $HOME/.pai-engineering/hooks/EngineeringContextLoader.ts
[ ] ls $HOME/.pai-engineering/hooks/HistorySystemHook.ts
[ ] ls $HOME/.pai-engineering/hooks/ProjectContextHook.ts
```

### Archivo .env

```bash
[ ] cat $HOME/.pai-engineering/.env   # debe mostrar las variables (sin exponer API keys)
```

### Claude Code Settings

```bash
[ ] cat ~/.claude/settings.json | grep "ipea"   # debe mostrar referencias a los hooks
```

### Test de Seguridad

En una sesión de Claude Code:
```
[ ] Intentar ejecutar: rm -rf /tmp/test_ipea
    → Hook debe interceptar y solicitar confirmación o bloquear
```

### Test de Historia

```bash
[ ] ls $HOME/.pai-engineering/history/HISTORY_INDEX.md   # debe existir
```

---

## Resultado Esperado

Si todos los checks pasan: **ipea-core está correctamente instalado**.

Si alguno falla: revisar el paso correspondiente en INSTALL.md.

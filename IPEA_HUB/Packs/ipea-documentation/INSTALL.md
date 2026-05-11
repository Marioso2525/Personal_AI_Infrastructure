# INSTALL — ipea-documentation

## Prerequisito
ipea-core instalado.

## Paso 1: Copiar Skill
```bash
mkdir -p $PAI_DIR/skills/documentation
cp src/skills/*.md $PAI_DIR/skills/documentation/
```

## Paso 2: Copiar Scripts (si existen)
```bash
[ -d src/python ] && cp src/python/*.py $PAI_DIR/scripts/python/ 2>/dev/null
[ -d src/scripts ] && cp src/scripts/* $PAI_DIR/scripts/ 2>/dev/null
```

## Paso 3: Verificar
Revisar VERIFY.md

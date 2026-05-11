# SKILL: Gas Systems Engineering — IPEA_HUB

## Identidad

Eres un ingeniero especialista en instalaciones de gas LP y Gas Natural conforme NOM-004-SEDG-2004 y NOM-002-SECRE-2010.

## Workflows

### 1. Dimensionar Tubería de Gas
**Comando:** `dimensionar tubería gas` | `gas pipe sizing`

Proceso:
1. Inventario de aparatos de consumo
2. Factor de simultaneidad
3. Caudal total m³/h
4. Caída de presión Darcy-Weisbach
5. Seleccionar diámetro estándar

### 2. Calcular Caída de Presión
**Comando:** `caída de presión gas` | `pressure drop gas`

Fórmula: Darcy-Weisbach con factor de fricción Colebrook-White
- ΔP = f × (L/D) × (ρ × v²/2)

### 3. Verificar Seguridad
**Comando:** `verificar seguridad gas` | `safety check`

Verificaciones:
- Ventilación del local (NOM-002-SECRE)
- Distancias de seguridad
- Materiales permitidos
- Pendientes de tubería

## Consumos de Referencia (m³/h por aparato)

| Aparato | Gas LP | Gas Natural |
|---------|--------|-------------|
| Estufa doméstica | 2.0 | 4.0 |
| Calentador 15L | 6.0 | 12.0 |
| Calentador paso 11L | 5.0 | 10.0 |
| Caldera pequeña | 15.0 | 28.0 |

## Parámetros de Diseño (Baja Presión México)

| Parámetro | Valor |
|-----------|-------|
| Presión servicio LP | 2.8 kPa |
| Caída de presión máx. | 125 Pa |
| Velocidad máxima | 10 m/s |
| Material predominante | Acero negro / Cobre |

## Normas Aplicables

- NOM-004-SEDG-2004: Instalaciones de gas LP
- NOM-002-SECRE-2010: Gas Natural
- NOM-003-SEDG: Estaciones de carburación

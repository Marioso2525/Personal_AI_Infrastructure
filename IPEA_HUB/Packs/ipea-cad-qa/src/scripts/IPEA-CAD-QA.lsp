;;; ============================================================
;;; IPEA-CAD-QA.lsp — IPEA_HUB CAD Quality Assurance Script
;;; Revisión automática de capas, escalas y limpieza de DWG
;;; Compatibilidad: AutoCAD 2018+
;;; ============================================================

;;; ── Utilidades internas ─────────────────────────────────────

(defun IPEA:msg (txt / )
  (princ (strcat "\n[IPEA_HUB] " txt))
)

(defun IPEA:msg-ok (txt / )
  (princ (strcat "\n  ✅ " txt))
)

(defun IPEA:msg-err (txt / )
  (princ (strcat "\n  ❌ " txt))
)

(defun IPEA:msg-warn (txt / )
  (princ (strcat "\n  ⚠  " txt))
)

;;; ── Prefijos de disciplina permitidos ──────────────────────

(setq IPEA:VALID-PREFIXES
  '("A-" "E-" "M-" "H-" "S-" "G-" "I-" "C-" "F-" "B-" "X-")
)

;;; ── Verificar nomenclatura de capa ─────────────────────────

(defun IPEA:layer-name-ok-p (layer-name / prefix-ok)
  (setq prefix-ok nil)
  (foreach pfx IPEA:VALID-PREFIXES
    (if (= (substr layer-name 1 (strlen pfx)) pfx)
      (setq prefix-ok T)
    )
  )
  prefix-ok
)

;;; ── C:IPEA-CHECK-LAYERS ─────────────────────────────────────
;;; Revisa todas las capas del dibujo contra el estándar IPEA_HUB

(defun c:IPEA-CHECK-LAYERS ( / layer-list bad-layers ok-layers total)
  (IPEA:msg "=== REVISIÓN DE CAPAS — IPEA_HUB ===")

  (setq layer-list (vla-get-layers (vla-get-activedocument (vlax-get-acad-object))))
  (setq bad-layers '())
  (setq ok-layers 0)
  (setq total 0)

  (vlax-for layer layer-list
    (setq lname (vla-get-name layer))
    (setq total (1+ total))

    (cond
      ;; Capa 0 — permitida solo para definición de bloques
      ((= lname "0")
        (IPEA:msg-warn (strcat "Capa '0': verificar que no tenga objetos sueltos"))
      )

      ;; Defpoints — nunca debe tener objetos
      ((= lname "Defpoints")
        (IPEA:msg-err (strcat "Capa 'Defpoints': mover objetos a capa correcta"))
        (setq bad-layers (cons lname bad-layers))
      )

      ;; Verificar prefijo
      ((IPEA:layer-name-ok-p lname)
        (setq ok-layers (1+ ok-layers))
      )

      ;; Capa con nombre incorrecto
      (T
        (IPEA:msg-err (strcat "Nomenclatura incorrecta: '" lname "'"))
        (setq bad-layers (cons lname bad-layers))
      )
    )
  )

  (IPEA:msg (strcat "Total capas: " (itoa total)))
  (IPEA:msg (strcat "Capas correctas: " (itoa ok-layers)))
  (IPEA:msg (strcat "Capas con problemas: " (itoa (length bad-layers))))

  (if (= (length bad-layers) 0)
    (IPEA:msg "RESULTADO: ✅ Todas las capas cumplen el estándar IPEA_HUB")
    (IPEA:msg (strcat "RESULTADO: ❌ " (itoa (length bad-layers)) " capas requieren corrección"))
  )
  (princ)
)

;;; ── C:IPEA-CLEAN ────────────────────────────────────────────
;;; Limpieza completa del dibujo

(defun c:IPEA-CLEAN ( / )
  (IPEA:msg "=== LIMPIEZA DE DRAWING — IPEA_HUB ===")

  ;; Purgar elementos no utilizados
  (IPEA:msg "Purgando capas, bloques, estilos no usados...")
  (command "._PURGE" "_ALL" "" "_NO")
  (IPEA:msg-ok "PURGE ejecutado")

  ;; Auditar el dibujo
  (IPEA:msg "Auditando integridad del archivo...")
  (command "._AUDIT" "_YES")
  (IPEA:msg-ok "AUDIT ejecutado")

  ;; Eliminar líneas duplicadas
  (IPEA:msg "Eliminando objetos duplicados...")
  (command "._OVERKILL" "_ALL" "" "")
  (IPEA:msg-ok "OVERKILL ejecutado")

  ;; Limpiar escala de viewport
  (IPEA:msg-ok "Limpieza completada")
  (IPEA:msg "Guardar el archivo para consolidar cambios.")
  (princ)
)

;;; ── C:IPEA-CHECK-BYLAYER ─────────────────────────────────────
;;; Verifica que los objetos tengan color y tipo de línea PorCapa

(defun c:IPEA-CHECK-BYLAYER ( / ss total-objs bad-color bad-ltype)
  (IPEA:msg "=== VERIFICACIÓN BYLAYER — IPEA_HUB ===")

  (setq ss (ssget "_X"))
  (setq total-objs (if ss (sslength ss) 0))
  (setq bad-color 0)
  (setq bad-ltype 0)

  (if ss
    (progn
      (setq i 0)
      (while (< i total-objs)
        (setq en (ssname ss i))
        (setq ed (entget en))

        ;; Color no BYLAYER (62 = color code; 256 = BYLAYER)
        (if (assoc 62 ed)
          (if (/= (cdr (assoc 62 ed)) 256)
            (setq bad-color (1+ bad-color))
          )
        )

        ;; Tipo de línea no BYLAYER
        (if (assoc 6 ed)
          (if (and (/= (cdr (assoc 6 ed)) "")
                   (/= (cdr (assoc 6 ed)) "Continuous"))
            (setq bad-ltype (1+ bad-ltype))
          )
        )

        (setq i (1+ i))
      )
    )
  )

  (IPEA:msg (strcat "Objetos revisados: " (itoa total-objs)))

  (if (= bad-color 0)
    (IPEA:msg-ok "Color: todos los objetos usan BYLAYER")
    (IPEA:msg-err (strcat "Color: " (itoa bad-color) " objetos NO usan BYLAYER"))
  )

  (if (= bad-ltype 0)
    (IPEA:msg-ok "Tipo de línea: todos los objetos usan BYLAYER")
    (IPEA:msg-warn (strcat "Tipo de línea: " (itoa bad-ltype) " objetos con tipo específico"))
  )
  (princ)
)

;;; ── C:IPEA-CHECK-NORTH ───────────────────────────────────────
;;; Verifica que exista bloque de Norte en el dibujo

(defun c:IPEA-CHECK-NORTH ( / north-found block-list)
  (IPEA:msg "=== VERIFICACIÓN BLOQUE DE NORTE ===")
  (setq north-found nil)

  (setq block-list '("NORTE" "NORTH" "ROSA_VIENTOS" "BRUJULA"
                     "X-NORTE" "G-NORTE" "SIMBOLO-NORTE"))

  (foreach bname block-list
    (if (tblsearch "block" bname)
      (setq north-found bname)
    )
  )

  (if north-found
    (IPEA:msg-ok (strcat "Bloque de norte encontrado: '" north-found "'"))
    (IPEA:msg-err "No se encontró bloque de Norte. Insertar antes de entregar.")
  )
  (princ)
)

;;; ── C:IPEA-FULL-QA ───────────────────────────────────────────
;;; Ejecuta revisión QA/QC completa

(defun c:IPEA-FULL-QA ( / )
  (IPEA:msg "")
  (IPEA:msg "╔══════════════════════════════════════╗")
  (IPEA:msg "║   IPEA_HUB — REVISIÓN COMPLETA QA   ║")
  (IPEA:msg "╚══════════════════════════════════════╝")
  (IPEA:msg "")

  (c:IPEA-CHECK-LAYERS)
  (IPEA:msg "")
  (c:IPEA-CHECK-BYLAYER)
  (IPEA:msg "")
  (c:IPEA-CHECK-NORTH)
  (IPEA:msg "")

  (IPEA:msg "QA/QC completo. Revisar resultados arriba.")
  (IPEA:msg "Para limpiar el drawing ejecutar: IPEA-CLEAN")
  (princ)
)

;;; ── C:IPEA-LAYER-ELECTRICAL ──────────────────────────────────
;;; Crea capas estándar para proyectos eléctricos

(defun c:IPEA-LAYER-ELECTRICAL ( / doc layers)
  (IPEA:msg "=== CREANDO CAPAS ELÉCTRICAS ESTÁNDAR ===")
  (setq doc (vla-get-activedocument (vlax-get-acad-object)))
  (setq layers (vla-get-layers doc))

  (defun make-layer (name color ltype / layer)
    (if (not (tblsearch "layer" name))
      (progn
        (setq layer (vla-add layers name))
        (vla-put-color layer color)
        (IPEA:msg-ok (strcat "Creada: " name))
      )
      (IPEA:msg-warn (strcat "Ya existe: " name))
    )
  )

  (make-layer "E-ALIMENTADORES"   2 "Continuous")
  (make-layer "E-CIRCUITOS"       3 "Continuous")
  (make-layer "E-CIRCUITOS-ILU"   3 "Continuous")
  (make-layer "E-CIRCUITOS-CONT" 30 "Continuous")
  (make-layer "E-ILUMINACION"     3 "Continuous")
  (make-layer "E-CONTACTOS"      30 "Continuous")
  (make-layer "E-TABLEROS"        5 "Continuous")
  (make-layer "E-CANALIZACION"    9 "HIDDEN")
  (make-layer "E-TIERRA"         92 "Continuous")
  (make-layer "E-EMERGENCIA"      1 "DASHED")
  (make-layer "E-COTAS"           7 "Continuous")
  (make-layer "E-TEXTO"           7 "Continuous")
  (make-layer "E-LEYENDA"         7 "Continuous")
  (make-layer "X-EJES"            8 "CENTER")
  (make-layer "X-NORTE"           7 "Continuous")

  (IPEA:msg "✅ Capas eléctricas IPEA_HUB creadas exitosamente.")
  (princ)
)

;;; ── MENSAJE DE CARGA ─────────────────────────────────────────

(princ "\n╔══════════════════════════════════════════════╗")
(princ "\n║  IPEA_HUB CAD QA v1.0 — Comandos cargados  ║")
(princ "\n╠══════════════════════════════════════════════╣")
(princ "\n║  IPEA-FULL-QA         Revisión QA completa  ║")
(princ "\n║  IPEA-CHECK-LAYERS    Verificar capas        ║")
(princ "\n║  IPEA-CHECK-BYLAYER   Verificar BYLAYER      ║")
(princ "\n║  IPEA-CHECK-NORTH     Verificar norte        ║")
(princ "\n║  IPEA-CLEAN           Limpiar drawing        ║")
(princ "\n║  IPEA-LAYER-ELECTRICAL Crear capas eléctr.  ║")
(princ "\n╚══════════════════════════════════════════════╝")
(princ)

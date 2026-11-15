# Cómo usar Spec Kit y las reglas

Guía corta del **flujo de trabajo**. Los requisitos del producto están en `docs/requisitos/` (dentro de este repo; portable).

## Piezas

| Ruta | Rol |
|---|---|
| `docs/requisitos/` | Enunciado, contrato, FAQ, guía, fuentes (canónico) |
| `.specify/memory/constitution.md` | Principios MUST |
| `.cursor/skills/speckit-*` | Skills Spec Kit **adaptadas** al observatorio (ES + gates) |
| `.cursor/rules/*.mdc` | Reglas Cursor |
| `specs/001-observatorio-sismico/` | Spec/plan/modelo/contratos |
| `frontend/` | Panel Angular base |

## Flujo

En el chat de Cursor, **una skill cada vez**:

1. `/speckit-constitution` — solo si cambian principios (v1.1.0 actual).
2. `/speckit-specify` — qué/porqué (cuadrar con `docs/requisitos/`).
3. `/speckit-clarify` — opcional.
4. `/speckit-plan` — cómo técnico.
5. `/speckit-checklist` — opcional.
6. `/speckit-tasks` — tareas.
7. `/speckit-analyze` — opcional, antes de codear.
8. `/speckit-implement` — ejecutar.
9. `/speckit-converge` — cerrar huecos.

Camino corto: constitution → specify → plan → tasks → implement → converge.

## Reglas Cursor

- Siempre: `observatorio-core`, `codigo-estilo`, `requisitos-rubrica`.
- Backend/SQL: `pipeline-datos`.
- `frontend/`: `frontend-angular`.

## Portabilidad

Un clon de **este** repositorio MUST bastar. No hace falta ninguna carpeta externa de aula: su contenido relevante está en `docs/requisitos/`.

## Comprobar Spec Kit

```powershell
uvx --from git+https://github.com/github/spec-kit.git specify check
```

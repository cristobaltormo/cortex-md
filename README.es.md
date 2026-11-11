<p align="center">
  <img src="docs/assets/banner.svg" alt="cortex-md" width="100%">
</p>

<p align="center">
  <a href="README.md">English</a> | <b>Español</b>
</p>

# cortex-md

Sistema de memoria para Claude Code que se mantiene honesto. Markdown plano en un repo git, sin
base de datos y sin servicios externos.

La mayoría de herramientas de memoria guardan lo que dijo el agente y lo recuperan después.
Envejecen mal: una dirección apuntada en una nota en primavera es una mentira segura en otoño.
cortex-md separa lo que sabe el agente en tres capas y mantiene cada una fresca de forma distinta.

```
brain/
├── inventory/    Lo que la máquina sabe de sí misma.    Lo escribe un script, nunca a mano.
├── memory/       Hechos, decisiones y sus porqués.      Los escribe Claude y un curador nocturno.
├── skills/       Cómo se hacen las cosas aquí.          Las escribe Claude al aprender un procedimiento.
├── PENDING.md    Lo que está a medias. Se carga al empezar cada sesión.
└── bin/          La maquinaria (ver bin/README.md).
```

La regla que lo mantiene sano: **si el inventario ya lo sabe, no lo escribas en la memoria.**
Guarda el porqué, no el cuánto.

## Qué hace

| Cuándo | Qué pasa |
|---|---|
| Al abrir sesión | Hace pull, rescata cambios sin guardar de una sesión que murió, refresca el inventario y cuenta a Claude dónde lo dejasteis: conversaciones recientes, lo último aprendido, qué ha cambiado en la máquina, frentes abiertos y avisos |
| En cada mensaje | Un hook sugiere las notas más probables y las que enlazan |
| Al cerrar sesión | Commit y push de lo escrito |
| Cada noche | Foto de la máquina y comparación con la de ayer; después, un curador destila las conversaciones del día en notas, reacciona a los cambios (desaparece un contenedor: sus notas pasan a históricas), reverifica notas viejas contra la realidad y arregla lo que encuentre el validador |
| A demanda | `bin/health.py` revisa índice, enlaces, fechas, tamaños, notas huérfanas, entidades muertas y secretos filtrados |

## Qué lo distingue

- **Inventario autogenerado con detección de cambios.** Las notas sobre una máquina que ya no existe se señalan solas.
- **Un curador que reverifica, no solo acumula.** Las notas llevan fecha `verified`; las viejas se comprueban contra el host.
- **Un validador con dientes.** Notas huérfanas, `[[enlaces]]` rotos, notas sin enlaces, notas enormes y secretos son defectos que el curador debe arreglar.
- **Disciplina de contexto.** El índice siempre cargado es pequeño; los índices por área se abren a demanda; un hook sugiere notas por mensaje.
- **Skills como procedimientos.** Los how-to repetibles viven fuera de la memoria y se cargan solo cuando hacen falta.

## Instalación

Requisitos: Linux, bash, git, python3 (solo librería estándar) y [Claude Code](https://claude.com/claude-code). Docker, LXC y Proxmox se detectan si existen y son opcionales.

```bash
git clone https://github.com/cristobaltormo/cortex-md ~/brain
cd ~/brain
./install.sh
```

El instalador fusiona los hooks en `~/.claude/settings.json` (con copia de seguridad), fija
`autoMemoryDirectory`, genera el primer inventario y pasa el validador. Después:

1. Copia `CLAUDE.example.md` al `CLAUDE.md` que lee Claude Code y edítalo.
2. Añade las líneas de cron que imprime el instalador.
3. Opcional: copia `.env.example` a `.env` para recibir avisos push por cualquier webhook.
4. Sustituye las notas de ejemplo de `memory/` por las tuyas, o bórralas.

El cerebro puede vivir en cualquier sitio: los scripts encuentran su directorio, o usan `BRAIN_DIR`.

## Escribir notas

Un hecho por fichero, con frontmatter (ver el ejemplo en el README en inglés). Añade la nota al
índice de su área, enlázala con `[[otra-nota]]` y ejecuta `bin/health.py`. La skill
`memory-keeping` tiene las reglas completas y el razonamiento; Claude la carga sola.

## Seguridad

- El curador lee las transcripciones de tus conversaciones, que contienen contenido web y salida de herramientas. Para limitar una inyección de prompt corre con una lista de permisos estrecha: solo escribe en `memory/`, `skills/` y `PENDING.md`, ejecuta git de solo lectura más `git add` y `git commit`, y `bin/health.py`. El push lo hace el script, no el modelo. Revisa `bin/curator.sh` antes de confiarle un repo con un remoto que te importe.
- `inventory/` está en `.gitignore` salvo `CHANGES.md`: los volcados de host, puertos y crontab no salen de la máquina. Nunca pongas credenciales en las notas; `bin/health.py` detecta formatos comunes de token.
- `.env` está ignorado por git y se lee línea a línea (nunca se ejecuta).
- Los hooks de sesión se disparan en todos los proyectos de Claude Code de la máquina, así que el cerebro se commitea y se sube al cerrar cualquier sesión.

## Operación

- El curador solo corre si hay transcripciones nuevas (que no sean las suyas) o defectos del validador, y gasta tu cuota de Claude. Define `CLAUDE_BIN` en `.env` porque cron tiene un PATH mínimo.
- Si el curador topa con el límite de cuota, programa un reintento justo después del reinicio.
- Si la foto pierde casi todos los contenedores de golpe, `changes.py` supone que falló el inventario y no compara; ejecuta `bin/changes.py --accept` cuando el cambio sea real.

## Más documentación

La documentación detallada (arquitectura, formato de notas, configuración, preguntas frecuentes) está en inglés en [docs/](docs/). Para contribuir, mira [CONTRIBUTING.md](CONTRIBUTING.md); para seguridad, [SECURITY.md](SECURITY.md).

## Pruebas

```bash
python3 -m unittest discover -s tests
```

## Límites

- La recuperación es puntuación por palabras clave sobre un corpus pequeño, no embeddings. Con unos cientos de notas basta `grep`; si deja de bastar, añade un índice.
- El curador necesita el CLI `claude` y gasta tu cuota una vez por noche, solo si hay algo que hacer.
- Los recolectores cubren Linux, Docker, LXC y Proxmox. Otras plataformas requieren añadir un recolector a `bin/snapshot.py`.

## Licencia

[MIT](LICENSE)

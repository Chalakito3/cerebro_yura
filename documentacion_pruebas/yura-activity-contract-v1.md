# Contrato de actividades Yura v1.2

Este documento define el intercambio entre Laravel y el cerebro Python/Flask
que se ejecuta en Yura. Laravel es la fuente oficial de participantes,
agrupación, actividades y calificaciones. El cerebro no necesita conectarse a
la base de datos de alumnos: Laravel le envía la lista mínima necesaria.

El contrato se mantiene sincronizado con
`cerebro_yura/documentacion_pruebas/yura-activity-contract-v1.md`.

## Reglas de la actividad

- El docente elige paralelo, asignatura, trimestre (`1` a `3`), casilla HACER
  (`1` a `5`), participantes, categoría, máximo de integrantes por grupo,
  respondientes por grupo y preguntas por respondiente.
- Laravel mezcla a los participantes, forma grupos equilibrados sin superar el
  tamaño máximo configurado y sortea a los respondientes de cada grupo.
- Cada grupo incluye todos sus integrantes y la lista
  `respondent_student_ids` escogida por Laravel. Si un grupo tiene menos
  integrantes que la cantidad solicitada, participan todos sus integrantes.
- Grupos, integrantes y respondientes se guardan con la actividad y permanecen
  iguales durante los reintentos.
- `display_name` contiene solo el nombre corto para llamar al alumno. No se
  envían CI, información familiar, credenciales ni audio.
- Yura usa el vocabulario local de la categoría, mezcla globalmente el orden de
  las preguntas entre grupos, escucha las respuestas y calcula el resultado.
- Cada grupo recibe una nota porcentual sobre 100. Todas las respuestas
  planificadas tienen el mismo peso; una respuesta incorrecta o sin respuesta
  aporta cero. Todos los integrantes reciben la nota de su grupo.
- No se define duración límite. La ejecución normal termina al completar las
  preguntas planificadas.
- Solo una actividad fallida sin nota se puede reintentar. El reintento conserva
  el mismo plan y genera un `attempt_id` nuevo.
- Laravel rechaza resultados de intentos anteriores, no reemplaza notas y
  garantiza idempotencia para el mismo resumen aceptado.

## Categorías y diccionario

`content.category` es un identificador de tabla SQLite, no una instrucción libre.
La web permite únicamente categorías para las que el cerebro encontró
vocabulario utilizable en `palabras_para_juego`: alimentos, colores, elementos
de casa, elementos naturales, familia, números, objetos escolares, partes del
cuerpo, saludos y animales. Si una categoría no tiene vocabulario utilizable en
la base local, el cerebro devuelve `failed` con un motivo explícito y sin notas.

El cerebro consulta las palabras y traducciones en SQLite y construye cada
pregunta mediante una regla fija («¿Cómo se dice [palabra] en quechua?»). No
usa prompts/instrucciones de texto libre para inventar preguntas o respuestas.
El archivo `diccionario_quechua_sqlite_29-07-2026.db` se prefiere cuando está en
la raíz del proyecto. En otras instalaciones, `YURA_DICTIONARY_PATH` puede
señalar el diccionario activo; si no se configura ni existe el archivo indicado,
se usa `cerebro_yura/diccionario.db`.

## Transporte y autenticación

En despliegue se usa HTTPS. HTTP solo se permite en una red privada controlada
para desarrollo. El token Sanctum de la cuenta de servicio Yura se configura
fuera del repositorio y nunca forma parte del JSON.

| Método | Ruta | Propósito |
| --- | --- | --- |
| `GET` | `/api/v1/robot/activities/next` | Reclamar la actividad pendiente más antigua. |
| `GET` | `/api/v1/robot/activities/{activity_id}/attempts/{attempt_id}/status` | Consultar el estado del intento activo y recibir cancelaciones. |
| `POST` | `/api/v1/robot/activities/{activity_id}/results` | Enviar el resumen final. |

Ambas rutas requieren autenticación de servicio. La cola vacía devuelve `204`.
Al reclamar una actividad, Laravel la marca `in_progress`; las consultas
posteriores reciben el mismo intento hasta que finaliza o se reintenta.
Mientras ejecuta un intento, Yura consulta periódicamente su estado con la ruta
de estado. Si Laravel responde `cancelled` o `superseded`, el cerebro debe
detener la captura/ejecución de forma segura y no enviar resultados ni aplicar
notas parciales. La ruta requiere el token de servicio Yura y responde:

```json
{
  "activity_id": "0199c204-5f70-7aa1-8d47-e4b1a7bb0925",
  "attempt_id": "0199c204-5f70-7aa1-8d47-e4b1a7bb0930",
  "status": "in_progress"
}
```

`status` devuelve el estado de la actividad o `cancelled` cuando fue detenida.
Devuelve `superseded` si el intento ya no es el actual; Yura debe tratarlo como
una señal de parada para evitar ejecutar o entregar resultados de un intento
obsoleto. Al cancelar una actividad en curso, Laravel marca también su intento
actual como `cancelled`; no registra calificaciones parciales.

## Actividad enviada a Yura

Una respuesta `200` de `GET /api/v1/robot/activities/next` tiene esta forma:

```json
{
  "contract_version": "1.2",
  "activity": {
    "activity_id": "0199c204-5f70-7aa1-8d47-e4b1a7bb0925",
    "attempt_id": "0199c204-5f70-7aa1-8d47-e4b1a7bb0930",
    "attempt_number": 1,
    "created_at": "2026-10-06T17:00:00Z",
    "course": {"id": 6, "name": "Sexto de Primaria"},
    "parallel": {"id": 12, "name": "A"},
    "subject": {"id": 3, "name": "Quechua"},
    "content": {"category": "nivel1_colores"},
    "grading_target": {
      "quarter": 1,
      "activity_number": 2,
      "type": "robot"
    },
    "groups": [
      {
        "group_id": "0199c204-6ae7-7553-90d4-e5d9592bc776",
        "members": [
          {"student_id": 101, "display_name": "María"},
          {"student_id": 102, "display_name": "Luis"},
          {"student_id": 103, "display_name": "Ana"}
        ],
        "respondent_student_ids": [103, 101]
      }
    ],
    "execution": {
      "group_size": 20,
      "respondents_per_group": 2,
      "questions_per_respondent": 1
    },
    "scoring": {
      "max_score": 100,
      "correct_rule": "equal_weight_per_planned_response",
      "incorrect_points": 0,
      "unanswered_points": 0,
      "normalization": "round(points_earned / points_possible * 100, 2)"
    }
  }
}
```

`group_size` es el tamaño máximo configurado. El número de grupos depende de
los participantes seleccionados. Yura debe evaluar exactamente los IDs de
`respondent_student_ids`; no vuelve a sortearlos. La unidad de calificación es
el grupo: `points_possible` suma el peso de las respuestas evaluadas y
`score_percentage` es el porcentaje calculado a partir de sus totales.

## Resultado enviado a Laravel

Yura envía un resumen por actividad. Cada grupo aparece como máximo una vez e
incluye sus integrantes y respondientes:

```json
{
  "contract_version": "1.2",
  "activity_id": "0199c204-5f70-7aa1-8d47-e4b1a7bb0925",
  "attempt_id": "0199c204-5f70-7aa1-8d47-e4b1a7bb0930",
  "status": "completed",
  "started_at": "2026-10-06T17:02:00Z",
  "finished_at": "2026-10-06T17:08:15Z",
  "group_results": [
    {
      "group_id": "0199c204-6ae7-7553-90d4-e5d9592bc776",
      "member_student_ids": [101, 102, 103],
      "respondent_student_ids": [103, 101],
      "points_earned": 50,
      "points_possible": 100,
      "score_percentage": 50,
      "responses": [
        {
          "student_id": 103,
          "question_id": "group-1-103-1",
          "correct": true,
          "points_earned": 50,
          "points_possible": 50,
          "answered_at": "2026-10-06T17:03:12Z"
        },
        {
          "student_id": 101,
          "question_id": "group-1-101-1",
          "correct": false,
          "points_earned": 0,
          "points_possible": 50,
          "answered_at": "2026-10-06T17:04:12Z"
        }
      ]
    }
  ]
}
```

`status` admite `completed`, `partial` o `failed`. Una respuesta vacía por
silencio se representa como una respuesta `correct: false` con cero puntos.
Un resultado `failed` incluye `failure_reason` y no lleva grupos ni notas.
Laravel contrasta IDs, integrantes, respondientes, recuento de preguntas y
cálculos con el plan guardado. Al aceptar el resultado, guarda
`score_percentage` en la nota `robot` de todos los integrantes del grupo para
la asignatura, trimestre y HACER elegidos.

## Reintentos e idempotencia

El par `activity_id` y `attempt_id` identifica una ejecución. Laravel conserva
el resumen aceptado y aplica cada intento en una transacción:

- Reenviar el mismo resumen devuelve éxito sin duplicar calificaciones.
- Reenviar el mismo `attempt_id` con un resumen distinto devuelve `409`.
- Un intento anterior devuelve `409`, aunque su resultado llegue después del
  reintento.
- Los errores HTTP de cliente quedan para revisión; los errores de red y
  servidor permanecen en el outbox para reintento.
- Errores de validación devuelven `422`; errores de autenticación devuelven
  `401` o `403`.

La ruta anterior `POST /api/v1/robot/activity` no reemplaza estas rutas.

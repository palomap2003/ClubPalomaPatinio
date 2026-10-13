# Modelo de datos

Base de datos relacional (PostgreSQL). Las contraseñas **no** se almacenan: las administra Firebase Authentication.

```mermaid
erDiagram
    USUARIOS ||--o{ RESERVAS : realiza
    ESPACIOS ||--o{ RESERVAS : "es reservado en"
    SEDES ||--o{ ESPACIOS : contiene
    DEPORTES ||--o{ TIPOS_ESPACIO : "tiene variantes"
    TIPOS_ESPACIO ||--o{ ESPACIOS : clasifica

    USUARIOS {
        int id PK
        string firebase_uid UK "identificador en Firebase Auth"
        string email UK
        string nombre
        string apellido
        string dni UK
        date fecha_nacimiento
        string fcm_token "dispositivo para push (opcional)"
        datetime creado_en
    }
    SEDES {
        int id PK
        string nombre UK
        string calle
        string altura
        smallint hora_apertura "0-23"
        smallint hora_cierre "1-24, mayor a apertura"
        bool activa
    }
    DEPORTES {
        int id PK
        string nombre UK "Futbol, Tenis, Paddle..."
    }
    TIPOS_ESPACIO {
        int id PK
        int deporte_id FK
        string nombre "Futbol 5"
        string codigo "F5, usado en el nombre del espacio"
    }
    ESPACIOS {
        int id PK
        int sede_id FK
        int tipo_espacio_id FK
        int numero "correlativo por sede y tipo"
        string nombre UK "Sede_Calle_Deporte_Tipo_Numero"
        decimal precio_hora
        bool techado
        bool iluminacion
        bool activo
    }
    RESERVAS {
        int id PK
        int usuario_id FK
        int espacio_id FK
        date fecha
        smallint hora_inicio "hora completa"
        smallint hora_fin "hora completa, mayor a inicio"
        string estado "confirmada | cancelada"
        decimal precio_total "se congela al reservar"
        datetime creada_en
        datetime cancelada_en
        bool recordatorio_enviado
    }
```

## Relaciones

| Relación | Cardinalidad | Detalle |
|---|---|---|
| Sede – Espacio | 1 a N | Todo espacio pertenece a una sede. |
| Deporte – Tipo de espacio | 1 a N | Fútbol → Fútbol 5 / 7 / 8 / 11. El tipo depende del deporte. |
| Tipo de espacio – Espacio | 1 a N | Cada espacio tiene un tipo (y por él, un deporte). |
| Usuario – Reserva | 1 a N | Un usuario puede tener muchas reservas. |
| Espacio – Reserva | 1 a N | Un espacio se reserva muchas veces, nunca en horarios superpuestos. |

## Restricciones e integridad

- `usuarios`: `firebase_uid`, `email` y `dni` únicos.
- `sedes`: `0 <= hora_apertura < hora_cierre <= 24`.
- `espacios`: único por (`sede_id`, `tipo_espacio_id`, `numero`) y `nombre` único. El nombre se genera automáticamente, p. ej. `Moron_Rivadavia_Futbol_F5_1`.
- `reservas`: `0 <= hora_inicio < hora_fin <= 24` (duración mínima de 1 hora y horas completas por construcción). La no superposición entre reservas `confirmada` del mismo espacio y fecha se valida en el backend dentro de una transacción con bloqueo del espacio.
- Cancelar una reserva cambia `estado` a `cancelada` (no se borra), de modo que queda en el historial y el horario se libera.

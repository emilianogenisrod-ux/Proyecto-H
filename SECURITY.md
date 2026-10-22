# Qué ve el profesor y qué queda privado

El repositorio es **público** para que se pueda revisar el código:

https://github.com/emilianogenisrod-ux/Proyecto-H

Supabase (la base de datos) y MinIO (los archivos) **no se publican ahí**.

## Lo que sí se puede ver en GitHub

- El programa en Python
- Las pantallas en HTML y CSS
- El diseño de las tablas (nombres de columnas, sin datos reales)
- Las pruebas
- Una plantilla de despliegue, sin claves

## Lo que no va en GitHub

- Contraseñas de entrada
- Contraseña de PostgreSQL / Supabase
- Usuario y clave de MinIO
- Llaves `anon` o `service_role` de Supabase
- El archivo `.env` del servidor
- Direcciones internas de la base y del almacén de archivos

Esas cosas viven en **secretos de Docker** en el servidor. El programa las lee desde archivos dentro del contenedor, no desde este repositorio.

## Cómo se conecta el sistema, sin abrir esas puertas

En producción, la aplicación habla con la base y con MinIO **por una red interna del servidor**.

- La base no se abre a internet para que cualquiera entre.
- MinIO no se usa desde una consola pública en este proyecto: el programa sube y baja archivos por dentro.
- La página que sí se ve es la del gestor de citas, no la consola de la base ni la de MinIO.

Quien clone el repositorio puede correrlo en su computadora con SQLite, sin tocar Supabase ni MinIO.

# Roadmap ChatSender

Este documento detalla la evolución planificada para **ChatSender**, enfocándose en la privacidad extrema, la soberanía de datos y una experiencia de usuario refinada.

---

## Fase 1: Criptografía Avanzada y Seguridad

> *Objetivo: Fortalecer el núcleo de privacidad antes de añadir capas de contenido.*

* **[ ] Implementación de Perfect Forward Secrecy (PFS):**
* Integración del protocolo **Double Ratchet** (tipo Signal).
* Renovación periódica de claves de sesión para asegurar que el compromiso de una clave no afecte mensajes pasados.


* **[ ] Intercambio de Llaves vía QR Offline:**
* Generación de códigos QR con la clave pública del usuario.
* Módulo de escaneo integrado en la app para verificar la identidad de forma física (OOB - Out of Band).



---

## Fase 2: Capacidades de Mensajería

> *Objetivo: Expandir las formas en las que los usuarios pueden comunicarse.*

* **[ ] Grupos y Salas Multiusuario:**
* Implementación de gestión de grupos por parte del administrador de la red.
* Cifrado de grupo mediante llaves compartidas rotativas.


* **[ ] Envío de Multimedia y Archivos:**
* Soporte para imágenes, vídeos y documentos.
* Cifrado de archivos en el lado del cliente antes de la subida.


* **[ ] Gestión de Mensajes (Eliminación):**
* Función "Eliminar para todos" mediante el envío de un paquete de revocación de mensaje firmado por el autor.



---

## Fase 3: UX/UI y Enriquecimiento Visual

> *Objetivo: Hacer que la herramienta sea tan intuitiva como moderna sin sacrificar el rendimiento local.*

* **[ ] Rediseño de /chat:**
* Estética **Glassmorphism** o Neo-minimalista manteniendo la paleta de colores original.
* Mejora de la responsividad y animaciones suaves para las transiciones de mensajes.


* **[ ] Vistas Previas de Enlaces:**
* Generador de metadatos (título, descripción, imagen).
* **Importante:** Implementar la generación de vista previa en el lado del servidor para evitar fugas de IP.
* Opción de abrir enlaces en pestañas nuevas con atributos `rel="noopener noreferrer"`.



---

## Tabla de Prioridades

| Prioridad | Feature | Dificultad | Impacto |
| --- | --- | --- | --- |
| 🔴 Alta | Perfect Forward Secrecy | Alta | Máximo |
| 🔴 Alta | QR Offline | Baja | Alto |
| 🟡 Media | Multimedia y Archivos | Media | Alto |
| 🟡 Media | Rediseño de UX | Media | Medio |
| 🟢 Baja | Vista previa de enlaces | Baja | Bajo |

---

## Notas Técnicas

* Todos los archivos multimedia deben ser fragmentados y cifrados antes de tocar el almacenamiento local del servidor.
* La UI debe priorizar tiempos de carga rápidos al ser una aplicación que corre sobre VPN.
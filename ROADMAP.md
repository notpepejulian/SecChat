# Roadmap ChatSender

Este documento detalla la evolución planificada para **ChatSender**, enfocándose en la privacidad extrema, la soberanía de datos y una experiencia de usuario refinada.

---

## 1. Intercambio de Llaves Offline

> Escaneo de códigos QR para intercambiar llaves de forma segura y física.

* **[ ] Generación de QR:** Creación de códigos QR que contienen la clave pública del usuario directamente en la interfaz.
* **[ ] Módulo de Escaneo:** Integración de cámara para verificar la identidad de forma física (OOB - Out of Band), eliminando el riesgo de ataques Man-in-the-Middle durante el intercambio inicial.

---

## 2. Modern UX/UI

> Rediseño estético del chat conservando la identidad de ChatSender pero con una mejor experiencia de usuario.

* **[ ] Estética Actualizada:** Implementación de estilos **Glassmorphism** o Neo-minimalismo sobre la paleta de colores original tanto en la landing page como en el chat.
* **[ ] Interactividad:** Mejora de la responsividad y animaciones fluidas para la entrada/salida de mensajes y estados de conexión.

---

## 3. Multimedia Seguro

> Envío de imágenes y archivos encriptados con la misma rigurosidad que los mensajes de texto.

* **[ ] Cifrado en Origen:** Los archivos se fragmentan y cifran en el cliente antes de ser subidos al servidor.
* **[ ] Soporte Universal:** Compatibilidad con imágenes, vídeos y documentos manteniendo la soberanía del dato y eliminando metadatos.

---

## 4. Rich Links

> Vistas previas de enlaces seguras y navegación externa controlada.

* **[ ] Previsualización Segura:** Generación de metadatos (título e imagen) gestionada por un proxy o en el servidor para evitar que la IP del usuario sea rastreada por el sitio web del enlace.
* **[ ] Navegación Controlada:** Apertura de enlaces en pestañas nuevas utilizando atributos `rel="noopener noreferrer"`.

---

## 5. Borrado Bilateral

> Posibilidad de eliminar mensajes específicos para ambos participantes en la conversación.

* **[ ] Revocación de Mensajes:** Envío de un paquete de control firmado digitalmente que instruye al cliente del receptor a eliminar localmente un mensaje específico.
* **[ ] Sincronización:** Asegurar que la base de datos local de ambos usuarios refleje la eliminación de forma inmediata.

---

## 6. Salas Grupales

> Creación de grupos y espacios compartidos con cifrado multi-usuario.

* **[ ] Gestión de Salas:** Administración de acceso por parte del host de la red privada.
* **[ ] Cifrado Grupal:** Implementación de llaves compartidas rotativas para asegurar que solo los miembros actuales del grupo puedan leer el historial pertinente.

---

## 7. Perfect Forward Secrecy (PFS)

> Rotación de llaves privadas por cada mensaje enviado, imposibilitando el descifrado de mensajes anteriores.

* **[ ] Double Ratchet Protocol:** Integración del algoritmo de trinquete doble para derivar nuevas llaves de cifrado en cada paso de la conversación.
* **[ ] Protección de Historial:** Garantía de que, en caso de compromiso de una llave actual, los mensajes pasados sigan siendo criptográficamente ilegibles.

---

## Resumen de Prioridades

| Orden | Feature | Dificultad | Impacto |
| --- | --- | --- | --- |
| 1 | Intercambio Offline (QR) | Baja | Alto |
| 2 | Modern UX/UI | Media | Medio |
| 3 | Multimedia Seguro | Media | Alto |
| 4 | Rich Links | Baja | Bajo |
| 5 | Borrado Bilateral | Media | Medio |
| 6 | Salas Grupales | Alta | Alto |
| 7 | Perfect Forward Secrecy | Alta | Máximo |

---

## Notas Técnicas adicionales

* **Rendimiento:** Al operar sobre VPN, todas las nuevas funciones de UI deben ser ligeras para no penalizar la latencia.
* **Privacidad de Archivos:** El almacenamiento en el servidor siempre será "Zero-Knowledge"; el administrador nunca podrá visualizar el contenido multimedia.
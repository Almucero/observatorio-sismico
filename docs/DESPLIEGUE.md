# Despliegue (feature 002) — qué necesitas y cómo conseguirlo

## A) ngrok (túnel HTTPS → API local)

### 1. Crear cuenta
1. Entra en https://dashboard.ngrok.com/signup  
2. Regístrate (GitHub o email).

### 2. Copiar el authtoken
1. Tras login: https://dashboard.ngrok.com/get-started/your-authtoken  
2. Copia el token (empieza por `2…` o similar).  
3. **No lo subas a Git.** Pégalo solo en tu `.env` local:

```env
NGROK_AUTHTOKEN=pega_aqui_el_token
```

### 3. Instalar el cliente (Windows)
- Opción winget: `winget install ngrok.ngrok`  
- O descarga: https://ngrok.com/download  

Luego:

```powershell
ngrok config add-authtoken TU_TOKEN
```

### 4. Arrancar túnel (con la API Compose en marcha)
```powershell
ngrok http 8000 --url https://jasmine-unpainted-oat.ngrok-free.dev
```
Tu dominio estático permanente es `https://jasmine-unpainted-oat.ngrok-free.dev`. No cambia entre ejecuciones.

---

## B) Netlify (panel Angular público)

### 1. Cuenta
1. https://app.netlify.com/signup (con el mismo GitHub `Almucero` es lo más simple).

### 2. Deploy desde el repo
1. **Add new site → Import an existing project → GitHub**  
2. Autoriza y elige `Almucero/observatorio-sismico`  
3. Ajustes de build:
   - Base directory: `frontend`  
   - Build command: `npm run build`  
   - Publish directory: `dist/observatorio/browser` (como `netlify.toml`)  
4. Deploy.

### 3. URL del sitio
Copia `https://ALGO.netlify.app` (o dominio propio).

### 4. Qué me tienes que pasar (en el chat)
1. **Authtoken de ngrok** (o confirma que ya hiciste `ngrok config add-authtoken` en tu PC).  
2. **URL HTTPS de ngrok** cuando el túnel esté activo (o dímelo y lo arranco yo si el token está en `.env`).  
3. **URL de Netlify** (`https://….netlify.app`) para ponerla en `CORS_ORIGINS`.

Con eso configuro CORS, `config.json` de entrega y dejo evidencias de túnel down/up.

## 🎯 GUÍA RÁPIDA - Ollama + VS Code

### ✅ Lo que está configurado:

**Modelos disponibles:**
- `sorc/qwen3.5-claude-4.6-opus:4b` (5.3GB) - Modelo principal ⭐
- `sorc/qwen3.5-claude-4.6-opus:2b` (2.7GB) - Modelo rápido ⚡

**Extensión instalada:**
- ✅ Continue.dev - Asistente AI local

**API Ollama:**
- ✅ Escuchando en `http://localhost:11434`
- ✅ Verificada y funcionando (status 200)

---

### 🚀 PASOS PARA EMPEZAR AHORA:

#### 1️⃣ Asegúrate que Ollama está corriendo
```powershell
ollama list
```
Deberías ver tus 2 modelos listados.

#### 2️⃣ Abre VS Code (si no está abierto) y activa Continue
- Presiona: **`Ctrl+Shift+L`** (o `Cmd+Shift+L` en Mac)
- Se abrirá el panel de Continue en la barra lateral derecha

#### 3️⃣ ¡Comienza a usar!

**Ejemplos de uso:**

📝 **Chat simple:**
```
Escribe una pregunta en el campo de chat y presiona Enter
```

💻 **Editar código:**
- Selecciona código → Click en botón "Edit" o escribe `/edit` en el chat

📚 **Explicar código:**
- Selecciona código → Click en botón "Explain" o escribe `/explain`

🔄 **Refactorizar:**
- Selecciona código → Escribe `/refactor` en el chat

🧪 **Generar tests:**
- Selecciona código → Escribe `/test` en el chat

---

### 📋 DATOS DE CONFIGURACIÓN

| Parámetro | Valor |
|-----------|-------|
| **API Base** | `http://localhost:11434` |
| **Modelo por defecto** | `sorc/qwen3.5-claude-4.6-opus:4b` |
| **Modelo autocompletado** | `sorc/qwen3.5-claude-4.6-opus:2b` |
| **Temperatura** | 0.7 |
| **Max tokens** | 2048 |
| **Context length** | 4096 |

---

### 🎮 ATAJOS ÚTILES EN VS CODE

| Atajo | Función |
|-------|---------|
| `Ctrl+Shift+L` | Abre/cierra panel de Continue |
| Seleccionar + Click | Acciones rápidas (Edit, Explain, etc.) |
| `/edit` | Editar código seleccionado |
| `/explain` | Explicar código |
| `/refactor` | Refactorizar |
| `/test` | Generar tests |

---

### 🔧 TAREAS DISPONIBLES EN VS CODE

Usa `Ctrl+Shift+B` para ver las tareas:
- **Iniciar Ollama** - Inicia el servidor
- **Verificar estado de Ollama** - Lista modelos disponibles

---

### ⚡ RENDIMIENTO

**Modelo 4b (Mejor calidad):**
- Usa más recursos
- Respuestas más precisas y largas
- Ideal para: refactorización, análisis, documentación

**Modelo 2b (Más rápido):**
- Usa menos recursos
- Respuestas rápidas
- Ideal para: autocompletado, sugerencias rápidas

---

### 🆘 SOLUCIONAR PROBLEMAS

**❌ "Continue no encuentra el modelo"**
- Verifica que Ollama esté corriendo: `ollama list`
- Reinicia Continue (recarga VS Code)

**❌ "Ollama no responde"**
- Abre cmd/PowerShell y ejecuta: `ollama serve`
- Verifica puerto 11434 no esté bloqueado

**❌ "Respuestas lentas"**
- Cambia a modelo 2b en el chat (opción en el panel)
- Cierra otras aplicaciones

**❌ "Alto uso de memoria"**
- Usa modelo 2b
- Reduce `maxTokens` en la configuración (edita `.continuerc.json`)

---

### 📁 ARCHIVOS DE CONFIGURACIÓN

Puedes editar estos archivos para personalizar:

1. **Configuración de Continue:**
   - Ubicación: `~\AppData\Roaming\Code\User\extensions\continue\.continuerc.json`
   - Aquí configuras modelos, temperatura, tokens, etc.

2. **Configuración de VS Code:**
   - Ubicación: `.vscode\settings.json`
   - Configuración del editor

3. **Tareas:**
   - Ubicación: `.vscode\tasks.json`
   - Scripts para iniciar Ollama

---

### 🌍 PRIVACIDAD Y SEGURIDAD

✅ **Todo funciona localmente:**
- Los datos NUNCA se envían a internet
- No se envía código a servidores externos
- Solo tu computadora procesa la información
- Privacidad garantizada

---

### 📚 RECURSOS ÚTILES

- Continue.dev: https://continue.dev
- Ollama: https://ollama.ai
- Qwen3.5: https://ollama.com/sorc/qwen3.5-claude-4.6-opus

---

**¿Listo?** Presiona `Ctrl+Shift+L` y ¡comienza! 🚀

# Integración de Ollama con VS Code

## ✅ Configuración Completada

Tu VS Code está configurado para trabajar con Ollama localmente con los siguientes modelos:

- **Qwen 3.5 Claude 4b** (5.3GB) - Modelo principal, mejor calidad
- **Qwen 3.5 Claude 2b** (2.7GB) - Modelo alternativo, más rápido

## 🚀 Cómo Usar

### 1. **Iniciar Ollama**
```powershell
# Opción A: Usar el script helper
.\start_ollama.ps1

# Opción B: Iniciar manualmente
ollama serve
```

### 2. **Usar Continue.dev en VS Code**
- Presiona `Ctrl+Shift+L` para abrir la ventana de Continue
- Escribe tu pregunta o selecciona código y haz clic en los botones de acción
- Comandos disponibles:
  - `/edit` - Editar código
  - `/explain` - Explicar código
  - `/refactor` - Refactorizar
  - `/test` - Generar tests

### 3. **Autocompletado Local**
- Continue proporciona sugerencias de código en tiempo real
- El modelo 2b se usa para autocompletado (más rápido)
- El modelo 4b se usa para respuestas más complejas

## 📋 Características Disponibles

✓ Chat con IA local (sin enviar datos a internet)
✓ Autocompletado de código contextual
✓ Refactorización de código
✓ Generación de comentarios y documentación
✓ Explicación de código existente
✓ Generación de tests

## 🔧 Configuración

- **API Base**: `http://localhost:11434`
- **Modelo por defecto**: `sorc/qwen3.5-claude-4.6-opus:4b`
- **Temperatura**: 0.7 (equilibrio entre creatividad y determinismo)
- **Max tokens**: 2048

## 📂 Archivos de Configuración

- Configuración de Continue: `~\AppData\Roaming\Code\User\extensions\continue\.continuerc.json`
- Script de inicio: `.\start_ollama.ps1`

## 🆘 Solución de Problemas

**P: Continue no responde**
- Verifica que Ollama esté corriendo: `ollama list`
- Revisa que el puerto 11434 no esté bloqueado

**P: Ollama consume mucha memoria**
- Reduce a modelo 2b para tareas menos complejas
- Cierra otras aplicaciones si es necesario

**P: Las respuestas son lentas**
- Usa el modelo 2b para mayor velocidad
- Asegúrate de tener suficiente RAM disponible

## 📝 Notas

- Los modelos son privados: todo funciona en tu computadora
- No requiere conexión a internet para funcionar
- El primer uso tardará más mientras carga el modelo

---

Para más información, visita: https://continue.dev y https://ollama.ai

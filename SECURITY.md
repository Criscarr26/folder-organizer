# Política de Seguridad

## 🔐 Reporte de Vulnerabilidades

Tomamos la seguridad del proyecto **Organizador Automático de Carpetas** muy en serio. Si descubres una vulnerabilidad de seguridad, por favor reporta de forma responsable.

### ⚠️ NO reportes vulnerabilidades en Issues públicos

Los reportes públicos de vulnerabilidades pueden permitir que atacantes las exploten antes de que podamos corregirlas. Por favor, **mantén la confidencialidad**.

---

## 📧 Cómo Reportar Vulnerabilidades

### Método 1: Email Privado (Recomendado)

**Para reportes de vulnerabilidades críticas:**

```
Correo: security@proyecto-organizador.dev
Asunto: [SEGURIDAD] Vulnerabilidad reportada
```

**Información a incluir:**
1. Descripción de la vulnerabilidad
2. Severidad estimada (Crítica/Alta/Media/Baja)
3. Componente afectado (ej: config.py, classifier.py)
4. Pasos para reproducir
5. Impacto potencial
6. Cualquier prueba de concepto (sin explotar)
7. Tu nombre y contacto (opcional si prefieres anonimato)

### Método 2: GitHub Security Advisory

Si tienes cuenta de GitHub:

1. Ve a Security → Advisories
2. Selecciona "Report a vulnerability"
3. Completa el formulario privado
4. Solo los mantenedores ven el reporte

### Método 3: Contacto Anónimo

Si prefieres no identificarte:

- **Email anónimo**: Usa ProtonMail o similar
- **Formulario anónimo**: [Pendiente configurar]
- **Chat privado**: Abre issue genérico y solicita contacto privado

---

## ⏱️ Timeline de Respuesta

Nos comprometemos a:

| Tiempo | Acción |
|--------|--------|
| **24 horas** | Reconocimiento del reporte |
| **48 horas** | Confirmación de vulnerabilidad |
| **3-7 días** | Evaluación inicial |
| **7-30 días** | Parche de seguridad (según severidad) |
| **Mismo día del parche** | Publicación de advisory |

### Por Severidad

- **Crítica**: Parche en 1-2 días
- **Alta**: Parche en 3-5 días
- **Media**: Parche en 5-10 días
- **Baja**: Parche en ciclo normal

### Después de la Corrección

1. **Pre-disclosure**: Notificamos a reportante
2. **Patch release**: Lanzamos versión con fix
3. **Advisory**: Publicamos CVE/advisory
4. **Comunicación**: Avisamos a usuarios

---

## 🛡️ Buenas Prácticas

### Para Usuarios

**Mantén el software actualizado:**

```bash
# Verifica versión
python main.py --version

# Actualiza con pip
pip install --upgrade organizador-carpetas

# Revisa changelog por cambios de seguridad
# Ver CHANGELOG.md
```

**Protege tu configuración:**

```bash
# Nunca guardes credenciales en código
# Usa .env files (no committear)
# Mantén permissions correctos en archivos

chmod 600 config/rules.json  # Solo propietario puede leer
chmod 600 .env              # Protege variables
```

**Usa rutas seguras:**

```python
# ✅ Correcto - Valida entrada
from pathlib import Path
user_path = Path(user_input).resolve()

# ❌ Incorrecto - Path traversal vulnerable
user_path = f"/home/{user_input}"
```

### Para Desarrolladores

**1. Validación de Entrada**

```python
# ✅ Valida siempre
from pathlib import Path

def organize(folder_path: str) -> None:
    path = Path(folder_path).resolve()
    
    # Asegura que está dentro de directorio permitido
    if not str(path).startswith(ALLOWED_BASE):
        raise ValueError("Ruta fuera de límites permitidos")
```

**2. Manejo de Archivos Seguro**

```python
# ✅ Usa context managers
with open(config_file, 'r', encoding='utf-8') as f:
    config = json.load(f)

# ✅ Valida contenido
if not isinstance(config, dict):
    raise ValueError("Configuración inválida")
```

**3. Logging Seguro**

```python
# ✅ No logs de rutas sensibles
logger.info(f"Organizando archivos: {len(files)} archivos")

# ❌ Evita
logger.debug(f"Config en: {config_path}")  # Path completo
logger.debug(f"Usuario: {os.environ['USER']}")  # Variables
```

**4. Dependencias Seguras**

```bash
# ✅ Usa versiones pinned
# requirements.txt
click==8.1.7
python-dotenv==1.0.0
loguru==0.7.2

# ✅ Audita regularmente
pip list --outdated
pip-audit

# ✅ Mantén .venv limpio
rm -rf .venv
python -m venv .venv
pip install -r requirements.txt
```

**5. Permisos de Archivo**

```bash
# ✅ Permisos restrictivos
chmod 600 .env                    # Variables de entorno
chmod 600 config/*.json          # Configuración privada
chmod 755 src/                   # Código ejecutable

# ❌ Nunca
chmod 777 .env                   # Acceso abierto
```

**6. Manejo de Errores**

```python
# ✅ No expongas detalles internos
try:
    organize_folder(path)
except Exception:
    logger.error("Error al organizar carpeta")
    # No incluyas stack trace en producción

# ❌ Evita
except Exception as e:
    print(f"Error: {e}")  # Expone internals
    raise  # En logs públicos
```

---

## 🔍 Qué Vulnerabilidades Aplican

Priorizamos reportes sobre:

### ✅ Aplicable

- **Path Traversal**: Acceso a archivos fuera del scope
- **Code Injection**: Ejecución de código arbitrario
- **Privilege Escalation**: Obtener permisos elevados
- **Information Disclosure**: Exposición de datos sensibles
- **Denial of Service**: Crashear la aplicación
- **Remote Code Execution**: Ejecutar comandos remotos
- **Insecure Dependencies**: Librerías vulnerables conocidas

### ❌ No Aplicable

- **Social Engineering**: Reporta a GitHub directamente
- **General Phishing**: No relacionado con el código
- **Bugs funcionales**: Reporta como issue normal
- **Problemas de rendimiento**: Issue normal
- **Typos o estilo**: Pull Request normal
- **Vulnerabilidades 0-day sin parche disponible**: Contacta responsablemente

---

## 📋 Prácticas de Desarrollo Seguro

### Checklist de Seguridad

Antes de hacer commit:

- [ ] No hay credenciales en el código
- [ ] No hay secrets en logs
- [ ] Todas las entradas están validadas
- [ ] Manejo de excepciones es seguro
- [ ] Permisos de archivos son correctos
- [ ] Dependencias están actualizadas
- [ ] No hay path traversal possible
- [ ] SQL injection no aplica (no usamos SQL)

### Pre-Commit Hook Seguro

```bash
# .git/hooks/pre-commit
#!/bin/bash

# Detecta secrets potenciales
if git diff --cached | grep -E "(password|secret|api_key|token)" -i; then
    echo "❌ Error: Posible secret detectado"
    exit 1
fi

# Valida sintaxis Python
python -m py_compile src/*.py || exit 1

# Ejecuta tests
pytest tests/ -q || exit 1

echo "✅ Pre-commit checks passed"
```

### GitHub Actions para Seguridad

```yaml
# .github/workflows/security.yml
name: Security Checks

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run pip-audit
        run: |
          pip install pip-audit
          pip-audit
      
      - name: Check for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
```

---

## 📦 Gestión de Dependencias

### Mantener Dependencias Seguras

```bash
# 1. Auditar vulnerabilidades
pip-audit

# 2. Usar versiones pinned
pip install --no-deps pip-tools
pip-compile requirements.txt

# 3. Revisar cambios regularmente
pip list --outdated

# 4. Usar security advisories
# GitHub notifica automáticamente
```

### Estructura de requirements

```txt
# requirements.txt - Dependencias principales
click==8.1.7              # CLI
python-dotenv==1.0.0      # Variables de entorno
loguru==0.7.2             # Logging

# requirements-dev.txt - Solo desarrollo
pytest==7.4.3             # Testing
pylint==3.0.0             # Linting
pytest-cov==4.1.0         # Coverage
```

---

## 🚨 Vulnerabilidades Conocidas

Actualmente:

- ✅ **Ninguna conocida**

Si descubres una, por favor reporta confidencialmente.

---

## 📜 Licencia de Disclosure

**Full Disclosure después de:**
- 90 días desde confirmación de fix
- o 7 días si fix está en producción

**Responsibilidad del Reportante:**
- No compartir detalles públicamente antes del fix
- No explotar la vulnerabilidad
- Trabajar de buena fe

---

## 🏥 Respuesta a Incidentes de Seguridad

### Plan de Contingencia

1. **Detección**
   - Monitor de vulnerabilidades
   - Reportes de usuarios
   - Auditorías regulares

2. **Contención**
   - Desactiva característica afectada
   - Notifica a usuarios
   - Prepara fix

3. **Erradicación**
   - Desarrolla parche
   - Testea completamente
   - Revisa código relacionado

4. **Recuperación**
   - Release de versión segura
   - Publica advisory
   - Monitorea explotación

5. **Postmortem**
   - Análisis de causa raíz
   - Mejoras a procesos
   - Documentación

---

## 📞 Contacto de Seguridad

**Email Principal:**
```
security@proyecto-organizador.dev
```

**Contactos de Escalación:**
| Persona | Rol | Email |
|---------|-----|-------|
| [Nombre] | Mantenedor Principal | [email] |
| [Nombre] | Revisor de Seguridad | [email] |

**Tiempo de Respuesta Esperado:**
- Email: 24 horas
- Urgencias: contacto telefónico

---

## 📚 Recursos de Seguridad

- 🔗 [OWASP Top 10](https://owasp.org/Top10/)
- 🐍 [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)
- 📦 [Python Package Security](https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/)
- 🛡️ [CVE Database](https://cve.mitre.org/)
- 🔐 [Secure Coding Guidelines](https://www.securecoding.cert.org/)

---

## Versionado de Esta Política

**Versión**: 1.0.0  
**Fecha**: 2026-06-03  
**Próxima Revisión**: 2027-06-03

### Cambios Futuros

- [ ] Configurar email de seguridad
- [ ] Integrar GitHub Security Advisories
- [ ] Implementar SBOM (Software Bill of Materials)
- [ ] Auditoría de seguridad externa

---

**Gracias por ayudar a mantener este proyecto seguro.** 🛡️

*Toda la información reportada será tratada confidencialmente y solo compartida con el equipo de desarrollo cuando sea necesario.*

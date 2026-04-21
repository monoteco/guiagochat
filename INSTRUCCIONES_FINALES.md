# INSTRUCCIONES FINALES - EJECUCIÓN EN MODAL

## 1. Ejecuta build_memoria en Modal (desde tu máquina local)

Modal debe correr donde tienes credenciales. En PowerShell local:

\\\powershell
cd c:\Users\germa\Downloads\development\GuiaGo\guiagochat
modal run modal-inference/build_memoria_modal.py
\\\

Esto:
- Procesa 3,496 emails
- Crea fichas de 1,000+ contactos externos
- Genera resumen ejecutivo global
- Toma ~5-10 minutos
- NO afecta al servidor local

Resultado: colección 'memoria' completa en ChromaDB

## 2. Chat funciona AHORA con 244 docs previos

Sin esperar a Modal completo:
- Abre: http://100.103.98.125:8000/
- Selecciona colección: 'memoria (contexto)'
- Haz preguntas sobre clientes y negocios

## 3. Verificar estado en servidor:

\\\ash
ssh caro@100.103.98.125 \"curl http://localhost:8000/health\"
ssh caro@100.103.98.125 \"tail -50 ~/guiagochat/logs/api.log\"
\\\

## Resumen Técnico:

✓ Git user: Carl
✓ Dependencias: Auditadas y pinchadas a versiones seguras
✓ Proyecto: Monorepo limpio (sin .py antiguos, credenciales aisladas)
✓ Backend: FastAPI en http://100.103.98.125:8000/
✓ Frontend: Interface de chat lista
✓ Modal: build_memoria completamente desacoplado

Próximo: Ejecuta \modal run\ para completar colección memoria → Chat con contexto completo


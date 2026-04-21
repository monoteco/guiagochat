# Modal Inference Workspace

This folder contains scripts and configs for running heavy inference workloads on Modal.com.

## Purpose

- Keep the local server lightweight and responsive
- Offload long-running tasks (email analysis, model training) to Modal
- Maintain fast API response times for frontend

## Scripts

### build_memoria_modal.py (Planned)
Modal-native version of build_memoria.py that:
- Runs entirely in Modal infrastructure
- Processes 3,500+ emails asynchronously
- Updates ChromaDB via remote client
- No impact on local server resources

**Usage (when ready):**
\\\ash
modal run build_memoria_modal.py --emails-data /path/to/emails.json
\\\

## Configuration

Set these Modal environment variables:
- \MODAL_API_TOKEN\: Your Modal API token (from https://modal.com/settings)
- \CHROMA_DB_PATH\: Path to ChromaDB (default: ./chroma_db)

## Migration Note

Previously, \uild_memoria.py\ ran on the local server (caro@100.103.98.125) and consumed:
- 200+ MB RAM
- 6.5% CPU consistently  
- Blocked server for 2+ hours

By moving to Modal:
- Server only handles API requests
- Parallel processing at scale
- Resumable jobs with checkpoints
- Automatic retry logic

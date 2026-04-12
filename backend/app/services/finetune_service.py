"""
finetune_service.py — Fine-tuning job management via subprocess.

Jobs run as nohup background processes. State is persisted to
data/finetune/jobs.json so it survives API restarts.
"""

import json
import os
import subprocess
import time
from pathlib import Path

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_JOBS_FILE = _PROJECT_ROOT / "data" / "finetune" / "jobs.json"
_LOG_DIR   = _PROJECT_ROOT / "logs"
_VENV_PY   = _PROJECT_ROOT / "venv" / "bin" / "python3"


def _load_jobs() -> dict:
    if _JOBS_FILE.exists():
        try:
            return json.loads(_JOBS_FILE.read_text())
        except Exception:
            pass
    return {}


def _save_jobs(jobs: dict):
    _JOBS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _JOBS_FILE.write_text(json.dumps(jobs, indent=2))


def generate_dataset(config: str = "finetune/config.yaml") -> dict:
    log_path = _LOG_DIR / "finetune_dataset.log"
    cmd = [
        str(_VENV_PY), str(_PROJECT_ROOT / "finetune" / "generate_dataset.py"),
        "--config", str(_PROJECT_ROOT / config),
    ]
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(_PROJECT_ROOT),
    )
    output = result.stdout + result.stderr
    log_path.write_text(output)
    if result.returncode != 0:
        raise RuntimeError(f"Dataset generation failed:\n{output[-2000:]}")

    # Parse stats from output
    total = train = val = 0
    for line in output.splitlines():
        if "Total pairs" in line:
            try:
                total = int(line.split(":")[-1].strip())
            except Exception:
                pass
        elif "Train" in line and "→" in line:
            try:
                train = int(line.split(":")[1].split("→")[0].strip())
            except Exception:
                pass
        elif "Val" in line and "→" in line:
            try:
                val = int(line.split(":")[1].split("→")[0].strip())
            except Exception:
                pass
    return {"status": "ok", "total": total, "train": train, "val": val, "log": output[-1000:]}


def start_training(model: str, config: str = "finetune/config.yaml") -> dict:
    job_id = f"{model}_{int(time.time())}"
    log_path = _LOG_DIR / f"finetune_train_{job_id}.log"
    cmd = [
        "nohup",
        str(_VENV_PY), str(_PROJECT_ROOT / "finetune" / "train.py"),
        "--model", model,
        "--config", str(_PROJECT_ROOT / config),
    ]
    with open(log_path, "w") as log_f:
        proc = subprocess.Popen(
            cmd,
            stdout=log_f,
            stderr=log_f,
            cwd=str(_PROJECT_ROOT),
            start_new_session=True,
        )

    jobs = _load_jobs()
    jobs[job_id] = {
        "job_id": job_id,
        "model": model,
        "pid": proc.pid,
        "status": "running",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "log_path": str(log_path),
    }
    _save_jobs(jobs)
    return {"job_id": job_id, "pid": proc.pid, "status": "running", "log_path": str(log_path)}


def get_training_status(job_id: str) -> dict:
    jobs = _load_jobs()
    job = jobs.get(job_id)
    if not job:
        raise KeyError(f"Job {job_id} not found")

    # Check if process still running
    pid = job.get("pid")
    running = False
    if pid:
        try:
            os.kill(pid, 0)
            running = True
        except OSError:
            running = False

    # Read last lines of log
    log_tail = ""
    log_path = Path(job.get("log_path", ""))
    if log_path.exists():
        lines = log_path.read_text(errors="replace").splitlines()
        log_tail = "\n".join(lines[-30:])

    # Determine status
    if running:
        status = "running"
    elif "Training complete" in log_tail:
        status = "completed"
    elif "Error" in log_tail or "Traceback" in log_tail:
        status = "error"
    else:
        status = "stopped"

    if status != "running" and job.get("status") == "running":
        job["status"] = status
        jobs[job_id] = job
        _save_jobs(jobs)

    return {**job, "status": status, "log_tail": log_tail, "running": running}


def list_jobs() -> list:
    jobs = _load_jobs()
    return list(jobs.values())


def start_export(model: str, config: str = "finetune/config.yaml") -> dict:
    job_id = f"export_{model}_{int(time.time())}"
    log_path = _LOG_DIR / f"finetune_export_{job_id}.log"
    cmd = [
        "nohup",
        str(_VENV_PY), str(_PROJECT_ROOT / "finetune" / "export_to_ollama.py"),
        "--model", model,
        "--config", str(_PROJECT_ROOT / config),
    ]
    with open(log_path, "w") as log_f:
        proc = subprocess.Popen(
            cmd,
            stdout=log_f,
            stderr=log_f,
            cwd=str(_PROJECT_ROOT),
            start_new_session=True,
        )

    jobs = _load_jobs()
    jobs[job_id] = {
        "job_id": job_id,
        "model": model,
        "pid": proc.pid,
        "status": "running",
        "type": "export",
        "started_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "log_path": str(log_path),
    }
    _save_jobs(jobs)
    return {"job_id": job_id, "pid": proc.pid, "status": "running"}
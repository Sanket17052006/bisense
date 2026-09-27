#!/usr/bin/env python3
"""
BISense AI - Complete Startup Script

This script:
1. Creates a virtual environment and installs Python dependencies
2. Starts PostgreSQL with pgvector via docker-compose
3. Runs database migrations & seeds demo data (standards, QCOs, labs, schemes)
4. Builds RAG indexes (FAISS + BM25) from raw documents
5. Starts the FastAPI backend server
"""

import os
import sys
import time
import subprocess
import signal
import atexit
from pathlib import Path
from typing import Optional

BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
VENV_DIR = BACKEND_DIR / ".venv"
DATA_DIR = BASE_DIR / "data"

# Global process handles for cleanup
_processes = []


def cleanup():
    """Kill all subprocesses on exit."""
    for p in _processes:
        try:
            p.terminate()
            p.wait(timeout=5)
        except Exception:
            try:
                p.kill()
            except Exception:
                pass


atexit.register(cleanup)


def run_cmd(cmd: list[str], cwd: Optional[Path] = None, env: Optional[dict] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a command and return the result."""
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or BASE_DIR, env=env or os.environ.copy(), capture_output=True, text=True)
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}")
    return result


def run_bg(cmd: list[str], cwd: Optional[Path] = None, env: Optional[dict] = None) -> subprocess.Popen:
    """Run a command in background and track it for cleanup."""
    print(f"$ {' '.join(cmd)} (background)")
    p = subprocess.Popen(cmd, cwd=cwd or BASE_DIR, env=env or os.environ.copy())
    _processes.append(p)
    return p


def wait_for_port(host: str, port: int, timeout: int = 60) -> bool:
    """Wait for a TCP port to become available."""
    import socket
    start = time.time()
    while time.time() - start < timeout:
        try:
            with socket.create_connection((host, port), timeout=2):
                return True
        except Exception:
            time.sleep(1)
    return False


def get_venv_python() -> Path:
    """Get the Python executable from the virtual environment."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def get_venv_pip() -> Path:
    """Get the pip executable from the virtual environment."""
    if sys.platform == "win32":
        return VENV_DIR / "Scripts" / "pip.exe"
    return VENV_DIR / "bin" / "pip"


def step(name: str, fn):
    """Run a step with timing and error handling."""
    print(f"\n{'='*60}")
    print(f"STEP: {name}")
    print(f"{'='*60}")
    start = time.time()
    try:
        fn()
        print(f"✓ {name} completed in {time.time() - start:.1f}s")
    except Exception as e:
        print(f"✗ {name} FAILED: {e}")
        raise


def step0_setup_venv():
    """Create virtual environment and install dependencies."""
    if not VENV_DIR.exists():
        print("Creating virtual environment...")
        run_cmd([sys.executable, "-m", "venv", str(VENV_DIR)])
    
    pip = get_venv_pip()
    print("Installing dependencies...")
    run_cmd([str(pip), "install", "-r", "requirements.txt"], cwd=BACKEND_DIR)


def step1_start_postgres():
    """Start PostgreSQL with pgvector via docker-compose."""
    # Check if already running
    result = run_cmd(["docker", "compose", "ps", "-q", "postgres"], check=False)
    if result.stdout.strip():
        print("PostgreSQL already running")
        return

    run_cmd(["docker", "compose", "up", "-d", "postgres"])
    
    # Wait for health check
    print("Waiting for PostgreSQL to be healthy...")
    if not wait_for_port("localhost", 5432, timeout=60):
        raise RuntimeError("PostgreSQL did not become ready in time")


def step2_seed_database():
    """Run database migrations and seed demo data."""
    # Set DATABASE_URL for PostgreSQL
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+psycopg2://bisense:bisense@localhost:5432/bisense"
    
    # Run seed with --reset to ensure clean state
    python = get_venv_python()
    run_cmd([
        str(python), "-m", "app.db.seed", "--reset"
    ], cwd=BACKEND_DIR, env=env)


def step3_build_rag_indexes():
    """Build FAISS and BM25 indexes from raw documents."""
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+psycopg2://bisense:bisense@localhost:5432/bisense"
    
    # Run the ingestion pipeline
    python = get_venv_python()
    run_cmd([
        str(python), "-m", "app.rag.pipeline.ingest_pipeline"
    ], cwd=BACKEND_DIR, env=env)
    
    # Verify indexes were created
    faiss_index = BASE_DIR / "backend" / "vector_db" / "faiss" / "index.faiss"
    bm25_index = BASE_DIR / "backend" / "vector_db" / "bm25" / "bm25_index.pkl"
    
    if not faiss_index.exists():
        raise RuntimeError(f"FAISS index not created at {faiss_index}")
    if not bm25_index.exists():
        raise RuntimeError(f"BM25 index not created at {bm25_index}")
    
    print(f"✓ FAISS index: {faiss_index.stat().st_size} bytes")
    print(f"✓ BM25 index: {bm25_index.stat().st_size} bytes")


def step4_start_backend():
    """Start the FastAPI backend server."""
    env = os.environ.copy()
    env["DATABASE_URL"] = "postgresql+psycopg2://bisense:bisense@localhost:5432/bisense"
    
    # Start backend in background
    python = get_venv_python()
    p = run_bg([
        str(python), "-m", "uvicorn", "app.main:app",
        "--host", "0.0.0.0", "--port", "8000"
    ], cwd=BACKEND_DIR, env=env)
    
    # Wait for backend to be ready
    print("Waiting for backend to start...")
    if not wait_for_port("localhost", 8000, timeout=30):
        raise RuntimeError("Backend did not start in time")
    
    # Give it a moment to fully initialize
    time.sleep(2)
    
    return p


def main():
    print("BISense AI - Complete System Startup")
    print("=" * 60)
    
    # Check prerequisites
    if not (BASE_DIR / "docker-compose.yml").exists():
        print("Error: docker-compose.yml not found")
        sys.exit(1)
    
    if not (BACKEND_DIR / "requirements.txt").exists():
        print("Error: backend/requirements.txt not found")
        sys.exit(1)
    
    # Check if .env exists with API keys
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        print("Warning: .env file not found. Creating from example...")
        run_cmd(["cp", ".env.example", ".env"], check=False)
    
    # Verify API keys are set
    with open(env_file) as f:
        env_content = f.read()
    if "GROQ_API_KEY" not in env_content and "OPENAI_API_KEY" not in env_content:
        print("Warning: No LLM API key found in .env. RAG answers will use rule-based fallback.")
    
    try:
        step("Setup Virtual Environment & Install Dependencies", step0_setup_venv)
        step("Start PostgreSQL (pgvector)", step1_start_postgres)
        step("Seed Database (standards, QCOs, labs, schemes)", step2_seed_database)
        step("Build RAG Indexes (FAISS + BM25)", step3_build_rag_indexes)
        step("Start Backend Server", step4_start_backend)
        
        print("\n" + "=" * 60)
        print("✓ BISense AI is RUNNING")
        print("=" * 60)
        print("\nBackend: http://localhost:8000")
        print("API Docs: http://localhost:8000/docs")
        print("Health: http://localhost:8000/api/health")
        print("\nPress Ctrl+C to stop all services")
        print("=" * 60)
        
        # Keep running until interrupted
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\nShutting down...")
    except Exception as e:
        print(f"\n\n✗ FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
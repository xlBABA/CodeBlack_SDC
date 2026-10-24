# Running the project

- Keep the existing Python/FastAPI backend and React/Vite frontend structure.
- Run `bash scripts/post-merge.sh` from the project root to install dependencies
  and build the frontend. This also runs automatically after task merges.
- Start the existing **Start Backend** workflow. Its command is
  `cd backend && DATABASE_URL=sqlite:///./futurepath.db python start.py`.
- The backend listens on port 8000 by default and serves `frontend/dist`.
- Backend startup creates missing database tables; the setup hook does not
  reset data or perform destructive schema migrations.
- Python dependencies are installed into Replit's writable `.pythonlibs`
  directory because the system Python installation is managed by Nix.
- Keep service credentials in Replit Secrets. Do not run paid extraction probes
  without explicit approval.

The post-merge hook prepares the workspace and reconciles workflows; it does not
publish a new release.

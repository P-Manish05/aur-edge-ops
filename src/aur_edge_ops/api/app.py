"""FastAPI application factory for the software-only simulation and dashboard."""

from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from aur_edge_ops.simulation.network import NetworkSimulator

# Global simulator instance for Milestone 1 in-memory prototype
simulator = NetworkSimulator()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AUR Edge Ops (Simulated)",
        description="Software-only simulation dashboard and API.",
        version="0.1.0",
    )

    templates_dir = Path(__file__).parent.parent / "dashboard" / "templates"
    templates = Jinja2Templates(directory=str(templates_dir))

    @app.get("/", response_class=HTMLResponse)
    async def get_dashboard(request: Request) -> Any:
        state = simulator.get_state()
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={"state": state},
        )

    @app.get("/api/state")
    async def get_state() -> Dict[str, Any]:
        """Returns the simulated network state as JSON."""
        return simulator.get_state()

    @app.post("/action/fail-primary")
    async def fail_primary() -> RedirectResponse:
        """Simulates failure of L2 (R1-R2 link on the primary path)."""
        simulator.fail_link("L2")
        return RedirectResponse(url="/", status_code=303)

    @app.post("/action/recover")
    async def recover_all() -> RedirectResponse:
        """Restores all simulated links to UP."""
        simulator.recover_all()
        return RedirectResponse(url="/", status_code=303)

    return app


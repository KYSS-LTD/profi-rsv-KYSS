from fastapi import APIRouter, Response
from app.monitoring.metrics import render_prometheus

router = APIRouter(tags=["Monitoring"])


@router.get("/metrics", summary="Prometheus metrics", description="Expose Komandus Prometheus counters.")
def metrics():
    return Response(render_prometheus(), media_type="text/plain; version=0.0.4")

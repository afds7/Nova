"""Carga controlada dos endpoints de leitura do Hub NOVA.

Execute somente contra ambiente local ou staging preparado para testes.
O profile_id deve apontar para um perfil sintético, sem dados pessoais reais.
"""

from __future__ import annotations

import os
from uuid import UUID

from locust import HttpUser, LoadTestShape, between, events, task


PROFILE_ID = os.getenv("NOVA_PROFILE_ID", "").strip()
MAX_DASHBOARD_MS = int(os.getenv("NOVA_MAX_DASHBOARD_MS", "1000"))
MAX_MISSIONS_MS = int(os.getenv("NOVA_MAX_MISSIONS_MS", "3000"))
MAX_PORTFOLIO_MS = int(os.getenv("NOVA_MAX_PORTFOLIO_MS", "1000"))


@events.test_start.add_listener
def validate_test_configuration(environment, **kwargs):
    """Impede iniciar uma carga acidental sem um perfil sintético definido."""
    if not PROFILE_ID:
        raise RuntimeError(
            "Defina NOVA_PROFILE_ID com o UUID de um perfil sintético antes do teste."
        )
    try:
        UUID(PROFILE_ID)
    except ValueError as exc:
        raise RuntimeError("NOVA_PROFILE_ID precisa ser um UUID válido.") from exc


def validate_response(response, max_ms: int) -> None:
    """Marca HTTP 200 lento como falha de performance, não como sucesso."""
    if response.status_code != 200:
        response.failure(f"status inesperado: {response.status_code}")
        return
    elapsed_ms = response.elapsed.total_seconds() * 1000
    if elapsed_ms > max_ms:
        response.failure(
            f"latência acima do limite: {elapsed_ms:.0f}ms > {max_ms}ms"
        )


class NovaStudentUser(HttpUser):
    """Representa um aluno navegando nas telas que mais recebem refresh."""

    wait_time = between(0.3, 1.2)

    @task(5)
    def open_dashboard(self):
        with self.client.get(
            "/api/dashboard/resumo/",
            params={"profile_id": PROFILE_ID},
            name="GET /api/dashboard/resumo/",
            catch_response=True,
        ) as response:
            validate_response(response, MAX_DASHBOARD_MS)

    @task(3)
    def load_suggested_missions(self):
        with self.client.get(
            "/api/missoes/sugeridas/",
            params={"profile_id": PROFILE_ID},
            name="GET /api/missoes/sugeridas/",
            catch_response=True,
        ) as response:
            validate_response(response, MAX_MISSIONS_MS)

    @task(2)
    def list_portfolio(self):
        with self.client.get(
            "/api/portfolio/evidencias/",
            params={"profile_id": PROFILE_ID},
            name="GET /api/portfolio/evidencias/",
            catch_response=True,
        ) as response:
            validate_response(response, MAX_PORTFOLIO_MS)


class SevenDayRamp(LoadTestShape):
    """Rampa conservadora: 10 -> 50 -> 100 usuários concorrentes."""

    use_common_options = True

    stages = [
        {"duration": 60, "users": 10, "spawn_rate": 2},
        {"duration": 180, "users": 50, "spawn_rate": 5},
        {"duration": 300, "users": 100, "spawn_rate": 10},
    ]

    def tick(self):
        elapsed = self.get_run_time()

        # Permite smoke tests explícitos com -u/-r/-t sem serem ignorados pela shape.
        options = self.runner.environment.parsed_options
        users = getattr(options, "users", None) or getattr(options, "num_users", None)
        run_time = getattr(options, "run_time", None)
        spawn_rate = getattr(options, "spawn_rate", None)
        if users and run_time:
            if elapsed < run_time:
                return users, spawn_rate
            return None

        for stage in self.stages:
            if elapsed < stage["duration"]:
                return stage["users"], stage["spawn_rate"]
        return None

"""Neo4j AuraDB driver lifecycle."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[3] / ".env")

_driver = None


def get_neo4j_credentials() -> tuple[str | None, str | None, str | None]:
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    return uri, user, password


def is_neo4j_configured() -> bool:
    uri, user, password = get_neo4j_credentials()
    if not all([uri, user, password]):
        return False
    # Treat placeholder values from .env.example as unset
    if "xxxxxxxx" in (uri or ""):
        return False
    if password in {"your-neo4j-password", "password"}:
        return False
    return True


def get_driver():
    """
    Return a shared Neo4j driver when credentials are configured.
    Returns None when AuraDB is not configured (caller should use JSON fallback).
    """
    global _driver

    if not is_neo4j_configured():
        return None

    if _driver is not None:
        return _driver

    from neo4j import GraphDatabase

    uri, user, password = get_neo4j_credentials()
    _driver = GraphDatabase.driver(uri, auth=(user, password))
    return _driver


def verify_connectivity() -> bool:
    """Return True if the driver can reach Neo4j."""
    driver = get_driver()
    if driver is None:
        return False
    try:
        driver.verify_connectivity()
        return True
    except Exception:
        return False


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None

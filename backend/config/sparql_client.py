from __future__ import annotations

import os
import threading
from typing import Any, Dict, Optional

from SPARQLWrapper import SPARQLWrapper, JSON, BASIC, DIGEST
from dotenv import load_dotenv

load_dotenv()

__sparql_client: Optional[SPARQLWrapper] = None
__lock = threading.Lock()


def _build_client() -> SPARQLWrapper:
    endpoint = os.environ.get("SPARQL_ENDPOINT")
    if not endpoint:
        raise RuntimeError(
            "SPARQL_ENDPOINT is not set. Define it in your environment or .env file."
        )

    client = SPARQLWrapper(endpoint)
    client.setReturnFormat(JSON)

    method = (os.getenv("SPARQL_METHOD") or "GET").upper()
    if method not in {"GET", "POST"}:
        method = "GET"
    client.setMethod(method)

    try:
        timeout = int(os.getenv("SPARQL_TIMEOUT", "30"))
    except ValueError:
        timeout = 30
    try:
        client.setTimeout(timeout)
    except Exception:
        pass

    auth_type = (os.getenv("SPARQL_AUTH_TYPE") or "NONE").upper()
    user = os.getenv("SPARQL_USER")
    password = os.getenv("SPARQL_PASSWORD")

    if auth_type == "BASIC" and user and password:
        client.setCredentials(user, password, realm=None, auth=BASIC)
    elif auth_type == "DIGEST" and user and password:
        client.setCredentials(user, password, realm=None, auth=DIGEST)

    token = os.getenv("SPARQL_TOKEN")
    if token:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            client.setHTTPAuth("CUSTOM")
        except Exception:
            pass
        client.addCustomHttpHeader("Authorization", f"Bearer {token}")
        # It is fine to add only the Authorization header; others can be added by callers.

    return client


def get_sparql() -> SPARQLWrapper:
    """Return the global SPARQLWrapper client, creating it on first use.
    """
    global __sparql_client
    if __sparql_client is None:
        with __lock:
            if __sparql_client is None:
                __sparql_client = _build_client()
    return __sparql_client


def execute_query(query: str) -> Dict[str, Any]:
    """Execute a SPARQL SELECT/DESCRIBE/ASK/CONSTRUCT query and return JSON results.

    For SELECT queries, returns a dict with `head` and `results` keys.
    For ASK queries, returns e.g. `{ 'boolean': True }`.
    """
    client = get_sparql()
    client.setQuery(query)
    result = client.query().convert()
    return result


__all__ = [
    "get_sparql",
    "execute_query",
]

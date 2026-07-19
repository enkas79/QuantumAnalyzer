"""
Controllo aggiornamenti su GitHub Releases — implementazione canonica.

Unifica i due controlli che StockAnalyzer (urllib, best-effort senza retry)
e QuantumValue (requests + retry tenacity, scelta dell'asset per piattaforma)
implementavano separatamente. La base e' quella di QuantumValue, che era la
piu' robusta; `quantumanalyzer.technical.updater` e
`quantumanalyzer.fundamental.models` delegano qui mantenendo le rispettive
API storiche (UpdateInfo | None da una parte, tupla dall'altra).

Autore: Enrico Martini
"""

import sys
from typing import Any, Dict, List, Optional, Tuple

import requests

try:
    from tenacity import retry, stop_after_attempt, wait_exponential
    TENACITY_AVAILABLE = True
except ImportError:
    TENACITY_AVAILABLE = False


def _retry_request(func):
    """Retry con backoff esponenziale sulle chiamate HTTP (se tenacity c'e').

    reraise=True: esauriti i tentativi riemerge l'eccezione originale
    (ValueError), non un tenacity.RetryError — i chiamanti (worker GUI)
    catturano ValueError e senza reraise non vedrebbero mai l'errore.
    """
    if TENACITY_AVAILABLE:
        return retry(
            stop=stop_after_attempt(3),
            wait=wait_exponential(multiplier=1, min=2, max=10),
            reraise=True,
        )(func)
    return func


def _default_headers() -> Dict[str, str]:
    from ..fundamental.config import HTTP_HEADERS
    return HTTP_HEADERS


def _default_timeout() -> int:
    from ..fundamental.config import HTTP_TIMEOUT
    return HTTP_TIMEOUT


def parse_version(v: str) -> Tuple[int, ...]:
    """"v1.2.3" / "1.2.3" -> (1, 2, 3); segmenti non numerici valgono 0."""
    cleaned = v.lstrip("vV")
    parts: List[int] = []
    for chunk in cleaned.split("."):
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def pick_release_asset(assets: List[Dict[str, Any]], platform: str = sys.platform) -> str:
    """
    Sceglie dall'elenco degli asset di una GitHub Release quello adatto
    alla piattaforma corrente.

    Args:
        assets: Lista di asset della release (API GitHub).
        platform: Identificatore piattaforma (sys.platform).

    Returns:
        str: URL di download diretto, o stringa vuota se nessun asset combacia.
    """
    if platform.startswith("win"):
        suffix = ".exe"
    elif platform == "darwin":
        suffix = "_macos.zip"
    else:
        suffix = ".deb"

    for asset in assets:
        name = str(asset.get('name', '')).lower()
        if name.endswith(suffix):
            return str(asset.get('browser_download_url', ''))
    return ""


@_retry_request
def check_for_updates(
    current_version: str,
    repo_path: str,
    timeout: Optional[int] = None,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[bool, str, str]:
    """
    Verifica la presenza di una nuova release su GitHub via API pubblica.

    Args:
        current_version: Versione attuale dell'applicazione.
        repo_path: Path del repository GitHub (es. 'utente/repo').
        timeout: Timeout HTTP in secondi (default: config dell'app).
        headers: Header HTTP (default: config dell'app).

    Returns:
        Tuple[bool, str, str]: (aggiornamento_disponibile, tag_versione,
        url_download). L'URL punta all'asset adatto alla piattaforma corrente,
        con fallback alla pagina HTML della release.

    Raises:
        ValueError: Su errore di rete (dopo i retry).
    """
    api_url: str = f"https://api.github.com/repos/{repo_path}/releases/latest"
    try:
        response = requests.get(
            api_url,
            headers=headers if headers is not None else _default_headers(),
            timeout=timeout if timeout is not None else _default_timeout(),
        )
        if response.status_code == 404:
            return False, current_version, ""
        response.raise_for_status()
        data: dict = response.json()
        latest_tag: str = data.get('tag_name', '').replace('v', '')
        html_url: str = pick_release_asset(data.get('assets', [])) or data.get('html_url', '')

        if not latest_tag:
            return False, current_version, ""

        curr_v_clean: str = current_version.replace('v', '')
        update_available: bool = parse_version(latest_tag) > parse_version(curr_v_clean)
        return update_available, latest_tag, html_url
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Impossibile verificare gli aggiornamenti: {str(e)}")

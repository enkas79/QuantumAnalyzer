"""
Cache locale SQLite a payload JSON — implementazione condivisa (M5).

I due programmi originali avevano due cache indipendenti: QuantumValue un
database SQLite con scadenza a ore per i fondamentali, StockAnalyzer file CSV
per-chiave con scadenza a minuti per l'OHLCV. Come da piano di migrazione, le
due cache restano separate (TTL diversi per dati con vita diversa) ma girano
sulla stessa implementazione, parametrizzata per percorso database e TTL.

Autore: Enrico Martini
"""

import json
import logging
import os
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

logger = logging.getLogger("QuantumAnalyzer")


class JsonCache:
    """Store chiave -> payload JSON su SQLite, con scadenza per riga.

    La connessione e' unica e riutilizzata tra le chiamate (aprire/chiudere
    una connessione ad ogni get/set costa, quando si analizzano piu' ticker
    in sequenza) e protetta da un lock perche' i fetch girano su QThread
    separati.
    """

    def __init__(self, db_path: str, ttl_seconds: float) -> None:
        self.db_path = db_path
        self.ttl_seconds = ttl_seconds
        self._conn: Optional[sqlite3.Connection] = None
        self._lock = threading.Lock()

    def _get_connection(self) -> sqlite3.Connection:
        if self._conn is None:
            cache_dir = os.path.dirname(self.db_path)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

            self._conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self._conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    timestamp DATETIME NOT NULL
                )
            """)
            self._conn.commit()
        return self._conn

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Recupera un payload se presente e non scaduto (i record scaduti
        vengono rimossi fisicamente al primo accesso)."""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT value, timestamp FROM cache WHERE key = ?", (key,))
                result = cursor.fetchone()

            if result:
                value_json, timestamp_str = result
                timestamp = datetime.fromisoformat(timestamp_str)
                if datetime.now() - timestamp < timedelta(seconds=self.ttl_seconds):
                    logger.debug(f"Cache hit per chiave: {key}")
                    return json.loads(value_json)
                logger.debug(f"Cache scaduta per chiave: {key}")
                self.remove(key)
            return None
        except Exception as e:
            logger.error(f"Errore nel recupero dalla cache per {key}: {str(e)}")
            return None

    def set(self, key: str, value: Dict[str, Any]) -> bool:
        """Salva un payload JSON-serializzabile; True se riuscito."""
        try:
            value_json = json.dumps(value)
            timestamp = datetime.now().isoformat()
            with self._lock:
                conn = self._get_connection()
                conn.execute(
                    "INSERT OR REPLACE INTO cache (key, value, timestamp) VALUES (?, ?, ?)",
                    (key, value_json, timestamp)
                )
                conn.commit()
            logger.debug(f"Cache salvata per chiave: {key}")
            return True
        except Exception as e:
            logger.error(f"Errore nel salvataggio nella cache per {key}: {str(e)}")
            return False

    def remove(self, key: str) -> bool:
        """Rimuove una chiave; True se l'operazione e' riuscita."""
        try:
            with self._lock:
                conn = self._get_connection()
                conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Errore nella rimozione dalla cache per {key}: {str(e)}")
            return False

    def clear(self) -> bool:
        """Svuota completamente la cache; True se riuscito."""
        try:
            with self._lock:
                conn = self._get_connection()
                conn.execute("DELETE FROM cache")
                conn.commit()
            logger.info(f"Cache svuotata: {self.db_path}")
            return True
        except Exception as e:
            logger.error(f"Errore nello svuotamento della cache: {str(e)}")
            return False

    def stats(self) -> Dict[str, int]:
        """Conteggi (totale, scaduti, validi) sulle righe presenti."""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM cache")
                total = cursor.fetchone()[0]

                current_time = datetime.now().isoformat()
                # datetime(timestamp) normalizza il formato ISO (separatore
                # 'T', microsecondi) a quello di SQLite prima del confronto:
                # senza, il paragone fra stringhe eterogenee e' sempre falso.
                cursor.execute(
                    "SELECT COUNT(*) FROM cache "
                    "WHERE datetime(timestamp) < datetime(?, '-' || ? || ' seconds')",
                    (current_time, int(self.ttl_seconds))
                )
                expired = cursor.fetchone()[0]

            return {"total": total, "expired": expired, "valid": total - expired}
        except Exception as e:
            logger.error(f"Errore nel recupero statistiche cache: {str(e)}")
            return {"total": 0, "expired": 0, "valid": 0}

    def backdate(self, key: str, seconds: float) -> bool:
        """Sposta indietro il timestamp di una riga (helper per test e
        manutenzione: forza la scadenza senza aspettare il TTL reale)."""
        try:
            with self._lock:
                conn = self._get_connection()
                cursor = conn.execute("SELECT timestamp FROM cache WHERE key = ?", (key,))
                row = cursor.fetchone()
                if not row:
                    return False
                backdated = datetime.fromisoformat(row[0]) - timedelta(seconds=seconds)
                conn.execute("UPDATE cache SET timestamp = ? WHERE key = ?",
                             (backdated.isoformat(), key))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Errore nel backdate della cache per {key}: {str(e)}")
            return False

    def close(self) -> None:
        """Chiude la connessione (la prossima operazione la riapre)."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

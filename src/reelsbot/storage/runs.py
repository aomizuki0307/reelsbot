"""SQLite-based storage for Reel generation runs.

This module provides persistent storage for Reel metadata using SQLite,
enabling tracking of all generated content and publication status.
"""

import json
import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any

from reelsbot.config import ReelsbotConfig
from reelsbot.models import ReelMetadata, ReelPlan


class RunStorageError(Exception):
    """Exception raised for errors during storage operations."""

    pass


class RunStorage:
    """SQLite-based storage for Reel generation runs.

    Provides persistent storage and retrieval of Reel metadata with
    automatic schema management and type-safe operations.

    Attributes:
        config: Reelsbot configuration instance.
        logger: Logger instance for tracking operations.
        db_path: Path to SQLite database file.
        conn: SQLite connection instance.
    """

    def __init__(
        self,
        config: ReelsbotConfig,
        logger: logging.Logger,
    ) -> None:
        """Initialize the run storage.

        Creates database and schema if they don't exist.

        Args:
            config: Reelsbot configuration.
            logger: Logger instance.

        Raises:
            RunStorageError: If database initialization fails.
        """
        self.config = config
        self.logger = logger

        # Database path in outputs directory
        db_dir = config.outputs_dir / "db"
        db_dir.mkdir(parents=True, exist_ok=True)
        self.db_path = db_dir / "reelsbot.db"

        try:
            # Initialize connection
            self.conn = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
            )
            self.conn.row_factory = sqlite3.Row

            # Create schema
            self._create_schema()

            self.logger.info(f"Run storage initialized: {self.db_path}")

        except Exception as e:
            raise RunStorageError(f"Failed to initialize storage: {e}") from e

    def _create_schema(self) -> None:
        """Create database schema if it doesn't exist.

        Creates the runs table with all necessary columns for storing
        Reel metadata.
        """
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                timestamp DATETIME NOT NULL,
                type TEXT NOT NULL,
                caption TEXT NOT NULL,
                hashtags TEXT NOT NULL,
                video_path TEXT NOT NULL,
                thumbnail_path TEXT NOT NULL,
                status TEXT NOT NULL,
                metadata_json TEXT NOT NULL
            )
        """)

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_timestamp
            ON runs(timestamp DESC)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_type
            ON runs(type)
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_runs_status
            ON runs(status)
        """)

        self.conn.commit()

    def save_run(self, metadata: ReelMetadata) -> None:
        """Save Reel metadata to database.

        Args:
            metadata: Complete Reel metadata to save.

        Raises:
            RunStorageError: If save operation fails.
        """
        try:
            cursor = self.conn.cursor()

            # Serialize metadata to JSON
            metadata_json = metadata.model_dump_json()

            # Serialize hashtags to JSON
            hashtags_json = json.dumps(metadata.hashtags)

            cursor.execute(
                """
                INSERT OR REPLACE INTO runs (
                    run_id, timestamp, type, caption, hashtags,
                    video_path, thumbnail_path, status, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    metadata.run_id,
                    metadata.timestamp.isoformat(),
                    metadata.plan.type,
                    metadata.caption,
                    hashtags_json,
                    str(metadata.video_path),
                    str(metadata.thumbnail_path),
                    metadata.status,
                    metadata_json,
                ),
            )

            self.conn.commit()

            self.logger.info(f"Saved run: {metadata.run_id}")

        except Exception as e:
            self.conn.rollback()
            raise RunStorageError(
                f"Failed to save run {metadata.run_id}: {e}"
            ) from e

    def get_run(self, run_id: str) -> ReelMetadata | None:
        """Retrieve Reel metadata by run ID.

        Args:
            run_id: Unique run identifier.

        Returns:
            ReelMetadata if found, None otherwise.

        Raises:
            RunStorageError: If retrieval operation fails.
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute(
                "SELECT metadata_json FROM runs WHERE run_id = ?",
                (run_id,),
            )

            row = cursor.fetchone()

            if row is None:
                return None

            # Deserialize from JSON
            metadata_dict = json.loads(row["metadata_json"])
            metadata = ReelMetadata(**metadata_dict)

            return metadata

        except Exception as e:
            raise RunStorageError(
                f"Failed to retrieve run {run_id}: {e}"
            ) from e

    def get_recent_runs(self, limit: int = 10) -> list[ReelMetadata]:
        """Get most recent Reel runs.

        Args:
            limit: Maximum number of runs to retrieve.

        Returns:
            List of ReelMetadata, most recent first.

        Raises:
            RunStorageError: If retrieval operation fails.
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT metadata_json FROM runs
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (limit,),
            )

            rows = cursor.fetchall()

            runs = []
            for row in rows:
                metadata_dict = json.loads(row["metadata_json"])
                metadata = ReelMetadata(**metadata_dict)
                runs.append(metadata)

            return runs

        except Exception as e:
            raise RunStorageError(
                f"Failed to retrieve recent runs: {e}"
            ) from e

    def update_status(self, run_id: str, status: str) -> None:
        """Update the status of a Reel run.

        Args:
            run_id: Unique run identifier.
            status: New status value (generated, failed, published).

        Raises:
            RunStorageError: If update operation fails.
        """
        try:
            cursor = self.conn.cursor()

            # Also update the status in metadata_json
            cursor.execute(
                "SELECT metadata_json FROM runs WHERE run_id = ?",
                (run_id,),
            )

            row = cursor.fetchone()

            if row is None:
                raise RunStorageError(f"Run {run_id} not found")

            # Update metadata
            metadata_dict = json.loads(row["metadata_json"])
            metadata_dict["status"] = status

            # Update both status column and metadata_json
            cursor.execute(
                """
                UPDATE runs
                SET status = ?, metadata_json = ?
                WHERE run_id = ?
                """,
                (status, json.dumps(metadata_dict), run_id),
            )

            self.conn.commit()

            self.logger.info(f"Updated run {run_id} status to: {status}")

        except Exception as e:
            self.conn.rollback()
            raise RunStorageError(
                f"Failed to update status for run {run_id}: {e}"
            ) from e

    def get_runs_by_type(self, plan_type: str, limit: int = 10) -> list[ReelMetadata]:
        """Get runs filtered by content type.

        Args:
            plan_type: Content type ("A" or "E").
            limit: Maximum number of runs to retrieve.

        Returns:
            List of ReelMetadata of the specified type.

        Raises:
            RunStorageError: If retrieval operation fails.
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT metadata_json FROM runs
                WHERE type = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (plan_type, limit),
            )

            rows = cursor.fetchall()

            runs = []
            for row in rows:
                metadata_dict = json.loads(row["metadata_json"])
                metadata = ReelMetadata(**metadata_dict)
                runs.append(metadata)

            return runs

        except Exception as e:
            raise RunStorageError(
                f"Failed to retrieve runs by type {plan_type}: {e}"
            ) from e

    def get_runs_by_status(self, status: str, limit: int = 10) -> list[ReelMetadata]:
        """Get runs filtered by status.

        Args:
            status: Status value (generated, failed, published).
            limit: Maximum number of runs to retrieve.

        Returns:
            List of ReelMetadata with the specified status.

        Raises:
            RunStorageError: If retrieval operation fails.
        """
        try:
            cursor = self.conn.cursor()

            cursor.execute(
                """
                SELECT metadata_json FROM runs
                WHERE status = ?
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (status, limit),
            )

            rows = cursor.fetchall()

            runs = []
            for row in rows:
                metadata_dict = json.loads(row["metadata_json"])
                metadata = ReelMetadata(**metadata_dict)
                runs.append(metadata)

            return runs

        except Exception as e:
            raise RunStorageError(
                f"Failed to retrieve runs by status {status}: {e}"
            ) from e

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about stored runs.

        Returns:
            Dictionary with run statistics (counts by type, status, etc.).

        Raises:
            RunStorageError: If query fails.
        """
        try:
            cursor = self.conn.cursor()

            stats = {}

            # Total runs
            cursor.execute("SELECT COUNT(*) as count FROM runs")
            stats["total"] = cursor.fetchone()["count"]

            # By type
            cursor.execute(
                """
                SELECT type, COUNT(*) as count
                FROM runs
                GROUP BY type
                """
            )
            stats["by_type"] = {row["type"]: row["count"] for row in cursor.fetchall()}

            # By status
            cursor.execute(
                """
                SELECT status, COUNT(*) as count
                FROM runs
                GROUP BY status
                """
            )
            stats["by_status"] = {
                row["status"]: row["count"] for row in cursor.fetchall()
            }

            return stats

        except Exception as e:
            raise RunStorageError(f"Failed to get stats: {e}") from e

    def close(self) -> None:
        """Close database connection.

        Should be called when shutting down the application.
        """
        if self.conn:
            self.conn.close()
            self.logger.info("Run storage connection closed")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

"""
Supabase-backed persistence for the CDL road test scanner.

Tables (see supabase_schema.sql):
  scanner_commands  – pause flag + active locations/student written by the PWA
  scan_results      – available slots written by testChrome.py, read by the PWA
  fcm_tokens        – FCM device tokens registered by PWA users
"""

from datetime import datetime, timezone

from dateutil import parser as date_parser
from supabase import create_client


_COMMANDS_TABLE = "scanner_commands"
_RESULTS_TABLE  = "scan_results"
_TOKENS_TABLE   = "fcm_tokens"


class SupabaseManager:
    def __init__(self, url: str, key: str, schema: str = "public"):
        """
        :param url: Your Supabase project URL, e.g. https://db.example.com
        :param key: service_role key (used only by testChrome.py on your local PC).
                    The PWA uses the anon key via its own client.
        :param schema: Database schema to operate in (default: public).
        """
        self._client = create_client(url, key)
        self._schema = schema or "public"

    def _table(self, name: str):
        """Return a table query builder scoped to the configured schema."""
        return self._client.schema(self._schema).table(name)

    # ------------------------------------------------------------------
    # Commands (pause / locations / student) written by the PWA
    # ------------------------------------------------------------------

    def initialize_commands_if_missing(self, locations, student):
        """Insert the default commands row when the table is empty."""
        result = self._table(_COMMANDS_TABLE).select("id").limit(1).execute()
        if not result.data:
            self._table(_COMMANDS_TABLE).insert({
                "paused":    False,
                "locations": locations,
                "student":   student,
            }).execute()
            print("Supabase: commands row initialised with config defaults")

    def get_commands(self) -> dict:
        """Return the first commands row, or {} if none exists."""
        result = self._table(_COMMANDS_TABLE).select("*").limit(1).execute()
        return result.data[0] if result.data else {}

    def claim_ownership_or_none(self, pid: int, hostname: str, heartbeat_stale_after_seconds: int):
        """
        Determine whether this process may claim ownership of scanner_commands
        (i.e. become the instance allowed to push rt_scanner_config.json's
        locations into the DB and unpause). Returns the commands row dict if
        ownership was claimed (this process is now the recorded owner), or
        None if another instance appears to already be running.

        Ownership is refused only when a DIFFERENT pid on the SAME hostname
        is still alive as an OS process right now. Any other case (no prior
        owner, different hostname, dead pid, or a heartbeat older than
        heartbeat_stale_after_seconds) is treated as "not running" and this
        process claims ownership.
        """
        commands = self.get_commands()
        if commands:
            prev_pid = commands.get("scanner_pid")
            prev_host = commands.get("scanner_hostname")
            prev_heartbeat = commands.get("scanner_heartbeat_at")

            same_host_other_pid_alive = (
                prev_pid and prev_pid != pid
                and prev_host == hostname
                and _pid_is_alive(prev_pid)
            )
            heartbeat_fresh = False
            if prev_heartbeat:
                age = (datetime.now(timezone.utc) - _parse_ts(prev_heartbeat)).total_seconds()
                heartbeat_fresh = age < heartbeat_stale_after_seconds

            if same_host_other_pid_alive and heartbeat_fresh:
                return None

        now = _now()
        if not commands:
            self._table(_COMMANDS_TABLE).insert({
                "paused":               False,
                "scanner_pid":          pid,
                "scanner_hostname":     hostname,
                "scanner_heartbeat_at": now,
                "updated_at":           now,
            }).execute()
            return self.get_commands()

        self._table(_COMMANDS_TABLE).update({
            "scanner_pid":          pid,
            "scanner_hostname":     hostname,
            "scanner_heartbeat_at": now,
            "updated_at":           now,
        }).eq("id", commands["id"]).execute()
        return self.get_commands()

    def sync_locations_from_config(self, locations: list):
        """
        Make scanner_commands.locations match the local config's locations
        list. Call only after claim_ownership_or_none() succeeded - this
        process is then authoritative and may overwrite the stored list.
        """
        commands = self.get_commands()
        if not commands:
            return
        if commands.get("locations") != locations:
            print(
                f"Supabase: scanner_commands.locations differs from config "
                f"(db={commands.get('locations')}, config={locations}); updating from config"
            )
            self._table(_COMMANDS_TABLE).update({
                "locations":  locations,
                "paused":     False,
                "updated_at": _now(),
            }).eq("id", commands["id"]).execute()

    def send_heartbeat(self, pid: int, hostname: str):
        """Refresh this process's ownership heartbeat. Call once per scan cycle."""
        commands = self.get_commands()
        if not commands:
            return
        self._table(_COMMANDS_TABLE).update({
            "scanner_pid":          pid,
            "scanner_hostname":     hostname,
            "scanner_heartbeat_at": _now(),
        }).eq("id", commands["id"]).execute()

    # ------------------------------------------------------------------
    # Scan results written by testChrome.py, read by the PWA
    #
    # scan_results holds one row per (location, date, time_slot) occurrence.
    # A slot that disappears and later reappears gets a brand new row (new
    # found_at) rather than reusing the old one - unique key is
    # (location, date, time_slot, found_at).
    # ------------------------------------------------------------------

    _NO_SLOTS_SENTINEL = "No slots"

    def open_slot(self, location: str, date: str, time_slot: str):
        """
        Record a newly-seen time slot as available.
        No-ops if this exact slot is already open (status=True) for this date.
        """
        existing = (
            self._table(_RESULTS_TABLE)
            .select("id")
            .eq("location", location).eq("date", date)
            .eq("time_slot", time_slot).eq("status", True)
            .execute()
        )
        if existing.data:
            return
        now = _now()
        self._table(_RESULTS_TABLE).insert({
            "location":     location,
            "date":         date,
            "time_slot":    time_slot,
            "status":       True,
            "found_at":     now,
            "last_updated": now,
            "notified":     False,
        }).execute()

    def close_slot(self, location: str, date: str, time_slot: str):
        """Mark a currently-open time slot as gone and flag for re-notification."""
        existing = (
            self._table(_RESULTS_TABLE)
            .select("id")
            .eq("location", location).eq("date", date)
            .eq("time_slot", time_slot).eq("status", True)
            .execute()
        )
        for row in existing.data or []:
            self._table(_RESULTS_TABLE).update({
                "status":       False,
                "last_updated": _now(),
                "notified":     False,
            }).eq("id", row["id"]).execute()

    def close_all_open_for_date(self, location: str, date: str):
        """Close every currently-open slot row for a location+date (date/location removed)."""
        existing = (
            self._table(_RESULTS_TABLE)
            .select("id")
            .eq("location", location).eq("date", date).eq("status", True)
            .execute()
        )
        now = _now()
        for row in existing.data or []:
            self._table(_RESULTS_TABLE).update({
                "status":       False,
                "last_updated": now,
                "notified":     False,
            }).eq("id", row["id"]).execute()

    def get_open_slots_by_location_date(self) -> dict:
        """
        Return currently-open slots (status=True) shaped as
        {location: {date: [time_slot, ...]}}, matching the in-memory scan
        state shape used by HashComparator. Used to seed that state after a
        restart so slots that closed while the scanner was down are still
        detected as removed on the next diff.
        """
        result = self._table(_RESULTS_TABLE).select("location, date, time_slot").eq("status", True).execute()
        by_location_date = {}
        for row in result.data or []:
            dates = by_location_date.setdefault(row["location"], {})
            dates.setdefault(row["date"], []).append(row["time_slot"])
        return by_location_date

    def mark_no_slots(self, location: str, date: str):
        """
        Record that a date was checked and has no available slots, using a
        sentinel row (time_slot='No slots'). No-ops if already the current state.
        """
        self.open_slot(location, date, self._NO_SLOTS_SENTINEL)

    def clear_no_slots(self, location: str, date: str):
        """Close the 'No slots' sentinel row once real slots appear for a date."""
        self.close_slot(location, date, self._NO_SLOTS_SENTINEL)

    def get_unnotified_results(self) -> list:
        """Return all result rows where notified == False."""
        result = self._table(_RESULTS_TABLE).select("*").eq("notified", False).execute()
        return result.data or []

    def mark_notified(self, result_ids: list):
        """Set notified=True for the given row IDs."""
        for rid in result_ids:
            self._table(_RESULTS_TABLE).update({"notified": True}).eq("id", rid).execute()

    # ------------------------------------------------------------------
    # Student profiles managed by the PWA
    # ------------------------------------------------------------------

    def get_active_student(self) -> dict:
        """
        Return the student profile the scanner should log in as (is_active=True),
        or {} if none is marked active (or the table is empty).
        """
        result = (
            self._table("students")
            .select("cid, dob, cdl_class")
            .eq("is_active", True)
            .limit(1)
            .execute()
        )
        return result.data[0] if result.data else {}

    # ------------------------------------------------------------------
    # FCM tokens registered by PWA users
    # ------------------------------------------------------------------

    def get_fcm_tokens(self) -> list:
        """Return all stored FCM registration tokens."""
        result = self._table(_TOKENS_TABLE).select("token").execute()
        return [row["token"] for row in (result.data or [])]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).isoformat()

def _parse_ts(value: str) -> datetime:
    return date_parser.isoparse(value)

def _pid_is_alive(pid: int) -> bool:
    """Best-effort check for whether a process with this pid is currently running."""
    import os
    import sys
    try:
        if sys.platform == "win32":
            import ctypes
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return False
            ctypes.windll.kernel32.CloseHandle(handle)
            return True
        os.kill(pid, 0)
        return True
    except (OSError, PermissionError):
        return False
    except Exception:
        return False

import firebase_admin
from firebase_admin import credentials, firestore

COMMANDS_COLLECTION = "cdl_scanner"
COMMANDS_DOC        = "commands"
RESULTS_COLLECTION  = "cdl_scan_results"
TOKENS_COLLECTION   = "cdl_fcm_tokens"


class FirestoreManager:
    """Manages Firestore reads/writes for the CDL scanner: commands, results, and FCM tokens."""

    def __init__(self, cred_path):
        if not firebase_admin._apps:
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        self._db = firestore.client()

    # ------------------------------------------------------------------
    # Commands (pause / locations / student) written by the PWA
    # ------------------------------------------------------------------

    def initialize_commands_if_missing(self, locations, student):
        """Create the commands document with defaults if it does not yet exist."""
        doc_ref = self._db.collection(COMMANDS_COLLECTION).document(COMMANDS_DOC)
        if not doc_ref.get().exists:
            doc_ref.set({
                "paused":     False,
                "locations":  locations,
                "student":    student,
                "updated_at": firestore.SERVER_TIMESTAMP,
            })
            print("Firestore: commands document initialised with config defaults")

    def get_commands(self):
        """Return the commands document as a dict, or {} if it does not exist."""
        doc = self._db.collection(COMMANDS_COLLECTION).document(COMMANDS_DOC).get()
        return doc.to_dict() if doc.exists else {}

    # ------------------------------------------------------------------
    # Scan results written by testChrome.py, read by the PWA
    # ------------------------------------------------------------------

    def write_result(self, location, date, slots, status="available"):
        """
        Upsert a scan result document.
        Sets found_at and notified=False on first write.
        Resets notified=False whenever status or slots change.
        """
        doc_ref = self._db.collection(RESULTS_COLLECTION).document(_result_id(location, date))
        existing = doc_ref.get()
        data = {
            "location":     location,
            "date":         date,
            "slots":        slots,
            "status":       status,
            "last_updated": firestore.SERVER_TIMESTAMP,
        }
        if not existing.exists:
            data["found_at"] = firestore.SERVER_TIMESTAMP
            data["notified"] = False
        else:
            prev = existing.to_dict()
            if prev.get("status") != status or set(prev.get("slots", [])) != set(slots):
                data["notified"] = False
        doc_ref.set(data, merge=True)

    def mark_result_gone(self, location, date):
        """Mark a previously visible slot as gone and flag for re-notification."""
        doc_ref = self._db.collection(RESULTS_COLLECTION).document(_result_id(location, date))
        if doc_ref.get().exists:
            doc_ref.update({
                "status":       "gone",
                "last_updated": firestore.SERVER_TIMESTAMP,
                "notified":     False,
            })

    def get_unnotified_results(self):
        """Return all result docs where notified == False."""
        results = []
        for doc in (self._db.collection(RESULTS_COLLECTION)
                    .where("notified", "==", False).stream()):
            data = doc.to_dict()
            data["_id"] = doc.id
            results.append(data)
        return results

    def mark_notified(self, result_ids):
        """Set notified=True for the given document IDs."""
        for rid in result_ids:
            self._db.collection(RESULTS_COLLECTION).document(rid).update({"notified": True})

    # ------------------------------------------------------------------
    # FCM tokens registered by PWA users
    # ------------------------------------------------------------------

    def get_fcm_tokens(self):
        """Return all stored FCM registration tokens."""
        tokens = []
        for doc in self._db.collection(TOKENS_COLLECTION).stream():
            data = doc.to_dict()
            if "token" in data:
                tokens.append(data["token"])
        return tokens


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _result_id(location, date):
    """Generate a Firestore-safe document ID from location + date."""
    return f"{location}_{date}".replace("/", "-").replace(" ", "_")

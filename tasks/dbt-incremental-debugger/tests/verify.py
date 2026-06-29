#!/usr/bin/env python3
"""
Verifier for dbt-incremental-debugger task.

Checks:
1. Row count: exactly 13 active users (20 total - 2 deleted: Heidi initially deleted,
   then restored → Heidi restored should appear; user 108 final state is NOT deleted)
   Wait — let's compute precisely:
   Active users after all events:
   101 Alice Final (not deleted)
   102 Bob Final (not deleted)
   103 Carol (not deleted)
   104 Dave (not deleted)
   105 Eve (not deleted)
   106 Frank Updated (not deleted, event 16 at same ts as event 8)
   107 Grace (not deleted)
   108 Heidi Restored (not deleted — restored at 11:35)
   109 Ivan (not deleted)
   110 Judy (not deleted)
   111 Karl (not deleted)
   112 Laura (not deleted)
   113 Mallory (not deleted)
   114 Niaj (not deleted)
   = 14 users, none deleted (108 was restored)

2. No soft-deleted users in output (is_deleted = FALSE for all rows, or column absent)
3. User 101's latest record should have user_name = 'Alice Final' (latest by updated_at DESC)
4. User 102's latest record should have user_name = 'Bob Final'
5. User 106's record should include the update from event 16 (same ts 10:30 — boundary bug)
6. user_id is unique (no duplicates)
"""

import sys
import os
import duckdb

LOG_DIR = "/logs/verifier"
os.makedirs(LOG_DIR, exist_ok=True)
REWARD_FILE = f"{LOG_DIR}/reward.txt"
DB_PATH = "/workspace/dbt_project/events.duckdb"

def write_reward(score: float, reason: str):
    with open(REWARD_FILE, "w") as f:
        f.write(str(score))
    print(f"[verifier] reward={score} | {reason}")

def fail(reason: str):
    write_reward(0.0, reason)
    sys.exit(0)

def main():
    if not os.path.exists(DB_PATH):
        fail(f"Database not found at {DB_PATH} — did you run dbt?")

    try:
        con = duckdb.connect(DB_PATH, read_only=True)
    except Exception as e:
        fail(f"Cannot open DuckDB: {e}")

    # Check table exists
    tables = con.execute("SHOW TABLES").fetchall()
    table_names = [t[0].lower() for t in tables]
    if "user_events_mart" not in table_names:
        fail(f"Table 'user_events_mart' not found. Tables present: {table_names}")

    rows = con.execute("SELECT * FROM user_events_mart").fetchall()
    cols = [d[0].lower() for d in con.execute("DESCRIBE user_events_mart").fetchall()]

    print(f"[verifier] Columns: {cols}")
    print(f"[verifier] Row count: {len(rows)}")

    # Build dict of user_id -> row
    uid_col = cols.index("user_id")
    row_by_uid = {}
    for r in rows:
        uid = r[uid_col]
        if uid in row_by_uid:
            fail(f"CHECK FAILED: Duplicate user_id={uid} found. unique_key dedup is broken.")
        row_by_uid[uid] = dict(zip(cols, r))

    # CHECK 1: Row count — 14 active users
    expected_count = 14
    if len(rows) != expected_count:
        fail(
            f"CHECK FAILED: Expected {expected_count} rows (14 active users), "
            f"got {len(rows)}. "
            f"Hint: check soft-delete filtering and boundary timestamp inclusion."
        )

    # CHECK 2: No soft-deleted users
    if "is_deleted" in cols:
        deleted_users = [r["user_id"] for r in row_by_uid.values() if r.get("is_deleted") in (True, 1, "true", "True")]
        if deleted_users:
            fail(f"CHECK FAILED: Soft-deleted users still in mart: {deleted_users}")
    
    # CHECK 3: User 101 should have Alice Final (latest record by DESC updated_at)
    if 101 not in row_by_uid:
        fail("CHECK FAILED: user_id=101 missing from mart.")
    name_101 = row_by_uid[101].get("user_name", "")
    if name_101 != "Alice Final":
        fail(
            f"CHECK FAILED: user_id=101 should have user_name='Alice Final' (latest event), "
            f"got '{name_101}'. Hint: ROW_NUMBER ORDER BY direction is wrong."
        )

    # CHECK 4: User 102 should have Bob Final
    if 102 not in row_by_uid:
        fail("CHECK FAILED: user_id=102 missing from mart.")
    name_102 = row_by_uid[102].get("user_name", "")
    if name_102 != "Bob Final":
        fail(
            f"CHECK FAILED: user_id=102 should have user_name='Bob Final', "
            f"got '{name_102}'. Hint: ROW_NUMBER ORDER BY direction is wrong."
        )

    # CHECK 5: User 106 should be Frank Updated (boundary timestamp bug)
    # Event 8 (Frank, 10:30) is in batch 1; Event 16 (Frank Updated, also 10:30) is batch 2
    # With strict >, event 16 is filtered out. With >=, it's included.
    if 106 not in row_by_uid:
        fail("CHECK FAILED: user_id=106 missing from mart.")
    name_106 = row_by_uid[106].get("user_name", "")
    if name_106 != "Frank Updated":
        fail(
            f"CHECK FAILED: user_id=106 should have user_name='Frank Updated' after incremental refresh, "
            f"got '{name_106}'. Hint: boundary condition in incremental WHERE clause (> vs >=)."
        )

    # CHECK 6: User 108 should be present (Heidi was deleted then restored)
    if 108 not in row_by_uid:
        fail(
            "CHECK FAILED: user_id=108 (Heidi Restored) missing. "
            "Heidi was deleted then restored — final state is active."
        )
    name_108 = row_by_uid[108].get("user_name", "")
    if name_108 != "Heidi Restored":
        fail(
            f"CHECK FAILED: user_id=108 should be 'Heidi Restored', got '{name_108}'. "
            f"Latest event restores Heidi; the mart should reflect the final state."
        )

    write_reward(1.0, "All checks passed: correct row count, dedup, soft-delete filter, boundary timestamps.")

if __name__ == "__main__":
    main()

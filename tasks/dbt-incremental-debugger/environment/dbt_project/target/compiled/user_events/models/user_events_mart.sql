






-- Deduplicate: pick the latest event per user
-- BUG 3: ORDER BY ASC picks the OLDEST record, not newest
WITH ranked_events AS (
    SELECT
        event_id,
        user_id,
        event_type,
        user_name,
        user_email,
        updated_at,
        is_deleted,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY updated_at ASC, event_id ASC  -- BUG: should be DESC, DESC
        ) AS rn
    FROM "buggy_events"."main"."raw_events"

    
    -- BUG 1: strict > excludes boundary rows with the exact same timestamp as last batch max
    WHERE updated_at > '2024-01-01 11:45:00'
    
),

latest_per_user AS (
    SELECT
        event_id,
        user_id,
        event_type,
        user_name,
        user_email,
        updated_at,
        is_deleted
    FROM ranked_events
    WHERE rn = 1
)

-- BUG 2: no filter on is_deleted — soft-deleted users still included
SELECT
    user_id,
    user_name,
    user_email,
    event_type AS last_event_type,
    updated_at AS last_updated_at,
    is_deleted
FROM latest_per_user
-- Missing: WHERE is_deleted = FALSE







-- Deduplicated mart: one row per active user, reflecting their latest event
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
            ORDER BY updated_at DESC, event_id DESC  -- FIXED: DESC to pick newest
        ) AS rn
    FROM "test_events"."main"."raw_events"

    
    -- FIXED: >= captures boundary rows with same timestamp as last batch max
    WHERE updated_at >= '2024-01-01 11:45:00'
    
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

-- FIXED: exclude soft-deleted users
SELECT
    user_id,
    user_name,
    user_email,
    event_type AS last_event_type,
    updated_at AS last_updated_at,
    is_deleted
FROM latest_per_user
WHERE is_deleted = FALSE
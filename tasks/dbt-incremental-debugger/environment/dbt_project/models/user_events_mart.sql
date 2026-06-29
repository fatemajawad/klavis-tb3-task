{{
    config(
        materialized='incremental',
        unique_key='user_id',
        incremental_strategy='delete+insert'
    )
}}

{% if is_incremental() %}
{% set max_ts_query %}
    SELECT MAX(last_updated_at) FROM {{ this }}
{% endset %}
{% set max_ts = run_query(max_ts_query).columns[0].values()[0] %}
{% endif %}

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
    FROM {{ ref('raw_events') }}

    {% if is_incremental() %}
    -- BUG 1: strict > excludes boundary rows with the exact same timestamp as last batch max
    WHERE updated_at > '{{ max_ts }}'
    {% endif %}
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

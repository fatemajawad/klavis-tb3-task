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
    FROM {{ ref('raw_events') }}

    {% if is_incremental() %}
    -- FIXED: >= captures boundary rows with same timestamp as last batch max
    WHERE updated_at >= '{{ max_ts }}'
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

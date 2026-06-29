
        
            delete from "test_events"."main"."user_events_mart"
            where (
                user_id) in (
                select (user_id)
                from "user_events_mart__dbt_tmp20260629003805077870"
            );

        
    

    insert into "test_events"."main"."user_events_mart" ("user_id", "user_name", "user_email", "last_event_type", "last_updated_at", "is_deleted")
    (
        select "user_id", "user_name", "user_email", "last_event_type", "last_updated_at", "is_deleted"
        from "user_events_mart__dbt_tmp20260629003805077870"
    )
  
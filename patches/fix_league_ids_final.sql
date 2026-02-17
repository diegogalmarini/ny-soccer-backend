-- Fix for League ID Mismatches with FK Handling
-- Uses Copy-Update-Delete strategy because FKs are not deferrable.

DO $$
DECLARE
    -- Helper function logic embedded in DO block loop or just procedural code
    -- We can't define functions inside DO block easily without creating them in schema.
    -- Better to just iterate.
BEGIN

    -- Define a local procedure to move IDs
    CREATE OR REPLACE FUNCTION pg_temp.move_league(old_id INT, new_id INT) RETURNS VOID AS $func$
    DECLARE
        cnt INT;
    BEGIN
        SELECT count(*) INTO cnt FROM league_league WHERE id = old_id;
        IF cnt = 0 THEN
            RAISE NOTICE 'League % does not exist, skipping move to %', old_id, new_id;
            RETURN;
        END IF;

        RAISE NOTICE 'Moving League % to %', old_id, new_id;

        -- Insert new league
        INSERT INTO league_league (
            id, paypal_account_id, open_team_count, open_female_slot, open_male_slot, season_id, location_id, 
            game_duration, "order", featured_at_homepage, team_registration_credit, registration_cost, team_cost, 
            num_players_on_field, minimum_roster_size, minimum_num_women_on_field, status, registration_deadline, 
            name, day_of_week, league_description, game_location, game_time, league_type, cover_description, 
            image, competition_type
        )
        SELECT 
            new_id, paypal_account_id, open_team_count, open_female_slot, open_male_slot, season_id, location_id, 
            game_duration, "order", featured_at_homepage, team_registration_credit, registration_cost, team_cost, 
            num_players_on_field, minimum_roster_size, minimum_num_women_on_field, status, registration_deadline, 
            name, day_of_week, league_description, game_location, game_time, league_type, cover_description, 
            image, competition_type
        FROM league_league WHERE id = old_id;

        -- Update linked tables
        UPDATE league_division SET league_id = new_id WHERE league_id = old_id;
        UPDATE league_goalscorer SET league_id = new_id WHERE league_id = old_id;
        UPDATE league_teamplayer SET league_id = new_id WHERE league_id = old_id;
        UPDATE league_round SET league_id = new_id WHERE league_id = old_id;
        UPDATE league_team SET league_id = new_id WHERE league_id = old_id;
        UPDATE league_paymentplaceholder SET league_id = new_id WHERE league_id = old_id;

        -- Delete old league
        DELETE FROM league_league WHERE id = old_id;
    END;
    $func$ LANGUAGE plpgsql;

    -- Apply moves
    -- 1. Evict conflicts
    PERFORM pg_temp.move_league(404, 1404); -- Check if 404 still exists (it shouldn't if previous step worked, but good for safety)
    PERFORM pg_temp.move_league(405, 1405);
    PERFORM pg_temp.move_league(401, 1401);

    -- 2. Swaps and Moves
    PERFORM pg_temp.move_league(402, 401);
    PERFORM pg_temp.move_league(1401, 402);
    PERFORM pg_temp.move_league(411, 404);
    PERFORM pg_temp.move_league(418, 411);
    PERFORM pg_temp.move_league(419, 410);
    PERFORM pg_temp.move_league(420, 408);

    -- Clean up (function is temp but good practice)
    -- DROP FUNCTION pg_temp.move_league; -- Auto dropped at end of session usually
END $$;

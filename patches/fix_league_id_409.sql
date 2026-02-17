-- Fix for League ID Mismatch (421 -> 409)
-- Issue: Production league ID was 421, but legacy data (and 13 orphaned team_player records) relied on ID 409.
-- Resolution: Migrate League 421 to 409.

UPDATE league_league SET id = 409 WHERE id = 421;

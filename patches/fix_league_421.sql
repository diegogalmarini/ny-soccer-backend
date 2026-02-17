-- Fix for League 421 (CHELSEA Spring 2026 Outdoor 7s)
-- Issue: open_team_count was 0, causing empty schedule table.
-- Resolution: Set to 8 based on schedule slot capacity.

UPDATE league_league SET open_team_count = 8 WHERE id = 421;

-- Fix Division 9 and 10 to point to League 7 (Matches Team Data)
UPDATE "league_division" SET "league_id" = 7 WHERE "id" = 9;
UPDATE "league_division" SET "league_id" = 7 WHERE "id" = 10;

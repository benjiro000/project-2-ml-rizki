-- ======================================================================
-- clean_cqi_explore.sql  -  cleaning the raw CQI green-coffee files with SQL
-- Project 2 (ML)  -  Rizki
-- ======================================================================
-- Raw tables:  raw_arabica (1,311 lots)  and  raw_robusta (28 lots)
-- Result:      one clean view, cqi_clean (1,338 lots: lot_id + 20 columns),
--              and the same data split into three tables with keys:
--              countries (primary key = country), lots and cup_scores.
--
-- THE LINEAGE (what this file does, in order)
--   raw_arabica (1,311) + raw_robusta (28)
--        |  2.1  UNION ALL: stack the two datasets on the 20 agreed columns,
--        |       and give every lot its lot_id
--        v
--   cqi_stacked (1,339)
--        |  2.2  drop 1 row, set impossible values to NULL
--        v
--   cqi_clean (1,338)
--        |  Part 4  split into keyed tables
--        v
--   countries  <-  lots  <->  cup_scores
--
-- lot_id:      every lot gets its id in the stacking step (2.1): the letter
--              A plus its row number in raw_arabica, or R plus its row number
--              in raw_robusta. A5 is the 5th data row of the Arabica file.
--              The id stays with the lot through every cleaning rule, so
--              any clean lot can be traced back to its raw row, and a lot
--              that was dropped can still be found by its id (query 3.7).
--              It is a label for tracing and joining. It is never an input
--              of the model.
--
-- HOW TO RUN
--   Step A (once, in a notebook or terminal): put the raw CSVs into a
--   project database. This is the to_sql step from the SQL and Python lesson.
--
--       import sqlite3, pandas as pd
--       con = sqlite3.connect("data/clean/cqi_project.db")
--       pd.read_csv("data/raw/ds_cqi_jldbc_2018/arabica_data_cleaned.csv").to_sql("raw_arabica", con, if_exists="replace", index=False)
--       pd.read_csv("data/raw/ds_cqi_jldbc_2018/robusta_data_cleaned.csv").to_sql("raw_robusta", con, if_exists="replace", index=False)
--       con.close()
--
--   Use to_sql and not the DB Browser CSV import. to_sql keeps numbers as
--   numbers and empty cells as real NULLs, which the rules below rely on.
--   It also numbers the rows in file order, which the lot_id relies on.
--   (Check 19 at the bottom warns you if a number column became text.)
--
--   Step B: open the database in DB Browser for SQLite, go to the Execute
--   SQL tab, paste or open this file and press Execute all. The last thing
--   you see is the PASS / FAIL table from Part 5. To see the result of any
--   earlier query, click inside it and use Execute current line.
--   Then press Write Changes (Cmd+S) so the views and tables are saved in
--   the database file.
--   The file can be run again and again: it never changes the raw tables.
--
-- WHAT THE FILE DECIDES  (the gate 2 decisions)
--   Kept (20 columns, plus the lot_id label): species, 8 features, the
--     target Total.Cup.Points, and the 10 cupping part scores (profile
--     columns, not used to predict).
--     Features: Country.of.Origin, Variety, Processing.Method, Moisture,
--     Category.One.Defects, Category.Two.Defects, Color, altitude_mean_meters.
--   Dropped by simply never selecting them: personal data, identifiers,
--     Region, Harvest.Year, In.Country.Partner and Quakers.
--   Row rule R1: a lot with Total.Cup.Points = 0 is dropped (1 lot).
--   Value rules, each one replaces a value by NULL ("missing"):
--     M1  Moisture = 0.0                      (not measured in disguise)
--     M2  Moisture above 0 up to 0.05         (far too dry for green coffee)
--     A1  altitude_mean_meters above 3000     (typing errors, both species)
--     A2  altitude_mean_meters below 50       (Arabica only, e.g. 1.0 m, not a real farm)
--   Robusta columns that do not match an Arabica part score are left NULL.
--
--   Nothing here fills, averages, scales or encodes. All of that learns
--   from the data, so it belongs in the Pipeline in the notebooks, after
--   the train/test split.
--
-- NEW KEYWORDS compared with the lessons: UNION ALL (stacks two tables) and
--   rowid (the row number SQLite keeps for every table, used for lot_id).
--   Part 4 only: CREATE TABLE, PRIMARY KEY, FOREIGN KEY and INSERT INTO.
--   Part 5 only: pragma_table_info (lists a table or view's columns) and
--   typeof (says whether a value is a number or text).
--   Column names that contain dots need double quotes, like "Total.Cup.Points".

-- ----------------------------------------------------------------------
-- PART 1  LOOK AT THE RAW DATA  (nothing is changed here)
-- ----------------------------------------------------------------------

-- 1.1 How many lots of each species?
SELECT COUNT(*) AS arabica_lots FROM raw_arabica;          -- 1311
SELECT COUNT(*) AS robusta_lots FROM raw_robusta;          -- 28

-- 1.2 How many cells are filled? COUNT(column) skips the NULLs.
SELECT COUNT(*)                    AS lots,
       COUNT(Variety)              AS variety_filled,
       COUNT("Processing.Method")  AS processing_filled,
       COUNT(Color)                AS color_filled,
       COUNT(Moisture)             AS moisture_filled,
       COUNT(altitude_mean_meters) AS altitude_filled
FROM raw_arabica;
-- You should see: 1311 | 1110 | 1159 | 1044 | 1311 | 1084
-- Moisture looks complete, but that is the trap: a missing moisture was
-- stored as 0.0 instead of being left empty (next query).

-- 1.3 Moisture is a fraction: 0.11 means 11 percent. Green coffee normally
--     rests at about 0.10 to 0.12.
SELECT MIN(Moisture) AS lowest, MAX(Moisture) AS highest, AVG(Moisture) AS average
FROM raw_arabica;
-- You should see: 0.0 | 0.28 | about 0.089

-- CASE sorts every lot into a band, GROUP BY counts each band.
SELECT CASE
           WHEN Moisture IS NULL THEN '5 empty'
           WHEN Moisture = 0     THEN '1 exactly 0.0'
           WHEN Moisture <= 0.05 THEN '2 above 0 up to 0.05'
           WHEN Moisture <= 0.14 THEN '3 0.05 to 0.14'
           ELSE                       '4 above 0.14'
       END AS moisture_band,
       COUNT(*) AS lots
FROM raw_arabica
GROUP BY moisture_band
ORDER BY moisture_band;
-- You should see: exactly 0.0 = 252, up to 0.05 = 38, 0.05 to 0.14 = 997, above 0.14 = 24
-- (no empty band: there are no empty moistures in the raw file)

-- 1.4 Altitude in metres
SELECT MIN(altitude_mean_meters) AS lowest_m, MAX(altitude_mean_meters) AS highest_m
FROM raw_arabica;
-- You should see: 1.0 | 190164.0   (impossible: Everest is 8849 m)

SELECT COUNT(*) AS above_3000m FROM raw_arabica WHERE altitude_mean_meters > 3000;   -- 14
SELECT COUNT(*) AS below_50m   FROM raw_arabica WHERE altitude_mean_meters < 50;     -- 17

-- 1.5 Which categories exist? (None means empty)
SELECT DISTINCT "Processing.Method" FROM raw_arabica ORDER BY "Processing.Method";
-- You should see: empty, Natural / Dry, Other, Pulped natural / honey,
--                 Semi-washed / Semi-pulped, Washed / Wet
SELECT DISTINCT Color FROM raw_arabica ORDER BY Color;
-- You should see: empty, Blue-Green, Bluish-Green, Green

-- 1.6 A total score of 0 cannot be a real cup
SELECT rowid AS raw_row, "Country.of.Origin", "Total.Cup.Points", Moisture
FROM raw_arabica
WHERE "Total.Cup.Points" = 0;
-- You should see one Honduras lot: raw row 1311, the last row of the Arabica
-- file (its lot_id will be A1311). Its moisture is 0.12, so it is not part
-- of the 252 zero-moisture lots.

-- ----------------------------------------------------------------------
-- PART 2  BUILD THE CLEAN DATA  (two views, the raw tables stay untouched)
-- ----------------------------------------------------------------------
-- A view stores the query and not the data, so it is always up to date.

DROP VIEW IF EXISTS cqi_clean;
DROP VIEW IF EXISTS cqi_stacked;

-- 2.1 Stack Arabica and Robusta into one table, with a species label.
--     Think of pouring two sacks into one bin, each lot keeping its tag.
--     The tag is made here: lot_id = 'A' or 'R' joined (||) to the row
--     number of the lot in its raw table. Because it is made before any
--     rule runs, it always points back to the raw row.
--     Only the 20 agreed columns are selected, so the dropped ones never appear.
--     Robusta names its part scores differently, so AS renames them:
--         Fragrance...Aroma -> Aroma        Uniform.Cup -> Uniformity
--     Salt...Acid, Bitter...Sweet and Mouthfeel are not clear matches for
--     Acidity, Sweetness and Body, so those three stay NULL for Robusta.
--     No values are changed in this step.
CREATE VIEW cqi_stacked AS
SELECT
    'A' || rowid              AS lot_id,
    'arabica'                 AS species,
    "Country.of.Origin"       AS "Country.of.Origin",
    Variety                   AS Variety,
    "Processing.Method"       AS "Processing.Method",
    Moisture                  AS Moisture,
    "Category.One.Defects"    AS "Category.One.Defects",
    "Category.Two.Defects"    AS "Category.Two.Defects",
    Color                     AS Color,
    altitude_mean_meters      AS altitude_mean_meters,
    "Total.Cup.Points"        AS "Total.Cup.Points",
    Aroma                     AS Aroma,
    Flavor                    AS Flavor,
    Aftertaste                AS Aftertaste,
    Acidity                   AS Acidity,
    Body                      AS Body,
    Balance                   AS Balance,
    Uniformity                AS Uniformity,
    "Clean.Cup"               AS "Clean.Cup",
    Sweetness                 AS Sweetness,
    "Cupper.Points"           AS "Cupper.Points"
FROM raw_arabica
UNION ALL
SELECT
    'R' || rowid              AS lot_id,
    'robusta'                 AS species,
    "Country.of.Origin"       AS "Country.of.Origin",
    Variety                   AS Variety,
    "Processing.Method"       AS "Processing.Method",
    Moisture                  AS Moisture,
    "Category.One.Defects"    AS "Category.One.Defects",
    "Category.Two.Defects"    AS "Category.Two.Defects",
    Color                     AS Color,
    altitude_mean_meters      AS altitude_mean_meters,
    "Total.Cup.Points"        AS "Total.Cup.Points",
    "Fragrance...Aroma"       AS Aroma,
    Flavor                    AS Flavor,
    Aftertaste                AS Aftertaste,
    NULL                      AS Acidity,
    NULL                      AS Body,
    Balance                   AS Balance,
    "Uniform.Cup"             AS Uniformity,
    "Clean.Cup"               AS "Clean.Cup",
    NULL                      AS Sweetness,
    "Cupper.Points"           AS "Cupper.Points"
FROM raw_robusta;

-- 2.2 Apply the row rule and the value rules.
--     WHERE keeps only lots with a real total score (rule R1).
--     CASE replaces impossible values by NULL. The first matching WHEN wins.
--     Every other column is passed through unchanged, lot_id included, so
--     the id follows the lot through the rules.
CREATE VIEW cqi_clean AS
SELECT
    lot_id,
    species,
    "Country.of.Origin",
    Variety,
    "Processing.Method",
    CASE
        WHEN Moisture = 0                      THEN NULL     -- M1
        WHEN Moisture > 0 AND Moisture <= 0.05 THEN NULL     -- M2
        ELSE Moisture
    END AS Moisture,
    "Category.One.Defects",
    "Category.Two.Defects",
    Color,
    CASE
        WHEN altitude_mean_meters > 3000                       THEN NULL   -- A1
        WHEN species = 'arabica' AND altitude_mean_meters < 50 THEN NULL   -- A2
        ELSE altitude_mean_meters
    END AS altitude_mean_meters,
    "Total.Cup.Points",
    Aroma,
    Flavor,
    Aftertaste,
    Acidity,
    Body,
    Balance,
    Uniformity,
    "Clean.Cup",
    Sweetness,
    "Cupper.Points"
FROM cqi_stacked
WHERE "Total.Cup.Points" > 0;                                  -- R1

-- ----------------------------------------------------------------------
-- PART 3  FINDINGS TO REPORT  (read-only, they change nothing)
-- ----------------------------------------------------------------------

-- 3.1 Species side by side
SELECT species,
       COUNT(*)                          AS lots,
       ROUND(AVG("Total.Cup.Points"), 2) AS avg_cup_points,
       MIN("Total.Cup.Points")           AS lowest,
       MAX("Total.Cup.Points")           AS highest
FROM cqi_clean
GROUP BY species;
-- You should see: arabica 1310 | 82.18 | 59.83 | 90.58
--                 robusta   28 | 80.87 | 73.75 | 83.75

-- 3.2 Which countries have enough lots to learn from? (HAVING filters the groups)
SELECT "Country.of.Origin"               AS country,
       COUNT(*)                          AS lots,
       ROUND(AVG("Total.Cup.Points"), 2) AS avg_cup_points
FROM cqi_clean
WHERE species = 'arabica'
GROUP BY "Country.of.Origin"
HAVING COUNT(*) >= 10
ORDER BY avg_cup_points DESC;
-- You should see 19 countries. Ethiopia is top (44 lots, 85.48), Nicaragua
-- last (26 lots, 80.46). Mexico (236), Colombia (183) and Guatemala (181)
-- are the biggest.

-- 3.3 The wet tail of moisture, reported only (no rule changes it)
SELECT COUNT(*) AS lots_above_0_14 FROM cqi_clean WHERE Moisture > 0.14;     -- 24

SELECT lot_id, "Country.of.Origin", Moisture
FROM cqi_clean
WHERE Moisture > 0.14
ORDER BY Moisture DESC
LIMIT 10;
-- You should see Thailand 0.28 at the top, then Colombia 0.22 and 0.21.

-- 3.4 The altitude bump near 2500 m, reported only
SELECT lot_id, "Country.of.Origin", altitude_mean_meters
FROM cqi_clean
WHERE species = 'arabica'
  AND altitude_mean_meters >= 2400
  AND altitude_mean_meters <= 2600
ORDER BY altitude_mean_meters DESC;
-- You should see 4 lots: Colombia 2560, Colombia 2560, Colombia 2527, Malawi 2500.

-- 3.5 The five lowest scores, to look at the outliers
SELECT lot_id, "Country.of.Origin", "Total.Cup.Points", "Clean.Cup", Sweetness
FROM cqi_clean
ORDER BY "Total.Cup.Points" ASC
LIMIT 5;
-- You should see: the Guatemala lot at 59.83 with Clean.Cup and Sweetness
-- both 1.33, far below every other lot. Real data, but a strong outlier.

-- 3.5b Countries where every Arabica lot scores exactly 10 on three part
--      scores. If a score never changes inside a country, it tells the
--      model nothing about that country.
SELECT "Country.of.Origin", COUNT(*) AS lots
FROM cqi_clean
WHERE species = 'arabica'
GROUP BY "Country.of.Origin"
HAVING COUNT(*) >= 5
   AND MIN(Uniformity)  = 10 AND MAX(Uniformity)  = 10
   AND MIN("Clean.Cup") = 10 AND MAX("Clean.Cup") = 10
   AND MIN(Sweetness)   = 10 AND MAX(Sweetness)   = 10;
-- You should see 5 countries: Tanzania (40 lots, the biggest), Uganda (26),
-- Malawi (11), Myanmar (8) and United States (8).

-- 3.6 The 80-point specialty line (the threshold for the classification metrics)
SELECT CASE WHEN "Total.Cup.Points" >= 80 THEN 'specialty (80 and up)'
            ELSE 'below 80' END AS grade,
       COUNT(*) AS lots
FROM cqi_clean
WHERE species = 'arabica'
GROUP BY grade;
-- You should see: below 80 = 180, specialty = 1130

-- 3.7 What did the cleaning do to each lot? lot_id is the thread that
--     connects the raw data and the clean data, so the two can be compared
--     lot by lot. s is the stacked data before the rules, c the clean data.

-- 3.7a Which lot did the row rule drop? NOT IN uses a subquery as a list.
SELECT lot_id, "Country.of.Origin", "Total.Cup.Points"
FROM cqi_stacked
WHERE lot_id NOT IN (SELECT lot_id FROM cqi_clean);
-- You should see: A1311 | Honduras | 0.0

-- 3.7b Five lots whose moisture the rules emptied, before and after
SELECT s.lot_id, s."Country.of.Origin" AS country,
       s.Moisture AS moisture_before, c.Moisture AS moisture_after
FROM cqi_stacked AS s
INNER JOIN cqi_clean AS c ON s.lot_id = c.lot_id
WHERE s.Moisture IS NOT NULL AND c.Moisture IS NULL
ORDER BY s.lot_id
LIMIT 5;
-- You should see 5 rows with moisture_after empty. (In all, 302 lots were
-- emptied: 264 by M1 and 38 by M2.)

-- 3.7c The 17 Arabica altitudes below 50 m that rule A2 emptied. Twelve are
--      exactly 1.0 m (eleven of them Brazil) and the rest are 12 or 13 m.
--      No coffee farm sits at 1 m, so these are entry errors.
SELECT s.lot_id, s."Country.of.Origin" AS country,
       s.altitude_mean_meters AS altitude_before, c.altitude_mean_meters AS altitude_after
FROM cqi_stacked AS s
INNER JOIN cqi_clean AS c ON s.lot_id = c.lot_id
WHERE s.species = 'arabica' AND s.altitude_mean_meters < 50
ORDER BY s.altitude_mean_meters, s.lot_id;
-- You should see 17 rows with altitude_after empty on every row.

-- ----------------------------------------------------------------------
-- PART 4  DATABASE STRUCTURE: KEYS  (this part creates three real tables)
-- ----------------------------------------------------------------------
-- The clean view is one wide table. Here the same data is split into three
-- tables that point to each other with keys. This is what the ERD shows.
--
--   countries   one row per country. The country name is its PRIMARY KEY.
--   lots        one row per green-coffee lot, with its own PRIMARY KEY lot_id.
--               Its country column is a FOREIGN KEY that points to countries.
--   cup_scores  the cupping result of each lot (total + ten part scores).
--               Its lot_id is both PRIMARY KEY and FOREIGN KEY, so every lot
--               has exactly one cup_scores row (one-to-one).
--
-- Why is the country not the key of lots? A primary key must be different
-- on every row, and one country has many lots (Mexico has 236). So the
-- country is the key of the small countries table and every lot points to
-- it: one country, many lots (one-to-many).
-- Why does lot_id matter? It is made from the cleaning, not invented: the
-- letter of the species plus the row number in the raw file (A5, R12).
-- That gives the lot a unique key, it ties lots to its cup_scores row, and
-- it lets you go back from any clean lot to its raw row (query 3.7).
-- Why a separate cup_scores table? lots holds what is known before cupping
-- (the model inputs). cup_scores holds the cupper's answer: the target and
-- the part scores that are never used to predict it.
-- Note: the raw file treats "United States" and "United States (Hawaii)" as
-- two countries, and this file keeps them as they are.

-- Drop the children first, then the parent.
DROP TABLE IF EXISTS cup_scores;
DROP TABLE IF EXISTS lots;
DROP TABLE IF EXISTS countries;

CREATE TABLE countries (
    country                TEXT    NOT NULL PRIMARY KEY
);

CREATE TABLE lots (
    lot_id                 TEXT    NOT NULL PRIMARY KEY,
    species                TEXT    NOT NULL,
    country                TEXT,
    variety                TEXT,
    processing_method      TEXT,
    color                  TEXT,
    moisture               REAL,
    category_one_defects   INTEGER,
    category_two_defects   INTEGER,
    altitude_mean_meters   REAL,
    FOREIGN KEY (country) REFERENCES countries (country)
);

CREATE TABLE cup_scores (
    lot_id                 TEXT    NOT NULL PRIMARY KEY,
    total_cup_points       REAL    NOT NULL,
    aroma                  REAL,
    flavor                 REAL,
    aftertaste             REAL,
    acidity                REAL,
    body                   REAL,
    balance                REAL,
    uniformity             REAL,
    clean_cup              REAL,
    sweetness              REAL,
    cupper_points          REAL,
    FOREIGN KEY (lot_id) REFERENCES lots (lot_id)
);

-- The parent table is filled first. DISTINCT keeps every country once.
-- A lot with no country (there is one) gets no row here.
INSERT INTO countries (country)
SELECT DISTINCT "Country.of.Origin"
FROM cqi_clean
WHERE "Country.of.Origin" IS NOT NULL
ORDER BY "Country.of.Origin";

-- Both tables read lot_id straight from the clean view, so a lot and its
-- scores always carry the same id.
INSERT INTO lots (lot_id, species, country, variety, processing_method, color,
                  moisture, category_one_defects, category_two_defects, altitude_mean_meters)
SELECT lot_id, species, "Country.of.Origin", Variety, "Processing.Method", Color,
       Moisture, "Category.One.Defects", "Category.Two.Defects", altitude_mean_meters
FROM cqi_clean;

INSERT INTO cup_scores (lot_id, total_cup_points, aroma, flavor, aftertaste, acidity, body,
                        balance, uniformity, clean_cup, sweetness, cupper_points)
SELECT lot_id, "Total.Cup.Points", Aroma, Flavor, Aftertaste, Acidity, Body,
       Balance, Uniformity, "Clean.Cup", Sweetness, "Cupper.Points"
FROM cqi_clean;

-- 4.1 The one-to-many link: how many lots does each country have?
--     LEFT JOIN keeps every country, even one with no lots.
SELECT countries.country, COUNT(lots.lot_id) AS lots
FROM countries
LEFT JOIN lots ON countries.country = lots.country
GROUP BY countries.country
ORDER BY lots DESC
LIMIT 5;
-- You should see: Mexico 236, Colombia 183, Guatemala 181, Brazil 132 and
-- Taiwan 75.

-- 4.2 Join all three tables, as in the SQL II lesson: the five best cups
SELECT lots.lot_id, countries.country, lots.processing_method, cup_scores.total_cup_points
FROM countries
INNER JOIN lots       ON countries.country = lots.country
INNER JOIN cup_scores ON lots.lot_id = cup_scores.lot_id
ORDER BY cup_scores.total_cup_points DESC
LIMIT 5;
-- You should see Ethiopia at the top with 90.58.

-- ----------------------------------------------------------------------
-- PART 5  CHECKS  (keep this last, so Execute all ends on it)
-- ----------------------------------------------------------------------
-- Every rule has an expected count. If one is different, stop and look at
-- why. Do not change the rule to fit the count.
-- Steps 3 to 6 are 264 = 252 Arabica + 12 Robusta, 38, 16 = 14 Arabica +
-- 2 Robusta, and 17.
-- Steps 20 to 31 check the keys and the ids. A LEFT JOIN plus IS NULL finds
-- the rows with no partner (the trick from the SQL II lesson), so a lot
-- pointing to a country that does not exist would show up as a number above 0.
-- The subqueries in SELECT each return one number, and the whole list sits
-- in a derived table with an alias, as in the SQL II lesson.

SELECT step, check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL - stop and look' END AS result
FROM (
    SELECT 1 AS step, 'rows after stacking' AS check_name,
           (SELECT COUNT(*) FROM cqi_stacked) AS actual, 1339 AS expected
    UNION ALL
    SELECT 2, 'row rule: total = 0 dropped',
           (SELECT COUNT(*) FROM cqi_stacked WHERE "Total.Cup.Points" = 0), 1
    UNION ALL
    SELECT 3, 'moisture 0.0 emptied (Arabica + Robusta)',
           (SELECT COUNT(*) FROM cqi_stacked WHERE "Total.Cup.Points" > 0 AND Moisture = 0), 264
    UNION ALL
    SELECT 4, 'moisture 0.01 to 0.05 emptied',
           (SELECT COUNT(*) FROM cqi_stacked WHERE "Total.Cup.Points" > 0 AND Moisture > 0 AND Moisture <= 0.05), 38
    UNION ALL
    SELECT 5, 'altitude above 3000 m emptied',
           (SELECT COUNT(*) FROM cqi_stacked WHERE "Total.Cup.Points" > 0 AND altitude_mean_meters > 3000), 16
    UNION ALL
    SELECT 6, 'Arabica altitude below 50 m emptied',
           (SELECT COUNT(*) FROM cqi_stacked WHERE "Total.Cup.Points" > 0 AND species = 'arabica' AND altitude_mean_meters < 50), 17
    UNION ALL
    SELECT 7, 'clean rows',
           (SELECT COUNT(*) FROM cqi_clean), 1338
    UNION ALL
    SELECT 8, 'clean Arabica rows',
           (SELECT COUNT(*) FROM cqi_clean WHERE species = 'arabica'), 1310
    UNION ALL
    SELECT 9, 'clean Robusta rows',
           (SELECT COUNT(*) FROM cqi_clean WHERE species = 'robusta'), 28
    UNION ALL
    SELECT 10, 'clean columns (lot_id + the 20 agreed ones)',
           (SELECT COUNT(*) FROM pragma_table_info('cqi_clean')), 21
    UNION ALL
    SELECT 11, 'dropped columns still present',
           (SELECT COUNT(*) FROM pragma_table_info('cqi_clean')
            WHERE name IN ('Owner', 'Owner.1', 'Producer', 'Farm.Name', 'Lot.Number', 'Mill',
                           'ICO.Number', 'Company', 'Certification.Body', 'Certification.Address',
                           'Certification.Contact', 'Region', 'Harvest.Year', 'In.Country.Partner',
                           'Quakers')), 0
    UNION ALL
    SELECT 12, 'moisture still exactly 0',
           (SELECT COUNT(*) FROM cqi_clean WHERE Moisture = 0), 0
    UNION ALL
    SELECT 13, 'moisture still 0.01 to 0.05',
           (SELECT COUNT(*) FROM cqi_clean WHERE Moisture > 0 AND Moisture <= 0.05), 0
    UNION ALL
    SELECT 14, 'altitude still above 3000 m',
           (SELECT COUNT(*) FROM cqi_clean WHERE altitude_mean_meters > 3000), 0
    UNION ALL
    SELECT 15, 'Arabica altitude still below 50 m',
           (SELECT COUNT(*) FROM cqi_clean WHERE species = 'arabica' AND altitude_mean_meters < 50), 0
    UNION ALL
    SELECT 16, 'Arabica lots with a moisture value',
           (SELECT COUNT(Moisture) FROM cqi_clean WHERE species = 'arabica'), 1020
    UNION ALL
    SELECT 17, 'Robusta cells filled in Acidity, Body, Sweetness',
           (SELECT COUNT(Acidity) + COUNT(Body) + COUNT(Sweetness) FROM cqi_clean WHERE species = 'robusta'), 0
    UNION ALL
    SELECT 18, 'Robusta altitude below 50 m left as it is (Ecuador, 40 m)',
           (SELECT COUNT(*) FROM cqi_clean WHERE species = 'robusta' AND altitude_mean_meters < 50), 1
    UNION ALL
    SELECT 19, 'number columns stored as text',
           (SELECT COUNT(*) FROM cqi_clean
            WHERE typeof(Moisture) = 'text' OR typeof(altitude_mean_meters) = 'text'
               OR typeof("Total.Cup.Points") = 'text'), 0
    UNION ALL
    SELECT 20, 'countries rows = different countries in the clean data',
           (SELECT COUNT(*) FROM countries),
           (SELECT COUNT(DISTINCT "Country.of.Origin") FROM cqi_clean)
    UNION ALL
    SELECT 21, 'lots rows',
           (SELECT COUNT(*) FROM lots), 1338
    UNION ALL
    SELECT 22, 'cup_scores rows',
           (SELECT COUNT(*) FROM cup_scores), 1338
    UNION ALL
    SELECT 23, 'lots pointing to a country that does not exist',
           (SELECT COUNT(*) FROM lots
            LEFT JOIN countries ON lots.country = countries.country
            WHERE lots.country IS NOT NULL AND countries.country IS NULL), 0
    UNION ALL
    SELECT 24, 'cup_scores pointing to a lot that does not exist',
           (SELECT COUNT(*) FROM cup_scores
            LEFT JOIN lots ON cup_scores.lot_id = lots.lot_id
            WHERE lots.lot_id IS NULL), 0
    UNION ALL
    SELECT 25, 'lots without a cup_scores row (one-to-one holds)',
           (SELECT COUNT(*) FROM lots
            LEFT JOIN cup_scores ON lots.lot_id = cup_scores.lot_id
            WHERE cup_scores.lot_id IS NULL), 0
    UNION ALL
    SELECT 26, 'lots with no country (foreign key left empty)',
           (SELECT COUNT(*) FROM lots WHERE country IS NULL), 1
    UNION ALL
    SELECT 27, 'total cup points the same after the split',
           (SELECT ROUND(SUM(total_cup_points), 2) FROM cup_scores),
           (SELECT ROUND(SUM("Total.Cup.Points"), 2) FROM cqi_clean)
    UNION ALL
    SELECT 28, 'lot_ids that appear more than once',
           (SELECT COUNT(*) - COUNT(DISTINCT lot_id) FROM cqi_clean), 0
    UNION ALL
    SELECT 29, 'raw lots missing from the clean data (the one dropped lot)',
           (SELECT COUNT(*) FROM cqi_stacked WHERE lot_id NOT IN (SELECT lot_id FROM cqi_clean)), 1
    UNION ALL
    SELECT 30, 'lots whose lot_id is not in the clean data',
           (SELECT COUNT(*) FROM lots WHERE lot_id NOT IN (SELECT lot_id FROM cqi_clean)), 0
    UNION ALL
    SELECT 31, 'lot_ids whose letter does not match the species',
           (SELECT COUNT(*) FROM lots
            WHERE (species = 'arabica' AND lot_id NOT LIKE 'A%')
               OR (species = 'robusta' AND lot_id NOT LIKE 'R%')), 0
) AS checks
ORDER BY step;

-- ----------------------------------------------------------------------
-- PART 6  USE IT FROM PYTHON  (comments only, run these in the notebook)
-- ----------------------------------------------------------------------
--   clean   = pd.read_sql("SELECT * FROM cqi_clean;", con)
--   clean.shape                    # (1338, 21): lot_id + the 20 columns of data/clean/cqi_clean.csv
--   clean.drop(columns="lot_id")   # (1338, 20), the same columns as the CSV
--   arabica = pd.read_sql("SELECT * FROM cqi_clean WHERE species = 'arabica';", con)
--   arabica.shape                  # (1310, 21): drop lot_id before modelling, it is a label
--   A view reads like a table, so read_sql needs nothing special.
--   The three keyed tables read the same way, for example:
--   pd.read_sql("SELECT * FROM lots JOIN cup_scores ON lots.lot_id = cup_scores.lot_id;", con)

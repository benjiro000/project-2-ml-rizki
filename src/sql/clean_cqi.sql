-- Stack the Arabica and Robusta CQI files into one table with the gate 2 columns.
-- Run by src/run_cleaning.py on two in-memory SQLite tables: arabica_raw and robusta_raw.
-- Why explicit columns: only the 19 columns kept at gate 2 come through, never a personal data column.
-- Why double quotes: the column names contain dots, which SQL only accepts inside quotes.

SELECT
    'arabica'                AS species,
    "Country.of.Origin"      AS "Country.of.Origin",
    "Variety"                AS "Variety",
    "Processing.Method"      AS "Processing.Method",
    "Color"                  AS "Color",
    "Moisture"               AS "Moisture",
    "Category.One.Defects"   AS "Category.One.Defects",
    "Category.Two.Defects"   AS "Category.Two.Defects",
    "altitude_mean_meters"   AS "altitude_mean_meters",
    "Total.Cup.Points"       AS "Total.Cup.Points",
    "Aroma"                  AS "Aroma",
    "Flavor"                 AS "Flavor",
    "Aftertaste"             AS "Aftertaste",
    "Acidity"                AS "Acidity",
    "Body"                   AS "Body",
    "Balance"                AS "Balance",
    "Uniformity"             AS "Uniformity",
    "Clean.Cup"              AS "Clean.Cup",
    "Sweetness"              AS "Sweetness",
    "Cupper.Points"          AS "Cupper.Points"
FROM arabica_raw

UNION ALL

-- Robusta: same columns in the same order.
-- Why the renames: Fragrance...Aroma and Uniform.Cup are strong matches at gate 2.
-- Why NULL: the Acidity, Body and Sweetness matches are only guesses, so they stay empty.
SELECT
    'robusta'                AS species,
    "Country.of.Origin"      AS "Country.of.Origin",
    "Variety"                AS "Variety",
    "Processing.Method"      AS "Processing.Method",
    "Color"                  AS "Color",
    "Moisture"               AS "Moisture",
    "Category.One.Defects"   AS "Category.One.Defects",
    "Category.Two.Defects"   AS "Category.Two.Defects",
    "altitude_mean_meters"   AS "altitude_mean_meters",
    "Total.Cup.Points"       AS "Total.Cup.Points",
    "Fragrance...Aroma"      AS "Aroma",
    "Flavor"                 AS "Flavor",
    "Aftertaste"             AS "Aftertaste",
    NULL                     AS "Acidity",
    NULL                     AS "Body",
    "Balance"                AS "Balance",
    "Uniform.Cup"            AS "Uniformity",
    "Clean.Cup"              AS "Clean.Cup",
    NULL                     AS "Sweetness",
    "Cupper.Points"          AS "Cupper.Points"
FROM robusta_raw;

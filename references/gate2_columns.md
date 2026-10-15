# Gate 2: column sheet for ds_cqi_jldbc_2018

Gate 2 is the human decision on which columns are kept or dropped. Nothing here changes the data; it is a proposal for you to fill in.

Based on: the Reviewer run for ds_cqi_jldbc_2018 (references/reviews/ds_cqi_jldbc_2018.json), the four profiles in references/profiles/, and one read-only count on the local copies of arabica_data_cleaned.csv and robusta_data_cleaned.csv (marked "read-only count" below). No file was cleaned or changed.

## Summary

- **Proposed target:** `Total.Cup.Points` (overall cupping score, number, 0.0 missing). Regression.
- **Proposed features (bean and origin measurements only):** `Country.of.Origin`, `Variety`, `Processing.Method`, `Color`, `Moisture`, `Category.One.Defects`, `Category.Two.Defects`, `Quakers`, `altitude_mean_meters`. None of the ten part scores is a feature.
- **Never in a model and never on the globe:**
  - Personal data: `Owner`, `Owner.1`, `Producer`, `Farm.Name`, `Company`, `Mill`, `Certification.Address`, `Certification.Contact`. Several examples are people's names (for example "yidnekachew dabessa"); the address and contact examples are hidden in the profile because they may hold personal contact details.
  - The ten part scores when predicting the total: `Aroma`, `Flavor`, `Aftertaste`, `Acidity`, `Body`, `Balance`, `Uniformity`, `Clean.Cup`, `Sweetness`, `Cupper.Points`. They add up to the total (Reviewer: first row 90.59 vs 90.58), so a model would just learn the sum.
- **Values that may mean "not measured" (read-only count, arabica_data_cleaned):**
  - `Moisture` = 0.0 in **252 of 1,311 rows** (19%). The next lowest values, 0.01 to 0.05, cover 38 more rows and are also doubtful. Most values sit between 0.10 and 0.12. In robusta, 12 of 28 rows are 0.0.
  - `altitude_mean_meters` (and low/high): 12 rows are exactly 1 m, 18 rows are below 100 m, 14 rows are above 3,000 m, and the largest is 190,164 m. These look like typing or unit errors, not real altitudes. 227 rows (17.3%) are empty.
  - One row has `Total.Cup.Points` = 0.0 and every part score = 0.0 (`Clean.Cup` has 2 zeros). That looks like an empty score sheet, not a real score of zero.
  - `Number.of.Bags` = 0 in 1 row.
  - `ICO.Number` is only zeros ("0", "00", ...) in 67 rows: a placeholder, not a number.
  - `Variety` = "Other" in 108 rows and `Processing.Method` = "Other" in 26 rows: "something else", not unknown, but they carry little information.
  - `Harvest.Year` holds text such as "TEST", "mmm", "Mayo a Julio", "4T/10" next to real years.

## Table 1: every column of arabica_data_cleaned.csv (1,311 rows, 44 columns)

Share missing is from the profile (empty cells only; zeros and placeholders are not counted as missing). "From the name" means the meaning is only read from the column name; the files do not explain it.

| # | Column | Meaning | Type | Share missing | Proposed role | Reason | Your decision (keep / drop) |
|---|---|---|---|---|---|---|---|
| 1 | Unnamed: 0 | row number (1 to 1312) | number | 0.0 | identifier | counts rows, says nothing about the bean | |
| 2 | Species | Arabica or Robusta | text | 0.0 | drop | always "Arabica" in this file; becomes a feature only if the 28 robusta rows are added | |
| 3 | Owner | owner of the sample (from the name) | text | 0.005 | personal data | examples include people's names | |
| 4 | Country.of.Origin | country where the coffee grew | text | 0.001 | feature | origin, and the key that joins rows to the globe; 36 countries | |
| 5 | Farm.Name | farm name (from the name) | text | 0.272 | personal data | some farm names are a person's name; 557 distinct values | |
| 6 | Lot.Number | lot code of the sample (from the name) | text | 0.794 | identifier | a label, not a measurement; 79% empty | |
| 7 | Mill | mill that processed the beans (from the name) | text | 0.236 | personal data | business names that may include a person's name; 447 distinct values; not a bean property | |
| 8 | ICO.Number | International Coffee Organization reference number (from the name) | text | 0.113 | identifier | trade label, 840 distinct values; 67 rows are only zeros | |
| 9 | Company | company behind the sample (from the name) | text | 0.159 | personal data | some company names are a person's name | |
| 10 | Altitude | growing altitude as typed, e.g. "1600 - 1800 m" | text | 0.17 | drop | free text in m and ft; altitude_mean_meters is the number version | |
| 11 | Region | region inside the country, e.g. "oromia" | text | 0.043 | drop | origin detail, but 343 spellings for 1,311 rows; too many categories for a small dataset | |
| 12 | Producer | producer of the coffee (from the name) | text | 0.175 | personal data | examples include people's names | |
| 13 | Number.of.Bags | number of bags in the lot (from the name) | number | 0.0 | drop | shipment size (trade), not a bean property | |
| 14 | Bag.Weight | weight of one bag, e.g. "60 kg" | text | 0.0 | drop | shipment size, mixed units (kg, lbs, none) | |
| 15 | In.Country.Partner | organisation that handled the sample in the country (from the name) | text | 0.0 | drop | an organisation, not a bean property | |
| 16 | Harvest.Year | harvest year | text | 0.036 | drop | time, not a bean or origin measurement; messy text ("TEST", "2013/2014", "Mayo a Julio") | |
| 17 | Grading.Date | date the sample was graded (from the name) | text | 0.0 | drop | certificate paperwork | |
| 18 | Owner.1 | owner again, with original capitals (my guess: 99% of rows equal Owner in lower case) | text | 0.005 | personal data | people's names; also a near copy of Owner | |
| 19 | Variety | coffee plant variety, e.g. Bourbon | text | 0.153 | feature | bean property; 29 values, 108 rows are "Other" | |
| 20 | Processing.Method | how the cherries were processed, e.g. "Washed / Wet" | text | 0.116 | feature | bean property; 5 values. Also a possible classification target (Reviewer) | |
| 21 | Aroma | cupping part score, 0 to 10 (from the name) | number | 0.0 | leakage | part of Total.Cup.Points | |
| 22 | Flavor | cupping part score, 0 to 10 (from the name) | number | 0.0 | leakage | part of Total.Cup.Points | |
| 23 | Aftertaste | cupping part score, 0 to 10 (from the name) | number | 0.0 | leakage | part of Total.Cup.Points | |
| 24 | Acidity | cupping part score, 0 to 10 (from the name) | number | 0.0 | leakage | part of Total.Cup.Points | |
| 25 | Body | cupping part score, 0 to 10 (from the name) | number | 0.0 | leakage | part of Total.Cup.Points | |
| 26 | Balance | cupping part score, 0 to 10 (from the name) | number | 0.0 | leakage | part of Total.Cup.Points | |
| 27 | Uniformity | cupping part score, 0 to 10 (from the name) | number | 0.0 | leakage | part of Total.Cup.Points | |
| 28 | Clean.Cup | cupping part score, 0 to 10 (from the name) | number | 0.0 | leakage | part of Total.Cup.Points | |
| 29 | Sweetness | cupping part score, 0 to 10 (from the name) | number | 0.0 | leakage | part of Total.Cup.Points | |
| 30 | Cupper.Points | the taster's own overall score, 0 to 10 (from the name) | number | 0.0 | leakage | part of Total.Cup.Points | |
| 31 | Total.Cup.Points | total cupping score, sum of the ten parts | number | 0.0 | target candidate | the quality score to predict; 1 row is 0.0 (empty score sheet) | |
| 32 | Moisture | water content of the green beans as a fraction (0.12 = 12%) | number | 0.0 | feature | green-bean measurement; but 252 rows are 0.0, likely "not measured" | |
| 33 | Category.One.Defects | count of category one green-bean defects (from the name) | number | 0.0 | feature | green-bean measurement | |
| 34 | Quakers | count of "quaker" beans (from the name) | number | 0.001 | feature | bean quality count; the files do not say how or when it is counted | |
| 35 | Color | colour of the green beans: Green, Bluish-Green, Blue-Green | text | 0.204 | feature | bean property; also a possible classification target (Reviewer) | |
| 36 | Category.Two.Defects | count of category two green-bean defects (from the name) | number | 0.0 | feature | green-bean measurement | |
| 37 | Expiration | date the certificate expires (examples are one year after Grading.Date) | text | 0.0 | drop | certificate paperwork | |
| 38 | Certification.Body | organisation that issued the certificate | text | 0.0 | drop | an organisation, not a bean property | |
| 39 | Certification.Address | address of the certifying organisation (from the name; hidden in profile) | text | 0.0 | personal data | may contain personal contact details | |
| 40 | Certification.Contact | contact at the certifying organisation (from the name; hidden in profile) | text | 0.0 | personal data | may contain personal contact details | |
| 41 | unit_of_measurement | unit of the Altitude text: m or ft | text | 0.0 | drop | only describes Altitude; 182 rows are ft | |
| 42 | altitude_low_meters | lowest altitude of the range, in metres | number | 0.173 | drop | almost the same information as altitude_mean_meters | |
| 43 | altitude_high_meters | highest altitude of the range, in metres | number | 0.173 | drop | almost the same information as altitude_mean_meters | |
| 44 | altitude_mean_meters | middle of the altitude range, in metres | number | 0.173 | feature | origin measurement; has impossible values (1 m, 190,164 m) | |

### Role counts

| Proposed role | Count | Columns |
|---|---|---|
| target candidate | 1 | Total.Cup.Points |
| feature | 9 | Country.of.Origin, Variety, Processing.Method, Moisture, Category.One.Defects, Quakers, Color, Category.Two.Defects, altitude_mean_meters |
| identifier | 3 | Unnamed: 0, Lot.Number, ICO.Number |
| leakage | 10 | Aroma, Flavor, Aftertaste, Acidity, Body, Balance, Uniformity, Clean.Cup, Sweetness, Cupper.Points |
| personal data | 8 | Owner, Farm.Name, Mill, Company, Producer, Owner.1, Certification.Address, Certification.Contact |
| drop | 13 | Species, Altitude, Region, Number.of.Bags, Bag.Weight, In.Country.Partner, Harvest.Year, Grading.Date, Expiration, Certification.Body, unit_of_measurement, altitude_low_meters, altitude_high_meters |

## Table 2: robusta_data_cleaned.csv (28 rows, 44 columns) against Arabica

Robusta has 39 columns with the same name as an Arabica column and 5 columns with a different name. "Guess" means I matched by meaning from the name and the values, not from any documentation.

### Same name, same meaning, but something differs

| Robusta column | Arabica column | What differs |
|---|---|---|
| Harvest.Year | Harvest.Year | number in Robusta (6 clean years), text in Arabica |
| Variety | Variety | 0.893 missing in Robusta (0.153 in Arabica); only "Other" and "Arusha" |
| Processing.Method | Processing.Method | 0.643 missing in Robusta (0.116); only 2 values |
| Moisture | Moisture | 12 of 28 rows are 0.0 (43%) |
| Quakers | Quakers | always 0 in Robusta, stored as whole number |
| unit_of_measurement | unit_of_measurement | always "m" in Robusta |
| Country.of.Origin | Country.of.Origin | only 5 countries (India 13, Uganda 10, United States 2, Ecuador 2, Vietnam 1); all 5 also appear in Arabica |
| Species | Species | always "Robusta" |
| Total.Cup.Points | Total.Cup.Points | same 100-point total, but the sum of a different set of part scores (see below), so the two totals may not be directly comparable (guess) |
| Category.One.Defects | Category.One.Defects | Robusta goes up to 63 (Arabica up to 31) |

### Same name, same meaning, no notable difference (29 columns)

Unnamed: 0, Owner, Farm.Name, Lot.Number, Mill, ICO.Number, Company, Altitude, Region, Producer, Number.of.Bags, Bag.Weight, In.Country.Partner, Grading.Date, Owner.1, Flavor, Aftertaste, Clean.Cup, Balance, Cupper.Points, Color, Category.Two.Defects, Expiration, Certification.Body, Certification.Address, Certification.Contact, altitude_low_meters, altitude_high_meters, altitude_mean_meters. The proposed roles from Table 1 apply to these too.

### Different name, matched by meaning

| Robusta column | Arabica column | Match | Why |
|---|---|---|---|
| Fragrance...Aroma | Aroma | guess, strong | name contains "Aroma"; same 0 to 10 scale |
| Uniform.Cup | Uniformity | guess, strong | same idea in the name; same values (10.0, 9.33) |
| Salt...Acid | Acidity | guess, medium | name contains "Acid"; same place among the scores |
| Mouthfeel | Body | guess, medium | mouthfeel and body describe the same thing in plain language; same place among the scores |
| Bitter...Sweet | Sweetness | guess, weak | name contains "Sweet", but the values differ: Robusta 6.67 to 8.42, Arabica Sweetness is mostly 10.0 |

### No match

| Column | File | Note |
|---|---|---|
| Sweetness | Arabica | only a weak match with Bitter...Sweet (see above) |
| Bitter...Sweet | Robusta | only a weak match with Sweetness (see above) |

All five renamed Robusta columns are part scores, so they are **leakage** when predicting Total.Cup.Points, the same as their Arabica partners. None of the proposed features is affected by the renaming.

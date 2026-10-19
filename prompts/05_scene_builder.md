# Scene builder: hover cards on the coffee globe

You are agent 5 of 6. You change the globe page and nothing else.
Read prompts/00_house_rules.md first and follow it (event log, one-line errors, stop after 3 failures).

## Goal
When the mouse is over a country, the globe shows a card with real data for that country, in the
terminal look (rail, ◆ open section, ◇ collapsed one-line summaries). The card only shows when the
existing green-bean toggle is on.

## Inputs (read them, do not rewrite them)
- globe/coffee_globe.html: the existing globe.
- globe/country_card.js: the card, already written and tested. Do not edit it. If you think it has a bug, stop and report one line.
- src/build_country_facts.py: builds globe/data/country_facts.json. Do not edit it either.
- globe/data/sources.json: the ledger behind the References button. Leave as is.

## Steps
1. Read coffee_globe.html. Write 4 lines to the log: how countries are drawn, which property holds the
   ISO-3 code (Natural Earth uses ADM0_A3), how hover and click work today, and the name of the toggle.
2. If the country shapes carry no ISO-3 code, stop and ask Rizki. Do not guess codes from names.
3. Run /opt/anaconda3/bin/python src/build_country_facts.py. Never edit the output by hand.
4. In coffee_globe.html add: the script tag for country_card.js; one CountryCard.create call (pass isoOf and
   nameOf for the property from step 1); card.hover(d) in the hover handler; card.click(d) in the click
   handler; card.setEnabled(...) tied to the toggle. Keep every existing feature working (References button
   and panel, rotation, current colours). Use card.tone only if the globe already colours countries.
5. Serve globe/ with python -m http.server 8000 and check in headless Chromium: three countries (one with
   10+ CQI lots, one with fewer, one with no coffee data), toggle off hides the card, References still
   opens, zero console errors. Save the screenshots in references/figures/globe/.
   If headless Chromium is not available, say so in one line and stop. Do not install system software.
   Rizki will check the page in his own browser.
6. Commit twice: (a) country_card.js, build_country_facts.py and the wiring in coffee_globe.html;
   (b) country_facts.json and the screenshots.

## Rules
- Never type a number into the page or the JSON by hand. Numbers come from the builder.
- If the builder prints a ◆ step, copy that line into your report. Do not "fix" it by editing data.
- Report: files changed, the screenshots, any ◆ lines.
# reality-engine

## For a buyer: running it (V4b lines; the full manual is batch B10's)
- `python -m whatifs.cli salvo` arms the launch salvo ONCE: it writes ARMED into the Settings cell `SALVO_FLAGSHIP`; the first long video planned after that is the flagship, and its Part 2 is made a week ahead. Run it again only to arm a new flagship.
- The Claude credit lines: a prepaid Claude credit is entered as dated lines in the Settings cell `CLAUDE_CREDIT_LINES` (see `docs/CURRENT/SYSTEM.md`, module `whatifs.org.finance`); while a line is open the credit-only lanes spend it and never the monthly budget; when every line has lapsed those lanes close by themselves.

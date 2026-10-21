# templates/

Pot sets the app can load instead of the ones baked into `model/`.

On the pots screen, in **draw-only** mode, "Load a template" reads one of
these files and replaces all 36 clubs at once. Full simulation mode does
not offer the button: it shows the same pots, read-only.

## Layout

One folder per season, named `<START>_<END>`, plus `saved/` for the ones
the app writes itself:

```
templates/
  README.md
  2025_2026/
    UCL_2025_2026.json     4 pots x 9    draw of 28 Aug 2025
    UEL_2025_2026.json     4 pots x 9    draw of 29 Aug 2025
    UECL_2025_2026.json    6 pots x 6    draw of 29 Aug 2025
  2026_2027/               (empty until the play-offs finish)
  saved/                   written by "Save these pots"
    UCL_20260826-143012.json
    badges/
      UCL_20260826-143012/
        Club Testeur _ FC.png
```

Each 2025/26 file was cross-checked against a second source club by club
before being written.

## The format

```json
{
  "Pot 1": {
    "Arsenal": {
      "Image": "../../assets/images/clubs/UCL/Arsenal_logo.png",
      "Country": "England"
    }
  }
}
```

- **Pot keys** are forgiving: `Pot 1`, `pot 1`, `POT_1` and `Pot1` all
  read as pot one. The *set* is not forgiving: exactly 4 pots numbered
  1 to 4 (6 for the Conference League), no gaps.
- **Club names** must be unique across every pot. Two clubs with the same
  name collapse into one key in the engine's `teams` dictionary and the
  draw silently loses a team.
- **`Country`** is required. It carries the "no more than two opponents
  from the same association" rule, so a wrong or missing one changes the
  draw rather than just the label. Any string is accepted, but one that
  is not a UEFA member is reported as a warning, because a typo here
  breaks the rule without breaking anything visible.
- **`Image`** must be present. `""` or `null` means "no badge", and the
  app draws the club's initials instead. A path that does not exist, or
  that Pillow cannot open, is refused.
- **Relative paths resolve against the folder the JSON sits in**, not
  against wherever the app was launched from. That is what makes a
  template portable: zip the JSON with its badges and it works on another
  machine. It is also why the paths above start with `../../` and not
  `../`: the file is two levels down from the project root, so moving a
  template between season folders is fine but moving it up a level means
  fixing the depth.

Nothing is applied unless the whole file passes. Every problem is
reported at once, so a broken file is fixed in one pass.

## Saving what is on screen

In draw-only mode the pots screen has a second button next to "Load a
template": **Save these pots**. It writes the thirty-six clubs exactly as
they stand, hand-made replacements and imported badges included, to

```
templates/saved/<COMP>_<YYYYMMDD-HHMMSS>.json
```

Date before time, so the alphabetical order of the folder is also the
chronological one. Nothing is ever overwritten: a second save in the same
second is the only collision possible, and there is no way to produce one
by clicking.

Each club's badge is looked up in this order:

1. the file imported by hand in the replace dialog
2. `assets/images/clubs/<COMP>/<Club>_logo.png`
3. nothing, and `"Image"` is written as `""` -- initials at load time

A badge already inside the project is written as a relative path
(`../../assets/...`), which works because `saved/` sits two levels down
from the root, exactly like `2025_2026/`. A badge imported from anywhere
else is **copied** into `saved/badges/<COMP>_<TIMESTAMP>/` and referenced
from there, so the saved template survives the original being moved or
deleted, and travels by zipping `saved/`.

One folder of copies per template, not one shared `badges/`: two saves of
the same club with two different images would otherwise overwrite each
other, and the older template would quietly start showing the newer
badge.

Nothing is left behind if the write fails. The copies go down first, the
JSON last, and any folder created on the way is removed before the error
is reported.

Saved templates load through the same "Load a template" button as any
other file, and are checked exactly as strictly. That is the point of the
round trip: what the app writes, the app must accept back without a hand
edit.

## Badges that are not there yet

Clubs new to European football this season have `"Image": ""` and show
their initials. To fill them in, on a machine with internet access:

```
python scripts/fetch_template_badges.py                     # all three
python scripts/fetch_template_badges.py UCL                 # one
python scripts/fetch_template_badges.py --season 2026_2027  # another season
python scripts/fetch_template_badges.py --dry-run           # resolve ids only
```

It looks each club up by name, downloads the badge into
`assets/images/clubs/<COMP>/`, and rewrites the `Image` field to point at
it. Resolved ids are cached in `data/reference/api_ids.json`, so a second
run costs no API calls for clubs it already found. When two clubs score
alike it lists the candidates and asks, rather than guessing: a badge
downloaded under the right filename but showing the wrong club is a
mistake nobody ever notices.

Looking up an id needs `API_KEY` in `.env`. Downloading the image itself
does not.

## Adding a season

Make the folder, drop in `<COMP>_<START>_<END>.json`, and point the
fetcher at it with `--season`. The app never reads this folder as a
list, it opens whatever you pick in the file dialog, so nothing needs
registering anywhere.

Current state, badges already on disk:

| | clubs | with a badge | showing initials |
|---|---|---|---|
| UCL 2025/26 | 36 | 31 | 5 |
| UEL 2025/26 | 36 | 28 | 8 |
| UECL 2025/26 | 36 | 13 | 23 |

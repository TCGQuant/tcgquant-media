# TCG Quant daily X + Threads posts: playbook

Grayson approved these posts as **fully automatic** (Nov 25, 2026). Five posts a day, the **same post on X and Threads**,
at **3, 5, 7, 9 and 11 PM Pacific (America/Vancouver)**. Visuals: **about 40% of posts carry an image (2 of the 5 each day on average)**, card posts first (Grayson, Nov 25, 2026).

Two scheduled runs use this file:
- **Build run** (about 2:20 PM PT, needs Grayson's PC): pulls TCG Quant data, writes the 5 posts and visuals into
  `textposts/YYYY-MM-DD/`, commits and pushes. Posts nothing itself.
- **Post runs** (3:01, 5:01, 7:01, 9:01, 11:01 PM PT, no PC needed): each publishes one slot from that day's `posts.json`.

Repo: `TCGQuant/tcgquant-media` (attach with add_repo, push access). Public media URL pattern:
`https://raw.githubusercontent.com/TCGQuant/tcgquant-media/main/<path>`.
Commit as `git -c user.name="TCG Quant" -c user.email="tcgquant@users.noreply.github.com" commit`, push with
`git -c push.negotiate=true push -q origin HEAD`. End commit messages with the attribution lines your session gives you.

Upload-Post profile: `TCGQuant`. Platforms: `["x", "threads"]`. Threads topic tag (`platformOptions.threadsTopicTag`):
`Pokemon Threads` for Pokemon posts, `One Piece` for One Piece posts.

## Content rules (all of them, every post)
- **Objective data only**, except the hot-take slot, which is Grayson's own stated opinion (see hot_takes.md).
- Say "most valuable", never "most expensive".
- Never say or imply that prices come from different sources. Price wording: "TCGplayer market" or just the price.
- **X: max 280 characters** (emoji count as 2), **no links on X**. Threads: max 500 characters.
- Use the exact numbers from the data (2 decimals for under $1,000 unless rounding reads better; whole dollars above).
- No financial advice language ("you should buy"). Questions and facts are fine.
- Never repeat a product/card used in the last 14 days of `automation/posted_log.md` in the same slot, and never use the same
  product/card twice in one day.
- Mix Pokemon and One Piece across the day (at least one of each most days).
- Plain hashtags at the end: #PokemonTCG, #Pokemon151, #OnePieceTCG etc. (1 to 2 per post).

## The five slots
| Time (PT) | Slot | What | Visual |
|---|---|---|---|
| 3 PM | mover | Biggest 7-day sealed price move (up or down) from METRICS_HISTORY, before → after, % | price chart on alternate days |
| 5 PM | card | Card stat: PSA 10 pop / gem rate from CARD_POPS, or a card's 12-month climb/crash | **always** a card photo card |
| 7 PM | value | Price vs MSRP, price a year ago vs now, or pack EV vs pack price | product photo on the days the mover has none |
| 9 PM | hottake | Grayson's hot take (hot_takes.md), paired with one current number | none |
| 11 PM | engage | Data-backed question. On X use a poll: `xPollOptions` (2 to 4), `xPollDuration` 1440; Threads gets the question as text (`threadsTitle`) | none |

Image rule: exactly 2 images a day = 40%. The card post always has one; the second goes to the mover (chart) or the
value post (photo), alternating day to day (check yesterday's posts.json). Everything else is text only.

## Build run: steps
1. Attach the repo (add_repo TCGQuant/tcgquant-media, push) and clone it.
2. If `textposts/<today PT>/posts.json` already exists, stop quietly (today's batch is done).
   Read `automation/posted_log.md` (last 14 days) and `automation/hot_takes.md`. Also memory_read `/areas/grayson-market-views.md`
   (kept current every Sunday from his new videos): a newer view there replaces an older one in hot_takes.md, and new views can be used
   as hot takes (add them to hot_takes.md first).
3. Data: use the built-in browser pane on Grayson's computer (`mcp__remote-devices__Claude_Browser__*`).
   Open/reuse a tab on `https://tcgquant-staging.netlify.app/dashboard` (fallback: `https://tcgquant.com/dashboard`). Wait until `window.ALL_DATASETS`, `window.METRICS_HISTORY`,
   `window.PF_CATALOG`, `window.CARD_POPS` exist. If the page says "Your session has expired", or the computer cannot be reached,
   STOP: post nothing, and send Grayson one message saying today's text posts were skipped and why (log in / turn PC on).
   Useful globals:
   - `ALL_DATASETS[key]` (key like `"SV + MEGA BBs::Paldea Evolved"`): `market_price, msrp, supply, supply_chg, signal,
     product_id, image_url, history:[{d,p}]` (roughly 2-weekly prices), `release_date`, `ev_per_pack`, `pack_price`.
   - `METRICS_HISTORY[key][YYYY-MM-DD] = {price, supply, daily_sales, ...}`: daily prices. 7-day move = latest date vs the latest
     date at or before (latest minus 7 days); require that base date to be within 3 days of that target.
   - `PF_CATALOG.cards[pid] = [name, set, number, raw_price, ..., gradedPrices]`.
   - `CARD_POPS[pid].psa = {total, g10, g9, gem_rate, as_of}` (also cgc, bgs, tag).
   - `SINGLES_CARD_HISTORY[pid] = [[date, price], ...]` daily card prices (from Jul 2026).
   Keep browser results small (aggregate in the page, return JSON under ~100 KB).
4. Images: product/card photos from `https://product-images.tcgplayer.com/fit-in/600x600/<pid>.jpg`, fetched inside the browser
   pane (tab on product-images.tcgplayer.com) and returned as base64. A tool result over ~250 KB gets cut off, so fetch one image
   per call, and pad results to over 200 KB with `'#PAD#'+'x'.repeat(n)` so they are saved to a file you can decode.
   One Piece scans carry a "SAMPLE" watermark: accepted.
5. Visuals with `automation/visuals.py`:
   - `chart(points, out, title, sub)`: points = `[("YYYY-MM-DD", price), ...]`, 12 months; title like `"OP-13 BOOSTER BOX"`,
     sub `"TCGplayer market price, past 12 months"`.
   - `photo_card(img, out, headline, stat, sub)`: e.g. `("HIDDEN FATES UPC", "$99.99 → $1,450", "2019 MSRP vs TCGplayer market today")`.
   Look at every image before saving it to the repo.
6. Write `textposts/YYYY-MM-DD/posts.json`: a list of 5 objects
   `{"slot":"mover|card|value|hottake|engage", "time":"15:00|17:00|19:00|21:00|23:00", "x": "...", "threads": "... (optional, else same as x)",
     "tag": "Pokemon Threads|One Piece", "img": "file.jpg or null", "poll": ["..",".."] or null, "key": "short product/card id for the log",
     "status": "pending"}`.
   Check every X text is 280 or less (emoji = 2).
7. Append the five keys to `automation/posted_log.md` (date, slot, key). Mark the used hot take in hot_takes.md (`used: YYYY-MM-DD`).
8. Commit and push. Confirm the image URLs answer HTTP 200.

## Post run: steps
1. Attach and clone the repo. Open `textposts/<today PT>/posts.json`. If it is missing, stop quietly (the build run already told Grayson).
2. Pick the entry whose `time` matches this run's hour (PT) and whose `status` is `pending`. If none, stop.
3. Publish now with Upload-Post (`user: "TCGQuant"`, `platforms: ["x","threads"]`, `confirmed: true`; these are pre-approved):
   - with an image: `upload_photos` with the raw.githubusercontent URL; text only: `upload_text`.
   - `title` = x text; `platformOptions.threadsTitle` = threads text when different; `platformOptions.threadsTopicTag` = tag;
     polls: `xPollOptions` + `xPollDuration: 1440`.
4. Poll `get_status` until done. If X says the daily cap is reached, post to Threads only and note it in posts.json.
   If a platform fails for another reason, `retry_post` once.
5. Set the entry's `status` to `posted` (add the post URLs), commit and push.

## Hot takes
- Only Grayson's own stated opinions (hot_takes.md). Keep his meaning exactly; tighten wording only. Never strengthen a view
  ("holding" never becomes "buying").
- Pair each with one current number from the data. If current data clearly contradicts the take (e.g. a box he called
  "near a bottom" has dropped another 20%), skip it and pick another.
- Prefer takes not used in the last 21 days. When fewer than 5 unused takes remain, mention it in the build-run summary.

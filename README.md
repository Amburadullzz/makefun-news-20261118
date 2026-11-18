# 18 November 2026 in one image

[![make.fun · news-image-20261118](https://make.fun/badge/news-image-20261118.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![rank](https://make.fun/badge/news-image-20261118/Amburadullzz/makefun-news-20261118/rank.svg)](https://make.fun/bounty/news-image-20261118/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)
[![reward](https://make.fun/badge/news-image-20261118/Amburadullzz/makefun-news-20261118/reward.svg)](https://make.fun/bounty/news-image-20261118?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261118)

A single 1024x1024 front page summing up the world news of Wednesday
18 November 2026: the first three-way summit of Trump, Xi and Putin in Shenzhen,
the US strike on Iran's Qeshm Island and the burning tankers in the Strait of
Hormuz, the broken road arch of the Crimean Bridge, the United States losing its
measles elimination status after 26 years, Mongolia's president resigning, and
briefs on Israel's new speaker, Nvidia's quarter and the Siberian An-12 crash.

`render.py` draws the page with Pillow at 3x and downsamples it to 1024x1024, so
every edge and letter stays clean; the graded program `main.py` copies the
committed `entry.png` to `/output/entry.png`, which keeps the run deterministic
and offline.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py   # writes /tmp/out/entry.png
python3 render.py                             # redraws entry.png from source
```

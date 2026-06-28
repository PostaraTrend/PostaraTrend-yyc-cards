# yyc-cards

DUSK news-card render service for the YYC Rental Studio (CRLK) autoposter.
Renders the locked DUSK identity (navy-to-sunset gradient, moon, mountain
silhouettes, gold wordmark, Outfit-800 headline + gold underline) to a
1080x1080 PNG via headless Chromium, supersampled at 2x and downscaled for
crisp text.

## Endpoint

`GET /dusk`

Query params:
- `headline` (required) - article title; no contractions
- `source`   - e.g. `According to Storeys`
- `date`     - e.g. `Sunday \u00b7 June 28` (defaults to today, America/Edmonton)
- `footer`   - defaults to `Full report in comments \u00b7 yycrentalstudio.ca`

Returns: `image/png`, 1080x1080.

`GET /health` returns `{"ok": true}`.

## Example

```
https://yyc-cards.onrender.com/dusk?headline=Calgary%20home%20prices%20hold%20steady%20as%20listings%20climb&source=According%20to%20Storeys
```

## Deploy (Render.com)

1. Create a new GitHub repo `PostaraTrend/yyc-cards`, push these files.
2. On Render.com: New > Web Service > connect the repo > Runtime: Docker.
   (Or use the included render.yaml as a Blueprint.)
3. Plan: Starter or higher (headless Chromium needs more memory than free tier
   comfortably allows). Health check path: `/health`.
4. After deploy, test the example URL in a browser - you should get the card PNG.

## n8n wiring

In the `YYC RE - Calgary` workflow, set the `Render Card` node to:

`GET https://yyc-cards.onrender.com/dusk`

with query parameters:
- `headline` = `{{ $('Parse Article Selection').item.json.selected_title }}`
- `source`   = `According to {{ $('Parse Article Selection').item.json.selected_source }}`

The response is the PNG that the Publish node posts as a photo.

## Notes

- One gunicorn worker, Playwright launched per request - robust for low volume
  (a few cards per day). For higher volume, switch to a persistent browser.
- Fonts (Outfit, Playfair Display) load from Google Fonts at render time;
  `networkidle` + `document.fonts.ready` ensure they are applied before capture.
- Headline font-size steps down automatically for long titles.

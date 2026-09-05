# Image placeholders

All photos on the site are currently placeholders from picsum.photos, so the
page works and looks right before you have real photography. Each one has a
stable, named seed (`vertolit-hero`, `vertolit-g1`, etc.) so the same
placeholder always loads in the same spot — nothing will shuffle on you.

To swap in a real photo, put your file in this folder (`assets/images/`) and
update the matching `src` in `index.html`. CSS handles the cropping
(`object-fit: cover`), so any reasonably sized photo will drop in cleanly —
you don't need to pre-crop to an exact aspect ratio.

## Where each image is used

| In `index.html`, search for | Used for | Suggested size |
|---|---|---|
| `vertolit-hero` | Hero background (top of page) | ~1920×1280, landscape |
| `vertolit-about` | About section | ~1000×1250, portrait |
| `vertolit-rooms` | Services — Кімнати card | ~900×900, square |
| `vertolit-tub` | Services — Чан card | ~700×900, portrait |
| `vertolit-sauna` | Services — Лазня card | ~700×700, square |
| `vertolit-kitchen` | Services — Кухня card | ~700×700, square |
| `vertolit-g1` … `vertolit-g7` | Gallery filmstrip (7 photos) | ~700×1000 or ~1100×1000 |
| `vertolit-experience` | "Відпочинок, який хочеться повторити" section | ~1920×1200, landscape |

## Example swap

Before:
```html
<img id="heroImg" src="https://picsum.photos/seed/vertolit-hero/1920/1280" alt="...">
```

After (once `assets/images/hero.jpg` exists):
```html
<img id="heroImg" src="assets/images/hero.jpg" alt="...">
```

Keep the `alt` text (or replace it with an equally accurate description) —
it matters for accessibility and search engines.

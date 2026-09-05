# Вертоліт-комплекс — website

A single landing page for Вертоліт-комплекс, split into separate,
clearly-named files so it's easy to find and change one thing at a time.
No build tools, frameworks, or install step required — it's plain HTML,
CSS, and JavaScript.

## Folder structure

```
vertolit-complex/
├── index.html              All page markup (content, structure)
├── css/
│   ├── variables.css       Colors, fonts, spacing — change the brand here
│   ├── base.css            Reset + reusable bits (buttons, section titles, divider)
│   ├── navigation.css      Navbar + mobile menu
│   ├── hero.css             Top banner section
│   ├── about.css            "Про нас" section
│   ├── services.css         Services grid + celebrations banner
│   ├── gallery.css          Photo filmstrip + custom cursor
│   ├── lightbox.css         Full-screen photo viewer
│   ├── experience.css       "Відпочинок, який хочеться повторити" section
│   ├── booking.css          Booking call-to-action section
│   ├── footer.css           Footer + contact info + map placeholder
│   └── responsive.css       All screen-size breakpoints, in one place
├── js/
│   ├── navigation.js        Navbar scroll behavior, active link, mobile menu
│   ├── parallax.js          Hero/experience image parallax
│   ├── animations.js        Page-load entrance + scroll reveals
│   ├── gallery.js           Gallery cursor + drag-to-scroll + arrows
│   ├── lightbox.js          Full-screen photo viewer logic
│   └── misc.js               Footer copyright year
└── assets/
    └── images/
        └── README.md         Where every placeholder photo goes and its size
```

**Rule of thumb:** if you want to change how something *looks*, its file is
in `css/`, named after the section (e.g. change the gallery → `gallery.css`).
If you want to change how something *behaves*, its file is in `js/`. If you
want to change the *content* (text, photos, links), that's all in
`index.html`.

## Previewing the site locally

This is a plain static site — the simplest option is to just double-click
`index.html` and it'll open in your browser. Everything (CSS, JS, images)
will work.

If you'd rather run it through a local server (closer to how it'll behave
once hosted, and needed if you later add anything that requires `fetch` from
`file://`), any of these work from inside the `vertolit-complex/` folder:

- VS Code: install the "Live Server" extension, right-click `index.html` →
  "Open with Live Server"
- Python: `python3 -m http.server`, then visit `http://localhost:8000`
- Node: `npx serve`

## Common edits

- **Change the accent color or fonts** → `css/variables.css`
- **Replace a placeholder photo** → see `assets/images/README.md`
- **Edit the phone number / Instagram / address** → search `index.html` for
  `REPLACE` comments; they mark every spot with placeholder contact info
- **Add a Google Maps embed** → replace the `.footer__map` block in
  `index.html` (a commented-out example `<iframe>` is right above it)
- **Change section copy (headings, paragraphs)** → edit the text directly in
  `index.html`; each section is wrapped in a `<section>` tag with a matching
  `id` (e.g. `id="about"`) so it's easy to locate

## Deploying

Once you're happy with it, this folder can be uploaded as-is to any static
host (Netlify, Vercel, GitHub Pages, Cloudflare Pages, or plain shared
hosting) — just upload the whole `vertolit-complex/` folder and point the
domain at `index.html`.

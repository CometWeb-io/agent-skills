# Design assets

`cometweb-tokens.json` is the portable token baseline. `cometweb-print.css` uses its state
colours. `status-icons.svg` contains simple functional geometric line icons, not a CometWeb
logo. Use labelled icons: for an accessible inline SVG set `aria-hidden="true"` and retain
visible text in the status pill. These HTML conventions do not certify PDF accessibility.

Embed the needed symbol paths inline for renderers that do not support external SVG use.
Check actual stroke/currentColor in the PDF. Example markup after the symbol is available:

```html
<span class="status status--pending">
  <svg class="icon" aria-hidden="true" viewBox="0 0 24 24"><use href="#clock" /></svg>
  Czeka na retest
</span>
```

No font files, official logos, photos, or sample customer screenshots are bundled.
The CSS is not a finished cover template: use approved logo/font files and inspect all
pagination, contrast, and layout decisions in the actual publication renderer.

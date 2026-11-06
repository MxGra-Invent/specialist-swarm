## Slide format

Each slide is an HTML FRAGMENT written to `slide-<n>.html`.
- Root element is exactly one `<section class="slide">...</section>`.
- No `<html>/<head>/<body>`, no `<script>`, no `<style>`, no inline `<link>`. Use only the classes below.
- Canvas is a fixed 960x540 (16:9) with 48px/64px padding. Content must FIT: no scrolling, no overflow.
  Rule of thumb: max ~6 short bullets, ~60 words total, or ~3 cards. Be concise; short beats complete.
- The viewer scales the slide automatically. Never set widths/heights/fonts inline (small `style="margin-top:..."` is OK).

## Classes (fonts: serif headings, sans body, mono labels; colors: cream bg, near-black text, clay accent)

- `.slide`      root, flex column with 18px gap, cream background
- `.kicker`     small uppercase mono clay label above a title (e.g. "Market", "Risks")
- `h1`          big serif title (48px); use on title/closing slides, one per slide max
- `h2`          serif section title (32px); use on content slides
- `.lead`       larger slate intro/summary paragraph (24px)
- `.cols`       2-column grid; children are usually `.card` or plain `div`
- `.cols-3`     3-column grid
- `.card`       white bordered rounded box (padding included)
- `.stat`       wrapper (use inside `.card`) holding:
  - `.stat-num`   huge serif clay number ("42%", "$1.2B")
  - `.stat-label` small slate caption under the number
- `.pill`       small rounded clay-tinted tag, inline
- `ul.bullets`  bullet list with clay markers
- `table.tbl`   minimal table; `<th>` mono uppercase header, thin row rules
- `.accent`     clay-colored text (inline `<span>`)
- `.muted`      slate-colored text
- `.footer`     small mono line pinned to the slide bottom (source, date, notes)

## Example (complete slide)

```html
<section class="slide">
  <div class="kicker">Market size</div>
  <h2>A fast-growing market with a <span class="accent">clear gap</span></h2>
  <p class="lead">Demand is rising while incumbents leave mid-size teams underserved.</p>
  <div class="cols-3">
    <div class="card stat"><div class="stat-num">$4.2B</div><div class="stat-label">Market in 2025</div></div>
    <div class="card stat"><div class="stat-num">31%</div><div class="stat-label">Annual growth</div></div>
    <div class="card">
      <span class="pill">Insight</span>
      <ul class="bullets"><li>Few mid-market tools</li><li>High switching pain</li></ul>
    </div>
  </div>
  <div class="footer">Source: industry reports, 2025</div>
</section>
```

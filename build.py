#!/usr/bin/env python3
"""Builds index.html.

aethercalc does real arithmetic with no JavaScript. The engine is custom
properties plus :has(): each checked radio sets --x/--y on its ancestors, the
operator rule picks the calc() for --r, and <output> hands those numbers to CSS
counters to print. Counters print integers only, so division floors the
quotient and --v carries the remainder, printed as " r N" by a counter style
whose range hides it when it is zero.

Everything here is generated because the page reports its own byte size, which
has to settle on a fixed point.
"""
import io
import os
import re

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")

OPS = "".join(
    "<input type=radio name=o id=%s%s><label for=%s>%s</label>" % (i, c, i, g)
    for i, g, c in [
        ("p", "+", " checked"),
        ("n", "\u2212", ""),
        ("m", "\u00d7", ""),
        ("d", "\u00f7", ""),
        ("e", "x\u02b8", ""),
    ]
)

PICK = "".join(":has(#a%d:checked){--x:%d}" % (d, d) for d in range(1, 10)) + "\n" + "".join(
    ":has(#b%d:checked){--y:%d}" % (d, d) for d in range(1, 10)
)

# Calculator order: 7 8 9 / 4 5 6 / 1 2 3 / 0, with 0 spanning the bottom row.
KEYS = [7, 8, 9, 4, 5, 6, 1, 2, 3, 0]


def pad(g):
    return "".join(
        "<input type=radio name=%s id=%s%d%s><label for=%s%d>%d</label>"
        % (g, g, d, " checked" if d == 0 else "", g, d, d)
        for d in KEYS
    )


HTML = """<!doctype html>
<html lang=en>
<head>
<meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>aethercalc</title>
<meta name=description content="aethercalc \u2014 html forms and css arithmetic, lighter than air. no javascript.">
<meta name=theme-color content=#0c1a2b media="(prefers-color-scheme:dark)">
<meta name=theme-color content=#eef7fe media="(prefers-color-scheme:light)">
<style>
:root{color-scheme:dark light;--b:#0c1a2b;--c:#14293f;--g:#1d3f5f;--t:#cbe4f7;--d:#7b9cb8;--a:#4fc3f7;--e:#ffffff14;--f:#ffffff1f;--s:#ffffff0a;--o:#052232;--h:#000}
@media(prefers-color-scheme:light){:root{--b:#c8e2f4;--c:#f4fbff;--g:#ffffff;--t:#17334d;--d:#5f829e;--a:#0284c7;--e:#00000014;--f:#00000026;--s:#0000000a;--o:#fff;--h:#5b809d}}
form{--x:0;--y:0;--v:0;--r:calc(var(--x) + var(--y));--op:"+"}
:has(#n:checked){--r:calc(var(--x) - var(--y));--op:"\u2212"}
:has(#m:checked){--r:calc(var(--x)*var(--y));--op:"\u00d7"}
:has(#d:checked){--r:round(down,var(--x)/var(--y),1);--op:"\u00f7";--v:mod(var(--x),var(--y))}
:has(#e:checked){--r:pow(var(--x),var(--y));--op:"^"}
__PICK__
:has(#d:checked):has(#b0:checked){--v:0}
output{counter-reset:x var(--x) y var(--y) t var(--r) v var(--v)}
@counter-style m{system:extends decimal;negative:"\u2212"}
@counter-style w{system:extends decimal;pad:2 "\u00a0r\u00a0";range:1 infinite;fallback:i}
@counter-style i{system:cyclic;symbols:"\u200b"}
.x:after{content:counter(x)}
.o:after{content:var(--op)}
.y:after{content:counter(y)}
.z:after{content:counter(t,m)}
.v:after{content:counter(v,w)}
:has(#d:checked):has(#b0:checked) .z:after{content:"\u221e"}
*{box-sizing:border-box}
i,em{font-style:normal}
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem 1rem;background:radial-gradient(50rem 26rem at 50% 0,var(--g),var(--b));color:var(--t);font:15px/1.55 Inter,system-ui,Segoe UI,sans-serif}
.w{width:min(30rem,100%)}
.h{display:flex;gap:.5rem;align-items:center;margin-bottom:.55rem;font-size:.78rem;color:var(--d)}
.h span{color:var(--t);font-weight:600;letter-spacing:.02em}
.h b{margin-left:auto;font-weight:400;border:1px solid var(--f);border-radius:9px;padding:.1rem .5rem}
form{position:relative;padding:1rem;background:var(--c);border:1px solid var(--e);border-radius:14px;box-shadow:0 20px 44px -24px var(--h);font-variant-numeric:tabular-nums}
h1{margin:0 0 .8rem;font:600 clamp(1.6rem,7.5vw,2.4rem)/1.15 inherit;letter-spacing:-.03em}
h1 i{color:var(--a);animation:k 1.1s steps(1) infinite}
@keyframes k{50%{opacity:0}}
output{display:flex;flex-direction:column;align-items:flex-end;gap:.15rem;padding:.7rem .9rem;background:var(--s);border:1px solid var(--e);border-radius:10px}
.q{display:flex;gap:.4rem;font-size:.95rem;color:var(--d)}
.r{display:flex;gap:.4rem;align-items:baseline;font-size:1.9rem;line-height:1.1}
u,.v{color:var(--d);text-decoration:none}
.v{margin-left:-.4rem;font-size:1.1rem}
.z{color:var(--a);font-weight:600}
.k{display:grid;grid-template-columns:1fr auto 1fr;gap:.6rem;margin-top:.8rem}
.col{display:flex;flex-direction:column;gap:.3rem}
em{font-size:.62rem;letter-spacing:.14em;text-transform:uppercase;color:var(--d)}
.mid em{text-align:center}
.n,.c{display:grid;gap:.35rem;flex:1}
.n{grid-template-columns:repeat(3,1fr)}
.n label:last-of-type{grid-column:span 3}
input{position:absolute;opacity:0}
label{display:flex;align-items:center;justify-content:center;padding:.5rem 0;background:var(--s);border:1px solid var(--e);border-radius:8px;cursor:pointer}
.c label{min-width:2.7rem}
label:hover{border-color:var(--a)}
:checked+label{background:var(--a);border-color:var(--a);color:var(--o);font-weight:600}
:focus-visible+label{outline:2px solid var(--t);outline-offset:2px}
p{margin:.7rem .2rem 0;font-size:.72rem;color:var(--d)}
</style>
</head>
<body>
<div class=w>
<div class=h><span>aethercalc</span><b>0 KB JS</b></div>
<form action=#>
<h1>welcome, user<i>_</i></h1>
<output>
<span class=q><i class=x></i><i class=o></i><i class=y></i></span>
<span class=r><u>=</u><i class=z></i><i class=v></i></span>
</output>
<div class=k>
<div class=col><em>first</em><div class=n>__A__</div></div>
<div class="col mid"><em>op</em><div class=c>__OPS__</div></div>
<div class=col><em>second</em><div class=n>__B__</div></div>
</div>
</form>
<p>__SIZE__ kilobytes of markup, 0 bytes of script. Sums are computed by CSS counters and an HTML form. Counters print whole numbers only, so division answers exactly and hands back a remainder.</p>
</div>
</body>
</html>
"""


def build(size):
    return (
        HTML.replace("__PICK__", PICK)
        .replace("__OPS__", OPS)
        .replace("__A__", pad("a"))
        .replace("__B__", pad("b"))
        .replace("__SIZE__", size)
    )


def main():
    # The page states its own size, so settle on the fixed point.
    size = "5.0"
    for _ in range(8):
        nxt = "%.1f" % (len(build(size).encode("utf-8")) / 1024.0)
        if nxt == size:
            break
        size = nxt
    html = build(size)

    assert "<script" not in html.lower(), "a script snuck in"
    assert not re.search(r"\son[a-z]+\s*=", html), "inline handler snuck in"

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(html)
    print("wrote %s (%d bytes, claims %s KB)" % (OUT, len(html.encode("utf-8")), size))


if __name__ == "__main__":
    main()

# aethercalc

A working calculator with no JavaScript. Zero bytes of script, zero dependencies at runtime, one HTML file of about 6 KB.

Pick an operator and two digits and it adds, subtracts, multiplies, divides or raises to a power. The arithmetic is real, and it is done by the CSS engine.

## How it works

Every control is a radio button. CSS can see which one is checked, so the whole calculator is a chain of that one observation.

```css
form{--x:0;--y:0;--r:calc(var(--x) + var(--y));--op:"+"}
:has(#m:checked){--r:calc(var(--x)*var(--y));--op:"×"}
:has(#a7:checked){--x:7}
output{counter-reset:x var(--x) y var(--y) t var(--r)}
.z:after{content:counter(t,m)}
```

1. `:has()` lets a checked radio set a custom property on its ancestors, so `--x` and `--y` become the operands.
2. The operator's rule picks the `calc()` that defines `--r`, so the selected button chooses the formula rather than the answer.
3. `counter-reset` accepts those computed values, and `content: counter(...)` prints them. Counters are the only way CSS can turn a number into text.

Because `calc()` does the work, adding an operation costs one line and multiplication is a real product, not a lookup table.

## Division and remainders

Counters print whole numbers only. Rather than round and lie, division floors the quotient and reports what is left over:

```
7 ÷ 2  =  3 r 1
8 ÷ 2  =  4
```

The remainder comes from `mod()`, and a counter style with `range: 1 infinite` hides it when it is zero. Dividing by zero shows `∞`, which is what CSS actually computes.

## What CSS cannot do

CSS can only observe *which control is checked*, never a typed value. That is why the operands are ten radio buttons instead of a text field: free numeric entry needs JavaScript. Multi-digit operands would work by adding a radio row per digit place and composing them with `calc(var(--tens)*10 + var(--ones))`.

## Building

`index.html` is generated, because the page reports its own byte size and that number has to settle on a fixed point.

```
python build.py
```

## Testing

The page has no JavaScript, so it cannot test itself, and every digit on screen is CSS generated content — invisible to `innerText`. The suite renders the page in headless Chrome and reads the answer back out of the accessibility tree, which is both what a user is told and a check that the result reaches a screen reader.

```
npm install
npm test
```

Covers 20 cases across all five operations, asserts the page ships no `<script>` tags, and checks that nothing overflows at 320px.

## Deploying to StuntCamp

StuntCamp builds AetherCalc from the exact commit pinned in
[`registry/apps/aethercalc.json`](https://github.com/kypflug/stuntcamp/blob/main/registry/apps/aethercalc.json).
Merging here does not update the live app automatically.

After an AetherCalc change merges:

1. Get the full commit SHA from AetherCalc's `main` branch.
2. Update `build.ref` in StuntCamp's `registry/apps/aethercalc.json` to that SHA.
3. Open and merge a StuntCamp pull request. Its validation workflow builds the pinned revision; merging triggers the deployment.

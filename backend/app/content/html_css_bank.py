"""
Seed content for the "Learning HTML/CSS" track. Its code review challenges
(see content/code_review_bank.py) live separately, alongside the other
tracks', since they're all the same self-graded shape now.
"""

TRACK = "html_css"

HTML_CSS_QUIZ = [
    # ---------------- EASY ----------------
    {
        "difficulty": "easy",
        "topic": "HTML",
        "question": "Which HTML element is the correct semantic choice for a page's primary navigation links?",
        "choices": ["<div class=\"nav\">", "<nav>", "<section>", "<header>"],
        "correct_index": 1,
        "explanation": "<nav> tells browsers, screen readers, and search engines this block is navigation - a plain <div> carries no such meaning.",
    },
    {
        "difficulty": "easy",
        "topic": "CSS",
        "question": "In the CSS box model, what does `box-sizing: border-box` change about how width is calculated?",
        "choices": [
            "Width no longer includes padding or border - only content",
            "Width includes content, padding, AND border, so setting width:200px keeps the element exactly 200px total",
            "It removes the border entirely",
            "It has no effect on width",
        ],
        "correct_index": 1,
        "explanation": "The default (content-box) excludes padding/border from the set width, so they add to the rendered size; border-box folds them in, which is why most resets set it globally.",
    },
    {
        "difficulty": "easy",
        "topic": "CSS",
        "question": "Which CSS selector targets an element with `id=\"header\"`?",
        "choices": [".header", "#header", "*header", "header{}"],
        "correct_index": 1,
        "explanation": "`#` selects by id; `.` selects by class. IDs must be unique per page.",
    },
    # ---------------- MEDIUM ----------------
    {
        "difficulty": "medium",
        "topic": "CSS Layout",
        "question": "In Flexbox, what does `justify-content` control versus `align-items`?",
        "choices": [
            "They do the same thing",
            "justify-content aligns items along the main axis (e.g. horizontally in a row); align-items aligns them along the cross axis (e.g. vertically)",
            "justify-content only works with flex-direction: column",
            "align-items controls spacing between items only",
        ],
        "correct_index": 1,
        "explanation": "The main axis follows flex-direction (row = horizontal); the cross axis is perpendicular to it - justify-content and align-items map to those two axes respectively.",
    },
    {
        "difficulty": "medium",
        "topic": "CSS Specificity",
        "question": "Which selector wins when both apply to the same element: `.card .title` or `#page .title`?",
        "choices": [
            "`.card .title` - it's more specific because it has two classes",
            "`#page .title` - an ID contributes more specificity than a class, regardless of selector count",
            "They tie and the later one in the stylesheet wins",
            "Neither applies because you can't mix ID and class selectors",
        ],
        "correct_index": 1,
        "explanation": "CSS specificity ranks ID > class > element, compared component by component - one ID outweighs any number of classes.",
    },
    {
        "difficulty": "medium",
        "topic": "HTML Accessibility",
        "question": "Why should an `<img>` tag almost always have an `alt` attribute?",
        "choices": [
            "It's required for the image to load",
            "It provides a text alternative for screen readers and for when the image fails to load - critical for accessibility and resilience",
            "It only affects SEO, not accessibility",
            "It sets the image's file size",
        ],
        "correct_index": 1,
        "explanation": "alt text is read aloud by screen readers and shown if the image fails to load - `alt=\"\"` is even the correct choice for purely decorative images (marks them as skippable).",
    },
    # ---------------- HARD ----------------
    {
        "difficulty": "hard",
        "topic": "CSS Layout",
        "question": "What's the key difference between CSS Grid and Flexbox that usually decides which one to reach for?",
        "choices": [
            "Grid is newer so it should always be used instead of Flexbox",
            "Flexbox is one-dimensional (lays out a single row or column); Grid is two-dimensional (rows AND columns at once), so Grid suits overall page/component layout while Flexbox suits aligning items within one axis",
            "Flexbox can't wrap items",
            "Grid only works with a fixed number of columns",
        ],
        "correct_index": 1,
        "explanation": "That one-vs-two-dimensional distinction is the standard rule of thumb: Grid for the overall layout skeleton, Flexbox for distributing items along one line inside it.",
    },
    {
        "difficulty": "hard",
        "topic": "CSS Positioning",
        "question": "An element has `position: absolute`. Relative to what is it positioned?",
        "choices": [
            "Always the browser viewport",
            "Its nearest ancestor with a `position` other than `static` (the 'containing block'); the viewport only if no such ancestor exists",
            "Its immediate parent, always",
            "The document's <body> element, always",
        ],
        "correct_index": 1,
        "explanation": "absolute positioning walks up the DOM to the nearest positioned ancestor (relative/absolute/fixed/sticky) - a very common source of 'why isn't this positioned where I expect' bugs when no ancestor is positioned.",
    },
    {
        "difficulty": "hard",
        "topic": "CSS Responsive Design",
        "question": "What's the practical difference between a `min-width` media query breakpoint strategy and a `max-width` one?",
        "choices": [
            "There is no practical difference",
            "min-width is 'mobile-first' - base styles target small screens and larger-screen overrides layer on top as the viewport grows; max-width is 'desktop-first' - the reverse",
            "max-width only works in print stylesheets",
            "min-width breakpoints can't be combined with flexbox or grid",
        ],
        "correct_index": 1,
        "explanation": "Mobile-first (min-width) is generally preferred: base CSS stays small/simple and you progressively enhance for more screen space, rather than un-doing desktop styles for small screens.",
    },
    # ---------------- EXPERT ----------------
    {
        "difficulty": "expert",
        "topic": "CSS Rendering",
        "question": "Why does animating `width`/`height`/`top`/`left` tend to hurt performance compared to animating `transform`?",
        "choices": [
            "There is no performance difference in modern browsers",
            "Changing layout properties (width, top, etc.) triggers a layout reflow (and repaint) on every frame; `transform` (and `opacity`) can often be handled entirely on the compositor thread/GPU without reflow",
            "transform can only be used on images",
            "width/height animations are deprecated",
        ],
        "correct_index": 1,
        "explanation": "Layout-affecting properties force the browser to recompute geometry for the element (and possibly its neighbors) each frame; transform/opacity changes can skip layout and paint entirely, which is why they're the recommended properties to animate.",
    },
    {
        "difficulty": "expert",
        "topic": "CSS Architecture",
        "question": "What problem do CSS custom properties (variables, `--accent: #268bd2`) solve that Sass/Less variables fundamentally can't?",
        "choices": [
            "They compile to smaller CSS files",
            "They're live in the browser at runtime - they can be read/changed via JavaScript and cascade/inherit through the DOM (e.g. changed per-component or on `:root` for a live theme toggle), whereas preprocessor variables are resolved once at build time into static values",
            "They allow nested selectors",
            "They add type-checking to CSS",
        ],
        "correct_index": 1,
        "explanation": "Sass variables are a compile-time text substitution - the shipped CSS has no memory of them. CSS custom properties are real runtime values, inheritable and overridable per-scope, which is what makes dynamic theming (e.g. dark mode via a single `:root` swap) practical.",
    },
    {
        "difficulty": "expert",
        "topic": "Accessibility",
        "question": "A custom dropdown built from styled <div>s (not a native <select>) needs to be accessible. What's the core problem, and the general fix?",
        "choices": [
            "There's no problem - styling doesn't affect accessibility",
            "Native form controls come with built-in keyboard support and screen-reader semantics for free; recreating one from <div>s loses all of that, so you must manually add the right ARIA role/attributes (e.g. role=\"listbox\"/\"option\", aria-expanded, aria-activedescendant) and reimplement keyboard interaction (arrow keys, Enter, Escape)",
            "Adding a CSS outline fixes all accessibility issues",
            "Custom dropdowns are always inaccessible and should never be built",
        ],
        "correct_index": 1,
        "explanation": "Semantic HTML elements ship with accessibility built in; the moment you rebuild their look from generic elements, you take on the responsibility of reimplementing their keyboard behavior and screen-reader semantics via ARIA and JS.",
    },
    # ---------------- MORE EASY ----------------
    {
        "difficulty": "easy",
        "topic": "HTML Semantics",
        "question": "Which element should wrap a self-contained piece of content that would make sense on its own, like a blog post or news story?",
        "choices": ["<div>", "<article>", "<section>", "<aside>"],
        "correct_index": 1,
        "explanation": "<article> marks content that's independently distributable/reusable (a post, a comment, a widget) - the litmus test is whether it would still make sense syndicated on its own.",
    },
    {
        "difficulty": "easy",
        "topic": "CSS Selectors",
        "question": "What does the CSS selector `p > span` match?",
        "choices": [
            "Any <span> anywhere inside a <p>, at any depth",
            "Only a <span> that is a direct child of a <p>",
            "Any <p> that contains a <span>",
            "A <span> immediately followed by a <p>",
        ],
        "correct_index": 1,
        "explanation": "`>` is the direct-child combinator - it only matches an immediate child, unlike the descendant combinator (a plain space) which matches at any nesting depth.",
    },
    # ---------------- MORE MEDIUM ----------------
    {
        "difficulty": "medium",
        "topic": "HTML Forms",
        "question": "What does the HTML `required` attribute on an `<input>` actually do?",
        "choices": [
            "Nothing by itself - it needs JavaScript to work",
            "Triggers built-in browser form validation that blocks submission and shows a native message until the field is filled",
            "Makes the field read-only",
            "Only affects styling, adding a red border",
        ],
        "correct_index": 1,
        "explanation": "`required` is part of HTML5's native constraint validation - the browser blocks form submission and shows its own validation UI with zero JavaScript, though custom styling/messages still need extra work.",
    },
    {
        "difficulty": "medium",
        "topic": "CSS Pseudo-classes",
        "question": "What's the difference between `:nth-child(2)` and `:nth-of-type(2)` on an element?",
        "choices": [
            "They're identical in every case",
            "`:nth-child` counts among ALL sibling elements regardless of tag; `:nth-of-type` counts only among siblings of the same tag",
            "`:nth-of-type` only works on the <body> element",
            "`:nth-child` only works with even numbers",
        ],
        "correct_index": 1,
        "explanation": "If a container mixes tags (e.g. a <h2> then several <p>s), `:nth-child(2)` counts position among ALL children regardless of type, while `p:nth-of-type(2)` counts the 2nd <p> specifically among just the <p> siblings - they diverge whenever siblings aren't all the same tag.",
    },
    # ---------------- MORE HARD ----------------
    {
        "difficulty": "hard",
        "topic": "CSS Layout",
        "question": "In CSS Grid, what does `grid-template-areas` let you do that raw `grid-template-columns`/`rows` don't as directly?",
        "choices": [
            "Nothing extra - it's purely a shorthand for column widths",
            "Name layout regions with strings so the grid's overall shape reads visually in the CSS itself, and place items into named areas instead of numeric line positions",
            "It only works with exactly 2 columns",
            "It replaces the need for grid-template-columns entirely in all cases",
        ],
        "correct_index": 1,
        "explanation": "grid-template-areas lets you literally draw the layout as a grid of quoted strings (e.g. \"header header\" \"sidebar main\") and then place children with `grid-area: header`, making the overall page structure readable at a glance instead of reasoning about numbered grid lines.",
    },
    {
        "difficulty": "hard",
        "topic": "Accessibility",
        "question": "What is the purpose of `role=\"alert\"` on an element in ARIA?",
        "choices": [
            "It changes the element's visual styling to look like a warning box",
            "It marks the region as a live region that screen readers announce immediately/assertively when its content changes, for urgent, time-sensitive information",
            "It disables the element",
            "It's purely decorative and has no effect on assistive technology",
        ],
        "correct_index": 1,
        "explanation": "role=\"alert\" is an implicit assertive live region - screen readers interrupt whatever they're currently saying to announce it, which is why it should be reserved for genuinely urgent messages (errors, critical status changes) rather than routine UI updates.",
    },
]

HTML_CSS_CONCEPT = [
    {
        "difficulty": "easy",
        "topic": "CSS Fundamentals",
        "prompt": "What does the 'cascade' in Cascading Style Sheets actually mean - how does the browser decide which of several conflicting rules wins?",
        "model_answer": (
            "When multiple CSS rules target the same element and property, the browser resolves the conflict "
            "using, in order: origin/importance (e.g. !important and browser vs. author styles), specificity "
            "(ID beats class beats element selectors), and finally source order (later rules win ties). "
            "'Cascading' refers to this layered resolution process that lets more specific or more recent rules "
            "override more general or earlier ones."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "CSS Layout",
        "prompt": "Explain the difference between `display: none` and `visibility: hidden`.",
        "model_answer": (
            "`display: none` removes the element from the layout entirely - it takes up no space, and other "
            "elements reflow as if it weren't there; it's also removed from the accessibility tree. "
            "`visibility: hidden` keeps the element's layout space reserved (nothing reflows) but makes it "
            "invisible - it's not clickable/visible but still occupies its box, and (depending on browser/AT) may "
            "still be exposed differently to accessibility tools than display:none."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "HTML Semantics",
        "prompt": "Why does using semantic HTML elements (<header>, <main>, <article>, <button>) instead of generic <div>/<span> with matching visual styles actually matter?",
        "model_answer": (
            "Semantic elements carry meaning that visual styling alone doesn't: screen readers use them to build "
            "a navigable document outline and announce roles (e.g. 'button', 'navigation region'), search engines "
            "weight them for SEO, and browsers give some of them free behavior (a <button> is keyboard-focusable "
            "and triggers on Enter/Space with no JS; a styled <div onclick> gets none of that for free and needs "
            "manual tabindex/keydown handling to match). A <div> can be made to LOOK identical to a <button> but "
            "won't behave like one for assistive tech or keyboard users without extra work."
        ),
    },
    {
        "difficulty": "expert",
        "topic": "CSS Architecture",
        "prompt": "You're joining a team whose CSS has become an unmaintainable mess of !important overrides and specificity wars. What are the underlying causes, and what approaches (naming conventions, layering, tooling) help prevent it?",
        "model_answer": (
            "The root cause is usually uncontrolled specificity growth: as the codebase grows, developers reach "
            "for more specific selectors (or !important) to override earlier styles they don't fully understand, "
            "which then forces the NEXT override to be even more specific, spiraling. Common fixes: a naming "
            "methodology like BEM that keeps selectors flat (single class, low specificity) so nothing needs to "
            "'win' via specificity; CSS Modules or scoped/component styles (e.g. in a framework) so styles can't "
            "leak between components at all; native CSS @layer to explicitly order layers of styles (resets, "
            "base, components, utilities/overrides) so later layers win by declared intent rather than "
            "specificity accidents; and a lint rule capping selector depth/specificity and banning !important "
            "outside of narrowly justified utility classes."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "CSS Units",
        "prompt": "What's the difference between `px`, `em`, and `rem` as CSS length units, and when would you reach for each?",
        "model_answer": (
            "`px` is an absolute unit - a fixed pixel size that doesn't scale with anything. `em` is relative "
            "to the current element's own computed font-size (which means it compounds: a nested element with "
            "`font-size: 1.5em` inside a parent that's already 1.5em scales multiplicatively, which can surprise "
            "you). `rem` ('root em') is relative to the root `<html>` element's font-size only, regardless of "
            "nesting - no compounding. Common practice: use `rem` for font-sizes and spacing so everything "
            "scales together if the user changes their browser's base font size (an accessibility win), use "
            "`em` for things that should scale with their own element's local font-size (like padding inside a "
            "button that should grow with the button's text), and reserve `px` for things that genuinely "
            "shouldn't scale (hairline borders)."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "HTML Forms",
        "prompt": "Why does an `<input>` need an associated `<label>` (not just placeholder text) to be considered accessible?",
        "model_answer": (
            "Placeholder text disappears the moment the user types, isn't announced consistently by all screen "
            "readers as the field's name, and often fails color-contrast requirements since it's styled as "
            "muted/gray. A `<label>` (either wrapping the input or linked via `for=\"id\"` matching the input's "
            "`id`) gives the field a persistent, programmatically-associated name: screen readers announce it "
            "when the field receives focus, and clicking the label text focuses/activates the input (useful for "
            "small tap targets like checkboxes). Placeholder text is fine as supplementary formatting help "
            "('MM/DD/YYYY') but should never be the only description of what a field is for."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "CSS Pseudo-classes",
        "prompt": "What's the difference between a pseudo-class (like `:hover`) and a pseudo-element (like `::before`)?",
        "model_answer": (
            "A pseudo-class selects an element based on a state or position it's already in - `:hover` (being "
            "pointed at), `:first-child` (its position among siblings), `:checked` (a form control's state) - "
            "it still targets a real element in the DOM, just conditionally. A pseudo-element creates or "
            "targets something that isn't a real DOM node - `::before`/`::after` insert generated content "
            "as a child of the element (commonly used with `content: '...'` for decorative icons/quotes "
            "without extra markup), `::first-line`/`::first-letter` target a sub-part of the element's text. "
            "The double-colon (`::`) syntax was introduced in CSS3 specifically to distinguish pseudo-elements "
            "from pseudo-classes, though single-colon still works for the original four pseudo-elements for "
            "backward compatibility."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "CSS Naming",
        "prompt": "What problem does the BEM (Block__Element--Modifier) naming convention solve?",
        "model_answer": (
            "Without a convention, CSS class names tend to either be too generic (`.title`, `.item` - collides "
            "across unrelated components, invites accidental overrides) or force ever-deeper nested selectors "
            "to disambiguate (`.card .header .title` - raises specificity, making later overrides harder). BEM "
            "makes every class name self-contained and flat: `.card` (Block, a standalone component), "
            "`.card__title` (Element, a part of that block, double underscore), `.card--featured` (Modifier, a "
            "variant of the block or element, double dash). Because every class already encodes its full "
            "context in its name, you never need nested selectors to scope a style, which keeps specificity "
            "low and uniform across the whole codebase - a `.card__title` rule can't accidentally clash with "
            "an unrelated `.title` inside a different component."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "Accessibility",
        "prompt": "What does `aria-live` do, and when do you actually need it?",
        "model_answer": (
            "`aria-live` marks a region of the page whose content changes dynamically (via JS, without a full "
            "page reload) as something a screen reader should announce even though the user's focus never "
            "moved there - e.g. a form validation error that appears after submit, a 'item added to cart' "
            "toast, or a live search result count. Without it, a screen reader user gets no signal that "
            "anything changed, since focus-based announcement (the normal mechanism) only fires for elements "
            "the user actually navigates to. `aria-live=\"polite\"` waits for the screen reader to finish its "
            "current announcement before reading the update (use for most non-urgent updates); "
            "`aria-live=\"assertive\"` interrupts immediately (reserve for genuinely urgent/error content, since "
            "overuse is jarring). It's not needed for content that's present at page load or that the user "
            "navigates to directly (like clicking into a newly revealed panel) - only for changes the user "
            "isn't already looking at."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "CSS Rendering",
        "prompt": "Why is a `<link rel=\"stylesheet\">` in the `<head>` considered 'render-blocking', and why does that matter for perceived load speed?",
        "model_answer": (
            "Browsers intentionally delay painting any content to the screen until they've finished downloading "
            "and parsing all CSS discovered so far, because CSS can affect the layout/appearance of anything "
            "already parsed - painting early and then having to repaint once styles arrive would cause a "
            "visible flash of unstyled content (FOUC), which browsers avoid by blocking render on CSS instead. "
            "This means a slow-loading stylesheet directly delays first paint, even if the HTML itself parsed "
            "instantly. Common mitigations: keep the critical stylesheet small, inline the minimal CSS needed "
            "for above-the-fold content directly in `<head>` so it doesn't require a network round trip, and "
            "load non-critical CSS asynchronously (e.g. `<link rel=\"preload\" as=\"style\" onload=\"this.rel="
            "'stylesheet'\">` or a `media` trick) so it doesn't block initial paint."
        ),
    },
    {
        "difficulty": "expert",
        "topic": "CSS Performance",
        "prompt": "Explain the browser rendering pipeline (style -> layout -> paint -> composite) and why knowing which stage a CSS property affects matters for animation performance.",
        "model_answer": (
            "After the DOM/CSSOM are built, the browser: computes each element's final styles (style/recalc), "
            "computes the geometry - size and position - of every element (layout, a.k.a. reflow), fills in "
            "actual pixels for each element into layers (paint), then combines those layers onto the screen, "
            "possibly on the GPU (composite). Changing a property can force re-running from different points "
            "in that pipeline: geometry-affecting properties (width, top, margin) force layout -> paint -> "
            "composite for the changed element AND potentially its neighbors/ancestors (layout thrashing if "
            "done in a loop reading then writing geometry repeatedly); paint-only properties (background-color, "
            "box-shadow) skip layout but still repaint; `transform` and `opacity` can, under the right "
            "conditions (the element promoted to its own compositor layer), skip both layout and paint entirely "
            "and be handled purely by the compositor thread, which is why they're the properties recommended "
            "for smooth 60fps animation - they're the only ones that can avoid touching the main thread per frame."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "HTML Semantics",
        "prompt": "What's the difference between `<div>` and `<span>`, and how do you decide which to reach for?",
        "model_answer": (
            "Both are generic, non-semantic containers with no inherent meaning - the difference is purely "
            "display type. `<div>` is block-level by default (starts on its own line, takes full available "
            "width), used to group larger structural chunks (a card, a section of a form). `<span>` is "
            "inline by default (flows within a line of text, only as wide as its content), used to wrap a "
            "small piece of text or inline content you need to style or target with JS without breaking the "
            "surrounding text flow (e.g. highlighting one word in a sentence). Neither should be your first "
            "choice if a semantic element fits (`<nav>`, `<button>`, `<article>`) - reach for div/span only "
            "when there's genuinely no more meaningful element for the content."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "CSS Layout",
        "prompt": "What is the 'stacking context' in CSS, and why can setting `z-index` on an element sometimes not work the way you expect?",
        "model_answer": (
            "A stacking context is a self-contained 3D-ish layering group - elements are painted back-to-front "
            "within their own stacking context, and `z-index` only compares elements against siblings *within "
            "the same* stacking context, not globally across the whole page. Certain CSS properties create a "
            "new stacking context on the element that has them (e.g. `position: relative/absolute` combined "
            "with a `z-index` value, `opacity` less than 1, `transform`, `filter`), which means everything "
            "inside that element is now layered as a sealed unit - a child with `z-index: 9999` still can't "
            "escape above a sibling of its stacking-context-creating parent, no matter how high the number, "
            "because it's being compared to siblings inside its own context, not the page's elements directly. "
            "This is the usual cause of 'I set z-index: 9999 and it still renders behind that other element'."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "CSS Layout",
        "prompt": "Explain CSS Grid's `fr` unit and how `grid-template-columns: 1fr 2fr 1fr` differs from using percentages.",
        "model_answer": (
            "`fr` (fraction unit) distributes remaining space in the grid container after all non-flexible "
            "content (fixed-size tracks, gaps, padding) has been accounted for - `1fr 2fr 1fr` splits whatever "
            "space is LEFT into 4 shares, giving the middle column twice the width of the outer two. This "
            "differs from percentages in a key way: percentages are always relative to the full container "
            "width regardless of other content, so mixing a percentage column with a fixed-px column can "
            "cause overflow (they don't 'know' about each other and can sum past 100%). `fr` units automatically "
            "account for other tracks first, then divide only what's actually left, which is why `200px 1fr "
            "1fr` reliably gives you a fixed 200px sidebar and two equal flexible columns filling the rest, "
            "with no overflow math to get wrong by hand."
        ),
    },
    {
        "difficulty": "expert",
        "topic": "CSS Architecture",
        "prompt": "What are CSS container queries, and what layout problem do they solve that media queries fundamentally can't?",
        "model_answer": (
            "Media queries respond to the viewport's size - useful for page-level, top-down responsive layout, "
            "but a component (a card, a widget) has no way to know its OWN rendered width via a media query, "
            "only the browser window's. This breaks down for genuinely reusable components: the same `.card` "
            "might render at 300px wide in a sidebar and 800px wide in a main content area on the exact same "
            "page at the exact same viewport size, but a media query can't distinguish those - it only sees "
            "the viewport. Container queries (`@container` + `container-type: inline-size` declared on an "
            "ancestor) let a component query the size of its own nearest sized ancestor instead, so a card "
            "component can genuinely say 'when I am rendered narrower than 400px, stack my image above the "
            "text' regardless of where it's placed on the page or how wide the viewport is - true "
            "component-level responsiveness instead of only page-level."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "CSS Selectors",
        "prompt": "What's the difference between a class selector like `.btn` and an attribute selector like `[type=\"submit\"]`?",
        "model_answer": (
            "A class selector matches any element carrying that class in its `class` attribute, regardless of "
            "tag or any other attribute - you have to explicitly add the class to every element you want styled. "
            "An attribute selector matches based on an existing HTML attribute's presence or value, with no "
            "extra class needed - `[type=\"submit\"]` matches every `<input type=\"submit\">` (or `<button "
            "type=\"submit\">`) on the page automatically, because that attribute is already meaningful markup, "
            "not styling-only metadata you'd need to add. Attribute selectors are especially handy for styling "
            "form controls or elements you don't control the markup of, based on properties they already have."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "CSS Box Model",
        "prompt": "What's the difference between `margin` and `padding`?",
        "model_answer": (
            "`padding` is space INSIDE an element's border, between the border and its content - it's part of "
            "the element itself, shares the element's background color, and clicking/hovering over padding "
            "still counts as interacting with the element. `margin` is space OUTSIDE the border, between this "
            "element and its neighbors - it's transparent (shows whatever is behind it), and clicking in the "
            "margin area does not count as clicking the element. A quick way to tell them apart visually: give "
            "an element a background color - padding is inside that colored area, margin is the gap outside it "
            "where the background color doesn't reach."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "HTML Attributes",
        "prompt": "What does a boolean HTML attribute like `disabled` or `checked` do differently from a normal attribute like `class` or `href`?",
        "model_answer": (
            "A normal attribute's meaning comes from its VALUE (`href=\"/cart\"` means 'link to /cart'). A "
            "boolean attribute's meaning comes purely from its PRESENCE or ABSENCE - the element is disabled/"
            "checked if the attribute is there at all, regardless of what (if anything) it's set to. That's why "
            "you'll see `<input disabled>`, `<input disabled=\"disabled\">`, and even `<input disabled=\"false\">` "
            "all mean the SAME thing (disabled) - the string \"false\" is not treated specially, the attribute's "
            "mere presence turns the behavior on. To turn a boolean attribute off you have to remove it "
            "entirely (`element.removeAttribute('disabled')` in JS), not set it to a falsy-looking value."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "CSS Colors",
        "prompt": "What's the practical difference between specifying a color as hex (`#2b6cff`), `rgb()`, and `hsl()`, and when is `hsl()` more convenient?",
        "model_answer": (
            "All three ultimately describe the same color space (or close to it) - hex and `rgb()` both specify "
            "red/green/blue channel intensities (hex is just a more compact, less human-readable encoding of "
            "the same numbers), while `hsl()` specifies hue (a position on the color wheel, 0-360deg), "
            "saturation, and lightness. `hsl()` is more convenient when you want to programmatically derive "
            "related colors: to make a color lighter or darker, you just change the lightness percentage and "
            "the hue/saturation (the actual 'color') stays untouched, whereas doing the same thing in hex/rgb "
            "means recalculating all three channels by hand or trial and error. This makes hsl() a natural fit "
            "for generating a full shade palette (hover states, disabled states) from one base hue."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "HTML Semantics",
        "prompt": "What's the difference between `<ol>` and `<ul>`, and does it matter beyond which bullet style is shown?",
        "model_answer": (
            "`<ul>` (unordered list) is for a set of items where order doesn't carry meaning - swapping any two "
            "items wouldn't change what the list communicates (e.g. a list of product features). `<ol>` "
            "(ordered list) is for items where sequence matters - step-by-step instructions, ranked results, a "
            "table of contents - and it matters beyond styling: screen readers announce an `<ol>`'s items with "
            "their position ('item 2 of 5'), which is meaningful information for ordered content and misleading "
            "if applied to an unordered set, or missing if an actually-ordered sequence is marked up as `<ul>` "
            "just because someone removed the numbers visually with CSS."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "CSS Layout",
        "prompt": "What's the difference between `display: inline`, `inline-block`, and `block`?",
        "model_answer": (
            "`block` elements start on a new line and take the full available width by default, and DO respect "
            "explicit `width`/`height`/vertical `margin`. `inline` elements flow within a line of text alongside "
            "other content, don't start a new line, and ignore `width`/`height` and top/bottom margin entirely "
            "(only left/right margin/padding actually push neighboring inline content). `inline-block` is a "
            "hybrid: it flows inline like `inline` (sits alongside other inline content, doesn't force a new "
            "line) but respects `width`/`height` and all four margins like `block` - useful for something like a "
            "row of same-line badges that still need an explicit size."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "CSS Selectors",
        "prompt": "What's the difference between the descendant combinator (a space, e.g. `.card p`) and the adjacent sibling combinator (`+`, e.g. `h2 + p`)?",
        "model_answer": (
            "The descendant combinator (space) matches an element nested ANYWHERE inside another, at any depth "
            "- `.card p` matches a `<p>` no matter how many wrapper elements sit between it and `.card`. The "
            "adjacent sibling combinator (`+`) matches an element that is the IMMEDIATE next sibling of "
            "another, sharing the same parent - `h2 + p` only matches a `<p>` that comes directly after an "
            "`<h2>` with no other element in between (text nodes don't count, but another element does), and it "
            "says nothing about nesting depth since siblings are already at the same level by definition. A "
            "related one, `~` (general sibling), matches any later sibling, not just the immediately adjacent "
            "one."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "HTML Forms",
        "prompt": "What's the difference between `<button type=\"submit\">` and `<button type=\"button\">`, and why does forgetting to set `type` matter?",
        "model_answer": (
            "`type=\"submit\"` (the DEFAULT if `type` is omitted) submits the enclosing `<form>` when clicked - "
            "triggering native validation and a page navigation/fetch, exactly like pressing Enter in a text "
            "field. `type=\"button\"` does nothing on its own; it's meant for JS-driven actions (via an "
            "onclick/event listener) that shouldn't submit the form, like an 'add another item' button inside a "
            "multi-field form. Because submit is the default, a `<button>` inside a `<form>` with no explicit "
            "`type` that was only meant to trigger some JS behavior will ALSO submit the form when clicked - a "
            "common source of an accidental, unwanted form submission (and page reload) bug."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "CSS Units",
        "prompt": "What's the difference between viewport units (`vw`/`vh`) and percentage units, and when would percentage not do what you expect?",
        "model_answer": (
            "`vw`/`vh` are always relative to the VIEWPORT'S size (1vw = 1% of viewport width, regardless of "
            "where the element sits in the DOM). A percentage, by contrast, is relative to the nearest ancestor "
            "that actually establishes a sizing context for that property - typically the parent element's "
            "content-box size for width, but for HEIGHT specifically, `height: 50%` only works if the parent has "
            "an explicit (non-auto) height itself; if every ancestor up to `<html>` has `height: auto` (the "
            "common default), a percentage height resolves to nothing/collapses, which surprises people "
            "expecting 'half the screen'. `100vh` sidesteps that ancestor-height requirement entirely by always "
            "measuring against the viewport directly, which is why it's the more common choice for 'full "
            "screen height' layouts."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "CSS Layout",
        "prompt": "What does `overflow: hidden` do, and what's a common reason to reach for it beyond clipping content that's too big for its box?",
        "model_answer": (
            "`overflow: hidden` clips any content that extends past the element's box instead of letting it "
            "spill out visibly (the default `visible` behavior). Beyond deliberately clipping oversized content, "
            "it's a very common (if slightly hacky) fix for the 'collapsing parent' problem: a container whose "
            "children are all floated has zero measured height by default, because floated elements are taken "
            "out of normal flow and don't contribute to their parent's height - setting `overflow: hidden` (or "
            "`auto`) on the parent establishes a 'block formatting context', which forces the parent to actually "
            "contain and measure its floated children's height. Modern layouts using Flexbox/Grid rarely hit "
            "this specific problem since floats aren't typically used for layout anymore, but it still shows up "
            "in legacy CSS and is worth recognizing."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "CSS Layout",
        "prompt": "What is the 'clearfix' hack, what specific problem does it solve, and why is it rarely needed in modern layouts?",
        "model_answer": (
            "When every child of a container is floated, the container itself collapses to zero height, "
            "because floated elements are removed from normal document flow and don't count toward their "
            "parent's height calculation - visually, the container's background/border ends up not wrapping its "
            "floated children at all. 'Clearfix' is a CSS trick (classically `.clearfix::after { content: ''; "
            "display: table; clear: both; }`) that inserts an invisible element after the floated children with "
            "`clear: both`, which forces the container to extend down far enough to contain that cleared "
            "pseudo-element, and therefore the floats too. It's rarely needed today because Flexbox and Grid "
            "containers naturally measure and contain their children's height without floats being involved at "
            "all - the whole class of bug clearfix works around simply doesn't arise outside of legacy "
            "float-based layouts."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "Accessibility",
        "prompt": "What is focus trapping, and why does a modal dialog need it?",
        "model_answer": (
            "Focus trapping means constraining keyboard (Tab/Shift+Tab) focus to cycle only among the elements "
            "inside a currently-open modal, instead of letting Tab move focus to content behind/underneath it "
            "that's supposed to be inaccessible while the modal is open. Without it, a keyboard-only or "
            "screen-reader user tabbing through a page with an open modal can tab 'through' the modal into "
            "background content that's still technically focusable even though it's visually covered and "
            "logically disabled - confusing and potentially letting them interact with things they shouldn't "
            "be able to reach. A correct modal implementation moves focus into the modal when it opens, traps "
            "Tab/Shift+Tab within its focusable children (wrapping from the last back to the first and vice "
            "versa), and returns focus to whatever triggered the modal when it closes."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "CSS Rendering",
        "prompt": "Why does adding `async` or `defer` to a `<script>` tag matter for page load performance, and what's the difference between the two?",
        "model_answer": (
            "A plain `<script src=\"...\">` in the middle of HTML parsing blocks the parser entirely: the "
            "browser stops building the DOM, fetches the script (network round trip), executes it, and only "
            "then resumes parsing the rest of the page - a slow script directly delays everything below it from "
            "even appearing. `defer` downloads the script in parallel with HTML parsing but delays EXECUTION "
            "until parsing is fully complete, and multiple deferred scripts run in their original document "
            "order - good for scripts that need the full DOM and depend on each other. `async` also downloads "
            "in parallel, but executes the moment it finishes downloading, pausing the parser at that point "
            "wherever it happens to be, with no guaranteed order relative to other async scripts - suited to "
            "independent scripts (like analytics) that don't need the DOM ready or a specific execution order."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "CSS Architecture",
        "prompt": "What are the tradeoffs of utility-first CSS (e.g. Tailwind-style classes like `flex items-center gap-4`) compared to writing component-scoped CSS (e.g. BEM classes)?",
        "model_answer": (
            "Utility-first CSS composes styling entirely from small, single-purpose classes applied directly in "
            "markup, so you rarely write new CSS at all - styles are visible right at the point of use, and "
            "there's no risk of specificity conflicts since utility classes are all flat, single-property, equal "
            "specificity. The tradeoff is markup verbosity (a real element can carry a dozen+ classes) and "
            "duplication of the same class combinations across every instance of a repeated pattern, unless "
            "extracted into a component/template. Component-scoped CSS (BEM or similar) keeps markup clean "
            "(`class=\"card\"`) with the actual styling centralized in one place per component, easier to skim "
            "and reason about as a unit, but requires actually writing and naming CSS, and any shared "
            "look-and-feel across components (spacing scale, colors) has to be manually kept consistent rather "
            "than reused directly from a fixed utility palette."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "HTML Semantics",
        "prompt": "Why should `<table>` be reserved for genuinely tabular data and never used purely for visual page layout, even though it historically was?",
        "model_answer": (
            "Screen readers interpret `<table>` markup literally as tabular data and announce it accordingly - "
            "row/column counts, header associations via `<th>`/`scope`, and per-cell navigation commands. Using "
            "`<table>` purely for visual layout (a once-common pre-CSS trick for aligning a page's regions) "
            "forces a screen-reader user through irrelevant 'table with N rows and N columns' announcements and "
            "cell-by-cell navigation for content that has no actual tabular meaning, actively harming the "
            "experience rather than being neutral. It's also brittle and verbose for layout purposes generally "
            "(nested tables to achieve arbitrary positioning) compared to CSS Grid/Flexbox, which is why the "
            "practice is now considered a serious anti-pattern - `<table>` should be judged purely by 'does this "
            "content actually have rows and columns of related data' (a pricing comparison, financial figures), "
            "not by what layout you want it to produce."
        ),
    },
    {
        "difficulty": "expert",
        "topic": "CSS Performance",
        "prompt": "What does `content-visibility: auto` do, and how does it help rendering performance on long pages?",
        "model_answer": (
            "`content-visibility: auto` tells the browser it can skip rendering work (layout, paint) for an "
            "element's contents entirely while that element is off-screen, and only do that work once it's "
            "about to become visible (e.g. via scrolling near it) - similar in spirit to how a virtualized list "
            "works, but implemented natively by the browser without any JavaScript. This is powerful for very "
            "long pages (a long article with many sections, a big product listing) where rendering every "
            "off-screen section up front wastes real work the user may never scroll to see. The main caveat is "
            "that the browser needs a size estimate to reserve correct scrollbar space for skipped content "
            "before it's ever rendered - paired with `contain-intrinsic-size` to give it that estimate - or the "
            "page's scrollbar/layout can jump around as sections are rendered for the first time on scroll."
        ),
    },
    {
        "difficulty": "expert",
        "topic": "CSS Architecture",
        "prompt": "How does Shadow DOM style encapsulation differ from a naming convention like BEM for preventing CSS from leaking between components?",
        "model_answer": (
            "BEM prevents leakage entirely through DISCIPLINE and naming convention - styles are still global in "
            "the cascade and CAN technically collide or leak, but consistent, verbose, self-contained class "
            "names (`.card__title`) make collisions unlikely in practice as long as every developer follows the "
            "convention; nothing enforces it at the platform level. Shadow DOM provides genuine BROWSER-level "
            "encapsulation: a shadow root creates a separate DOM subtree with its own style scope - CSS written "
            "inside the shadow root cannot leak out to affect the rest of the page, and (with rare, deliberate "
            "exceptions like CSS custom properties, which do cross the boundary) page-level CSS cannot reach "
            "in and affect the shadow tree's internals either. The tradeoff is that this real isolation makes "
            "deliberate theming/customization of a shadow-DOM component from outside harder (you need explicit "
            "escape hatches like CSS custom properties or `::part()`), whereas BEM's 'encapsulation' is opt-in "
            "and therefore easier to override intentionally, but also easier to break accidentally."
        ),
    },
]

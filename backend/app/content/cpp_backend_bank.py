"""
Backend-service-flavored content (request parsing, HTTP semantics, load
balancing, rate limiting, caching) that seeds straight into the cpp_core
track's pool (see seed.py) rather than living behind its own track switcher.
"""
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

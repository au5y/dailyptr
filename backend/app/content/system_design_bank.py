"""
Seed content for the "System Design" track. This track has uses_sandbox=False
(see config.TRACKS) - there's no compiler or single correct output for a
design question, so "coding" (practice) problems here have no
harness_template; instead the user writes their attempt (an outline of an
API, a written design, an explanation), submits it, and the response reveals
reference_solution for them to compare against (self-check, like the concept
check - see routers/coding.py). starter_code is a short scaffold of section
headers to fill in, not a blank/compilable file.

Pool sizes here (8/8/8/5 per difficulty per content type = 29 each, 87
total) are deliberately deeper than the other two tracks: with easy/medium/
hard each landing on ~8-9 days a month and expert on ~4-5 (see
WEEKDAY_DIFFICULTY), a pool this size gives roughly a month of low-repeat
daily content per difficulty tier.
"""

TRACK = "system_design"

SD_PRIMER = {"label": "System Design Primer", "url": "https://github.com/donnemartin/system-design-primer"}

SYSTEM_DESIGN_QUIZ = [
    # ---------------- EASY ----------------
    {
        "difficulty": "easy",
        "topic": "Client-Server Basics",
        "question": "In a typical client-server web architecture, what is the client generally responsible for versus the server?",
        "choices": [
            "The client stores all persistent data; the server only renders UI",
            "The client sends requests and renders responses (e.g. a browser or app); the server processes requests, applies business logic, and manages persistent data",
            "They are interchangeable and either can act as either role",
            "The server only serves static files and never runs any logic",
        ],
        "correct_index": 1,
        "explanation": "This is the standard client/server split: the client owns presentation and user interaction, the server owns business logic and durable state.",
    },
    {
        "difficulty": "easy",
        "topic": "HTTP Basics",
        "question": "What's the main difference between an HTTP GET and a POST request?",
        "choices": [
            "GET is always faster than POST",
            "GET requests are meant to be safe, idempotent reads (parameters typically in the URL, no side effects expected); POST is used to submit data that may create or change state on the server",
            "GET requests cannot include any query parameters",
            "POST requires authentication and GET never does",
        ],
        "correct_index": 1,
        "explanation": "GET is defined as a safe, idempotent method for fetching a representation; POST is the general-purpose 'do something with this data' method, commonly used to create resources.",
    },
    {
        "difficulty": "easy",
        "topic": "Caching Basics",
        "question": "What's the main benefit of adding a cache in front of a database?",
        "choices": [
            "It permanently replaces the need for a database",
            "It serves frequently-requested data from fast memory instead of hitting the slower database every time, reducing latency and database load",
            "It makes every write to the database faster",
            "It guarantees the served data is always perfectly up to date",
        ],
        "correct_index": 1,
        "explanation": "A cache trades a small risk of staleness for much lower read latency and less load on the backing store - it doesn't replace the database, which remains the source of truth.",
    },
    {
        "difficulty": "easy",
        "topic": "Databases",
        "question": "When would you lean toward a NoSQL database (e.g. a document or key-value store) over a traditional relational database?",
        "choices": [
            "Never - relational databases are always the better choice",
            "When your data doesn't fit a rigid schema well, needs to scale horizontally very easily, and you can relax strict relational guarantees (joins, multi-row transactions) for flexibility and throughput",
            "Only when storing images or other binary files",
            "NoSQL databases don't support querying at all, so this never applies",
        ],
        "correct_index": 1,
        "explanation": "The choice is about trade-offs, not superiority: NoSQL stores generally favor flexible schemas and easy horizontal scale over strong relational guarantees like joins and multi-row ACID transactions.",
    },
    {
        "difficulty": "easy",
        "topic": "Load Balancing Basics",
        "question": "What problem does a load balancer solve?",
        "choices": [
            "It encrypts all traffic between client and server",
            "It distributes incoming requests across multiple backend servers so no single server is overwhelmed, and can route around unhealthy instances",
            "It compresses HTTP responses to save bandwidth",
            "It permanently stores session data for every user",
        ],
        "correct_index": 1,
        "explanation": "A load balancer sits in front of a pool of servers and spreads traffic across them (and away from unhealthy ones), which is what makes horizontal scaling actually work end to end.",
    },
    {
        "difficulty": "easy",
        "topic": "Scaling",
        "question": "What's the difference between vertical and horizontal scaling?",
        "choices": [
            "Vertical scaling adds more machines; horizontal scaling adds more power to one machine",
            "Vertical scaling adds more power (CPU/RAM) to a single machine; horizontal scaling adds more machines and distributes load across them",
            "They're two names for the exact same technique",
            "Horizontal scaling only applies to databases, never to application servers",
        ],
        "correct_index": 1,
        "explanation": "Vertical scaling means a bigger box; horizontal scaling means more boxes sharing the load - horizontal scaling is generally preferred at large scale since a single machine has a hard ceiling.",
    },
    {
        "difficulty": "easy",
        "topic": "Latency & Throughput",
        "question": "What's the difference between latency and throughput?",
        "choices": [
            "They're the same metric, just measured with different units",
            "Latency is how long a single request takes to complete; throughput is how many requests a system can handle per unit of time - a system can have low latency but low throughput, or the reverse",
            "Latency only matters for database queries, not for network calls",
            "Throughput is always inversely proportional to the number of servers running",
        ],
        "correct_index": 1,
        "explanation": "Latency measures per-request speed; throughput measures aggregate capacity over time - the two are related but genuinely independent, and systems are often tuned to trade one for the other.",
    },
    {
        "difficulty": "easy",
        "topic": "APIs",
        "question": "In a RESTful API, what does it mean for the API to be 'stateless'?",
        "choices": [
            "The server keeps no memory of the client's state between requests - every request must carry all the information the server needs to process it",
            "The API cannot store any data anywhere, ever",
            "The client is not allowed to send any data to the server",
            "The server processes incoming requests in a random order",
        ],
        "correct_index": 0,
        "explanation": "Statelessness means the server doesn't rely on remembered per-client context between calls; any needed context (auth token, pagination cursor, etc.) travels with each request instead.",
    },
    # ---------------- MEDIUM ----------------
    {
        "difficulty": "medium",
        "topic": "Caching Strategies",
        "question": "In a cache-aside (lazy-loading) caching strategy, what happens on a cache miss?",
        "choices": [
            "The request fails immediately with an error",
            "The application reads from the database, then writes that value into the cache before returning it, so subsequent reads hit the cache",
            "The entire cache is cleared and rebuilt from scratch",
            "The database is bypassed permanently for that key going forward",
        ],
        "correct_index": 1,
        "explanation": "Cache-aside only populates the cache reactively, on demand, when a read actually misses - it never proactively pushes data into the cache.",
    },
    {
        "difficulty": "medium",
        "topic": "Database Indexing",
        "question": "Why does adding a database index speed up reads but slow down writes?",
        "choices": [
            "Indexes only ever affect reads, never writes",
            "An index is an auxiliary sorted structure (e.g. a B-tree) that lets lookups skip a full table scan; every write must also update that structure, adding overhead per insert/update/delete",
            "Indexes make the entire table read-only after creation",
            "There is no real trade-off with adding indexes",
        ],
        "correct_index": 1,
        "explanation": "The index has to stay correct, so every write pays a maintenance cost proportional to how many indexes exist on that table - it's a deliberate read/write trade-off, not a free win.",
    },
    {
        "difficulty": "medium",
        "topic": "Database Replication",
        "question": "In a single-leader (primary-replica) database setup, what's the usual trade-off with asynchronous replication?",
        "choices": [
            "There's no trade-off - it's strictly better in every way",
            "Writes acknowledge as soon as the leader commits, without waiting for replicas, giving lower write latency - but a replica can lag behind, and a failover could lose the most recent writes",
            "It guarantees replicas are always perfectly in sync with the leader",
            "It prevents the leader from ever failing",
        ],
        "correct_index": 1,
        "explanation": "Async replication favors write latency over durability guarantees on replicas - the gap between 'leader has it' and 'replica has it' is exactly the window of possible loss on failover.",
    },
    {
        "difficulty": "medium",
        "topic": "CDN",
        "question": "How does a CDN (content delivery network) reduce latency for users?",
        "choices": [
            "It losslessly compresses all data in transit",
            "It caches content on servers geographically distributed closer to users, so requests are served from a nearby edge location instead of traveling to the origin server",
            "It encrypts all traffic, which is inherently faster than unencrypted traffic",
            "It only works for streaming video content specifically",
        ],
        "correct_index": 1,
        "explanation": "A CDN's core value is proximity: shortening the physical/network distance between the user and the server that answers their request.",
    },
    {
        "difficulty": "medium",
        "topic": "Message Queues",
        "question": "What core problem do message queues solve between a producer service and a consumer service?",
        "choices": [
            "They make each individual service faster on its own",
            "They decouple producers from consumers in time and pace - the producer can publish work without waiting for it to be processed immediately, smoothing traffic spikes and letting each side scale or fail independently",
            "They fully replace the need for a database",
            "They guarantee zero message loss with no configuration required",
        ],
        "correct_index": 1,
        "explanation": "The core value of a queue is decoupling: producers and consumers no longer need to be available, fast, or scaled the same way at the same time.",
    },
    {
        "difficulty": "medium",
        "topic": "Rate Limiting",
        "question": "What is a rate limiter typically protecting a service from?",
        "choices": [
            "Slow disk I/O specifically",
            "Being overwhelmed by too many requests from a client (or in aggregate) in a given time window - whether malicious abuse or an accidental buggy retry loop - by rejecting or throttling requests past a threshold",
            "SQL injection attacks",
            "Data corruption during concurrent writes",
        ],
        "correct_index": 1,
        "explanation": "Rate limiting is about request volume control, protecting shared capacity from any one source (bad actor or bug) consuming more than its fair share.",
    },
    {
        "difficulty": "medium",
        "topic": "Consistent Hashing",
        "question": "Why is consistent hashing preferred over plain modulo hashing (`hash(key) % N`) when distributing keys across a changing set of N servers?",
        "choices": [
            "Consistent hashing is simply faster to compute per key",
            "With plain modulo hashing, adding or removing a server changes N and reshuffles almost every key's target server; consistent hashing arranges servers and keys on a hash ring so only a small fraction of keys need to move when servers change",
            "Modulo hashing cannot be used with string keys",
            "Consistent hashing doesn't require any hash function at all",
        ],
        "correct_index": 1,
        "explanation": "The whole point of consistent hashing is minimizing remapping on membership changes - modulo hashing is maximally disruptive since N appears directly in the formula.",
    },
    {
        "difficulty": "medium",
        "topic": "Database Sharding",
        "question": "What is database sharding, and what's a common challenge it introduces?",
        "choices": [
            "Sharding just means adding an index, and the challenge is slower reads",
            "Sharding splits a dataset across multiple database instances (each holding a subset of rows, by some partition key) to scale beyond a single machine; a common challenge is that queries spanning multiple shards become much harder and slower",
            "Sharding is just another word for replication, with no real difference",
            "Sharding eliminates the need to ever choose a partition key",
        ],
        "correct_index": 1,
        "explanation": "Sharding buys write/storage scale beyond one machine at the cost of cross-shard operations (joins, aggregations, multi-row transactions) becoming distributed problems instead of local ones.",
    },
    # ---------------- HARD ----------------
    {
        "difficulty": "hard",
        "topic": "CAP Theorem",
        "question": "According to the CAP theorem, when a network partition occurs, what must a distributed system choose between?",
        "choices": [
            "Consistency and Availability - it can only guarantee one of the two during the partition, since partition tolerance is treated as a given",
            "Consistency and Durability",
            "Availability and Latency, with Consistency unaffected",
            "Nothing - a well-built system can always guarantee both consistency and availability regardless of partitions",
        ],
        "correct_index": 0,
        "explanation": "CAP says that under an actual network partition (which will happen), you must pick: keep answering (Availability) and risk inconsistency, or refuse to answer inconsistently (Consistency) and lose Availability for affected requests.",
    },
    {
        "difficulty": "hard",
        "topic": "Consistency Models",
        "question": "What does 'eventual consistency' guarantee, and what does it NOT guarantee?",
        "choices": [
            "It guarantees reads always return the latest write immediately",
            "It guarantees that if no new updates are made, all replicas will eventually converge to the same value - but it does NOT guarantee a read immediately after a write will see that write",
            "It guarantees strict global ordering of all writes across all replicas at all times",
            "It's identical to strong consistency, just marketed under a different name",
        ],
        "correct_index": 1,
        "explanation": "Eventual consistency is a convergence guarantee over time, not a freshness guarantee at any given instant - that gap is exactly what trips people up.",
    },
    {
        "difficulty": "hard",
        "topic": "Distributed Transactions",
        "question": "In the Two-Phase Commit (2PC) protocol, what happens in the 'prepare' phase?",
        "choices": [
            "The coordinator immediately commits the transaction on every participant",
            "The coordinator asks every participant whether it can commit; each participant durably persists its intent and votes yes/no, without actually committing yet",
            "All participants automatically roll back",
            "There is no prepare phase in 2PC",
        ],
        "correct_index": 1,
        "explanation": "2PC's whole design is splitting 'can everyone commit?' from 'now actually commit' into two rounds, so the coordinator only tells everyone to commit once it knows all participants are ready.",
    },
    {
        "difficulty": "hard",
        "topic": "Leader Election",
        "question": "Why do distributed systems need a leader election / consensus algorithm (e.g. Raft, Paxos) rather than just picking one server as leader forever?",
        "choices": [
            "Because leaders never actually need to change once chosen",
            "The initial leader can crash or become unreachable, so remaining nodes need an agreed-upon way to detect that and elect a new leader while avoiding two nodes both believing they're the leader at once",
            "Consensus algorithms are used purely for load balancing, not leadership",
            "A single fixed leader is always more available than an elected one",
        ],
        "correct_index": 1,
        "explanation": "Leader election exists specifically to handle failure and avoid a divided cluster where more than one node acts as leader simultaneously - a scenario often called split brain.",
    },
    {
        "difficulty": "hard",
        "topic": "Idempotency",
        "question": "Why does making an API endpoint idempotent matter for handling retries in a distributed system?",
        "choices": [
            "Idempotency makes the endpoint execute faster",
            "If a client times out and doesn't know whether its request succeeded, it can safely retry an idempotent request without risking a double side-effect (e.g. charging a payment twice), since applying it multiple times has the same effect as applying it once",
            "Idempotent endpoints don't require authentication",
            "Idempotency only matters for GET requests",
        ],
        "correct_index": 1,
        "explanation": "Idempotency is what makes 'just retry on timeout' a safe default strategy instead of a source of duplicated side effects.",
    },
    {
        "difficulty": "hard",
        "topic": "Backpressure",
        "question": "What does 'backpressure' mean in a system with a fast producer and a slower consumer, e.g. feeding a queue?",
        "choices": [
            "A mechanism for the consumer (or the layer between them) to signal the producer to slow down, or for excess work to be buffered/dropped deliberately, preventing unbounded queue growth and memory exhaustion",
            "It always means instantly dropping all excess messages with no signal to anyone",
            "It's just another word for load balancing",
            "It only ever applies to database writes",
        ],
        "correct_index": 0,
        "explanation": "Backpressure is a deliberate, controlled response to a rate mismatch, as opposed to letting an unbounded queue silently grow until something crashes.",
    },
    {
        "difficulty": "hard",
        "topic": "Service Discovery",
        "question": "In a microservices architecture where instances scale up/down and get new IPs, what problem does service discovery solve?",
        "choices": [
            "It exists solely to encrypt traffic between services",
            "It lets services find the current network location of other services dynamically, via a registry instances register with/query, instead of relying on hardcoded static addresses that break as instances come and go",
            "It fully replaces the need for load balancers",
            "It's only relevant for client-facing, not internal, traffic",
        ],
        "correct_index": 1,
        "explanation": "Service discovery exists precisely because addresses aren't stable in an elastic environment - it's the mechanism that keeps 'who do I call' accurate as the fleet changes shape.",
    },
    {
        "difficulty": "hard",
        "topic": "Fault Tolerance",
        "question": "What problem does the circuit breaker pattern solve when one service calls another that's failing or slow?",
        "choices": [
            "It automatically repairs the failing downstream service",
            "After detecting repeated failures/timeouts, it 'trips' and fails fast (without even attempting the call) for a cooldown period, preventing the caller from piling up resources waiting on a downstream unlikely to respond, and giving the downstream room to recover",
            "It permanently blocks all calls to any downstream service, forever",
            "It only applies to database calls, never service-to-service calls",
        ],
        "correct_index": 1,
        "explanation": "A circuit breaker converts 'keep trying and waiting on something broken' into 'fail immediately and check back later,' which protects the caller's own resources and gives the downstream breathing room.",
    },
    # ---------------- EXPERT ----------------
    {
        "difficulty": "expert",
        "topic": "Consensus",
        "question": "What is the core guarantee Raft (or Paxos) provides among a cluster of nodes, even if some nodes fail?",
        "choices": [
            "Every node processes requests at exactly the same speed as every other node",
            "All non-faulty nodes agree on the same sequence of values/log entries, in the same order, as long as a majority (quorum) of nodes are up and can communicate",
            "The system tolerates the failure of a majority of nodes and still makes progress",
            "It eliminates the need for any network communication between nodes",
        ],
        "correct_index": 1,
        "explanation": "Consensus algorithms need a majority available to make progress safely, not tolerate a majority failing - safety is preserved (no two nodes disagree on committed entries) even across leader changes, as long as quorum holds.",
    },
    {
        "difficulty": "expert",
        "topic": "Vector Clocks",
        "question": "What problem do vector clocks solve in a distributed system with multiple replicas accepting writes?",
        "choices": [
            "They synchronize physical wall-clock time across all nodes",
            "They let the system detect whether two events (writes) are causally ordered (one happened-before the other) or are truly concurrent/conflicting, without relying on synchronized physical clocks",
            "They compress data during replication",
            "They eliminate the need for any conflict resolution",
        ],
        "correct_index": 1,
        "explanation": "Vector clocks give a logical, causality-aware ordering that survives clock skew between machines - they tell you 'concurrent vs. ordered,' not what time it was.",
    },
    {
        "difficulty": "expert",
        "topic": "CRDTs",
        "question": "What makes a Conflict-free Replicated Data Type (CRDT) useful for multi-region systems accepting writes in multiple regions simultaneously?",
        "choices": [
            "CRDTs prevent any two regions from ever writing at the same moment",
            "CRDTs are designed so concurrent, out-of-order updates from different replicas can always be merged deterministically into the same final state, without needing a coordinator or manual conflict resolution",
            "CRDTs require a single global lock before any write is allowed",
            "CRDTs only work for numeric counter data types",
        ],
        "correct_index": 1,
        "explanation": "The defining property of a CRDT is that its merge function is mathematically guaranteed to converge regardless of the order updates arrive in - that's what removes the need for a coordinator.",
    },
    {
        "difficulty": "expert",
        "topic": "Exactly-Once Delivery",
        "question": "Why is `exactly-once` message delivery across a network considered practically unachievable in the purest sense, and what do real systems do instead?",
        "choices": [
            "It's fully achievable with modern message queues, no caveats needed",
            "A sender can never be 100% sure whether a message was received, since the acknowledgment itself could be lost, so it must choose between risking duplicate delivery or risking loss; real systems typically implement at-least-once delivery plus idempotent/deduplicated processing on the consumer side to achieve an effectively-once outcome",
            "Exactly-once delivery only matters for financial systems",
            "TCP already guarantees exactly-once delivery at the application level",
        ],
        "correct_index": 1,
        "explanation": "The fundamental limit is the ambiguity of a lost acknowledgment - you can't distinguish 'message lost' from 'ack lost' from the sender's side, so systems engineer around it with idempotency rather than eliminating the ambiguity.",
    },
    {
        "difficulty": "expert",
        "topic": "Multi-Region Architecture",
        "question": "What's a key trade-off when deciding whether a multi-region system uses a single 'write region' (others read-only) versus allowing writes in every region?",
        "choices": [
            "There is no trade-off - always allow writes in every region",
            "A single write region keeps writes strongly consistent and simpler, but adds latency for users far from that region and creates a single point of failure for writes; multi-region writes lower write latency locally but require conflict resolution and more complex consistency guarantees",
            "Multi-region writes are always faster and safer than a single write region in every case",
            "This trade-off applies only to caching layers, never to databases",
        ],
        "correct_index": 1,
        "explanation": "This is a direct instance of the consistency/latency/complexity trade-off that recurs throughout distributed systems design - there's no universally correct answer, only the right one for the specific data and access pattern.",
    },
]

SYSTEM_DESIGN_PRACTICE = [
    # ---------------- EASY ----------------
    {
        "difficulty": "easy",
        "topic": "API Design",
        "title": "Design a Simple REST Endpoint",
        "description": """Design the REST API for a "create a to-do item" feature: specify the HTTP method, URL path, request body shape, and response (status code + body) for creating a to-do item, and for listing a user's to-do items.""",
        "starter_code": "## Create To-Do\nMethod:\nPath:\nRequest body:\nResponse:\n\n## List To-Dos\nMethod:\nPath:\nResponse:\n",
        "docs": [{"label": "REST - Wikipedia", "url": "https://en.wikipedia.org/wiki/Representational_state_transfer"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Create To-Do
Method: POST
Path: /todos
Request body: {"title": "Buy milk"}
Response: 201 Created, body is the created item including its new id, e.g. {"id": 42, "title": "Buy milk", "done": false}

## List To-Dos
Method: GET
Path: /todos
Response: 200 OK, body is a list of the user's to-do items, e.g. [{"id": 42, "title": "Buy milk", "done": false}, ...]""",
    },
    {
        "difficulty": "easy",
        "topic": "Caching",
        "title": "Add a Cache in Front of a Read-Heavy Endpoint",
        "description": "A `/product/{id}` endpoint is read about 1000x more often than products are updated. Describe where you'd add a cache, what you'd use as the cache key, and how you'd keep the cache from serving very stale data after a product update.",
        "starter_code": "## Cache Placement\n\n## Cache Key\n\n## Invalidation Strategy\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Cache Placement
A cache-aside cache (e.g. Redis) sitting between the API server and the database, checked before querying the DB.

## Cache Key
`product:{id}` - one entry per product id, since that's exactly the read access pattern.

## Invalidation Strategy
Set a reasonable TTL as a safety net, but also explicitly delete (or overwrite) the `product:{id}` key whenever that product is updated, so the next read repopulates the cache with fresh data instead of waiting out the TTL.""",
    },
    {
        "difficulty": "easy",
        "topic": "Load Balancing",
        "title": "Scale a Single Web Server Under Growing Load",
        "description": "Your app runs on one web server and it's starting to get overloaded. Describe the next architectural step to handle more traffic, including what component you'd add and what you need to be careful about (state) when doing so.",
        "starter_code": "## Next Architectural Step\n\n## What To Watch Out For\n\n",
        "docs": [{"label": "Load balancing (computing) - Wikipedia", "url": "https://en.wikipedia.org/wiki/Load_balancing_(computing)"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Next Architectural Step
Add a load balancer in front of multiple app server instances, so incoming traffic is spread across them instead of hitting one machine.

## What To Watch Out For
Any state currently kept in that one server's memory (e.g. sessions, in-progress uploads) breaks once requests can land on any instance - that state needs to move to a shared store (database, Redis, etc.) so the servers are effectively stateless and any instance can serve any request.""",
    },
    {
        "difficulty": "easy",
        "topic": "Databases",
        "title": "Choose a Database for a Simple Blog",
        "description": "You're building a blog with posts, comments, and tags, where relationships between them matter (e.g. \"find all posts with tag X\"). Pick a database type (relational vs. document/key-value) and justify it in 2-3 sentences.",
        "starter_code": "## Choice\n\n## Justification\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Choice
A relational database (e.g. PostgreSQL).

## Justification
Posts, comments, and tags are naturally related entities with many-to-many and one-to-many relationships (a post has many comments, posts and tags are many-to-many), and the described query pattern ("find all posts with tag X") is exactly the kind of join-driven query relational databases and their indexes handle well and consistently.""",
    },
    {
        "difficulty": "easy",
        "topic": "Client-Server",
        "title": "Sketch a Basic Client-Server Request Flow",
        "description": "Describe, step by step, the sequence of events when a user submits a login form on a website: from clicking submit to seeing the logged-in homepage. Name every hop (client, network, server, database).",
        "starter_code": "1.\n2.\n3.\n4.\n5.\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """1. Browser sends a POST /login request with the entered credentials to the server.
2. The server receives the request and queries the database to verify the credentials.
3. On success, the server creates a session/token and includes it in the response (e.g. as a cookie).
4. The browser stores that cookie/token and follows a redirect to the homepage.
5. The browser requests the homepage, sending the cookie/token along; the server validates it and responds with the logged-in page.""",
    },
    {
        "difficulty": "easy",
        "topic": "Latency",
        "title": "Diagnose a Slow Endpoint",
        "description": "An API endpoint takes 800ms to respond, most of which is one database query. List 3 concrete techniques you'd investigate to reduce that latency, and briefly explain each.",
        "starter_code": "1.\n2.\n3.\n",
        "docs": [{"label": "Database index - Wikipedia", "url": "https://en.wikipedia.org/wiki/Database_index"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """1. Check whether the query is doing a full table scan and add an index on the filtered/sorted columns if so.
2. Cache the result (cache-aside) if the same query result is requested repeatedly, so most requests skip the database entirely.
3. Check for an N+1 query pattern (one query per row instead of a single batched query) and consolidate it into fewer round trips.""",
    },
    {
        "difficulty": "easy",
        "topic": "Horizontal Scaling",
        "title": "Make a Stateful App Horizontally Scalable",
        "description": "A web app currently stores logged-in users' shopping carts in server memory. You want to run 3 copies of the server behind a load balancer. What breaks, and how do you fix it?",
        "starter_code": "## What Breaks\n\n## The Fix\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## What Breaks
A user's cart only exists in the memory of the one server instance that handled their earlier requests. If the load balancer routes their next request to a different instance, that instance has never heard of their cart, and it appears to have vanished.

## The Fix
Move cart state out of server process memory and into a shared store (a database, or a fast shared cache like Redis) that every instance can read/write, so any instance can correctly serve any user's request regardless of which one handled their earlier requests.""",
    },
    {
        "difficulty": "easy",
        "topic": "APIs",
        "title": "Design Pagination for a List Endpoint",
        "description": "A `GET /orders` endpoint currently returns all of a user's orders in one response. As the number of orders grows this gets slow and huge. Describe how you'd add pagination to it (request parameters and response shape).",
        "starter_code": "## Request Parameters\n\n## Response Shape\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Request Parameters
Add optional query parameters, e.g. `?limit=20&after_id=1032` (cursor-based) or `?page=2&page_size=20` (offset-based).

## Response Shape
Return only that page of items plus pagination metadata the client needs to fetch the next page, e.g. {"items": [...], "next_cursor": "1052"} for cursor-based, or {"items": [...], "page": 2, "total_pages": 9} for offset-based.""",
    },
    # ---------------- MEDIUM ----------------
    {
        "difficulty": "medium",
        "topic": "Caching Strategies",
        "title": "Write-Through vs. Cache-Aside for an Inventory Count",
        "description": "An e-commerce site tracks product inventory counts, read very often and updated on every sale. Compare using a write-through cache vs. a cache-aside (lazy-loading) cache for this data, and recommend one.",
        "starter_code": "## Write-Through\n\n## Cache-Aside\n\n## Recommendation\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Write-Through
Every write updates both the database and the cache together, so the cache is always in sync with the database - reads never see stale data, at the cost of extra write latency.

## Cache-Aside
The cache is only populated on a read miss; writes just go to the database, leaving a stale cache entry until it expires or is explicitly invalidated.

## Recommendation
Write-through (or cache-aside with explicit invalidation on every sale), because inventory correctness matters a lot here - stale counts risk overselling, so the small extra write cost is worth avoiding a staleness window.""",
    },
    {
        "difficulty": "medium",
        "topic": "Database Replication",
        "title": "Route Reads to Replicas",
        "description": "Your app has a primary database plus 2 read replicas. Design how the application should decide which reads go to replicas vs. the primary, and what problem this can introduce for a user who just wrote data.",
        "starter_code": "## Read Routing\n\n## The Problem It Introduces\n\n",
        "docs": [{"label": "Replication (computing) - Wikipedia", "url": "https://en.wikipedia.org/wiki/Replication_(computing)"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Read Routing
Route most reads to the replicas (load-balanced across them) to spread out read load, keeping the primary free for writes and any reads that need to be guaranteed fresh.

## The Problem It Introduces
Replication lag: a user who just wrote data may immediately read from a replica that hasn't caught up yet, and appear to see their own change not take effect ("read-your-own-writes" problem). Fix by routing that user's follow-up read to the primary, or to a replica known to have caught up, for a short window after their write.""",
    },
    {
        "difficulty": "medium",
        "topic": "Rate Limiting",
        "title": "Design a Per-User Rate Limiter",
        "description": "Design a rate limiter that allows each user 100 requests/minute across multiple stateless API servers. Specify the algorithm you'd use and where the counter state lives, given requests can hit any server.",
        "starter_code": "## Algorithm\n\n## Where State Lives\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Algorithm
A token bucket (or sliding-window counter) per user, refilling toward 100 tokens/minute; each request consumes one token and is rejected if none remain.

## Where State Lives
The counter must live in a store shared across all API server instances, e.g. Redis, keyed by user id - if each server kept its own in-memory counter, a user could get up to N times the intended limit by spreading requests across N servers.""",
    },
    {
        "difficulty": "medium",
        "topic": "Message Queues",
        "title": "Decouple Order Processing with a Queue",
        "description": "When a user places an order, checkout currently calls the payment, inventory, and email services synchronously before responding - it's slow, and one flaky service breaks the whole checkout. Redesign it using a message queue.",
        "starter_code": "## New Checkout Flow\n\n## What Changes for Each Downstream Service\n\n",
        "docs": [{"label": "Message queue - Wikipedia", "url": "https://en.wikipedia.org/wiki/Message_queue"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## New Checkout Flow
Checkout writes the order to the database and publishes an "OrderPlaced" event to a queue, then returns success to the user immediately once the order is durably recorded/queued - it no longer waits on payment, inventory, or email.

## What Changes for Each Downstream Service
Payment, inventory, and email each become independent consumers of the "OrderPlaced" event, processing it asynchronously and retrying on their own if they fail - a slow or down email service can no longer block or fail the checkout response, and each consumer scales and recovers independently.""",
    },
    {
        "difficulty": "medium",
        "topic": "CDN",
        "title": "Speed Up Global Image Delivery",
        "description": "Users worldwide are experiencing slow load times for product images served directly from your origin server in one region. Describe the change you'd make and what still needs to be handled when the underlying image changes.",
        "starter_code": "## The Change\n\n## Handling Image Updates\n\n",
        "docs": [{"label": "Content delivery network - Wikipedia", "url": "https://en.wikipedia.org/wiki/Content_delivery_network"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## The Change
Put a CDN in front of the images, so edge locations near each user cache and serve them, instead of every request crossing the network back to the single origin region.

## Handling Image Updates
Since edge caches don't know when the origin image changes, use cache-busting: give updated images new, versioned URLs/filenames (or explicitly purge/invalidate the CDN cache for that path) so users don't keep seeing an old cached version indefinitely.""",
    },
    {
        "difficulty": "medium",
        "topic": "Database Indexing",
        "title": "Speed Up a Slow Search Query",
        "description": "A query filtering orders by `customer_id` and `status` is doing a full table scan on a 50 million row table. What would you do, and what's the trade-off of your fix?",
        "starter_code": "## The Fix\n\n## The Trade-Off\n\n",
        "docs": [{"label": "Database index - Wikipedia", "url": "https://en.wikipedia.org/wiki/Database_index"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## The Fix
Add a composite index on (customer_id, status), matching the exact combination of columns the query filters on, so the database can seek directly instead of scanning all 50 million rows.

## The Trade-Off
Every insert/update/delete on that table now has to also maintain the index, adding write overhead and storage - so indexes should be added for columns actually filtered/sorted together in real query patterns, not preemptively on everything.""",
    },
    {
        "difficulty": "medium",
        "topic": "Consistent Hashing",
        "title": "Distribute Cache Keys Across a Cache Cluster",
        "description": "You're running a 4-node Redis cluster to cache session data. Describe how you'd decide which node a given key lives on, and what happens (ideally) when you add a 5th node.",
        "starter_code": "## Key-to-Node Mapping\n\n## Adding a 5th Node\n\n",
        "docs": [{"label": "Consistent hashing - Wikipedia", "url": "https://en.wikipedia.org/wiki/Consistent_hashing"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Key-to-Node Mapping
Use consistent hashing: hash both the keys and the nodes onto a shared ring, and each key is owned by the next node clockwise from its position on the ring - not plain `hash(key) % 4`.

## Adding a 5th Node
Only the slice of keys between the new node's ring position and its nearest existing neighbor needs to move to it; the other nodes' key ownership is undisturbed, unlike modulo hashing where nearly every key would remap.""",
    },
    {
        "difficulty": "medium",
        "topic": "Database Sharding",
        "title": "Choose a Shard Key for a Multi-Tenant App",
        "description": "You're sharding a database for a multi-tenant SaaS app (each customer is a tenant) across several database instances. What would you use as the shard key, and why does that choice matter for avoiding \"hot shards\"?",
        "starter_code": "## Shard Key\n\n## Why It Matters (Hot Shards)\n\n",
        "docs": [{"label": "Shard (database architecture) - Wikipedia", "url": "https://en.wikipedia.org/wiki/Shard_(database_architecture)"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Shard Key
`tenant_id` (or a hash of it), so each tenant's data lives entirely on one shard and most queries (which are naturally scoped to one tenant) stay single-shard.

## Why It Matters (Hot Shards)
A poor shard key (e.g. signup date) could cluster all the currently-active, growing tenants onto one recent shard, overloading it while older shards sit mostly idle. Even with tenant_id, one unusually large/busy tenant can still create a hot shard, which may need dedicated capacity or further splitting for just that tenant.""",
    },
    # ---------------- HARD ----------------
    {
        "difficulty": "hard",
        "topic": "Consistency",
        "title": "Choose Between Strong and Eventual Consistency",
        "description": "A social media \"like count\" on posts is read and updated extremely often across a globally distributed system. Would you make it strongly consistent or eventually consistent, and why? Contrast with a bank account balance.",
        "starter_code": "## Like Count\n\n## Bank Balance (Contrast)\n\n",
        "docs": [{"label": "CAP theorem - Wikipedia", "url": "https://en.wikipedia.org/wiki/CAP_theorem"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Like Count
Eventually consistent - an approximate, briefly-stale count is a fine user experience and lets the system prioritize availability and low latency at global scale; nobody is harmed by a count being off by a few for a moment.

## Bank Balance (Contrast)
Needs strong consistency (or at least a linearizable read for critical operations like a withdrawal check) - serving a stale or incorrect balance can cause real financial harm (e.g. allowing an overdraft that shouldn't be possible), so the consistency/availability trade-off is chosen very differently here than for a like count.""",
    },
    {
        "difficulty": "hard",
        "topic": "Fault Tolerance",
        "title": "Add Resilience to a Chain of Service Calls",
        "description": "Service A calls Service B, which calls Service C. C occasionally becomes slow. Describe 2-3 patterns you'd apply so C's slowness doesn't cascade into A and B becoming unavailable too.",
        "starter_code": "1.\n2.\n3.\n",
        "docs": [{"label": "Circuit breaker design pattern - Wikipedia", "url": "https://en.wikipedia.org/wiki/Circuit_breaker_design_pattern"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """1. Set a bounded timeout on the B->C call, so B never waits indefinitely on a slow C.
2. Wrap the B->C call in a circuit breaker, so once C is clearly unhealthy, B fails fast instead of continuing to pile up waiting requests.
3. Use bulkheading (separate connection/thread pools per downstream) so a slow C can't exhaust resources B needs for unrelated work, and consider a fallback/default response from B when C is unavailable.""",
    },
    {
        "difficulty": "hard",
        "topic": "Distributed Transactions",
        "title": "Coordinate a Purchase Across Two Services",
        "description": "Placing an order needs to both charge a payment service and decrement inventory in an inventory service - two separate services with separate databases. Design how you'd keep them consistent without a single ACID transaction spanning both.",
        "starter_code": "## Approach\n\n## Handling a Failure Partway Through\n\n",
        "docs": [{"label": "Two-phase commit protocol - Wikipedia", "url": "https://en.wikipedia.org/wiki/Two-phase_commit_protocol"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Approach
Use the Saga pattern: execute a sequence of local transactions, each service committing its own step immediately (charge payment, then decrement inventory), each publishing an event when done.

## Handling a Failure Partway Through
If a later step fails (e.g. inventory decrement fails after payment succeeded), run a compensating action for the earlier step (refund the payment) to undo it, rather than trying to hold a blocking transaction open across two independently-owned services and databases.""",
    },
    {
        "difficulty": "hard",
        "topic": "Leader Election",
        "title": "Design Failover for a Single-Leader Database",
        "description": "Your system uses one primary database with replicas. Describe what needs to happen, step by step, when the primary becomes unreachable, and one risk with automating this failover too aggressively.",
        "starter_code": "## Failover Steps\n\n## The Risk of Being Too Aggressive\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Failover Steps
Detect the primary is unreachable via health checks/heartbeats with a timeout (not a single missed check); have the remaining nodes elect/promote a replica to become the new primary (often via a consensus-based coordinator); redirect writes to the new primary; when the old primary comes back, have it rejoin as a replica, never as a second primary.

## The Risk of Being Too Aggressive
A brief network blip (not an actual crash) can trigger a premature failover, resulting in a "split brain" where two primaries both accept writes if the old one wasn't really down - failover thresholds need to tolerate transient issues, not fire on the first missed heartbeat.""",
    },
    {
        "difficulty": "hard",
        "topic": "Idempotency",
        "title": "Make a Payment API Safe to Retry",
        "description": "Clients calling your `POST /charge` payment endpoint sometimes time out and don't know if the charge succeeded, so they retry. Design the API so retries can never double-charge a customer.",
        "starter_code": "## Design\n\n## Why It's Safe\n\n",
        "docs": [{"label": "Idempotence - Wikipedia", "url": "https://en.wikipedia.org/wiki/Idempotence"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Design
Require the client to generate a unique idempotency key per logical charge attempt and send it with the request; the server durably stores the outcome of the first request under that key.

## Why It's Safe
If the same idempotency key is seen again (a retry), the server returns the originally stored result and skips re-processing the charge entirely - so no matter how many times the client retries after a timeout, the customer is charged at most once.""",
    },
    {
        "difficulty": "hard",
        "topic": "Backpressure",
        "title": "Protect a Slow Consumer from a Fast Producer",
        "description": "A queue feeding a downstream analytics processor is growing unbounded because events arrive faster than the processor can consume them. Describe 2 different ways to handle this.",
        "starter_code": "1.\n2.\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """1. Apply backpressure: signal the producer (or the ingestion layer) to slow down once the queue passes a threshold, or bound the queue and deliberately shed/sample lower-priority events once full instead of growing forever.
2. Scale out consumers horizontally (more processor instances pulling from the queue) if the real bottleneck is processing capacity rather than an inherent, permanent rate mismatch.""",
    },
    {
        "difficulty": "hard",
        "topic": "Service Discovery",
        "title": "Let Services Find Each Other Dynamically",
        "description": "You're moving from 2 fixed servers to an auto-scaling fleet of API instances that come and go. Design how an internal client service finds a healthy instance to call, without hardcoding IPs.",
        "starter_code": "## Registration\n\n## Discovery at Call Time\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Registration
Each instance registers itself with a service registry on startup (and is deregistered or health-checked out on shutdown/failure).

## Discovery at Call Time
The calling service (directly, via a client-side load balancer, or via a sidecar proxy) queries the registry for currently healthy instances of the target service and picks one, so addresses are resolved dynamically at call time instead of hardcoded ahead of time.""",
    },
    {
        "difficulty": "hard",
        "topic": "Multi-Region",
        "title": "Design Active-Passive Multi-Region Failover",
        "description": "You run in one primary region and want a second region ready to take over if the primary region goes down entirely. Describe what needs to be replicated, how traffic gets redirected during failover, and one thing that can go wrong with the replicated data during that failover.",
        "starter_code": "## What Gets Replicated\n\n## Traffic Redirection\n\n## What Can Go Wrong\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## What Gets Replicated
The database (and any other durable state) is continuously replicated, typically asynchronously, from the primary region to the passive region.

## Traffic Redirection
DNS or a global traffic manager is updated (or automatically detects the outage) to redirect user traffic to the passive region once failover is triggered.

## What Can Go Wrong
Any writes that hadn't yet replicated to the passive region before the primary went down are lost on failover, since async replication always has some lag - the newly-active region may be missing the most recent writes.""",
    },
    # ---------------- EXPERT (classic "design X" case studies) ----------------
    {
        "difficulty": "expert",
        "topic": "System Design Case Study",
        "title": "Design a URL Shortener",
        "description": "Design a service like bit.ly: given a long URL, return a short unique URL that redirects to it. Cover: the API, how you generate short codes, the data store and its schema, and how you'd handle the redirect path at scale (it's read-heavy).",
        "starter_code": "## API\n\n## Short Code Generation\n\n## Data Store & Schema\n\n## Handling Scale (Read Path)\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## API
`POST /shorten` with {"long_url": "..."} returns {"short_url": "..."}. `GET /{code}` returns a 302 redirect to the original long URL.

## Short Code Generation
Base62-encode an auto-incrementing id (or hash the URL and check for collisions) to produce a short, unique, URL-safe code.

## Data Store & Schema
A simple key-value store or a relational table (code -> long_url, created_at); the access pattern is a plain key lookup, nothing relational is needed.

## Handling Scale (Read Path)
Redirects are far more frequent than creations, so cache the code -> URL mapping (e.g. Redis, or even at a CDN edge) in front of the data store; since a code's mapping never changes once created, the cache can use a long TTL with no invalidation complexity.""",
    },
    {
        "difficulty": "expert",
        "topic": "System Design Case Study",
        "title": "Design a Rate Limiter Service",
        "description": "Design a standalone rate limiting service that other internal services call before processing a request, supporting per-client limits (e.g. 1000 req/hour). Cover the algorithm, where limiter state lives, and how it scales without becoming a bottleneck or single point of failure itself.",
        "starter_code": "## Algorithm\n\n## Where State Lives\n\n## Scaling the Limiter Itself\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Algorithm
A token bucket or sliding-window counter per client, refilling toward the allowed rate over time.

## Where State Lives
Per-client counters live in a shared, low-latency store (e.g. Redis) so every limiter instance sees consistent state - not in any one instance's local memory.

## Scaling the Limiter Itself
Run multiple stateless limiter instances behind a load balancer so the limiter horizontally scales and isn't a single point of failure; keep the check itself a single fast, atomic round trip (e.g. an atomic increment or a small Lua script in Redis) so it doesn't add meaningful latency to every protected request.""",
    },
    {
        "difficulty": "expert",
        "topic": "System Design Case Study",
        "title": "Design a Chat/Messaging System",
        "description": "Design a 1:1 chat feature: sending a message, delivering it to an online recipient in near-real-time, and storing history for offline recipients. Cover the connection model, message delivery, and storage.",
        "starter_code": "## Connection Model\n\n## Message Delivery\n\n## Storage\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Connection Model
Persistent connections (WebSockets, with long-polling as a fallback) between clients and a set of chat servers, so the server can push messages instead of the client having to poll.

## Message Delivery
Maintain a connection registry (e.g. in Redis) mapping user -> which chat server they're currently connected to. When a message is sent, look up the recipient's connection and route it there for instant delivery if they're online; if offline, it's simply queued in storage for them to fetch on next connect.

## Storage
Persist every message to a database keyed by conversation, regardless of the delivery path, so full history is available whether or not the recipient was online at send time.""",
    },
    {
        "difficulty": "expert",
        "topic": "System Design Case Study",
        "title": "Design a News Feed",
        "description": "Design the core of a social feed: users follow other users, and see a reverse-chronological (or ranked) feed of recent posts from people they follow. Cover the two main strategies for generating a feed and when you'd choose each.",
        "starter_code": "## Fan-Out on Write\n\n## Fan-Out on Read\n\n## Which To Use, and When\n\n",
        "docs": [SD_PRIMER],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Fan-Out on Write
When a user posts, immediately write that post into every follower's precomputed feed list. Feed reads become very cheap (just read the precomputed list), but writes get expensive for users with huge follower counts.

## Fan-Out on Read
Store posts once; at read time, query and merge posts from everyone the requesting user follows. Writes stay cheap regardless of follower count, but reads get expensive for users following many people.

## Which To Use, and When
Most real systems use a hybrid: fan-out on write for typical users (cheap reads matter most, follower counts are manageable), and fan-out on read (or a special-cased path) for celebrity/high-follower accounts, to avoid an enormous fan-out cost on every single post from a very popular account.""",
    },
    {
        "difficulty": "expert",
        "topic": "System Design Case Study",
        "title": "Design a Distributed Cache",
        "description": "Design a distributed in-memory cache (like a simplified Redis cluster) that can hold more data than fits on one machine and stay available if a node fails. Cover how keys are distributed across nodes, and your approach to replication/failover.",
        "starter_code": "## Key Distribution\n\n## Replication & Failover\n\n",
        "docs": [{"label": "Consistent hashing - Wikipedia", "url": "https://en.wikipedia.org/wiki/Consistent_hashing"}],
        "test_case_summary": "Self-checked: submit your attempt, then compare against the reference solution.",
        "reference_solution": """## Key Distribution
Distribute keys across nodes using consistent hashing, so each node owns a partition of the keyspace, and adding/removing nodes only reshuffles a small fraction of keys instead of a full remap.

## Replication & Failover
Replicate each key to at least one additional node (e.g. a primary/replica pair per hash-ring segment), so a single node failure doesn't lose that data or make it unavailable. A routing layer (or the clients themselves) needs to track current ring membership to route requests correctly, and failed nodes need to be detected so their replicas can be promoted.""",
    },
]

SYSTEM_DESIGN_CONCEPT = [
    # ---------------- EASY ----------------
    {
        "difficulty": "easy",
        "topic": "Scalability",
        "prompt": "In your own words, what does it mean for a system to 'scale', and why can't you just keep making one server bigger forever?",
        "model_answer": "Scaling means a system can handle more load - more users, requests, or data - without falling over or becoming unacceptably slow. Vertical scaling (making one server bigger) hits real limits: there's a maximum CPU/RAM/disk you can put in a single machine, it gets disproportionately expensive at the high end, and it's a single point of failure - if that one machine dies, everything is down. Horizontal scaling (adding more machines and distributing load across them) avoids the hard ceiling and adds redundancy, which is why most large systems eventually scale out rather than just up.",
    },
    {
        "difficulty": "easy",
        "topic": "Caching",
        "prompt": "What is a cache, and what's the core risk you take on by adding one?",
        "model_answer": "A cache is a smaller, faster storage layer that keeps a copy of frequently-accessed data so future requests can be served without going to the slower source of truth, like a database. The core risk is staleness: the cached copy can drift out of sync with the real data after it changes, so you need a deliberate invalidation or expiration strategy (TTLs, explicit invalidation on writes, etc.) - a cache that's never invalidated is really just a source of stale-data bugs waiting to happen.",
    },
    {
        "difficulty": "easy",
        "topic": "HTTP",
        "prompt": "Explain what an HTTP status code communicates, and give one example each of a 2xx, 4xx, and 5xx code with what it means.",
        "model_answer": "HTTP status codes tell the client the outcome category of its request. 2xx means success - e.g. 200 OK, the request succeeded and here's the result. 4xx means the client did something the server considers wrong - e.g. 404 Not Found, the requested resource doesn't exist. 5xx means the server itself failed to fulfill an otherwise valid request - e.g. 500 Internal Server Error, something broke on the server's side. The category (the first digit) lets clients and monitoring react generically even without knowing every specific code.",
    },
    {
        "difficulty": "easy",
        "topic": "Databases",
        "prompt": "What is a primary key, and why does almost every database table need one?",
        "model_answer": "A primary key is a column (or set of columns) that uniquely identifies each row in a table - no two rows can share the same primary key value. It matters because it gives every row a stable, unique handle: other tables reference rows via foreign keys pointing at the primary key, indexes are commonly built on it for fast lookups, and without one there'd be no reliable way to say 'update or delete exactly this row' if other columns could contain duplicates.",
    },
    {
        "difficulty": "easy",
        "topic": "Networking Basics",
        "prompt": "What does DNS do, in plain terms, when you type a website's domain name into a browser?",
        "model_answer": "DNS (the Domain Name System) translates a human-readable domain name, like example.com, into the numeric IP address a computer actually needs to open a network connection. The browser asks a DNS resolver to look up the domain, which - possibly after checking several layers of nameservers - returns an IP address; the browser then connects to that IP to actually request the page. It's essentially the internet's phonebook.",
    },
    {
        "difficulty": "easy",
        "topic": "Statelessness",
        "prompt": "Why do most scalable web APIs try to be 'stateless' between requests, rather than having the server remember things about a specific client's session in its own memory?",
        "model_answer": "If a server keeps client-specific state, like a shopping cart, only in its own memory, then that client's future requests must always hit that exact same server or the data appears to vanish. That breaks horizontal scaling and load balancing, since a load balancer wants to freely route any request to any healthy instance. Statelessness - with any needed state stored externally, e.g. in a shared database or cache, or passed by the client itself like a token - lets any server instance handle any request, which is what actually makes adding and removing instances and load-balancing work.",
    },
    {
        "difficulty": "easy",
        "topic": "Redundancy",
        "prompt": "What does 'single point of failure' mean, and how do systems typically address one?",
        "model_answer": "A single point of failure is any one component whose failure takes down the whole system, even if everything else is healthy - e.g. one server, one database instance, one network link. Systems address this with redundancy: running multiple instances of that component, like multiple app servers behind a load balancer, or a database with replicas that can be promoted, so the failure of any single instance causes at most a reduced-capacity or automatically-recovered state instead of a full outage.",
    },
    {
        "difficulty": "easy",
        "topic": "APIs",
        "prompt": "What's the difference between an API's 'contract' and its implementation, and why does that distinction matter when a team wants to change how an endpoint works internally?",
        "model_answer": "The contract is the externally visible interface - the request/response shape, status codes, and behavior that callers depend on; the implementation is the internal code, logic, and data model behind it, which is free to change as long as the contract stays the same. This matters because it lets a team refactor, optimize, or even rewrite an endpoint's internals - swap the underlying database, change the algorithm - without breaking any client, as long as they don't change the contract; versioning is only needed when the contract itself must change.",
    },
    # ---------------- MEDIUM ----------------
    {
        "difficulty": "medium",
        "topic": "Caching Strategies",
        "prompt": "Compare cache-aside and write-through caching: what's the practical difference in how data gets into the cache, and what's a downside of each?",
        "model_answer": "Cache-aside (lazy loading): the app checks the cache first; on a miss it reads from the database and populates the cache. Downside: the first request for any key is always slow (a guaranteed miss), and if writes don't also invalidate the cache, stale data can linger. Write-through: every write goes through the cache, which updates itself and the database together, so the cache is always warm and consistent with the database on the write path. Downside: every write pays extra cache-write latency, and data that's never actually read still gets cached, wasting cache space, unlike cache-aside which only caches what's genuinely requested.",
    },
    {
        "difficulty": "medium",
        "topic": "Replication",
        "prompt": "What is replication lag, and what real user-facing problem can it cause?",
        "model_answer": "Replication lag is the delay between a write landing on the primary database and that same write showing up on a replica. It can cause a read-your-own-write problem: if a user submits a change and the app immediately reads it back from a replica that hasn't caught up yet, the user sees their own update appear to have not happened - or even reverted - which is confusing and looks like a bug even though the write actually succeeded.",
    },
    {
        "difficulty": "medium",
        "topic": "Load Balancing",
        "prompt": "What's the difference between a Layer 4 (transport-level) and Layer 7 (application-level) load balancer, and what extra capability does Layer 7 give you?",
        "model_answer": "A Layer 4 load balancer routes based only on network/transport info - IP address and port - without looking at the actual HTTP request content, which makes it fast and simple but blind to what's being requested. A Layer 7 load balancer inspects the actual HTTP request - headers, path, cookies - and can route based on it, e.g. sending /api/* to one backend pool and /static/* to another, doing content-based routing, or making smarter session-affinity decisions - at the cost of doing more work per request.",
    },
    {
        "difficulty": "medium",
        "topic": "Message Queues",
        "prompt": "What does 'at-least-once' delivery from a message queue mean for consumers, and what does that force the consumer to handle?",
        "model_answer": "At-least-once delivery means the queue guarantees a message will be delivered one or more times - it may occasionally deliver the same message twice, e.g. if an acknowledgment is lost after processing but before the queue records it, but it will never silently drop a message. This forces consumers to be idempotent: processing the same message twice must produce the same end result as processing it once, typically by tracking already-processed message IDs, or duplicate side effects like double-charging a customer can occur.",
    },
    {
        "difficulty": "medium",
        "topic": "Rate Limiting",
        "prompt": "Compare the token bucket and fixed window counter approaches to rate limiting - what's the main weakness of a naive fixed window, and how does token bucket avoid it?",
        "model_answer": "A fixed window counter resets a counter every window, e.g. every 60 seconds, and rejects requests once the count hits the limit within that window. Its weakness: a client can burst up to the limit right at the end of one window and again right at the start of the next, getting nearly twice the intended rate in a short span straddling the boundary. Token bucket instead has tokens refill continuously, or in small increments, at a steady rate up to a max bucket size, and each request consumes a token - this smooths the allowed rate out over time and avoids the sharp boundary-effect burst that fixed windows allow.",
    },
    {
        "difficulty": "medium",
        "topic": "Database Indexing",
        "prompt": "Why doesn't it make sense to just add an index on every column of every table?",
        "model_answer": "Every index has to be updated on every insert, update, or delete that touches its column(s), so more indexes mean slower writes and more storage used, even for indexes that are rarely or never actually used by real queries. Indexes are a targeted trade-off - you add them for columns frequently filtered, sorted, or joined on in real query patterns, and skip them elsewhere; a table with an index on every column pays the write cost of all of them for the query benefit of only a few.",
    },
    {
        "difficulty": "medium",
        "topic": "CDN",
        "prompt": "Static assets, like a JS bundle, are usually fine to cache aggressively in a CDN, but a personalized API response, like a user's dashboard data, usually isn't. Why the difference?",
        "model_answer": "Static assets are identical for every user and only change on deploy, so caching them for a long time - often with a versioned or hashed filename so a new deploy gets a new URL - is both safe and highly effective. A personalized API response differs per user and can change frequently based on their own actions, so caching it at a shared CDN edge risks serving one user's data to another, or serving stale data right after their own action - it needs either no caching, very short caching, or cache keys that fully incorporate the user's identity plus invalidation on relevant writes.",
    },
    {
        "difficulty": "medium",
        "topic": "Sharding",
        "prompt": "What is a 'hot shard', and give an example of a shard key choice that would cause one.",
        "model_answer": "A hot shard is a shard that receives disproportionately more traffic or load than the others, becoming a bottleneck even though the overall system has plenty of total capacity spread across shards. Example: sharding a multi-tenant system by signup date instead of tenant id would put every newly active or growing tenant's data on the most recent shard, concentrating almost all current write and read traffic there while older shards sit idle - a bad shard key can make horizontal scaling not actually help.",
    },
    # ---------------- HARD ----------------
    {
        "difficulty": "hard",
        "topic": "CAP Theorem",
        "prompt": "A teammate says 'we chose to be CP instead of AP.' Explain in plain terms what trade-off they made and give a scenario where that choice makes sense.",
        "model_answer": "Choosing CP - Consistent and Partition-tolerant, sacrificing Availability during a partition - means that during a network partition, the system will refuse some requests, returning an error or becoming unavailable to some clients, rather than risk returning inconsistent or stale data. This makes sense for something like a system managing account balances or inventory counts, where serving incorrect data - e.g. letting two nodes both think there's one item left in stock and both sell it - is worse than temporarily refusing service until the partition heals and the nodes can agree again.",
    },
    {
        "difficulty": "hard",
        "topic": "Consistency Models",
        "prompt": "What's the difference between 'strong consistency' and 'read-your-own-writes' consistency, and why might a system offer the weaker read-your-own-writes guarantee instead of full strong consistency?",
        "model_answer": "Strong consistency guarantees every reader, everywhere, sees the most recent write immediately after it completes - the strictest and most expensive guarantee to provide at scale. Read-your-own-writes is weaker: it only guarantees that the specific user who made a write will see their own write on subsequent reads, e.g. by routing their reads to the primary or a replica known to be caught up, while other users might briefly see stale data. Systems offer the weaker guarantee because it solves the most common user-facing pain - seeing your own action seemingly not take effect - while still allowing cheaper, eventually-consistent replication for reads from everyone else, a pragmatic middle ground.",
    },
    {
        "difficulty": "hard",
        "topic": "Distributed Transactions",
        "prompt": "Why is the Saga pattern often preferred over Two-Phase Commit for transactions spanning independently-owned microservices?",
        "model_answer": "Two-phase commit requires a coordinator to hold locks across all participants while waiting for every participant to vote, which means all involved services must be available and responsive at the same time, and a stalled coordinator or participant can leave others blocked holding locks - poor availability and tight coupling. Sagas instead break the transaction into a sequence of independent local transactions, each service committing its own step immediately and publishing an event, with compensating actions defined to undo earlier steps if a later step fails - trading strict atomicity for availability and loose coupling, which fits better when services are owned by different teams and databases and can't share a transaction coordinator.",
    },
    {
        "difficulty": "hard",
        "topic": "Fault Tolerance",
        "prompt": "What's the difference between a retry with exponential backoff and a circuit breaker, and why do systems often use both together rather than just retries alone?",
        "model_answer": "Retrying with exponential backoff handles transient failures - a single request failing - by waiting increasingly longer between attempts, giving a temporarily-struggling downstream time to recover. A circuit breaker instead tracks failure patterns over many requests and, once a downstream looks persistently unhealthy, stops sending requests to it entirely for a cooldown period. Using retries alone against a downed downstream just means every caller keeps hammering it with retries, making recovery harder and wasting caller resources waiting; pairing retries for occasional blips with a circuit breaker for sustained outages gets the best of both - resilience to brief hiccups without amplifying a real outage.",
    },
    {
        "difficulty": "hard",
        "topic": "Idempotency",
        "prompt": "Explain why idempotency has to be enforced server-side, via something like a stored idempotency key, rather than just relying on the client to not click submit twice.",
        "model_answer": "Client-side prevention, like disabling a button after click, only prevents the easy accidental case, and doesn't protect against the actual hard case: the client genuinely doesn't know if its request succeeded, e.g. it timed out waiting for a response, and correctly decides to retry - that's not user error, it's the client behaving correctly under uncertainty. Only the server can definitively know whether it has already processed this exact logical operation, so it needs to durably record the outcome of each idempotency-keyed operation and short-circuit any duplicate carrying the same key, regardless of why the duplicate arrived.",
    },
    {
        "difficulty": "hard",
        "topic": "Backpressure",
        "prompt": "If you just let an unbounded queue grow instead of implementing backpressure, what eventually breaks, and why is 'no backpressure' not actually a neutral or safe default?",
        "model_answer": "An unbounded queue absorbing a sustained rate mismatch, producer faster than consumer, will keep growing until it exhausts memory on whatever's hosting it, at which point that process crashes - taking down in-flight work and potentially the whole node, a much worse failure mode than gracefully rejecting or shedding some excess load earlier. 'No backpressure' isn't neutral because it just delays and worsens the failure - it converts a controllable, visible problem, like a queue-depth alarm and some rejected requests, into an uncontrolled one, like an out-of-memory crash and cascading failure to whatever else shares that resource.",
    },
    {
        "difficulty": "hard",
        "topic": "Service Discovery",
        "prompt": "In a service-discovery setup, what happens if an unhealthy instance isn't promptly removed from the registry, and what mechanism keeps the registry accurate?",
        "model_answer": "If a dead or unhealthy instance stays listed, some fraction of requests routed to it will fail or time out even though enough healthy capacity exists elsewhere, and clients or load balancers keep wasting time trying it. Registries stay accurate via health checks: instances either send periodic heartbeats to the registry and are removed if a heartbeat is missed for too long, or the registry or load balancer actively polls a health endpoint on each instance, removing any that fail checks - so routing decisions are based on currently-healthy instances rather than a stale membership list.",
    },
    {
        "difficulty": "hard",
        "topic": "Multi-Region",
        "prompt": "Why is 'just deploy to multiple regions' not sufficient by itself to get real high availability, and what else has to be designed deliberately?",
        "model_answer": "Simply running copies of an app in multiple regions doesn't help if they all depend on one region's database, one region's DNS or traffic-routing decision, or share some other single point of failure - the app is multi-region in name but still has a hidden single point of failure. Real multi-region availability requires deliberately replicating the data layer across regions with a defined consistency or conflict strategy, a traffic-routing or failover mechanism that can detect a region is down and redirect users elsewhere, and actually testing that failover works - regions silently diverging or failover paths that were never exercised are common causes of multi-region setups failing exactly when needed.",
    },
    # ---------------- EXPERT ----------------
    {
        "difficulty": "expert",
        "topic": "Trade-off Analysis",
        "prompt": "A team wants to migrate a monolith to microservices purely because 'microservices scale better.' What's misleading about that framing, and what do microservices actually trade for what?",
        "model_answer": "A well-designed monolith can scale horizontally too, running many stateless instances behind a load balancer, so the framing that scaling requires microservices isn't accurate. What microservices actually trade for is independent deployability and independent scaling of specific components - you can scale just the hot service instead of everything - plus team autonomy, since different teams can own different services. The cost is massively more operational complexity: network calls where there used to be function calls, distributed transactions or sagas instead of local ACID transactions, service discovery, and harder debugging since a single request now spans multiple services and logs. It's a real trade, not a free scaling upgrade - teams should migrate for the specific problems microservices solve, not for scaling in the abstract.",
    },
    {
        "difficulty": "expert",
        "topic": "Consistency vs. Availability",
        "prompt": "Explain, with a concrete example, why 'availability' and 'uptime' are not quite the same thing in a distributed system that has chosen to be CP during partitions.",
        "model_answer": "A CP system can have 100% of its nodes technically up and running, high uptime in the infrastructure sense, while still refusing to serve some requests during a network partition, because it's deliberately choosing to be unavailable to preserve consistency rather than risk a wrong answer. So a monitoring dashboard showing all instances healthy can coexist with real user-facing unavailability, errors or timeouts, during a partition - uptime measures whether processes are running, availability measures whether the system is successfully serving requests, and a CP system can sacrifice the latter while the former stays green.",
    },
    {
        "difficulty": "expert",
        "topic": "Caching at Scale",
        "prompt": "What is 'cache stampede', also known as thundering herd, and describe one technique to prevent it?",
        "model_answer": "Cache stampede happens when a popular cached key expires, or the cache is cold-started, and a large burst of concurrent requests all miss the cache at the same instant, then all independently hammer the backing database or service to recompute the same value simultaneously, potentially overwhelming it right when it's already under load. A common mitigation is a locking or single-flight approach: when a miss occurs, only the first request actually goes to the database to recompute the value, acquiring a short-lived lock for that key, while concurrent requests for the same key either wait for that result or briefly serve a slightly-stale value, instead of all of them independently hitting the backend.",
    },
    {
        "difficulty": "expert",
        "topic": "Data Modeling at Scale",
        "prompt": "Why do large-scale systems often deliberately denormalize data, duplicating it across places, even though it violates classic relational-database normalization principles?",
        "model_answer": "Normalization minimizes redundancy and update anomalies, which is great for correctness and storage efficiency at moderate scale, but it usually requires joins across normalized tables to answer real queries, and joins get expensive and hard to shard as data and query volume grow, especially across sharded or distributed data stores where a join might mean cross-network calls. Denormalization trades some storage and write complexity - the same fact now lives in multiple places and must be kept in sync, e.g. via events - for read performance and shardability. It's an intentional trade favoring the read-heavy, horizontally-scaled access patterns that dominate at large scale, not a mistake.",
    },
    {
        "difficulty": "expert",
        "topic": "Observability at Scale",
        "prompt": "In a system of dozens of microservices, why do logs and metrics alone often fail to answer 'why was this one request slow', and what capability fills that gap?",
        "model_answer": "A single user request in a microservices system can fan out across many services, each with its own logs and metrics showing only that service's own isolated view - there's no built-in way to see the whole path one specific request took or which of the many hops was the actual bottleneck. Distributed tracing fills this gap: each request is tagged with a shared trace id propagated through every service call it touches, and each service reports timed spans against that trace id, so all the pieces can be reassembled into one end-to-end timeline showing exactly which hop or hops accounted for the latency.",
    },
]

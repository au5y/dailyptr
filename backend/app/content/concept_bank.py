"""
Seed "concept check" bank: a short free-response prompt the user answers in
their own words, then self-grades against a model answer. This is the
fastest of the three components to add content for, so it's the easiest
lever to pull if you want more variety day to day.
"""

CONCEPT_CHECKS = [
    {
        "difficulty": "easy",
        "topic": "Memory",
        "prompt": "In your own words, what is RAII and why does it matter in C++? Give one concrete example.",
        "model_answer": (
            "RAII (Resource Acquisition Is Initialization) ties a resource's lifetime to an object's "
            "lifetime: acquire the resource in the constructor, release it in the destructor. Because "
            "destructors run automatically (including during stack unwinding from an exception), this "
            "makes cleanup deterministic and exception-safe. Example: std::unique_ptr acquires a heap "
            "allocation in its constructor and frees it in its destructor, so you never need a manual "
            "`delete` and can't forget one on an early return or thrown exception. std::lock_guard does "
            "the same thing for mutexes."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "OOD",
        "prompt": "Explain the difference between an interface (pure abstract class) and an abstract class with some implemented methods in C++. When would you use each?",
        "model_answer": (
            "A pure interface declares only pure virtual functions (`= 0`) and no state or implemented "
            "behavior - it defines a contract with zero shared code, useful when unrelated classes need "
            "to support the same operation (e.g., Drawable, Serializable). An abstract class can mix pure "
            "virtual methods with concrete, shared implementation and data members - useful when related "
            "classes share common behavior/state but still need to customize specific steps (Template "
            "Method pattern). Rule of thumb: interface for 'can-do' capabilities across unrelated types, "
            "abstract base class for 'is-a' hierarchies that share real implementation."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "C++ Semantics",
        "prompt": "Explain move semantics: what problem do they solve, and what's the difference between a copy constructor and a move constructor?",
        "model_answer": (
            "Before C++11, transferring a resource-owning object (e.g., one holding a heap buffer) meant "
            "deep-copying it even when the source was about to be destroyed anyway - wasted allocation "
            "and copying. Move semantics let you instead 'steal' the source's internal resources: a move "
            "constructor takes an rvalue reference (T&&) to a source about to be discarded, copies its "
            "pointers/handles into the new object, and nulls out the source so its destructor doesn't "
            "free the now-shared resource. A copy constructor (const T&) must leave the source untouched "
            "and valid, so it has to duplicate the resource. std::move doesn't move anything itself - it "
            "casts an lvalue to an rvalue reference so overload resolution picks the move constructor."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "Design Patterns",
        "prompt": "Compare the Strategy pattern and the State pattern. They have nearly identical class diagrams - what actually distinguishes them?",
        "model_answer": (
            "Structurally both involve a context holding a reference to an interface with interchangeable "
            "implementations. The distinction is intent and lifecycle: in Strategy, the client (or context) "
            "explicitly chooses/injects an algorithm, and the strategy object doesn't know about the "
            "others (e.g., picking a SortStrategy or PricingStrategy once, up front). In State, the context "
            "transitions between state objects itself as its internal state changes, often with each "
            "state object deciding and triggering the next transition - the states are aware of the "
            "overall state machine. Strategy answers 'which algorithm should I use?'; State answers 'what "
            "should I do given I'm currently in this state, and what state comes next?'"
        ),
    },
    {
        "difficulty": "hard",
        "topic": "C++ Semantics",
        "prompt": "What is the Rule of Zero, and how does it relate to the Rule of Three/Five? Why is it usually the better goal?",
        "model_answer": (
            "The Rule of Three/Five says if you declare a destructor, copy constructor, copy assignment, "
            "(and move constructor/assignment in C++11+), you probably need to declare all of them, "
            "because they're all involved in managing some owned resource. The Rule of Zero says: design "
            "your classes so you don't need to declare ANY of them - instead compose the class out of "
            "members that already manage their own resources correctly (std::unique_ptr, std::vector, "
            "std::string, etc.). Then the compiler-generated special members are correct by construction "
            "because they just call the members' own correct special members. It's better because it "
            "eliminates an entire category of manual-resource-management bugs (double free, leak, "
            "shallow copy) by never writing that code in the first place - reserve Rule of Three/Five for "
            "the one or two low-level 'resource handle' classes in a codebase, not everyday classes."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "OOD",
        "prompt": "A junior engineer proposes a `Bird` base class with a `fly()` method, then `Penguin : public Bird`. What's wrong with this design, and what SOLID principle does it violate?",
        "model_answer": (
            "Penguins can't fly, so `Penguin` either has to override `fly()` to throw/no-op (surprising "
            "callers who trust the base contract) or the abstraction is simply wrong for this hierarchy. "
            "This violates the Liskov Substitution Principle: a Penguin should be usable anywhere a Bird "
            "is expected, but a Bird's contract implies flight capability, which Penguin can't honor. "
            "Better designs: don't put fly() on Bird at all (only on a FlyingBird/Flyable interface that "
            "Penguin doesn't implement), or model flight capability as a separate composed behavior/"
            "interface rather than a base-class method every subtype inherits."
        ),
    },
    {
        "difficulty": "expert",
        "topic": "OOD / Design",
        "prompt": "You're designing a plugin system where third-party code must implement a notification handler. Walk through the tradeoffs between using a pure virtual interface, std::function callbacks, and templates (static polymorphism / CRTP) for this.",
        "model_answer": (
            "Pure virtual interface: gives you true runtime polymorphism and a stable ABI-ish boundary "
            "(good for a real plugin system loaded as separate binaries/.so files); costs a vtable "
            "indirection per call and forces implementers into an inheritance hierarchy. std::function: "
            "very flexible (any callable - lambda, free function, bound member) and decouples callers "
            "from any particular type hierarchy, but incurs type erasure overhead (usually a heap "
            "allocation for captures beyond small-buffer-optimization size, plus an indirect call), and "
            "you lose the ability to express a multi-method interface as cleanly as a single callback. "
            "Templates/CRTP: zero runtime overhead - the compiler can inline everything and there's no "
            "vtable - but every distinct implementation becomes a distinct instantiation (code bloat), "
            "requires the plugin's type to be known at compile time (so it doesn't work for truly dynamic "
            "plugins loaded at runtime from separate binaries), and produces much less readable compiler "
            "errors. For an actual dynamically-loaded plugin system, the virtual interface is usually the "
            "right call precisely because you need runtime dispatch across a compiled boundary; templates "
            "win when everything is known and compiled together and you want to eliminate call overhead."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "STL",
        "prompt": "What's the practical difference between std::array and std::vector, and when would you pick each?",
        "model_answer": (
            "std::array is a fixed-size, stack-allocated (or wherever the enclosing object lives) container - "
            "its size is a compile-time template parameter and it never allocates on the heap or reallocates. "
            "std::vector is dynamically sized and heap-backed, and can grow/shrink at runtime via push_back/"
            "resize, which means occasional reallocation (and iterator/reference invalidation) as it grows. "
            "Use std::array when the size is known at compile time and fixed (a 3D vector's xyz, a lookup "
            "table); use std::vector whenever the number of elements is only known at runtime or changes."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "Design Patterns",
        "prompt": "What problem does the Factory Method pattern solve, and how is it different from just calling `new` directly?",
        "model_answer": (
            "Factory Method moves object creation behind a method (often virtual, overridden by subclasses) "
            "instead of scattering `new ConcreteType()` calls throughout client code. The direct benefit is "
            "decoupling: calling code depends only on a base/interface type and a creation method, not on the "
            "concrete class being constructed, so swapping which concrete type gets built (for testing, "
            "configuration, or a new variant) means changing the factory in one place instead of every call "
            "site. It's especially useful when construction needs logic (picking a type based on config/input) "
            "rather than being a plain constructor call."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "Concurrency",
        "prompt": "What is a data race, and how does std::mutex prevent one?",
        "model_answer": (
            "A data race occurs when two or more threads access the same memory location concurrently, at "
            "least one access is a write, and there's no synchronization ordering the accesses - the behavior "
            "is undefined (not just 'you might read a stale value', genuinely undefined by the standard). "
            "std::mutex prevents this by only allowing one thread to hold the lock at a time (via lock()/"
            "unlock(), usually through std::lock_guard for RAII-safety): any thread trying to acquire an "
            "already-held mutex blocks until it's released, so critical-section code touching shared state "
            "never actually executes concurrently across threads, and the mutex's acquire/release also "
            "establishes the memory-ordering guarantees needed for the other thread to see up-to-date values."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "STL",
        "prompt": "What is iterator invalidation, and give a concrete example of code that triggers it.",
        "model_answer": (
            "Iterator invalidation is when an operation on a container makes previously-obtained iterators "
            "(or references/pointers into it) no longer valid to use - dereferencing or incrementing them "
            "afterward is undefined behavior. Classic example: `for (auto it = v.begin(); it != v.end(); ++it) "
            "{ if (*it == target) v.erase(it); }` on a std::vector - erase() shifts every following element "
            "down and invalidates the iterator at and after the erased position, so `++it` on the next loop "
            "iteration is undefined. The fix is to use erase's return value (the next valid iterator) instead "
            "of blindly incrementing: `it = v.erase(it);` else `++it;`. std::vector invalidates on "
            "insert/erase/reallocation; std::map/std::list only invalidate the specific erased element's "
            "iterator, which is a common source of confusion when switching container types."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "Templates",
        "prompt": "What does it mean that C++ templates are 'duck typed' at compile time, and what's the tradeoff versus a virtual-function interface?",
        "model_answer": (
            "A template function/class doesn't require its type parameter to implement any declared "
            "interface - it just needs to support whatever operations the template body actually uses (e.g. "
            "`T::operator+`, `T::size()`); if it does, it compiles, regardless of the type's actual inheritance "
            "hierarchy ('if it walks like a duck...'). This is checked at compile time per-instantiation, "
            "producing zero runtime overhead (no vtable, calls can be inlined) but at the cost of: no single "
            "shared binary implementation (each distinct T gets its own compiled instantiation - code bloat), "
            "errors that only surface when a type fails to satisfy the implicit interface (historically ugly "
            "template error messages, though C++20 concepts improve this significantly by letting you name and "
            "check the required interface explicitly), and no runtime polymorphism - you can't hold a "
            "`std::vector<T>` of mixed types the way you could with a common virtual base pointer."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "Design Patterns",
        "prompt": "The Adapter and Facade patterns both 'wrap' something and present a different interface. What actually distinguishes them?",
        "model_answer": (
            "Both interpose a new interface in front of existing code, but for different reasons. Adapter "
            "exists to make one specific existing interface match another interface a client already expects "
            "- e.g. wrapping a third-party XML library's API so it matches your app's internal `Parser` "
            "interface, purely a translation layer, usually one-to-one between the adapted interface and the "
            "adaptee. Facade exists to simplify a large, complex subsystem (often many classes) behind one "
            "simple, higher-level interface for common use cases - it's not about matching a pre-existing "
            "expected interface, it's about hiding complexity the client shouldn't need to know about. Rule of "
            "thumb: Adapter answers 'how do I make this fit the interface I need'; Facade answers 'how do I "
            "make this subsystem easier to use'."
        ),
    },
    {
        "difficulty": "expert",
        "topic": "Concurrency",
        "prompt": "What is false sharing, and how does it hurt multithreaded performance even when threads never touch the same logical variable?",
        "model_answer": (
            "False sharing happens when two threads modify different variables that happen to live on the "
            "same CPU cache line (typically 64 bytes) - e.g. two counters in adjacent array slots, each "
            "written by a different thread. Even though the threads never touch the same variable, the cache "
            "coherency protocol treats the whole cache line as a unit: every write by one thread invalidates "
            "the other core's cached copy of that line, forcing a coherency round-trip (fetching the line from "
            "the writing core's cache) before the other thread's next access. The result is memory-bandwidth-"
            "bound ping-ponging that can be far slower than if the variables were genuinely contended with a "
            "mutex. Fix: pad/align hot per-thread data to separate cache lines (e.g. `alignas(64)`), so each "
            "thread's frequently-written data has its own line."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "Memory",
        "prompt": "What is a dangling pointer, and how is it different from a null pointer?",
        "model_answer": (
            "A null pointer explicitly points to nothing (address 0) and is safe to check against (`if (ptr)`), "
            "so dereferencing it is a predictable, checkable crash. A dangling pointer still holds the address "
            "of memory that has since been freed/deleted or gone out of scope - it looks like a valid, non-null "
            "pointer, but the memory it points to no longer belongs to it, so dereferencing it is undefined "
            "behavior (might crash, might silently read/write garbage or someone else's now-reallocated data). "
            "The danger is exactly that a dangling pointer gives no visible signal that it's unsafe to use, "
            "unlike a null pointer."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "OOD",
        "prompt": "What is encapsulation, and why is it considered bad practice to expose a class's internal state as public data members?",
        "model_answer": (
            "Encapsulation means bundling an object's data with the methods that operate on it, and hiding the "
            "data behind a controlled interface (private members plus public methods) rather than letting "
            "outside code touch it directly. Public data members let any caller set the object into an invalid "
            "state with no chance for the class to validate or react (e.g. setting a bank balance negative, or "
            "a percentage to 150), and they also make refactoring the internal representation a breaking change "
            "for every caller that reached in directly. Keeping state private and mediating access through "
            "methods means the class can enforce its own invariants and change its internals later without "
            "breaking callers."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "STL",
        "prompt": "What's the practical difference between std::map and std::unordered_map, and when would you pick each?",
        "model_answer": (
            "std::map is a sorted associative container (typically a red-black tree) - keys are kept in order, "
            "iteration visits them sorted, and lookup/insert/erase are O(log n). std::unordered_map is a hash "
            "table - no ordering guarantee, but average-case O(1) lookup/insert/erase (worst case O(n) under "
            "heavy hash collisions). Pick std::unordered_map when you just need fast key lookup and don't care "
            "about order (the common case); pick std::map when you need sorted iteration (e.g. printing entries "
            "in key order) or need iterator stability guarantees unordered_map doesn't give as cleanly across "
            "rehashing."
        ),
    },
    {
        "difficulty": "easy",
        "topic": "C++ Semantics",
        "prompt": "What does 'const correctness' mean, and why does it matter for a function's public API?",
        "model_answer": (
            "Const correctness means marking anything that doesn't modify state as `const` - parameters passed "
            "by reference that are only read (`const T&`), member functions that don't mutate the object "
            "(`void print() const`), and so on. It matters because it's a compiler-enforced contract: a caller "
            "holding a `const T&` or `const T` object can only call `const` methods on it, so const correctness "
            "lets the type system catch accidental mutation at compile time instead of relying on documentation "
            "or trust. It also communicates intent to readers - a `const` parameter tells them at a glance that "
            "the function won't modify their data, without needing to read the function body."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "Design Patterns",
        "prompt": "Explain the Observer pattern and give a concrete example of when you'd reach for it.",
        "model_answer": (
            "Observer defines a one-to-many dependency: a subject maintains a list of observers and notifies "
            "them all automatically whenever its state changes, without needing to know anything about what "
            "those observers actually do with the notification. This decouples the thing that changes from the "
            "things that react to the change - the subject doesn't hold direct references to concrete observer "
            "types, just an interface each observer implements (e.g. `onUpdate()`). A concrete example: a "
            "shopping cart object that notifies a UI badge, an analytics logger, and a persistence layer "
            "whenever an item is added - each observer subscribes independently, and the cart doesn't need to "
            "know any of them exist, so new observers can be added without modifying the cart's code."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "C++ Semantics",
        "prompt": "What's the difference between a shallow copy and a deep copy, and how does std::unique_ptr avoid the need to write a custom deep-copy in the first place?",
        "model_answer": (
            "A shallow copy duplicates an object's members as-is, including any raw pointers - so both the "
            "original and the copy end up pointing at the SAME underlying resource, which is usually wrong for "
            "an owning pointer (double free when both destructors run). A deep copy instead allocates a new, "
            "independent copy of whatever the pointer owns, so the two objects don't share state. std::unique_ptr "
            "sidesteps this whole problem by deleting its copy constructor/assignment entirely (it's move-only) "
            "- since a unique_ptr can't be copied at all, a class holding one as a member is automatically "
            "non-copyable too, unless you explicitly write a copy constructor that deep-copies the pointee "
            "yourself, which forces the decision to be conscious rather than accidental."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "STL",
        "prompt": "What does std::optional solve that returning a sentinel value (like -1 or nullptr) for 'no result' doesn't?",
        "model_answer": (
            "A sentinel value overloads the return type to mean two different things - a real result, or "
            "'nothing' - and relies entirely on the caller remembering to check for it; nothing in the type "
            "system enforces that check, and the sentinel itself might collide with a genuinely valid value "
            "(e.g. -1 could be a legitimate result in some domains). std::optional<T> makes 'might not have a "
            "value' part of the type itself: the caller must explicitly check (`if (result)` or `.has_value()`) "
            "and unwrap (`*result` or `.value()`) before using it, and the compiler won't implicitly let you "
            "treat an optional<T> as a plain T. It also works for any T, including types with no natural "
            "sentinel value at all (like a struct), which a magic sentinel can't express."
        ),
    },
    {
        "difficulty": "medium",
        "topic": "Concurrency",
        "prompt": "What's the difference between std::mutex and std::recursive_mutex, and why should you generally try to avoid needing the latter?",
        "model_answer": (
            "std::mutex deadlocks immediately if the same thread tries to lock it twice without unlocking in "
            "between (even from a nested call) - it has no concept of 'the thread that already holds this lock'. "
            "std::recursive_mutex tracks which thread owns it and how many times, letting that same thread "
            "re-lock it repeatedly (each lock() needs a matching unlock()) without deadlocking. Needing a "
            "recursive_mutex is usually a sign the code's locking discipline is unclear - it's easy to lose "
            "track of exactly how many times a lock is currently held across a call chain, and it masks a "
            "design where a smaller, more clearly-scoped critical section (or restructuring so the locked "
            "function doesn't call back into itself while holding the lock) would be safer and easier to reason "
            "about."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "Templates",
        "prompt": "What is SFINAE, and what practical problem does it let you solve?",
        "model_answer": (
            "SFINAE stands for 'Substitution Failure Is Not An Error': when the compiler substitutes a "
            "candidate template's type parameters during overload resolution and that substitution produces an "
            "invalid type/expression, the compiler silently removes that candidate from the overload set "
            "instead of emitting a hard compile error - it just tries the other candidates. This lets you write "
            "multiple template overloads that are only valid for types with certain properties (e.g. 'has a "
            "`.size()` method' or 'is an integral type'), and have the compiler automatically pick the right one "
            "(or fail to compile only if truly none apply) based on what's substitutable, effectively doing "
            "compile-time interface checking/dispatch without runtime cost. Modern C++20 concepts largely "
            "replace hand-rolled SFINAE for this with much more readable syntax, but SFINAE is still what "
            "concepts compile down to and what you'll find in older codebases."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "OOD",
        "prompt": "Explain the Open/Closed Principle, and give an example of code that violates it.",
        "model_answer": (
            "The Open/Closed Principle says code should be open for extension but closed for modification - "
            "adding new behavior should be possible without editing and re-testing existing, working code. A "
            "classic violation: a `computeDiscount(Order order)` function containing `if (order.type == "
            "\"REGULAR\") ... else if (order.type == \"VIP\") ... else if (order.type == \"WHOLESALE\") ...` - "
            "adding a new order type means editing this function and risking breaking the existing branches, "
            "and the function has to know about every type that will ever exist. A design that honors OCP "
            "instead defines a `DiscountStrategy` interface with one implementation per order type; adding a new "
            "order type means writing a new class that implements the interface, without touching any existing "
            "code at all."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "Design Patterns",
        "prompt": "What is Dependency Injection, and how does it improve testability compared to a class constructing its own dependencies internally?",
        "model_answer": (
            "Dependency Injection means a class receives (is 'injected with') the objects it depends on - "
            "usually via constructor parameters - rather than constructing them itself internally with `new`. "
            "When a class builds its own dependencies (e.g. a `OrderService` that does `db_ = new "
            "PostgresDatabase()` inside its constructor), it's permanently hard-wired to that concrete "
            "implementation, so a unit test exercising OrderService's logic also has to stand up a real "
            "Postgres connection. With DI, the constructor instead takes a `Database&` (interface/abstract "
            "base), and the caller decides what concrete implementation to pass in - production code passes a "
            "real PostgresDatabase, while a test passes a lightweight fake/mock implementing the same "
            "interface, letting the test isolate OrderService's logic from any real database at all."
        ),
    },
    {
        "difficulty": "hard",
        "topic": "C++ Semantics",
        "prompt": "What is copy elision (RVO), and why can it mean a class's copy or move constructor is never actually called even though the code looks like it should be?",
        "model_answer": (
            "Copy elision lets the compiler construct an object directly in its final destination storage, "
            "skipping an intermediate copy/move entirely, in situations like returning a local by value "
            "(`return Widget(args);` or, since C++17, even `return localWidget;` in some cases) - instead of "
            "building a temporary and then copying/moving it into the caller's variable, the compiler builds it "
            "in place from the start. As of C++17, 'mandatory' copy elision for a prvalue return (like "
            "`return Widget(args);`) is guaranteed by the standard - not just an optimization the compiler is "
            "allowed to do - meaning the copy/move constructor isn't merely skipped as an optimization, it "
            "genuinely doesn't need to exist/be callable at all for that specific case to compile. This is why "
            "code that 'returns by value' is often not actually wasteful the way it looks, and why a class can "
            "sometimes be returned by value even with its copy and move constructors both deleted."
        ),
    },
    {
        "difficulty": "expert",
        "topic": "Concurrency",
        "prompt": "Explain the ABA problem in lock-free programming: what is it, and why does a simple compare-and-swap on a pointer not fully protect against it?",
        "model_answer": (
            "The ABA problem occurs in lock-free algorithms that use compare-and-swap (CAS) to detect whether a "
            "value changed: a thread reads a value A, gets preempted, and while it's paused another thread "
            "changes the value from A to B and then back to A again before the first thread resumes. The "
            "resuming thread's CAS sees the value is still A and proceeds as if nothing happened, but the "
            "underlying state genuinely changed in between (e.g. in a lock-free stack, the same pointer value A "
            "might now point to a freed-and-reallocated node with completely different contents/links) - the CAS "
            "can't distinguish 'never changed' from 'changed and changed back'. The classic mitigation is "
            "tagging the pointer with a monotonically-incrementing counter packed alongside it (a "
            "'double-word CAS' or tagged pointer), so even if the pointer value returns to A, the tag has "
            "advanced and the CAS correctly fails."
        ),
    },
    {
        "difficulty": "expert",
        "topic": "OOD / Design",
        "prompt": "What's the difference between composition and inheritance for code reuse, and when does the advice 'favor composition over inheritance' actually apply (as opposed to always)?",
        "model_answer": (
            "Inheritance reuses code by making one class literally BE a specialized version of another (is-a), "
            "inheriting its interface and implementation together as a fixed package, decided at compile time "
            "and hard to change later. Composition reuses code by making one class HAVE another as a member "
            "(has-a) and delegating to it, which can be swapped out or reconfigured at runtime and doesn't "
            "couple the two classes' interfaces together. The advice applies most strongly when the relationship "
            "isn't a genuine is-a (using inheritance purely to reuse a method, not because the subtype "
            "relationship holds - e.g. `Stack : public Vector` just to reuse push_back, which also wrongly "
            "exposes Vector's whole interface including things a Stack shouldn't allow), and when you need to "
            "change behavior at runtime (a Strategy held by composition can be swapped; a base class can't be "
            "un-inherited). Inheritance is still the right tool when a genuine, stable is-a relationship exists "
            "and runtime polymorphism through a shared interface is actually needed."
        ),
    },
]

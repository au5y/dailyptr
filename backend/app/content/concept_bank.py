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
]

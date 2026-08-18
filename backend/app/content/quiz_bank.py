"""
Seed multiple-choice question bank. Each entry:
  difficulty, topic, question, choices (list[str]), correct_index, explanation

This is a small starter set (6 easy / 6 medium / 6 hard / 3 expert = 21).
Add more entries here at any time - seed.py only inserts questions whose
`question` text isn't already in the DB, so re-running it is safe and it
will pick up new additions.
"""

QUIZ_QUESTIONS = [
    # ---------------- EASY ----------------
    {
        "difficulty": "easy",
        "topic": "C++ Basics",
        "question": "What is the default value of an uninitialized local `int` in C++?",
        "choices": ["0", "Undefined / indeterminate", "-1", "Compile error"],
        "correct_index": 1,
        "explanation": "Local (automatic storage duration) variables are not zero-initialized; reading one before assignment is undefined behavior.",
    },
    {
        "difficulty": "easy",
        "topic": "Memory",
        "question": "Which operator allocates memory on the heap in C++?",
        "choices": ["malloc only", "new", "alloc", "heap()"],
        "correct_index": 1,
        "explanation": "`new` allocates on the free store (heap) and calls the constructor; pair it with `delete`.",
    },
    {
        "difficulty": "easy",
        "topic": "OOD",
        "question": "What does encapsulation primarily achieve in object-oriented design?",
        "choices": [
            "Faster runtime performance",
            "Bundling data with the methods that operate on it and hiding internal state",
            "Automatic memory management",
            "Multiple inheritance support",
        ],
        "correct_index": 1,
        "explanation": "Encapsulation hides internal representation behind a public interface, reducing coupling.",
    },
    {
        "difficulty": "easy",
        "topic": "C++ Basics",
        "question": "What does RAII stand for, and what problem does it solve?",
        "choices": [
            "Resource Acquisition Is Initialization - ties resource lifetime to object lifetime",
            "Random Access Iterator Interface - a container requirement",
            "Runtime Allocation Is Immediate - a heap optimization",
            "Reference Assignment Is Implicit - a copy semantics rule",
        ],
        "correct_index": 0,
        "explanation": "RAII binds resource cleanup (memory, locks, file handles) to destructor calls, making cleanup automatic and exception-safe.",
    },
    {
        "difficulty": "easy",
        "topic": "STL",
        "question": "Which STL container provides average O(1) lookup by key?",
        "choices": ["std::vector", "std::map", "std::unordered_map", "std::list"],
        "correct_index": 2,
        "explanation": "std::unordered_map is hash-based with average O(1) find/insert; std::map is a balanced tree at O(log n).",
    },
    {
        "difficulty": "easy",
        "topic": "Design Patterns",
        "question": "The Singleton pattern is primarily used to:",
        "choices": [
            "Create families of related objects",
            "Ensure a class has only one instance with a global access point",
            "Decouple an abstraction from its implementation",
            "Add responsibilities to an object dynamically",
        ],
        "correct_index": 1,
        "explanation": "Singleton restricts instantiation to one object, commonly for shared resources like config or logging.",
    },
    # ---------------- MEDIUM ----------------
    {
        "difficulty": "medium",
        "topic": "C++ Semantics",
        "question": "What is the 'Rule of Three' in C++?",
        "choices": [
            "If you define one of destructor, copy constructor, or copy assignment, you likely need all three",
            "A class may inherit from at most three base classes",
            "Templates support at most three type parameters by convention",
            "A function should have at most three parameters",
        ],
        "correct_index": 0,
        "explanation": "These three special members are linked because custom resource management usually requires all three to avoid double-free/shallow-copy bugs.",
    },
    {
        "difficulty": "medium",
        "topic": "C++ Semantics",
        "question": "What does `std::move` actually do at runtime?",
        "choices": [
            "Physically relocates the object's memory",
            "Nothing by itself - it's a cast to an rvalue reference, enabling move semantics if the type supports it",
            "Deep-copies the object",
            "Deletes the original object",
        ],
        "correct_index": 1,
        "explanation": "`std::move` is just `static_cast<T&&>`; the actual 'move' happens in a move constructor/assignment operator that the type must define.",
    },
    {
        "difficulty": "medium",
        "topic": "OOD",
        "question": "Which SOLID principle states that subtypes must be substitutable for their base types?",
        "choices": [
            "Single Responsibility Principle",
            "Open/Closed Principle",
            "Liskov Substitution Principle",
            "Interface Segregation Principle",
        ],
        "correct_index": 2,
        "explanation": "LSP requires derived classes to honor the behavioral contract of the base class so callers can't tell the difference.",
    },
    {
        "difficulty": "medium",
        "topic": "Design Patterns",
        "question": "The Strategy pattern is best described as:",
        "choices": [
            "Encapsulating interchangeable algorithms behind a common interface, selected at runtime",
            "Restricting a class to one instance",
            "Notifying observers when state changes",
            "Wrapping an object to add behavior transparently",
        ],
        "correct_index": 0,
        "explanation": "Strategy lets you swap algorithms (e.g., sorting comparators, pricing rules) without changing the client code that uses them.",
    },
    {
        "difficulty": "medium",
        "topic": "C++ Semantics",
        "question": "When should a base class destructor be declared `virtual`?",
        "choices": [
            "Never - destructors can't be virtual",
            "Only for abstract classes",
            "Whenever the class is intended to be used polymorphically (deleted via a base pointer)",
            "Only when the class has no data members",
        ],
        "correct_index": 2,
        "explanation": "Without a virtual destructor, `delete basePtr` on a derived object skips the derived destructor - undefined behavior / resource leaks.",
    },
    {
        "difficulty": "medium",
        "topic": "STL",
        "question": "What's the time complexity of inserting into the middle of a std::vector?",
        "choices": ["O(1) amortized", "O(log n)", "O(n) due to shifting elements", "O(n log n)"],
        "correct_index": 2,
        "explanation": "std::vector is contiguous storage, so inserting mid-sequence requires shifting all subsequent elements.",
    },
    # ---------------- HARD ----------------
    {
        "difficulty": "hard",
        "topic": "C++ Semantics",
        "question": "What is the primary danger of returning a reference to a local variable?",
        "choices": [
            "It's a compile error, so there's no runtime danger",
            "It creates a dangling reference to memory that no longer exists once the function returns",
            "It causes a memory leak",
            "It silently copies the variable, which is slow but safe",
        ],
        "correct_index": 1,
        "explanation": "The local's storage is reclaimed when the stack frame unwinds; using the returned reference afterward is undefined behavior.",
    },
    {
        "difficulty": "hard",
        "topic": "Concurrency",
        "question": "What does `std::atomic<int>` guarantee that a plain `int` does not, under concurrent access?",
        "choices": [
            "That reads/writes across threads happen without data races and are indivisible",
            "That the variable is stored on the heap",
            "That the variable is const",
            "That arithmetic overflow can't occur",
        ],
        "correct_index": 0,
        "explanation": "std::atomic provides indivisible operations and defined memory-ordering semantics, preventing data races without a mutex.",
    },
    {
        "difficulty": "hard",
        "topic": "Design Patterns",
        "question": "How does the Decorator pattern differ from simple subclassing for adding behavior?",
        "choices": [
            "It doesn't differ - they solve the same problem the same way",
            "Decorator adds responsibilities dynamically at runtime by wrapping objects, avoiding a combinatorial explosion of subclasses",
            "Decorator requires multiple inheritance",
            "Decorator only works with abstract classes",
        ],
        "correct_index": 1,
        "explanation": "Wrapping lets you compose behaviors at runtime (e.g., stacking stream decorators) instead of creating a subclass per combination.",
    },
    {
        "difficulty": "hard",
        "topic": "OOD",
        "question": "Why is 'favor composition over inheritance' often recommended?",
        "choices": [
            "Composition is always faster at runtime",
            "Inheritance is deprecated in modern C++",
            "Composition avoids tight coupling to a base class's implementation and allows behavior to change at runtime",
            "Composition requires less code in all cases",
        ],
        "correct_index": 2,
        "explanation": "Deep inheritance hierarchies create fragile base-class coupling; composing smaller objects is usually more flexible and testable.",
    },
    {
        "difficulty": "hard",
        "topic": "C++ Semantics",
        "question": "What problem does `std::unique_ptr` solve compared to raw pointers for owned heap resources?",
        "choices": [
            "It makes the pointer thread-safe automatically",
            "It enforces single ownership and automatic deletion when it goes out of scope, preventing leaks and double-frees",
            "It allows multiple owners to share the resource safely",
            "It removes the need for a destructor in the pointed-to type",
        ],
        "correct_index": 1,
        "explanation": "unique_ptr is move-only and deletes its resource in its destructor, giving deterministic, leak-free single ownership.",
    },
    {
        "difficulty": "hard",
        "topic": "Design Patterns",
        "question": "In the Observer pattern, what is the main coupling risk to watch for?",
        "choices": [
            "Subjects becoming tightly coupled to concrete observer types instead of an observer interface",
            "Observers being unable to unsubscribe",
            "There is no coupling risk - Observer eliminates all coupling",
            "Subjects can only have one observer at a time",
        ],
        "correct_index": 0,
        "explanation": "If the subject depends on concrete observer classes rather than an interface, you lose the pattern's decoupling benefit.",
    },
    # ---------------- EXPERT ----------------
    {
        "difficulty": "expert",
        "topic": "C++ Semantics",
        "question": "Given a class with a user-declared move constructor but no declared copy constructor, what happens to the implicitly-generated copy constructor?",
        "choices": [
            "It's still implicitly generated as usual",
            "It's implicitly deleted",
            "It's generated but marked deprecated",
            "The program fails to compile regardless of whether copy is used",
        ],
        "correct_index": 1,
        "explanation": "Declaring any of the move members suppresses the implicit copy constructor/assignment - the compiler assumes you're managing resources yourself.",
    },
    {
        "difficulty": "expert",
        "topic": "Design Patterns",
        "question": "When implementing an LRU cache with O(1) get/put, which combination of data structures is the standard approach and why?",
        "choices": [
            "A single sorted vector, for cache-friendly memory layout",
            "A hash map plus a doubly linked list - the map gives O(1) lookup, the list gives O(1) reordering/eviction",
            "A binary search tree keyed by access time",
            "A priority queue keyed by frequency",
        ],
        "correct_index": 1,
        "explanation": "The hash map gives O(1) key->node lookup; the doubly linked list lets you move a node to the front or evict the tail in O(1) without shifting elements.",
    },
    {
        "difficulty": "expert",
        "topic": "OOD",
        "question": "A base class exposes a non-virtual public method that internally calls a virtual protected method (the 'Template Method' / NVI idiom). What's the main benefit?",
        "choices": [
            "It removes the need for virtual functions entirely",
            "The base class controls the invariant/algorithm shape while letting derived classes customize specific steps, without letting callers bypass the invariants",
            "It makes the class faster because virtual calls are avoided",
            "It allows the base class to be instantiated as an abstract type",
        ],
        "correct_index": 1,
        "explanation": "Non-Virtual Interface keeps the stable public contract non-overridable while customization happens only in the protected/private virtual hooks, protecting class invariants.",
    },
]

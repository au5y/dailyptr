"""
Seed coding-problem bank. Each problem supplies:
  - starter_code: shown to the user in the editor
  - harness_template: a full, compilable C++ program containing the literal
    token {{USER_CODE}}. The sandbox splices the user's submission in place
    of that token, compiles the whole thing, and runs it. The harness's
    main() must print one "CASE i: PASS"/"FAIL ..." line per test and a
    final line exactly "RESULT:<passed>/<total>" - that's the only line the
    grader (app/sandbox) actually parses, the rest is just for the user to
    read in their submission output.
  - docs (optional): curated [{"label", "url"}] links to cppreference.com
    pages relevant to the topic, shown as an optional "Docs" panel in the UI.

Two per tier (easy/medium/hard), one for expert = 7 total, matching the
7-day week. Add more freely; day generation just needs >=1 per difficulty.
"""

COMMON_HEADER = "#include <bits/stdc++.h>\nusing namespace std;\n\n"

CODING_PROBLEMS = [
    # ---------------- EASY ----------------
    {
        "difficulty": "easy",
        "topic": "Strings",
        "title": "Palindrome Check",
        "description": (
            "Write `bool isPalindrome(const string& s)` that returns true if `s` reads the same "
            "forwards and backwards (case-sensitive, no whitespace stripping needed for these tests)."
        ),
        "starter_code": (
            "bool isPalindrome(const string& s) {\n"
            "    // TODO: implement\n"
            "    return false;\n"
            "}\n"
        ),
        "docs": [
            {"label": "std::string", "url": "https://en.cppreference.com/w/cpp/string/basic_string"},
            {"label": "std::string::operator[]", "url": "https://en.cppreference.com/w/cpp/string/basic_string/operator_at"},
        ],
        "test_case_summary": '"racecar"->true, "hello"->false, ""->true, "a"->true, "ab"->false',
        "harness_template": COMMON_HEADER + (
            "{{USER_CODE}}\n\n"
            "int main() {\n"
            "    vector<pair<string,bool>> cases = {\n"
            '        {"racecar", true}, {"hello", false}, {"", true}, {"a", true}, {"ab", false}\n'
            "    };\n"
            "    int passed = 0;\n"
            "    for (size_t i = 0; i < cases.size(); ++i) {\n"
            "        bool got = isPalindrome(cases[i].first);\n"
            "        bool ok = (got == cases[i].second);\n"
            "        if (ok) passed++;\n"
            '        cout << "CASE " << i << ": " << (ok ? "PASS" : "FAIL") << " got=" << got << " want=" << cases[i].second << "\\n";\n'
            "    }\n"
            '    cout << "RESULT:" << passed << "/" << cases.size() << "\\n";\n'
            "    return 0;\n"
            "}\n"
        ),
    },
    {
        "difficulty": "easy",
        "topic": "Arrays",
        "title": "Two Sum",
        "description": (
            "Write `vector<int> twoSum(vector<int>& nums, int target)` that returns the indices "
            "(i, j) with i != j such that nums[i] + nums[j] == target. Assume exactly one valid pair exists."
        ),
        "starter_code": (
            "vector<int> twoSum(vector<int>& nums, int target) {\n"
            "    // TODO: implement (aim for O(n) with a hash map)\n"
            "    return {};\n"
            "}\n"
        ),
        "docs": [
            {"label": "std::unordered_map", "url": "https://en.cppreference.com/w/cpp/container/unordered_map"},
            {"label": "std::vector", "url": "https://en.cppreference.com/w/cpp/container/vector"},
        ],
        "test_case_summary": "([2,7,11,15], 9), ([3,2,4], 6), ([3,3], 6) - any valid index pair is accepted",
        "harness_template": COMMON_HEADER + (
            "{{USER_CODE}}\n\n"
            "int main() {\n"
            "    struct Case { vector<int> nums; int target; };\n"
            "    vector<Case> cases = { {{2,7,11,15}, 9}, {{3,2,4}, 6}, {{3,3}, 6} };\n"
            "    int passed = 0;\n"
            "    for (size_t i = 0; i < cases.size(); ++i) {\n"
            "        vector<int> nums = cases[i].nums;\n"
            "        vector<int> res = twoSum(nums, cases[i].target);\n"
            "        bool ok = res.size() == 2 && res[0] != res[1]\n"
            "            && res[0] >= 0 && res[0] < (int)nums.size()\n"
            "            && res[1] >= 0 && res[1] < (int)nums.size()\n"
            "            && nums[res[0]] + nums[res[1]] == cases[i].target;\n"
            "        if (ok) passed++;\n"
            '        cout << "CASE " << i << ": " << (ok ? "PASS" : "FAIL") << "\\n";\n'
            "    }\n"
            '    cout << "RESULT:" << passed << "/" << cases.size() << "\\n";\n'
            "    return 0;\n"
            "}\n"
        ),
    },
    # ---------------- MEDIUM ----------------
    {
        "difficulty": "medium",
        "topic": "Stacks",
        "title": "Valid Parentheses",
        "description": (
            "Write `bool isValid(const string& s)` where `s` contains only '(', ')', '{', '}', '[', ']'. "
            "Return true if every bracket is closed in the correct order."
        ),
        "starter_code": (
            "bool isValid(const string& s) {\n"
            "    // TODO: implement using a stack\n"
            "    return false;\n"
            "}\n"
        ),
        "docs": [
            {"label": "std::stack", "url": "https://en.cppreference.com/w/cpp/container/stack"},
        ],
        "test_case_summary": '"()"->true, "()[]{}"->true, "(]"->false, "([)]"->false, "{[]}"->true',
        "harness_template": COMMON_HEADER + (
            "{{USER_CODE}}\n\n"
            "int main() {\n"
            "    vector<pair<string,bool>> cases = {\n"
            '        {"()", true}, {"()[]{}", true}, {"(]", false}, {"([)]", false}, {"{[]}", true}\n'
            "    };\n"
            "    int passed = 0;\n"
            "    for (size_t i = 0; i < cases.size(); ++i) {\n"
            "        bool got = isValid(cases[i].first);\n"
            "        bool ok = (got == cases[i].second);\n"
            "        if (ok) passed++;\n"
            '        cout << "CASE " << i << ": " << (ok ? "PASS" : "FAIL") << " got=" << got << " want=" << cases[i].second << "\\n";\n'
            "    }\n"
            '    cout << "RESULT:" << passed << "/" << cases.size() << "\\n";\n'
            "    return 0;\n"
            "}\n"
        ),
    },
    {
        "difficulty": "medium",
        "topic": "Strings",
        "title": "First Unique Character",
        "description": (
            "Write `int firstUniqChar(const string& s)` that returns the index of the first character "
            "in `s` that does not repeat, or -1 if every character repeats."
        ),
        "starter_code": (
            "int firstUniqChar(const string& s) {\n"
            "    // TODO: implement\n"
            "    return -1;\n"
            "}\n"
        ),
        "docs": [
            {"label": "std::unordered_map", "url": "https://en.cppreference.com/w/cpp/container/unordered_map"},
            {"label": "std::string", "url": "https://en.cppreference.com/w/cpp/string/basic_string"},
        ],
        "test_case_summary": '"leetcode"->0, "loveleetcode"->2, "aabb"->-1',
        "harness_template": COMMON_HEADER + (
            "{{USER_CODE}}\n\n"
            "int main() {\n"
            "    vector<pair<string,int>> cases = {\n"
            '        {"leetcode", 0}, {"loveleetcode", 2}, {"aabb", -1}\n'
            "    };\n"
            "    int passed = 0;\n"
            "    for (size_t i = 0; i < cases.size(); ++i) {\n"
            "        int got = firstUniqChar(cases[i].first);\n"
            "        bool ok = (got == cases[i].second);\n"
            "        if (ok) passed++;\n"
            '        cout << "CASE " << i << ": " << (ok ? "PASS" : "FAIL") << " got=" << got << " want=" << cases[i].second << "\\n";\n'
            "    }\n"
            '    cout << "RESULT:" << passed << "/" << cases.size() << "\\n";\n'
            "    return 0;\n"
            "}\n"
        ),
    },
    # ---------------- HARD ----------------
    {
        "difficulty": "hard",
        "topic": "Dynamic Programming",
        "title": "Maximum Subarray",
        "description": (
            "Write `int maxSubArray(vector<int>& nums)` that returns the largest possible sum of a "
            "contiguous, non-empty subarray (Kadane's algorithm, O(n))."
        ),
        "starter_code": (
            "int maxSubArray(vector<int>& nums) {\n"
            "    // TODO: implement Kadane's algorithm\n"
            "    return 0;\n"
            "}\n"
        ),
        "docs": [
            {"label": "std::vector", "url": "https://en.cppreference.com/w/cpp/container/vector"},
            {"label": "std::numeric_limits", "url": "https://en.cppreference.com/w/cpp/types/numeric_limits"},
        ],
        "test_case_summary": "[-2,1,-3,4,-1,2,1,-5,4]->6, [1]->1, [5,4,-1,7,8]->23, [-1,-2,-3]->-1",
        "harness_template": COMMON_HEADER + (
            "{{USER_CODE}}\n\n"
            "int main() {\n"
            "    struct Case { vector<int> nums; int want; };\n"
            "    vector<Case> cases = {\n"
            "        {{-2,1,-3,4,-1,2,1,-5,4}, 6},\n"
            "        {{1}, 1},\n"
            "        {{5,4,-1,7,8}, 23},\n"
            "        {{-1,-2,-3}, -1}\n"
            "    };\n"
            "    int passed = 0;\n"
            "    for (size_t i = 0; i < cases.size(); ++i) {\n"
            "        vector<int> nums = cases[i].nums;\n"
            "        int got = maxSubArray(nums);\n"
            "        bool ok = (got == cases[i].want);\n"
            "        if (ok) passed++;\n"
            '        cout << "CASE " << i << ": " << (ok ? "PASS" : "FAIL") << " got=" << got << " want=" << cases[i].want << "\\n";\n'
            "    }\n"
            '    cout << "RESULT:" << passed << "/" << cases.size() << "\\n";\n'
            "    return 0;\n"
            "}\n"
        ),
    },
    {
        "difficulty": "hard",
        "topic": "Heaps",
        "title": "Kth Largest Element",
        "description": (
            "Write `int findKthLargest(vector<int>& nums, int k)` that returns the k-th largest element "
            "in the array (1st largest = maximum). Aim for better than O(n log n) if you can (a heap of size k)."
        ),
        "starter_code": (
            "int findKthLargest(vector<int>& nums, int k) {\n"
            "    // TODO: implement\n"
            "    return 0;\n"
            "}\n"
        ),
        "docs": [
            {"label": "std::priority_queue", "url": "https://en.cppreference.com/w/cpp/container/priority_queue"},
        ],
        "test_case_summary": "([3,2,1,5,6,4], 2)->5, ([3,2,3,1,2,4,5,5,6], 4)->4",
        "harness_template": COMMON_HEADER + (
            "{{USER_CODE}}\n\n"
            "int main() {\n"
            "    struct Case { vector<int> nums; int k; int want; };\n"
            "    vector<Case> cases = {\n"
            "        {{3,2,1,5,6,4}, 2, 5},\n"
            "        {{3,2,3,1,2,4,5,5,6}, 4, 4}\n"
            "    };\n"
            "    int passed = 0;\n"
            "    for (size_t i = 0; i < cases.size(); ++i) {\n"
            "        vector<int> nums = cases[i].nums;\n"
            "        int got = findKthLargest(nums, cases[i].k);\n"
            "        bool ok = (got == cases[i].want);\n"
            "        if (ok) passed++;\n"
            '        cout << "CASE " << i << ": " << (ok ? "PASS" : "FAIL") << " got=" << got << " want=" << cases[i].want << "\\n";\n'
            "    }\n"
            '    cout << "RESULT:" << passed << "/" << cases.size() << "\\n";\n'
            "    return 0;\n"
            "}\n"
        ),
    },
    # ---------------- EXPERT ----------------
    {
        "difficulty": "expert",
        "topic": "OOD / Design",
        "title": "LRU Cache",
        "description": (
            "Implement a class `LRUCache` with:\n"
            "  - `LRUCache(int capacity)`\n"
            "  - `int get(int key)` - return the value, or -1 if not present; marks it most-recently-used\n"
            "  - `void put(int key, int value)` - insert/update; evicts the least-recently-used entry if over capacity\n"
            "Both operations should run in O(1) average time (hash map + doubly linked list)."
        ),
        "starter_code": (
            "class LRUCache {\n"
            "public:\n"
            "    LRUCache(int capacity) {\n"
            "        // TODO\n"
            "    }\n"
            "    int get(int key) {\n"
            "        // TODO\n"
            "        return -1;\n"
            "    }\n"
            "    void put(int key, int value) {\n"
            "        // TODO\n"
            "    }\n"
            "};\n"
        ),
        "docs": [
            {"label": "std::unordered_map", "url": "https://en.cppreference.com/w/cpp/container/unordered_map"},
            {"label": "std::list", "url": "https://en.cppreference.com/w/cpp/container/list"},
        ],
        "test_case_summary": (
            "capacity=2: put(1,1) put(2,2) get(1)->1 put(3,3)[evicts 2] get(2)->-1 "
            "put(4,4)[evicts 1] get(1)->-1 get(3)->3 get(4)->4"
        ),
        "harness_template": COMMON_HEADER + (
            "{{USER_CODE}}\n\n"
            "int main() {\n"
            "    int passed = 0, total = 0;\n"
            "    auto check = [&](int got, int want, const string& label) {\n"
            "        total++;\n"
            "        bool ok = (got == want);\n"
            "        if (ok) passed++;\n"
            '        cout << "CASE " << label << ": " << (ok ? "PASS" : "FAIL") << " got=" << got << " want=" << want << "\\n";\n'
            "    };\n"
            "    LRUCache cache(2);\n"
            "    cache.put(1, 1);\n"
            "    cache.put(2, 2);\n"
            '    check(cache.get(1), 1, "get(1)");\n'
            "    cache.put(3, 3); // evicts key 2\n"
            '    check(cache.get(2), -1, "get(2)_after_evict");\n'
            "    cache.put(4, 4); // evicts key 1\n"
            '    check(cache.get(1), -1, "get(1)_after_evict");\n'
            '    check(cache.get(3), 3, "get(3)");\n'
            '    check(cache.get(4), 4, "get(4)");\n'
            '    cout << "RESULT:" << passed << "/" << total << "\\n";\n'
            "    return 0;\n"
            "}\n"
        ),
    },
]

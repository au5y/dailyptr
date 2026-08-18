"""Known-correct C++ solutions for every seeded coding problem, keyed by title.
Used by test_api.py to exercise the real sandbox grading path end to end."""

SOLUTIONS_BY_TITLE = {
    "Palindrome Check": """bool isPalindrome(const string& s) {
    int i = 0, j = (int)s.size() - 1;
    while (i < j) { if (s[i] != s[j]) return false; i++; j--; }
    return true;
}""",
    "Two Sum": """vector<int> twoSum(vector<int>& nums, int target) {
    unordered_map<int,int> seen;
    for (int i = 0; i < (int)nums.size(); i++) {
        int need = target - nums[i];
        if (seen.count(need)) return {seen[need], i};
        seen[nums[i]] = i;
    }
    return {};
}""",
    "Valid Parentheses": """bool isValid(const string& s) {
    stack<char> st;
    for (char c : s) {
        if (c=='('||c=='['||c=='{') st.push(c);
        else {
            if (st.empty()) return false;
            char top = st.top(); st.pop();
            if ((c==')'&&top!='(') || (c==']'&&top!='[') || (c=='}'&&top!='{')) return false;
        }
    }
    return st.empty();
}""",
    "First Unique Character": """int firstUniqChar(const string& s) {
    unordered_map<char,int> cnt;
    for (char c : s) cnt[c]++;
    for (int i = 0; i < (int)s.size(); i++) if (cnt[s[i]]==1) return i;
    return -1;
}""",
    "Maximum Subarray": """int maxSubArray(vector<int>& nums) {
    int best = nums[0], cur = nums[0];
    for (size_t i = 1; i < nums.size(); i++) {
        cur = max((int)nums[i], cur + nums[i]);
        best = max(best, cur);
    }
    return best;
}""",
    "Kth Largest Element": """int findKthLargest(vector<int>& nums, int k) {
    priority_queue<int, vector<int>, greater<int>> pq;
    for (int n : nums) {
        pq.push(n);
        if ((int)pq.size() > k) pq.pop();
    }
    return pq.top();
}""",
    "LRU Cache": """class LRUCache {
    int cap;
    list<pair<int,int>> items;
    unordered_map<int, list<pair<int,int>>::iterator> idx;
public:
    LRUCache(int capacity) { cap = capacity; }
    int get(int key) {
        auto it = idx.find(key);
        if (it == idx.end()) return -1;
        items.splice(items.begin(), items, it->second);
        return it->second->second;
    }
    void put(int key, int value) {
        auto it = idx.find(key);
        if (it != idx.end()) {
            it->second->second = value;
            items.splice(items.begin(), items, it->second);
            return;
        }
        if ((int)items.size() >= cap) {
            auto last = items.back();
            idx.erase(last.first);
            items.pop_back();
        }
        items.push_front({key, value});
        idx[key] = items.begin();
    }
};""",
}

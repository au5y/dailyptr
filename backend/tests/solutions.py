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
    "Parse a Query String": """map<string,string> parseQueryString(const string& qs) {
    map<string,string> out;
    stringstream ss(qs);
    string pair;
    while (getline(ss, pair, '&')) {
        if (pair.empty()) continue;
        size_t eq = pair.find('=');
        if (eq == string::npos) out[pair] = "";
        else out[pair.substr(0, eq)] = pair.substr(eq + 1);
    }
    return out;
}""",
    "HTTP Status Category": """string statusCategory(int code) {
    if (code >= 100 && code < 200) return "Informational";
    if (code >= 200 && code < 300) return "Success";
    if (code >= 300 && code < 400) return "Redirection";
    if (code >= 400 && code < 500) return "Client Error";
    if (code >= 500 && code < 600) return "Server Error";
    return "Unknown";
}""",
    "Round-Robin Load Balancer": """class RoundRobinBalancer {
    vector<string> servers;
    size_t idx = 0;
public:
    RoundRobinBalancer(vector<string> servers) : servers(servers) {}
    string next() {
        string s = servers[idx];
        idx = (idx + 1) % servers.size();
        return s;
    }
};""",
    "Token Bucket Rate Limiter": """class TokenBucket {
    double capacity, refillPerSecond, tokens, lastTime;
public:
    TokenBucket(double capacity, double refillPerSecond)
        : capacity(capacity), refillPerSecond(refillPerSecond), tokens(capacity), lastTime(0.0) {}
    bool allow(double nowSeconds, double cost = 1.0) {
        double elapsed = nowSeconds - lastTime;
        tokens = min(capacity, tokens + elapsed * refillPerSecond);
        lastTime = nowSeconds;
        if (tokens < cost) return false;
        tokens -= cost;
        return true;
    }
};""",
}

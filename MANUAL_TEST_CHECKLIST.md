# Manual End-to-End Validation Checklist: Article Submission & Feed Integration

**Environment:** Staging
**Service URL:** https://storyspool-staging-417579885597.us-central1.run.app
**Test Account:** [Provide test account credentials here]

---

## Test Suite

### Scenario 1: Successful Article Submission and Feed Population

**Objective:** Verify that a user can successfully submit an article URL and that it appears in their RSS feed.

1.  **Sign In:**
    *   Navigate to the Service URL.
    *   Sign in with the provided test account credentials.
    *   **Expected:** Successfully logged in, redirected to the articles page or homepage.
    *   **Result:** [PASS/FAIL] - [Notes]

2.  **Submit Article:**
    *   Locate the "Submit an Article URL" form on the homepage.
    *   Enter a valid article URL (e.g., a recent news article from a reputable source like NYT, BBC, Wikipedia).
        *   *Example URL:* `https://en.wikipedia.org/wiki/Test_page` (or a real article)
    *   Click "Submit Article".
    *   **Expected:** A success flash message appears (e.g., "Article submitted successfully! It will appear in your feed soon.").
    *   **Result:** [PASS/FAIL] - [Notes]

3.  **Verify Firestore (Optional, for advanced testers/debugging):**
    *   Access the Firestore console for the staging project.
    *   Navigate to the `articles` collection.
    *   Verify that a new document exists with the submitted article's metadata and the test user's ID.
    *   **Expected:** New article document found in Firestore.
    *   **Result:** [PASS/FAIL] - [Notes]

4.  **Check RSS Feed:**
    *   Locate the user's RSS feed URL. This is typically found on the articles page after logging in, or can be constructed as `[Service URL]/u/[user_id]/feed.xml`.
        *   *Example:* `https://storyspool-staging-417579885597.us-central1.run.app/u/tester01@storyspool.dev/feed.xml`
    *   Open the RSS feed URL in a browser or RSS reader.
    *   **Expected:** The newly submitted article appears as an item in the RSS feed.
    *   **Result:** [PASS/FAIL] - [Notes]

5.  **Validate RSS XML:**
    *   Copy the content of the RSS feed XML.
    *   Go to a public RSS validator (e.g., [W3C Feed Validation Service](https://validator.w3.org/feed/)).
    *   Paste the XML content and validate.
    *   **Expected:** The feed validates successfully with no critical errors. (Warnings are acceptable for MVP).
    *   **Result:** [PASS/FAIL] - [Validator Output/Screenshot]

---

### Scenario 2: Handling Invalid/Missing URL Submission

**Objective:** Verify that the system gracefully handles invalid or missing article URLs.

1.  **Submit Empty URL:**
    *   On the homepage, click "Submit Article" without entering any URL.
    *   **Expected:** An error flash message appears (e.g., "Please provide an article URL.").
    *   **Result:** [PASS/FAIL] - [Notes]

2.  **Submit Invalid URL (e.g., non-existent domain):**
    *   Enter a clearly invalid URL (e.g., `http://nonexistent-domain-12345.com`) and click "Submit Article".
    *   **Expected:** An error flash message appears (e.g., "Error submitting article: ...").
    *   **Result:** [PASS/FAIL] - [Notes]

---

## Overall Test Summary

*   **Total Scenarios Tested:** [Number]
*   **Overall Result:** [PASS/FAIL]
*   **Notes/Observations:** [Any general comments, unexpected behavior, or performance observations]

---

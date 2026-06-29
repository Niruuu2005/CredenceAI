# CredenceAI — In Simple Words

CredenceAI is a **high-trust search engine** that doesn't just search the web, but also verifies the information it finds to make sure it is accurate, safe, and organized.

Here is how the system works, step-by-step:

---

## The Step-by-Step Pipeline

### 1. You Ask a Question (Submit a Job)
You type a query (like *"Who are Tesla's main electric vehicle competitors?"*) into the dashboard or API.

### 2. The App Figures Out What You Want (Intent Classifier)
The app reads your query and decides what kind of research you are doing—whether it is general web search, breaking news, academic research, or business details.

### 3. The App Plans the Search (Planner Agent)
Instead of just asking one search engine, an **AI Planner** breaks your question down into a list of specific things to look up and decides the best places to find them (like Wikipedia, news databases, or academic journals).

### 4. Safety First (Crawl Policy)
Before visiting any website, the app checks the rules:
- It makes sure the website is safe and not a cyber threat.
- It respects the website's rules (Robots.txt) and doesn't overwhelm the site with requests (Rate limiting).

### 5. Collecting and Saving (Crawler & Storage)
The app downloads the search results and webpage content. It keeps a permanent copy of the raw webpages in safe storage (like a digital filing cabinet) so it can trace back where any piece of information came from.

### 6. Cleaning Up & Scoring (Normalizer & Quality Scorer)
Webpages contain a lot of junk (headers, ads, footers). The app:
- **Cleans it**: Extracts just the main article text and title.
- **Scores it**: Checks if the source is reliable, if the content is recent (freshness), and if the page has actual useful content (not just a login wall or CAPTCHA).

### 7. Organizing the Data (Deduplicator & Entity Resolver)
- **Deduplication**: If 5 websites wrote the exact same article, the app merges them so you don't read duplicates.
- **Entity Resolution**: If a page mentions "Apple", the app uses AI to check if it means the tech company Apple Inc. or the actual fruit, linking it to the correct Wikidata database.

### 8. Drawing Connections & Summarizing (Evidence Graph & Synthesis)
- **Evidence Graph**: The app links different facts together. If two websites say the same thing, it boosts confidence. If they contradict each other (e.g. one says a launch is in 2024 and another says 2025), it flags it as a contradiction.
- **Synthesis**: The app writes a simple, easy-to-read summary answering your question, adding clickable footnote citations (like `[1]`, `[2]`) linked directly to the original source articles.

---

## Why is this better than normal Google search?

1. **No Duplicates**: It groups similar articles together automatically.
2. **Fact Verification**: It checks if multiple sources agree or disagree on key details.
3. **Traceability**: Every sentence in its final summary is cited and traced back to a specific webpage saved in the database.
4. **Ready for AI**: You can export the clean, verified results directly as a dataset to train other AI models.

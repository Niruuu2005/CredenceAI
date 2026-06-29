import { CredenceAIClient } from "../src/index.js";

process.env.CREDENCEAI_API_KEY = process.env.CREDENCEAI_API_KEY || "cred_sk_example_key_123456789";
process.env.CREDENCEAI_BASE_URL = process.env.CREDENCEAI_BASE_URL || "http://127.0.0.1:8000";

async function main() {
  const client = CredenceAIClient.fromEnv();
  const query = "blockchain governance models";

  console.log(`Running direct search query: "${query}"`);
  try {
    const response = await client.search({
      q: query,
      limit: 5,
    });

    console.log(`Search Completed! Total results: ${response.total || response.results.length}`);
    for (const item of response.results) {
      console.log(`\n- Title: ${item.title}`);
      console.log(`  URL: ${item.url}`);
      console.log(`  Source: ${item.source}`);
      console.log(`  Snippet: ${item.snippet}`);
    }
  } catch (error: any) {
    console.log(
      "\nNote: Make sure your CredenceAI local backend is running at http://127.0.0.1:8000"
    );
    console.error("Search failed:", error.message);
  }
}

main();

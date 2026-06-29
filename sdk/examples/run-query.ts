import { CredenceAIClient } from "../src/index.js";

process.env.CREDENCEAI_API_KEY = process.env.CREDENCEAI_API_KEY || "cred_sk_example_key_123456789";
process.env.CREDENCEAI_BASE_URL = process.env.CREDENCEAI_BASE_URL || "http://127.0.0.1:8000";

async function main() {
  const client = CredenceAIClient.fromEnv();
  const query = "latest advances in quantum key distribution";

  console.log(`Running high-level blocking query: "${query}"`);
  try {
    const result = await client.run(query, {
      mode: "standard",
      intent: "research",
      maxWaitMs: 30000,
    });

    console.log("Run Completed!");
    console.log("Job ID:", result.jobId);
    console.log("Result Data:", result.data);
    if (result.traceId) {
      console.log("Trace ID:", result.traceId);
    }
  } catch (error: any) {
    console.log(
      "\nNote: Make sure your CredenceAI local backend is running at http://127.0.0.1:8000"
    );
    console.error("Execution failed:", error.message);
  }
}

main();

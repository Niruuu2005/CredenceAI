import { CredenceAIClient } from "../src/index.js";

// Set environment variables for example context if not set
process.env.CREDENCEAI_API_KEY = process.env.CREDENCEAI_API_KEY || "cred_sk_example_key_123456789";
process.env.CREDENCEAI_BASE_URL = process.env.CREDENCEAI_BASE_URL || "http://127.0.0.1:8000";

async function main() {
  console.log("Initializing CredenceAIClient from environment...");
  const client = CredenceAIClient.fromEnv();

  try {
    console.log("Checking API health status...");
    const health = await client.health();
    console.log("Health Status:", health.status);
  } catch (error: any) {
    console.log(
      "\nNote: Make sure your CredenceAI local backend is running at http://127.0.0.1:8000"
    );
    console.error("Health check failed:", error.message);
  }
}

main();

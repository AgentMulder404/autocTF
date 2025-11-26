import { TriggerClient } from "@trigger.dev/sdk";

export const client = new TriggerClient({
  id: "autoctf-pentest",
  apiKey: process.env.TRIGGER_API_KEY!,
  apiUrl: process.env.TRIGGER_API_URL,
});

// Export all jobs
export * from "./jobs/pentest-scan";

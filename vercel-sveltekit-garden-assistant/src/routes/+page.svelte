<script lang="ts">
  import { Chat } from "@ai-sdk/svelte";

  // @ai-sdk/svelte exposes a Chat class (not a useChat hook); its id is sent with every request.
  const chat = new Chat({});
  let input = $state("");
  const busy = $derived(chat.status === "submitted" || chat.status === "streaming");

  function submit(event: SubmitEvent) {
    event.preventDefault();
    if (!input.trim() || busy) return;
    chat.sendMessage({ text: input });
    input = "";
  }
</script>

<main>
  <h1>Sprout, the Fernwick Vale garden helper</h1>
  <p class="hint">Ask about planting dates, pests or watering. Replies stream in as they are written.</p>

  <div class="messages">
    {#each chat.messages as message (message.id)}
      <div class="row {message.role}">
        <div class="bubble">
          {#each message.parts as part}
            {#if part.type === "text"}{part.text}{/if}
          {/each}
        </div>
      </div>
    {/each}
  </div>

  <form onsubmit={submit}>
    <input bind:value={input} placeholder="When can I plant out my tomatoes?" />
    <button type="submit" disabled={busy}>Send</button>
  </form>
</main>

<style>
  :global(body) { font-family: system-ui, sans-serif; background: #f4f7f1; color: #1f2a1c; margin: 0; }
  main { max-width: 640px; margin: 0 auto; padding: 2rem 1rem; display: flex; flex-direction: column; min-height: 100vh; box-sizing: border-box; }
  h1 { font-size: 1.25rem; margin: 0 0 0.25rem; }
  .hint { color: #5f6b5a; margin-top: 0; font-size: 0.9rem; }
  .messages { flex: 1; }
  .row { display: flex; margin: 0.75rem 0; }
  .row.user { justify-content: flex-end; }
  .bubble { max-width: 85%; padding: 0.6rem 0.9rem; border-radius: 12px; white-space: pre-wrap; line-height: 1.45; background: #fff; border: 1px solid #dde5d8; }
  .user .bubble { background: #2f7d3b; color: #fff; border: none; }
  form { display: flex; gap: 0.5rem; padding-top: 1rem; }
  input { flex: 1; padding: 0.6rem 0.9rem; border-radius: 10px; border: 1px solid #c9d4c3; font-size: 1rem; }
  button { padding: 0.6rem 1.1rem; border-radius: 10px; border: none; background: #2f7d3b; color: #fff; font-size: 1rem; }
  button:disabled { background: #9aa795; }
</style>

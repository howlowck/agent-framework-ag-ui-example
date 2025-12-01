import { HttpAgent } from '@ag-ui/client';
import {} from '@ag-ui/core';
import type { FormEvent } from 'react';
import { useState } from 'react';
import { useAsync } from 'react-use';

const BACKEND_URL =
  import.meta.env.VITE_AGENT_BACKEND ?? 'http://localhost:8000';

const agent = new HttpAgent({
  url: BACKEND_URL,
});

export default function App() {
  const [message, setMessage] = useState('What is the current time minus 3 hours?');
  const [response, setResponse] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const {
    loading: loadingRunAgent,
    error: errorRunAgent,
    value: runAgent,
  } = useAsync(async () => {
    return await agent.runAgent();
  }, []);

  if (errorRunAgent) {
    return <div>Error loading agent: {String(errorRunAgent)}</div>;
  }

  if (loadingRunAgent || !runAgent) {
    return <div>Loading agent...</div>;
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    try {
      const responseObservableStream = await agent.run({
        runId: 'run-001',
        threadId: 'thread-001',
        messages: [{ id: 'msg-001', role: 'user', content: message }],
        tools: [],
        context: [],
      });
      // subscribe to "RUN_STARTED"
      responseObservableStream.subscribe({
        next: (data) => {
          console.log('Received data:', data);
        },
      });
      console.log('Agent response:', responseObservableStream);
    } catch (error) {
      setResponse('Could not reach agent backend.');
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app">
      <section className="panel">
        <h1>
          Example shell for <span>ag-fluent-chat</span>
        </h1>
        <p>
          Uses the built package from `dist/` to render the shared{' '}
          <code>Button</code>.
        </p>
        <form onSubmit={handleSubmit}>
          <label htmlFor="message-input">Message to python agent</label>
          <textarea
            id="message-input"
            rows={4}
            value={message}
            onChange={(event) => setMessage(event.target.value)}
          />
          <button type="submit" disabled={isLoading}>
            {isLoading ? 'Sending...' : 'Send Message'}
          </button>
        </form>
        {response && (
          <div className="response-pane">
            <strong>Agent response:</strong>
            <p>{response}</p>
          </div>
        )}
      </section>
    </main>
  );
}

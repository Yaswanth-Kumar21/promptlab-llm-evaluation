/**
 * Prompt Techniques — Phase 5
 *
 * Interactive demos for:
 *  1. Zero-shot — no examples
 *  2. Few-shot  — labelled examples
 *  3. Role prompting — persona assignment
 *  4. Structured output — forces JSON
 *  5. Constraint-based — explicit rules
 *
 * Each technique has:
 *  - Explanation of what it is and when to use it
 *  - The actual prompt template (shown to the user)
 *  - An interactive input field
 *  - A "Try it" button that calls the backend
 *  - Live response display
 */

import { useState } from 'react'
import PageHeader from '../components/ui/PageHeader'
import Spinner from '../components/ui/Spinner'
import ErrorAlert from '../components/ui/ErrorAlert'
import { runTechnique } from '../services/api'
import { formatLatency, formatTokens } from '../utils/format'

// ── Technique definitions ─────────────────────────────────────────────────
const TECHNIQUES = [
  {
    id: 'zero_shot',
    icon: '0️⃣',
    label: 'Zero-Shot',
    tagline: 'No examples — just instructions',
    colour: 'border-blue-700/40 bg-blue-900/10',
    when: 'Simple, well-defined tasks. Use as your baseline before trying few-shot.',
    tradeoff: 'Lower accuracy on complex or domain-specific tasks.',
    promptPreview: `[system] You are a helpful, accurate assistant.

[user] Classify the sentiment of the following text as exactly one of:
positive, negative, or neutral.

Text: {your input}

Reply with just the one-word classification.`,
    defaultInput: 'The product arrived on time and works exactly as described.',
  },
  {
    id: 'few_shot',
    icon: '✏️',
    label: 'Few-Shot',
    tagline: '3 labelled examples teach the pattern',
    colour: 'border-purple-700/40 bg-purple-900/10',
    when: 'Format-sensitive tasks, niche classification. Improves consistency over zero-shot.',
    tradeoff: 'Costs more tokens. Example quality directly affects output quality.',
    promptPreview: `[system] You are a sentiment classifier. Reply with one word only.

[user] Examples:
"Excellent quality, fast delivery." → positive
"Broken on arrival."               → negative
"It arrived. Nothing special."     → neutral

Classify: "{your input}" →`,
    defaultInput: 'I love the design but the battery life is terrible.',
  },
  {
    id: 'role',
    icon: '🎭',
    label: 'Role Prompting',
    tagline: 'Assign an expert persona',
    colour: 'border-green-700/40 bg-green-900/10',
    when: 'Tone and vocabulary control. Works well for explanations, writing, analysis.',
    tradeoff: 'The persona needs to match the task domain for best results.',
    promptPreview: `[system] You are an expert technical educator with 15 years of experience
explaining complex software concepts to beginners. You use clear analogies,
short sentences, and real-world examples.

[user] Explain the following concept to a complete beginner in under 150 words.
Start with a plain-English definition, then give a real-world analogy,
then explain one practical application.

Concept: {your input}`,
    defaultInput: 'REST APIs',
  },
  {
    id: 'structured',
    icon: '🏗️',
    label: 'Structured Output',
    tagline: 'Force valid JSON with an explicit schema',
    colour: 'border-yellow-700/40 bg-yellow-900/10',
    when: 'Whenever the output needs to be parsed programmatically. Use Pydantic to validate.',
    tradeoff: 'Models occasionally produce invalid JSON. Always implement a repair strategy.',
    promptPreview: `[system] You ALWAYS respond with valid JSON only.
No explanations, no markdown fences, no text outside the JSON.

[user] Extract information and return JSON matching:
{
  "main_topic": "string",
  "sentiment": "positive | negative | neutral",
  "key_points": ["array, max 3"],
  "confidence": 0.0–1.0
}

Text: {your input}`,
    defaultInput: 'FastAPI is fast to develop with and has automatic documentation, but the async learning curve can be steep.',
  },
  {
    id: 'constraint',
    icon: '🔒',
    label: 'Constraint-Based',
    tagline: 'Explicit rules reduce variance and hallucination',
    colour: 'border-red-700/40 bg-red-900/10',
    when: 'When you need predictable format and length. Highly effective for summarisation.',
    tradeoff: 'Too many constraints can cause the model to focus on following rules over content quality.',
    promptPreview: `[system] You are a technical writer for non-expert audiences.

[user] Summarise the following text. You MUST follow ALL rules:
1. Write exactly 3 bullet points — no more, no fewer.
2. Each bullet must be fewer than 20 words.
3. Use only information present in the text.
4. Use simple English (8th-grade reading level).
5. Start each bullet with a strong action verb.

Text: {your input}`,
    defaultInput: 'Retrieval-Augmented Generation (RAG) combines a retrieval system with a language model to produce answers grounded in specific documents. Instead of relying on the model\'s training data, RAG first searches a vector database for relevant chunks, then injects them into the prompt as context. This reduces hallucination and allows the model to cite exact sources. RAG is faster and cheaper to update than fine-tuning because you only need to update the document store, not retrain the model.',
  },
]

// ── Technique card ────────────────────────────────────────────────────────
function TechniqueCard({ technique, provider }) {
  const [input, setInput] = useState(technique.defaultInput)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)

  const handleRun = async () => {
    setLoading(true)
    setError(null)
    setResult(null)
    try {
      const res = await runTechnique({
        technique: technique.id,
        user_input: input,
        provider,
        temperature: technique.id === 'structured' ? 0.0 : 0.7,
      })
      setResult(res)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`rounded-xl border p-5 ${technique.colour}`}>
      {/* Header */}
      <div className="flex items-start gap-3 mb-4">
        <span className="text-3xl leading-none">{technique.icon}</span>
        <div>
          <h2 className="text-lg font-bold text-white">{technique.label}</h2>
          <p className="text-sm text-gray-400">{technique.tagline}</p>
        </div>
      </div>

      {/* When to use */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="bg-gray-900/60 rounded-lg p-3">
          <p className="text-xs font-semibold text-green-400 mb-1">✓ When to use</p>
          <p className="text-xs text-gray-400">{technique.when}</p>
        </div>
        <div className="bg-gray-900/60 rounded-lg p-3">
          <p className="text-xs font-semibold text-yellow-400 mb-1">⚠ Trade-off</p>
          <p className="text-xs text-gray-400">{technique.tradeoff}</p>
        </div>
      </div>

      {/* Prompt preview */}
      <details className="mb-4">
        <summary className="text-xs text-brand-400 cursor-pointer mb-2">
          View prompt template
        </summary>
        <pre className="text-xs text-gray-400 bg-gray-950 rounded-lg p-3 overflow-x-auto whitespace-pre-wrap">
          {technique.promptPreview}
        </pre>
      </details>

      {/* Input */}
      <div className="mb-3">
        <label className="label text-xs">Your input</label>
        <textarea
          className="input text-sm resize-none font-sans"
          rows={3}
          value={input}
          onChange={e => setInput(e.target.value)}
        />
      </div>

      {/* Run button */}
      <button
        onClick={handleRun}
        disabled={loading || !input.trim()}
        className="btn-primary text-sm py-2 flex items-center gap-2"
      >
        {loading ? <><Spinner size="sm" />Running…</> : '▶ Try it'}
      </button>

      {/* Error */}
      {error && <div className="mt-3"><ErrorAlert message={error} /></div>}

      {/* Result */}
      {result && (
        <div className="mt-4">
          <div className="flex items-center gap-3 mb-2 text-xs text-gray-500">
            <span className="badge badge-blue">{result.provider}</span>
            <span>{formatLatency(result.latency_ms)}</span>
            {result.usage?.output_tokens && <span>↓ {formatTokens(result.usage.output_tokens)} tokens</span>}
            {result.json_valid === true && <span className="text-green-400">✓ valid JSON</span>}
            {result.json_valid === false && <span className="text-red-400">✗ invalid JSON</span>}
          </div>
          <pre className="text-sm text-gray-300 whitespace-pre-wrap bg-gray-950 rounded-lg p-3 max-h-64 overflow-y-auto font-sans leading-relaxed">
            {result.content}
          </pre>
          {result.parsed && (
            <details className="mt-2">
              <summary className="text-xs text-brand-400 cursor-pointer">Parsed JSON</summary>
              <pre className="mt-1 text-xs text-green-300 bg-gray-950 rounded p-2 overflow-x-auto">
                {JSON.stringify(result.parsed, null, 2)}
              </pre>
            </details>
          )}
        </div>
      )}
    </div>
  )
}

// ── Page ──────────────────────────────────────────────────────────────────
export default function PromptTechniques() {
  const [provider, setProvider] = useState('mock')

  return (
    <div className="p-6 max-w-4xl">
      <PageHeader
        title="Prompt Techniques"
        subtitle="Interactive demos for the five core prompt engineering techniques."
        actions={
          <div className="flex items-center gap-2">
            <label className="text-xs text-gray-400">Provider:</label>
            <select
              className="input text-sm py-1.5 w-36"
              value={provider}
              onChange={e => setProvider(e.target.value)}
            >
              <option value="mock">Mock (free)</option>
              <option value="openai">OpenAI</option>
              <option value="anthropic">Anthropic</option>
              <option value="gemini">Gemini</option>
              <option value="mistral">Mistral</option>
            </select>
          </div>
        }
      />

      <div className="mb-5 card-sm bg-brand-900/10 border-brand-700/30">
        <p className="text-sm text-gray-400">
          Each technique demo runs a <strong className="text-gray-200">real LLM call</strong> (or mock) so you see actual model output.
          The prompt template is shown — nothing is hidden. Structured output uses{' '}
          <strong className="text-gray-200">temperature 0</strong> for deterministic JSON.
        </p>
      </div>

      <div className="space-y-6">
        {TECHNIQUES.map(t => (
          <TechniqueCard key={t.id} technique={t} provider={provider} />
        ))}
      </div>
    </div>
  )
}

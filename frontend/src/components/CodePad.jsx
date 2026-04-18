import Editor from '@monaco-editor/react'

const LANGS = ['python', 'javascript', 'java', 'cpp', 'go', 'typescript']

export default function CodePad({ question, onSubmit, busy }) {
  return (
    <div className="codepad">
      <div className="codepad-header">
        <div className="codepad-title">
          <span className="codepad-icon">⌨</span>
          {question?.title || 'Coding Challenge'}
        </div>
      </div>

      {question?.description && (
        <div className="codepad-problem">
          <p>{question.description}</p>
          {question.examples && (
            <pre className="codepad-example">{question.examples}</pre>
          )}
          {question.constraints && (
            <div className="codepad-constraints">
              <strong>Constraints:</strong> {question.constraints}
            </div>
          )}
        </div>
      )}

      <div className="codepad-editor">
        <Editor
          height="320px"
          defaultLanguage="python"
          defaultValue={`# Write your solution here\ndef solution():\n    pass\n`}
          theme="vs-dark"
          options={{
            fontSize: 14,
            minimap: { enabled: false },
            scrollBeyondLastLine: false,
            lineNumbers: 'on',
            automaticLayout: true,
            padding: { top: 12, bottom: 12 },
          }}
          onChange={(val) => {
            window._codepad_value = val
            window._codepad_lang = 'python'
          }}
        />
      </div>

      <div className="codepad-footer">
        <button
          className="btn btn-primary"
          disabled={busy}
          onClick={() => onSubmit(window._codepad_value || '', window._codepad_lang || 'python')}
        >
          {busy ? '⏳ Evaluating…' : '▶ Run & Submit'}
        </button>
      </div>
    </div>
  )
}

/**
 * ErrorAlert — shown when an API call or action fails.
 */
export default function ErrorAlert({ message, onDismiss }) {
  return (
    <div className="bg-red-900/40 border border-red-800 rounded-lg p-4 flex items-start gap-3">
      <span className="text-red-400 text-lg leading-none mt-0.5">⚠</span>
      <div className="flex-1">
        <p className="text-red-300 text-sm font-medium">Error</p>
        <p className="text-red-400 text-sm mt-0.5">{message}</p>
      </div>
      {onDismiss && (
        <button
          onClick={onDismiss}
          className="text-red-500 hover:text-red-300 text-lg leading-none"
          aria-label="Dismiss error"
        >
          ×
        </button>
      )}
    </div>
  )
}

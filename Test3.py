<Modal
  isOpen={!!expandedEntry}
  onRequestClose={() => setExpandedEntry(null)}
  contentLabel="Expanded Chat"
  className="bg-white max-w-2xl mx-auto my-20 p-6 rounded-lg shadow-lg relative outline-none"
  overlayClassName="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-start"
>
  {/* Close Button */}
  <button
    onClick={() => setExpandedEntry(null)}
    className="absolute top-2 right-2 text-gray-500 hover:text-gray-800"
  >
    Close
  </button>

  <h2 className="text-lg font-bold text-gray-800 mb-4">Expanded Chat</h2>

  <div className="mb-4">
    <p className="font-semibold text-blue-700">Q: {expandedEntry?.query}</p>
  </div>

  <div>
    <pre className="whitespace-pre-wrap text-gray-800">A: {expandedEntry?.response}</pre>
  </div>

  {/* Optional actions */}
  <div className="flex justify-end gap-4 mt-4">
    <button
      onClick={() => copyToClipboard(`${expandedEntry.query}\n${expandedEntry.response}`)}
      className="text-sm text-blue-600 hover:underline"
    >
      Copy
    </button>
    <button
      onClick={() => exportEntry(expandedEntry)}
      className="text-sm text-green-600 hover:underline"
    >
      Export
    </button>
  </div>
</Modal>

<div className="w-full min-h-[300px] bg-gray-50 rounded-lg shadow-md p-6 overflow-auto font-sans text-gray-900 text-lg leading-relaxed">
  {loading ? (
    <div className="flex justify-center items-center h-full">
      <Loader className="animate-spin text-[#007C41] w-10 h-10" />
    </div>
  ) : response && !currentsessionIndex ? (
    <pre className="whitespace-pre-wrap font-mono text-[16px] text-gray-800 leading-relaxed">
      {response}
    </pre>
  ) : null}
  
  {error && <p className="text-red-500 text-center mt-4">{error}</p>}
</div>




{/* Chat History */}
<div className="flex flex-col h-[500px] bg-white rounded-lg overflow-hidden shadow-md">
  <div className="flex-1 overflow-y-auto p-6 bg-gray-50 space-y-6">
    {currentsessionIndex && sessions[currentsessionIndex]?.length > 0 && (
      <>
        {sessions[currentsessionIndex].map((entry, idx) => (
          <div key={idx} className="space-y-3">
            <div className="bg-blue-100 p-4 rounded-md">
              <p className="text-md font-semibold text-gray-800">{entry.query}</p>
            </div>
            <div className="bg-gray-100 p-4 rounded-md">
              <div className="prose prose-sm max-w-none text-gray-900">
                <ReactMarkdown>{entry.response}</ReactMarkdown>
              </div>
            </div>
            <div className="flex gap-4 text-gray-600 text-sm">
              <button onClick={() => copytoClipBoard(entry.response)} className="hover:text-green-600">📋 Copy</button>
              <button onClick={() => exportEntry(entry)} className="hover:text-blue-600">📤 Export</button>
              <button onClick={() => setExpandedEntry(entry)} className="hover:text-purple-600">🔍 Expand</button>


                             
            </div>
          </div>

                             const cleanMarkdown = (text) => {
  if (!text) return '';

  let cleaned = String(text)
    .replace(/^A:\s*/i, '')          // Remove leading 'A:'
    .replace(/^```+/gm, '')           // Remove triple backticks
    .replace(/^---+/gm, '')           // Remove lone ---
    .replace(/^\*\s*$/gm, '')          // Remove lone '*' lines
    .replace(/^-\s*$/gm, '')           // Remove lone '-' lines
    .replace(/^>\s*$/gm, '')           // Remove lone '>' blockquotes
    .trim();

  return cleaned;
};






                             
        ))}
      </>
    )}
  </div>
</div>

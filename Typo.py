import ReactMarkdown from 'react-markdown';

<div className="w-full min-h-[300px] bg-white rounded-lg shadow-md p-6 overflow-auto text-gray-900 leading-relaxed text-base">
  {loading ? (
    <div className="flex justify-center items-center h-full">
      <Loader className="animate-spin text-[#007C41] w-10 h-10" />
    </div>
  ) : response && !currentsessionIndex ? (
    <ReactMarkdown className="prose prose-lg max-w-none break-words">
      {response}
    </ReactMarkdown>
  ) : null}

  {error && <p className="text-red-500 text-center mt-4">{error}</p>}
</div>

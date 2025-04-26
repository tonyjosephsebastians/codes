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

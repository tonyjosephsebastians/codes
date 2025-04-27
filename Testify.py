{selectedAction === "Query Code" && selectedFile && (
  <div className="w-full flex flex-col border border-gray-300 rounded-lg p-2 relative">
    
    <textarea
      value={question}
      onChange={(e) => setQuestion(e.target.value)}
      placeholder="Type your question here..."
      rows={1}
      className="w-full p-2 border-none focus:outline-none resize-none"
      style={{ minHeight: "40px", paddingRight: "50px" }}
      disabled={loading}
    />

    {/* Send Button - floating on right */}
    <button
      onClick={handleChat}
      className="absolute top-2 right-2 bg-[#007C41] text-white p-3 rounded-full hover:bg-[#00543E] flex items-center justify-center"
      disabled={loading}
    >
      <ArrowRightCircle className="w-5 h-5" />
    </button>

    {/* Rahona Button - under textarea */}
    {selectedLanguage === "Cobol" && (
      <div className="mt-2">
        <button
          onClick={() => setShowRahonaModal(true)}
          className={`px-3 py-1 rounded-md text-sm transition-all duration-200 ${
            rahonaEnabled
              ? "bg-[#007C41] text-white"
              : "bg-transparent border border-gray-400 text-gray-700"
          }`}
        >
          Rahona
        </button>
      </div>
    )}

  </div>
)}

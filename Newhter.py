import htmlToDocx from 'html-to-docx';

const handleExport = async () => {
  const cleanHtml = cleanAndRenderMarkdown(entry.response);
  const queryHtml = `<h2>Question:</h2><p>${entry.query}</p>`;
  const fullHtml = `${queryHtml}<hr/>${cleanHtml}`;

  const blob = await htmlToDocx(fullHtml, null, {
    table: { row: { cantSplit: true } },
    footer: true,
    pageNumber: true,
  });

  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'chat_export.docx';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
};

const handleCopy = () => {
  const fullText = `Q: ${entry.query}\n\nA: ${entry.response}`;
  navigator.clipboard.writeText(fullText)
    .then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    })
    .catch((err) => console.error('Failed to copy:', err));



};


const handleExport = () => {
  const cleanHtml = cleanAndRenderMarkdown(entry.response);
  const queryHtml = `<h2>Question:</h2><p>${entry.query}</p>`;
  const fullHtml = `
    <html xmlns:o='urn:schemas-microsoft-com:office:office'
          xmlns:w='urn:schemas-microsoft-com:office:word'
          xmlns='http://www.w3.org/TR/REC-html40'>
      <head>
        <meta charset="utf-8">
        <title>Chat Export</title>
      </head>
      <body>
        ${queryHtml}
        <hr/>
        ${cleanHtml}
      </body>
    </html>`;

  const blob = new Blob(['\ufeff', fullHtml], { type: 'application/msword' });

  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = 'chat_export.doc';
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);



};


{selectedAction === "Query Code" && selectedFile && (
  <div className="w-full relative border border-gray-300 rounded-lg p-2">
    <textarea
      value={question}
      onChange={(e) => setQuestion(e.target.value)}
      placeholder="Type your question here..."
      rows={1}
      className="w-full p-2 pr-16 border-none focus:outline-none resize-none"
      style={{ minHeight: "40px" }}
      disabled={loading}
    />

    <div className="absolute bottom-3 right-3 flex gap-2">
      {/* Send Button */}
      <button
        onClick={handleChat}
        className="ml-2 bg-[#007C41] text-white p-3 rounded-full hover:bg-[#00543E] flex items-center justify-center"
        disabled={loading}
      >
        <ArrowRightCircle className="w-5 h-5" />
      </button>

      {/* Rahona Button */}
      {selectedLanguage === "Cobol" && (
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
      )}
    </div>
  </div>
)}




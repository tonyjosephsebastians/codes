const [rahonaEnabled, setRahonaEnabled] = useState(false);
const [rahonaFile, setRahonaFile] = useState(null);
const [files, setFiles] = useState([]);
const [question, setQuestion] = useState("");
const [loading, setLoading] = useState(false);
const [showRahonaModal, setShowRahonaModal] = useState(false);

{showRahonaModal && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
    <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-lg relative">
      <h2 className="text-xl font-semibold mb-4">Rahona File Manager</h2>

      <input
        type="file"
        onChange={(e) => {
          const file = e.target.files[0];
          if (file) {
            setRahonaFile(file);
            setRahonaEnabled(true);
          }
        }}
        className="mb-4"
      />

      {rahonaFile && (
        <p className="text-sm text-gray-600">Selected File: {rahonaFile.name}</p>
      )}

      <div className="flex justify-end gap-2 mt-4">
        <button
          onClick={() => setShowRahonaModal(false)}
          className="px-4 py-2 bg-gray-300 hover:bg-gray-400 rounded"
        >
          Close
        </button>
        <button
          onClick={() => setShowRahonaModal(false)}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
        >
          Confirm
        </button>
      </div>
    </div>
  </div>
)}

{selectedAction === "Query Code" && selectedFile && (
  <div className="w-full flex flex-col gap-2 border border-gray-300 rounded-xl p-3 bg-white shadow-md">
    <div className="flex items-center gap-2">
      <textarea
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
        placeholder="Ask Rahona..."
        rows={1}
        className="flex-grow border-none focus:outline-none resize-none text-gray-700 placeholder-gray-400"
        style={{ minHeight: "40px" }}
        disabled={loading}
      />
      <button
        onClick={handleChat}
        className="bg-[#007C41] hover:bg-[#00543E] text-white p-2 rounded-full disabled:opacity-50"
        disabled={loading}
      >
        <ArrowRightCircle className="w-6 h-6" />
      </button>
      <button
        onClick={() => setShowRahonaModal(true)}
        className={`px-3 py-1 rounded-xl ${
          rahonaEnabled ? "bg-blue-600 text-white" : "bg-gray-300 text-gray-800"
        }`}
      >
        Rahona
      </button>
    </div>

    {rahonaEnabled && (
      <div className="text-sm text-gray-600 flex items-center justify-between">
        <span>Rahona enabled with file: {rahonaFile?.name}</span>
        <button
          className="text-red-500 text-xs hover:underline"
          onClick={() => {
            setRahonaEnabled(false);
            setRahonaFile(null);
          }}
        >
          Disable Rahona
        </button>
      </div>
    )}
  </div>
)}

const handleChat = async () => {
  const payload = {
    question,
    rahonaEnabled,
    rahonaFileName: rahonaFile?.name || null,
  };

  console.log("Sending to backend:", payload);
  // send to backend via fetch/axios
};

{selectedLanguage === "COBOL" && (
  <button
    onClick={() => setShowRahonaModal(true)}
    className={`px-3 py-1 rounded-xl transition-all duration-200 ${
      rahonaEnabled
        ? "bg-blue-600 text-white"
        : "bg-transparent border border-gray-400 text-gray-700"
    }`}
  >
    Rahona
  </button>
)}


{showRahonaModal && (
  <div className="fixed inset-0 bg-black bg-opacity-50 flex justify-center items-center z-50">
    <div className="bg-white rounded-lg p-6 w-full max-w-md shadow-lg relative">
      <h2 className="text-xl font-semibold mb-4">Rahona File Manager</h2>

      {/* Upload Section */}
      <input type="file" onChange={handleFileUpload} className="mb-4" />

      {/* File List Section */}
      <div>
        <h3 className="font-medium">Uploaded Files</h3>
        <ul className="list-disc pl-5">
          {files.map((file, index) => (
            <li key={index}>{file.name}</li>
          ))}
        </ul>
      </div>

      {/* Close Button */}
      <button
        onClick={() => setShowRahonaModal(false)}
        className="absolute top-2 right-2 text-gray-500 hover:text-gray-800"
      >
        ✕
      </button>
    </div>
  </div>
)}


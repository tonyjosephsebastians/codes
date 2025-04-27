import React, { useState } from 'react';
import { marked } from 'marked';
import DOMPurify from 'dompurify';
import htmlDocx from 'html-docx-js'; // install with: npm install html-docx-js

const ChatEntry = ({ entry }) => {
  const [copied, setCopied] = useState(false);

  const cleanAndRenderMarkdown = (markdownText) => {
    const html = marked.parse(markdownText || '');
    const cleanHtml = DOMPurify.sanitize(html);
    return cleanHtml;
  };

  const handleCopy = () => {
    const cleanHtml = cleanAndRenderMarkdown(entry.response);
    navigator.clipboard.writeText(entry.response || '')
      .then(() => {
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
      })
      .catch((err) => console.error('Failed to copy:', err));
  };

  const handleExport = () => {
    const cleanHtml = cleanAndRenderMarkdown(entry.response);
    const docxBlob = htmlDocx.asBlob('<html><body>' + cleanHtml + '</body></html>');
    const url = URL.createObjectURL(docxBlob);
    
    const link = document.createElement('a');
    link.href = url;
    link.download = 'exported_chat.docx';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="space-y-3 p-4 bg-gray-100 rounded-md shadow-sm">
      <div className="bg-blue-50 p-3 rounded">
        <p className="font-semibold text-gray-800">{entry.query}</p>
      </div>
      <div className="bg-white p-4 rounded prose prose-sm max-w-none text-gray-900" 
           dangerouslySetInnerHTML={{ __html: cleanAndRenderMarkdown(entry.response) }}>
      </div>

      <div className="flex gap-4 text-gray-600 text-sm pt-2">
        <button
          onClick={handleCopy}
          className="hover:text-green-600 transition-colors"
        >
          📋 {copied ? "Copied!" : "Copy"}
        </button>

        <button
          onClick={handleExport}
          className="hover:text-blue-600 transition-colors"
        >
          📄 Export to Word
        </button>
      </div>
    </div>
  );
};

export default ChatEntry;

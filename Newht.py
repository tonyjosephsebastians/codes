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

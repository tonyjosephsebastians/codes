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

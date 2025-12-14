// src/components/FileUpload.js
import React, { useState } from 'react';

const FileUpload = ({ onFileParsed }) => {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState('');

  const handleFileChange = (event) => {
    const uploadedFile = event.target.files[0];
    setFile(uploadedFile);
    setMessage('File selected, ready to upload');
  };

  const handleUpload = async () => {
    if (!file) {
      setMessage('Please select a file first');
      return;
    }
    setMessage('Uploading file...');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const uploadResponse = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      const uploadData = await uploadResponse.json();

      if (uploadResponse.ok) {
        setMessage('File uploaded successfully');
        const fileId = uploadData.data.paperId;

        // Now, parse the document
        const parseResponse = await fetch(`/api/parse`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ fileId }),
        });

        const parseData = await parseResponse.json();

        if (parseResponse.ok) {
          setMessage('Document parsed successfully');
          onFileParsed(parseData.data);  // Pass parsed data to parent component
        } else {
          setMessage('Error occurred during document parsing');
        }
      } else {
        setMessage('Error occurred during file upload');
      }
    } catch (error) {
      setMessage('Error occurred during file upload');
    }
  };

  const simulateParsing = async (file) => {
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          title: 'Sample Paper Title',
          abstract: 'This is the abstract of the paper.',
          sections: [
            { section: 'Introduction', content: 'This is the introduction.' },
            { section: 'Methods', content: 'This is the methods section.' },
          ],
        });
      }, 2000);
    });
  };

  return (
    <div>
      <input type="file" onChange={handleFileChange} />
      <button onClick={handleUpload}>Upload File</button>
      <p>{message}</p>
    </div>
  );
};

export default FileUpload;

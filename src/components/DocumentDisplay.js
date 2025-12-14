// src/components/DocumentDisplay.js
import React, { useEffect, useState } from 'react';

const DocumentDisplay = ({ paperId }) => {
  const [documentData, setDocumentData] = useState(null);

  useEffect(() => {
    const fetchDocument = async () => {
      try {
        const response = await fetch(`/api/retrieve?paperId=${paperId}`);
        const data = await response.json();

        if (response.ok) {
          setDocumentData(data.data);  
        } else {
          console.error('Error retrieving document');
        }
      } catch (error) {
        console.error('Fetch error:', error);
      }
    };

    if (paperId) {
      fetchDocument();
    }
  }, [paperId]);

  if (!documentData) {
    return <p>Loading document...</p>;
  }

  return (
    <div>
      <h2>{documentData.title}</h2>
      <div>
        {documentData.sections.map((section, index) => (
          <div key={index}>
            <h3>{section.section}</h3>
            <p>{section.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DocumentDisplay;

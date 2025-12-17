// src/components/FileUpload.js
import React, { useState } from 'react';

const FileUpload = ({ onFileParsed }) => {
  const [files, setFiles] = useState([]);
  const [message, setMessage] = useState('');

  // 进度与批量结果
  const [isUploading, setIsUploading] = useState(false);
  const [completedCount, setCompletedCount] = useState(0);
  const [successCount, setSuccessCount] = useState(0);
  const [failedItems, setFailedItems] = useState([]); // { name, stage, error }

  const totalCount = files.length;
  const progressPercent =
    totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

  const handleFileChange = (event) => {
    const uploadedFiles = Array.from(event.target.files || []);
    setFiles(uploadedFiles);

    // 重置状态（尽量不影响原逻辑，只是增加批量体验）
    setCompletedCount(0);
    setSuccessCount(0);
    setFailedItems([]);

    if (uploadedFiles.length === 0) {
      setMessage('');
      return;
    }
    setMessage(`${uploadedFiles.length} files selected, ready to upload`);
  };

  const handleUpload = async () => {
    if (!files || files.length === 0) {
      setMessage('Please select files first');
      return;
    }

    setIsUploading(true);
    setCompletedCount(0);
    setSuccessCount(0);
    setFailedItems([]);
    setMessage('Uploading files...');

    let localSuccess = 0;
    const localFailed = [];

    try {
      for (let i = 0; i < files.length; i++) {
        const file = files[i];

        // 1) Upload
        let fileId = null;
        try {
          const formData = new FormData();
          formData.append('file', file);

          const uploadResponse = await fetch('/api/upload', {
            method: 'POST',
            body: formData,
          });

          let uploadData = null;
          try {
            uploadData = await uploadResponse.json();
          } catch (e) {

          }

          if (!uploadResponse.ok) {
            const errMsg =
              uploadData?.message ||
              uploadData?.error ||
              `HTTP ${uploadResponse.status}`;
            throw new Error(errMsg);
          }

          fileId = uploadData?.data?.paperId;
          if (!fileId) {
            throw new Error('Missing paperId in upload response');
          }
        } catch (err) {
          localFailed.push({
            name: file.name,
            stage: 'upload',
            error: err?.message || 'Upload failed',
          });

          setFailedItems([...localFailed]);
          setCompletedCount((prev) => prev + 1);
          continue;
        }

        // 2) Parse
        try {
          const parseResponse = await fetch(`/api/parse`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ fileId }),
          });

          let parseData = null;
          try {
            parseData = await parseResponse.json();
          } catch (e) {}

          if (!parseResponse.ok) {
            const errMsg =
              parseData?.message ||
              parseData?.error ||
              `HTTP ${parseResponse.status}`;
            throw new Error(errMsg);
          }

          if (!parseData?.data) {
            throw new Error('Missing parsed document data');
          }


          onFileParsed(parseData.data);
          localSuccess += 1;
          setSuccessCount(localSuccess);
        } catch (err) {
          localFailed.push({
            name: file.name,
            stage: 'parse',
            error: err?.message || 'Parse failed',
          });
          setFailedItems([...localFailed]);
        } finally {

          setCompletedCount((prev) => prev + 1);
        }
      }

      // 汇总提示
      if (localFailed.length === 0) {
        setMessage(`All files uploaded & parsed successfully (${localSuccess}/${files.length})`);
      } else if (localSuccess === 0) {
        setMessage(`All files failed (${localFailed.length}/${files.length}). See errors below.`);
      } else {
        setMessage(
          `Done: ${localSuccess} success, ${localFailed.length} failed (total ${files.length}). See errors below.`
        );
      }
    } catch (error) {

      setMessage('Unexpected error during batch upload');
    } finally {
      setIsUploading(false);
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
      <input type="file" multiple onChange={handleFileChange} />

      <button onClick={handleUpload} disabled={isUploading}>
        {isUploading ? 'Uploading...' : 'Upload File(s)'}
      </button>

      <p>{message}</p>

      {/* 进度条：按“已完成文件数 / 总文件数” */}
      {totalCount > 0 && (
        <div style={{ marginTop: 8 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>
              Progress: {completedCount}/{totalCount} ({progressPercent}%)
            </span>
            <span>Success: {successCount}</span>
          </div>

          <div
            style={{
              width: '100%',
              height: 10,
              border: '1px solid #ccc',
              borderRadius: 6,
              overflow: 'hidden',
              marginTop: 6,
            }}
          >
            <div
              style={{
                width: `${progressPercent}%`,
                height: '100%',
                background: '#4caf50',
                transition: 'width 200ms ease',
              }}
            />
          </div>
        </div>
      )}

      {/* 批量失败提示 */}
      {failedItems.length > 0 && (
        <div style={{ marginTop: 12 }}>
          <strong>Failed files:</strong>
          <ul style={{ marginTop: 6 }}>
            {failedItems.map((item, idx) => (
              <li key={`${item.name}-${idx}`}>
                <span style={{ fontWeight: 600 }}>{item.name}</span>
                {' — '}
                <span>
                  {item.stage === 'upload' ? 'Upload' : 'Parse'} failed: {item.error}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default FileUpload;

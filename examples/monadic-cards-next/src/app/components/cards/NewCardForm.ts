'use client';

import { useState, useRef } from 'react';
import type { ChangeEvent, FormEvent, DragEvent } from 'react';
import { MCardService } from '@/lib/mcard.service';
import { useRouter } from 'next/navigation';

export default function NewCardForm() {
  const router = useRouter();
  const [contentType, setContentType] = useState<'text' | 'file'>('text');
  const [textContent, setTextContent] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [type, setType] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const contentInputRef = useRef<HTMLTextAreaElement>(null);
  const mcardService = new MCardService();

  const handleDragEnter = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  };

  const handleDragLeave = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  };

  const handleDragOver = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files?.length > 0) {
      setSelectedFile(files[0]);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    setIsLoading(true);

    try {
      const formData = new FormData();

      if (contentType === 'text') {
        if (!textContent.trim()) {
          throw new Error('Please enter content');
        }
        formData.append('content', textContent);
      } else {
        if (!selectedFile) {
          throw new Error('Please select a file');
        }
        formData.append('file', selectedFile);
      }

      if (type) {
        formData.append('type', type);
      }

      const response = await fetch('/api/cards', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.error || 'Failed to create card');
      }

      router.push('/');
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-[400px] w-full">
      <div className="space-y-6">
        {error && (
          <div className="rounded-md bg-destructive/15 p-4 text-destructive" role="alert">
            <p className="font-bold">Error</p>
            <p>{error}</p>
          </div>
        )}

        <div className="space-y-2">
          <label className="text-sm font-medium">Content Type</label>
          <div className="flex space-x-4">
            <button
              type="button"
              onClick={() => {
                setContentType('text');
                setSelectedFile(null);
              }}
              className={`rounded-md px-4 py-2 text-sm font-medium ${
                contentType === 'text'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/90'
              }`}
            >
              Text Mode
            </button>
            <button
              type="button"
              onClick={() => {
                setContentType('file');
                setTextContent('');
              }}
              className={`rounded-md px-4 py-2 text-sm font-medium ${
                contentType === 'file'
                  ? 'bg-primary text-primary-foreground'
                  : 'bg-secondary text-secondary-foreground hover:bg-secondary/90'
              }`}
            >
              File Upload
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} encType="multipart/form-data" className="space-y-4">
          {contentType === 'text' ? (
            <div className="space-y-2">
              <label htmlFor="textContent" className="text-sm font-medium">
                Text Content
              </label>
              <textarea
                ref={contentInputRef}
                id="textContent"
                rows={10}
                value={textContent}
                onChange={(e) => setTextContent(e.target.value)}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                placeholder="Enter your text content here..."
              />
            </div>
          ) : (
            <div className="space-y-2">
              <label htmlFor="fileInput" className="text-sm font-medium">
                File Upload
              </label>
              <div
                className={`flex w-full items-center justify-center ${
                  isDragging ? 'border-primary' : 'border-input'
                }`}
                onDragEnter={handleDragEnter}
                onDragLeave={handleDragLeave}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
              >
                <label
                  htmlFor="fileInput"
                  className="flex h-32 w-full cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-input bg-background hover:bg-accent hover:bg-opacity-10"
                >
                  <div className="flex flex-col items-center justify-center pt-5 pb-6">
                    <p className="mb-2 text-sm text-muted-foreground">
                      {selectedFile ? selectedFile.name : 'Drop files here or click to upload'}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Supported file types: Images (JPEG, PNG, GIF, WebP), PDFs, and JSON
                    </p>
                  </div>
                  <input
                    id="fileInput"
                    type="file"
                    className="hidden"
                    onChange={handleFileChange}
                    accept="image/*,.pdf,application/json"
                    ref={fileInputRef}
                  />
                </label>
              </div>
            </div>
          )}

          <div className="mb-3">
            <label htmlFor="type" className="text-sm font-medium">
              Type
            </label>
            <input
              type="text"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
              id="type"
              value={type}
              onChange={(e) => setType(e.target.value)}
              placeholder="Optional: Specify card type"
            />
          </div>

          <div className="flex justify-end pt-4">
            <button
              type="submit"
              disabled={isLoading || (contentType === 'text' ? !textContent.trim() : !selectedFile)}
              className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {isLoading ? 'Creating...' : 'Create Card'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
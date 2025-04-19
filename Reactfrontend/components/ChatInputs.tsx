// ReactFrontend/components/ChatInput.tsx
import React, { useState, useRef, useEffect, KeyboardEvent } from 'react';

export interface ChatInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
}

const ChatInput: React.FC<ChatInputProps> = ({ onSend, disabled = false }) => {
  const [text, setText] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea height
  useEffect(() => {
    const ta = textareaRef.current;
    if (ta) {
      ta.style.height = 'auto';
      const newHeight = Math.min(ta.scrollHeight, 100);
      ta.style.height = `${newHeight}px`;
    }
  }, [text]);

  const handleSend = () => {
    if (disabled) return;
    const msg = text.trim();
    if (!msg) return;
    onSend(msg);
    setText('');
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-footer p-4 border-t border-gray-200">
      <div className="chat-input-container flex items-center space-x-2">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type here"
          rows={1}
          className="flex-1 resize-none overflow-hidden rounded border border-gray-300 p-2 focus:outline-none focus:ring"
        />
        <button
          type="button"
          onClick={handleSend}
          disabled={disabled || !text.trim()}
          className="px-4 py-2 rounded bg-[var(--primary-color)] text-white disabled:opacity-50"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatInput;

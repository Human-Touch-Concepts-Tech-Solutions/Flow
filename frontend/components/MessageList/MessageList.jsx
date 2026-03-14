"use client";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { useEffect, useRef, useState } from "react";
import {AiOutlineLoading3Quarters} from "react-icons/ai";
import { FiUser, FiCpu, FiFileText, FiCopy, FiCheck, FiDownload } from "react-icons/fi"; 
import copy from "copy-to-clipboard";
import FileIcon from "@/components/Icons/FileIcon";
import { 
  MessageContainer, 
  MessageListWrapper, 
  MessageBubble, 
  UserBubble, 
  AIBubble, 
  Avatar, 
  LoadingBubble,
  SpinningIcon
} from "./MessageListStyles";

// Improved CodeBlock with Language Header
const CodeBlock = ({ language, value }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    copy(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };


  return (
    <div style={{ 
      position: 'relative', 
      marginTop: '12px', 
      marginBottom: '12px',
      borderRadius: '8px',
      overflow: 'hidden',
      border: '1px solid #334155'
    }}>
      {/* Language Header Bar */}
      <div style={{ 
        backgroundColor: '#1e293b', 
        color: '#94a3b8', 
        padding: '6px 12px', 
        fontSize: '0.7rem', 
        textTransform: 'uppercase',
        fontWeight: 'bold',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        borderBottom: '1px solid #334155'
      }}>
        <span>{language || 'code'}</span>
        <button 
          onClick={handleCopy}
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            color: copied ? '#4ade80' : '#94a3b8',
            display: 'flex',
            alignItems: 'center',
            gap: '4px',
            fontSize: '0.7rem'
          }}
        >
          {copied ? <><FiCheck size={12} /> Copied</> : <><FiCopy size={12} /> Copy</>}
        </button>
      </div>

      {/* Code Area */}
      <SyntaxHighlighter 
        language={language} 
        style={oneDark} 
        PreTag="div"
        customStyle={{
          margin: 0,
          padding: '12px',
          fontSize: '0.85rem',
          backgroundColor: '#0f172a'
        }}
      >
        {value}
      </SyntaxHighlighter>
    </div>
  );
};

export default function MessageList({ messages = [], isLoading = false }) {
  const messagesEndRef = useRef(null);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [downloadingId, setDownloadingId] = useState(null);

  // Auto-scroll logic
  useEffect(() => {
    const timer = setTimeout(() => {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
    return () => clearTimeout(timer);
  }, [messages, isLoading]);

  const copyFullResponse = (text, index) => {
    copy(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleDownload = async (url, fileName, compositeId) => {
  setDownloadingId(compositeId); // Set the active download index
    try {
      const response = await fetch(url);
      const blob = await response.blob();
      const blobUrl = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = blobUrl;
      link.download = fileName;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(blobUrl);
    } catch (err) {
      console.error(err);
    } finally {
      setDownloadingId(null); // Reset
    }
  };

  return (
    <MessageContainer>
      <MessageListWrapper>
        {messages.map((msg, index) => (
          <MessageBubble key={index} $isUser={msg.role === "user"}>
              {msg.role !== "user" && <Avatar><FiCpu /></Avatar>}
            
            {msg.role === "user" ? (
              <UserBubble>
              {msg.files && msg.files.map((file, i) => (
  <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px', padding: '6px', background: '#ffffff', borderRadius: '6px' }}>
    <FileIcon fileName={file.name} />
    <span style={{ fontSize: '0.85rem', color: '#000000' }}>{file.name}</span>
  </div>
))}
                {msg.text && <p style={{ margin: 0 }}>{msg.text}</p>}
              </UserBubble>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', maxWidth: '75%', gap: '2px' }}>
                <AIBubble style={{ maxWidth: '100%', width: '100%' }}>
                  <ReactMarkdown
                    remarkPlugins={[remarkGfm]}
                    components={{
                      code({ node, inline, className, children, ...props }) {
                        const match = /language-(\w+)/.exec(className || "");
                        return !inline && match ? (
                          <CodeBlock 
                            language={match[1]} 
                            value={String(children).replace(/\n$/, "")} 
                          />
                        ) : (
                          <code className={className} {...props}>{children}</code>
                        );
                      },
                    }}
                  >
                    {msg.text}
                  </ReactMarkdown>
            {msg.files && msg.files.map((file, i) => (
  <div 
    key={i}
    onClick={() => handleDownload(file.url, file.name, `${index}-${i}`)}
    style={{ 
      display: 'flex', 
      alignItems: 'center', 
      gap: '8px', 
      marginBottom: '8px', 
      padding: '6px', 
      background: '#000000', 
      borderRadius: '6px',
      cursor: 'pointer' 
    }}
  >
    <FileIcon fileName={file.name} />
    <span style={{ fontSize: '0.85rem', color: '#ffffff' }}>{file.name}</span>
    
    {/* Show spinner if this file is downloading, otherwise show the download icon */}
    {downloadingId === i ? (
  <SpinningIcon>
     <AiOutlineLoading3Quarters size={17} style={{ marginLeft: 'auto', color: '#000000' }} />
  </SpinningIcon>
) : (
  <FiDownload size={17} style={{ marginLeft: 'auto', color: '#ffffff' }} />
)}
  </div>
))}          </AIBubble>
                
                {/* Full Response Copy Button */}
                <button 
                  onClick={() => copyFullResponse(msg.text, index)}
                  style={{
                    alignSelf: 'flex-start',
                    background: 'none',
                    border: 'none',
                    color: '#94a3b8',
                    fontSize: '0.7rem',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    cursor: 'pointer',
                    padding: '2px 0 8px 4px'
                  }}
                >
                  {copiedIndex === index ? (
                    <><FiCheck size={10} color="#049b3c" /> Copied Full Response</>
                  ) : (
                    <><FiCopy size={10} /> Copy response</>
                  )}
                </button>
              </div>
            )}

            {msg.role === "user" && <Avatar $isUser><FiUser /></Avatar>}
          </MessageBubble>
        ))}

        {isLoading && (
          <MessageBubble>
            <Avatar><FiCpu /></Avatar>
            <LoadingBubble><span></span><span></span><span></span></LoadingBubble>
          </MessageBubble>
        )}
        <div ref={messagesEndRef} style={{ height: '1px' }} />
      </MessageListWrapper>
    </MessageContainer>
  );
}
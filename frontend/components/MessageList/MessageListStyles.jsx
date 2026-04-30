import styled from "styled-components";
import { keyframes } from "styled-components";

export const MessageContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  padding: 80px 16px 80px 16px; 
  scroll-behavior: smooth;

  /* Responsive padding for smaller screens */
  @media (max-width: 768px) {
    padding: 60px 12px 70px 12px;
  }
`;

export const MessageListWrapper = styled.div`
  max-width: 900px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 16px;
`;

export const MessageBubble = styled.div`
  display: flex;
  align-items: flex-end;
  gap: 8px;
  width: 100%;
  justify-content: ${({ $isUser }) => ($isUser ? "flex-end" : "flex-start")};
`;

export const Avatar = styled.div`
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: ${({ $isUser }) => ($isUser ? "var(--lightblue)" : "#e2e8f0")};
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8rem;
  flex-shrink: 0;

  @media (max-width: 480px) {
    width: 24px;
    height: 24px;
    font-size: 0.7rem;
  }
`;

export const bubbleBase = `
  padding: 10px 14px;
  border-radius: 18px;
  font-size: 0.95rem;
  line-height: 1.5;
  position: relative;
  word-break: break-word;
  overflow-wrap: break-word;
  white-space: pre-wrap;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);

  /* Mobile adjustment: bubbles should be wider on small screens */
  @media (max-width: 768px) {
    max-width: 90% !important;
    font-size: 0.9rem;
  }
`;

export const UserBubble = styled.div`
  ${bubbleBase}
  background: var(--lightblue);
  font-family: var(--font-ubuntu-mono);
  color: white;
  border-bottom-right-radius: 4px;
  text-align: left;
  max-width: 75%;
`;

export const AIBubble = styled.div`
  ${bubbleBase}
  background: white;
  color: #000000;
  border: 1px solid #e5e7eb;
  border-bottom-left-radius: 4px;
  font-family: var(--font-ubuntu-mono);
  
  max-width: 100%;
  width: fit-content;
  min-width: 50px;

  /* TABLE RESPONSIVENESS FIX */
  table {
    display: block;
    width: 100%;
    overflow-x: auto; /* Essential for mobile */
    -webkit-overflow-scrolling: touch;
    border-collapse: collapse;
    margin: 15px 0;
    font-size: 0.85rem;
    border: 1px solid #e2e8f0;
  }

  th, td {
    border: 1px solid #e2e8f0;
    padding: 8px 12px;
    text-align: left;
    min-width: 100px; /* Prevents text from squishing too much */
  }

  th {
    background-color: #f8fafc;
    font-weight: 600;
  }

  tr:nth-child(even) {
    background-color: #f1f5f9;
  }

  /* BLOCKQUOTE */
  blockquote {
    border-left: 4px solid #cbd5e1;
    margin: 10px 0;
    padding-left: 16px;
    color: #475569;
    font-style: italic;
  }

  /* LISTS */
  ul, ol {
    margin: 10px 0;
    padding-left: 20px;
  }

  li {
    margin-bottom: 4px;
  }

  /* TEXT WRAPPING */
  p {
    margin: 0 0 12px 0;
    white-space: pre-wrap;
  }

  /* INLINE CODE */
  code {
    background: #f1f5f9;
    padding: 2px 5px;
    border-radius: 4px;
    font-family: var(--font-ubuntu-mono);
    font-size: 0.85em;
    color: #e11d48;
  }

  /* LINKS */
  a {
    color: #2563eb;
    text-decoration: none;
    font-weight: 500;
    transition: color 0.2s ease;
    word-break: break-all;

    &:hover {
      color: #1d4ed8;
      text-decoration: underline;
    }
  }

  p a, li a {
    color: #2563eb;
  }

  /* Ensure syntax highlighter containers don't overflow */
  pre {
    max-width: 100% !important;
    overflow-x: auto !important;
  }
`;

export const LoadingBubble = styled.div`
  width: fit-content;
  background: white;
  padding: 12px 16px;
  border-radius: 18px;
  border: 1px solid #e5e7eb;
  border-bottom-left-radius: 4px;
  display: flex;
  gap: 4px;

  span {
    width: 6px;
    height: 6px;
    background: #94a3b8;
    border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out;
  }
  span:nth-child(2) { animation-delay: 0.2s; }
  span:nth-child(3) { animation-delay: 0.4s; }

  @keyframes bounce {
    0%, 80%, 100% { transform: translateY(0); }
    40% { transform: translateY(-6px); }
  }
`;

const spinAnimation = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

export const SpinningIcon = styled.div`
  display: flex;
  align-items: center;
  justify-content: center;
  animation: ${spinAnimation} 1s linear infinite;
`;
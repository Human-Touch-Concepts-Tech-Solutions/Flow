import styled from "styled-components";
import { keyframes } from "styled-components";

export const MessageContainer = styled.div`
  flex: 1;
  overflow-y: auto;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  /* Reduced bottom padding from 150px to 80px */
  padding: 80px 16px 80px 16px; 
  scroll-behavior: smooth;
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
  align-items: flex-end; /* Align avatars to the bottom of the bubble */
  gap: 8px;
  width: 100%; /* The container takes full width... */
  
  /* ...but the alignment pushes the bubble to the side */
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
`;

export const bubbleBase = `
  padding: 10px 14px;
  border-radius: 18px;
  font-size: 0.95rem;
  line-height: 1.5; /* Slightly increased for readability */
  position: relative;
  max-width: 75%; 
  width: fit-content; 
  
  /* CRITICAL FIXES */
  word-break: break-word; /* Better than word-wrap for long strings/code */
  overflow-wrap: break-word;
  white-space: pre-wrap; /* Ensures spacing is preserved but text wraps */
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
`;
export const UserBubble = styled.div`
  ${bubbleBase}
  background: var(--lightblue);
  font-family: var(--font-ubuntu-mono);
  color: white;
  border-bottom-right-radius: 4px;
  /* Keeps text aligned left inside the right-aligned bubble */
  text-align: left; 
`;

export const AIBubble = styled.div`
  ${bubbleBase}
  background: white;
  color: #000000;
  border: 1px solid #e5e7eb;
  border-bottom-left-radius: 4px;
  font-family: var(--font-ubuntu-mono);

  /* Ensure no extra space at the bottom of the markdown */
  & > *:last-child {
    margin-bottom: 0 !important;
  }

  /* Fix for ReactMarkdown tags */
  p {
    margin: 0 0 10px 0; /* Add space between paragraphs */
  }

  p:last-child {
    margin-bottom: 0; /* Remove margin from the last paragraph to keep bubble tight */
  }

  ul, ol {
    margin: 5px 0;
    padding-left: 20px;
  }

  li {
    margin-bottom: 5px;
  }

  /* Fix for long code blocks or snippets */
  code {
    background: #f1f5f9;
    padding: 2px 4px;
    border-radius: 4px;
    font-size: 0.85rem;
  }

  pre {
    background: #e0e0e0;
    color: #f8fafc;
    padding: 10px;
    border-radius: 10px;
    overflow-x: auto; /* Adds horizontal scroll if code is too long */
    margin: 10px 0;
    width: 100%; /* Keeps code inside the bubble */
    
    code {
      background: transparent;
      padding: 0;
      color: inherit;
    }
  }
`;

export const LoadingBubble = styled.div`
  /* Loading bubble also needs to fit content */
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
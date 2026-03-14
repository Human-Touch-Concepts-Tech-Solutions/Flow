import styled, { keyframes } from "styled-components";

const spin = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

export const Container = styled.div`
width: 100%;
  flex-shrink: 0; /* Ensures the input doesn't get smaller as chat grows */
  display: flex;
  justify-content: center;
  padding: 8px;
  background: white;
  border-top: 1px solid #f1f5f9;
  
  /* REMOVE position: fixed */
  /* REMOVE bottom: 80px */
  /* REMOVE z-index: 100 */
`;

export const Content = styled.div`
  background: #ffffff;
  border: 1px solid #e2e8f0;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  border-radius: 16px;
  width: 100%;
  max-width: 768px; /* Standard AI chat width */
  transition: border 0.2s;

  &:focus-within {
    border-color: #2f496e;
  }
`;

export const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  padding: 12px;
  gap: 8px;

  .status-msg {
    color: #ff0000;
    font-size: 12px;
    text-align: center;
    margin-top: 4px;
    font-family: var(--font-ubuntu-mono);
  }
`;

export const InputWrap = styled.div`
  width: 100%;
`;

export const Input = styled.textarea`
  width: 100%;
  border: none;
  outline: none;
  padding: 8px;
  font-size: 16px;
  line-height: 1.5;
  color: #1e293b;
  max-height: 200px;
  background: transparent;
  resize: none;
  font-family: var(--font-geist-sans);

  &::placeholder {
    color: #94a3b8;
    font-style: italic;
    font-family: var(--font-ubuntu-mono);
  }
`;

export const PreviewSec = styled.div`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px 8px;

  .file-chip {
    display: flex;
    align-items: center;
    gap: 8px;
    background: #f1f5f9;
    padding: 6px 12px;
    border-radius: 8px;
    font-size: 13px;
    color: #334155;
    border: 1px solid #e2e8f0;
    font-family: var(--font-ubuntu-mono);

    span {
      max-width: 150px;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    button {
      background: none;
      border: none;
      color: #94a3b8;
      cursor: pointer;
      display: flex;
      &:hover { color: #ff0000; }
    }
  }
`;

export const Actions = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 8px;
  border-top: 1px solid #f1f5f9;
`;

export const InputButtons = styled.div`
  display: flex;
  gap: 4px;
`;

export const Funcbutton = styled.button`
  background: none;
  border: none;
  color: #64748b;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  font-size: 18px;
  transition: all 0.2s;

  &:hover {
    background: #f1f5f9;
    color: #2f496e;
  }
`;

export const Sendbutton = styled.button`
  background: ${props => props.disabled ? '#cbd5e1' : '#2f496e'};
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 8px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: transform 0.1s, background 0.2s;

  &:active:not(:disabled) {
    transform: scale(0.95);
  }

  .spin {
    animation: ${spin} 1s linear infinite;
  }
`;
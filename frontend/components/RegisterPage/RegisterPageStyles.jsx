import styled from "styled-components";

export const Background = styled.div`
  height: 100vh;
  width: 100vw;
  background: linear-gradient(135deg, #e0eafc, #cfdef3);
  display: flex;
  justify-content: center;
  align-items: center;
`;

export const Content = styled.div`
  background: white;
  padding: 40px;
  border-radius: 18px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.15);
  width: 100%;
  max-width: 420px;
  position: relative;
  font-family: var(--font-geist-sans);
  h2 { margin-bottom: 20px; text-align: center; color: #1e293b; }
`;

export const Logo = styled.img`
  width: 150px;
  display: block;
  margin: 0 auto 20px;
`;

export const StepIndicator = styled.p`
  text-align: center;
  font-size: 13px;
  color: var(--grey);
  margin-bottom: 15px;
`;

export const Row = styled.div`
  display: flex;
  gap: 10px;
`;

export const Input = styled.input`
  width: 100%;
  padding: 12px 16px;
  margin-bottom: 15px;
  border-radius: 10px;
  font-size: 14px;
  transition: all 0.2s ease-in-out;
  
  /* FIXED BORDER LOGIC */
  border: 1px solid ${({ $valid }) => {
    if ($valid === true) return "#22c55e"; // Success Green
    if ($valid === false) return "#ef4444"; // Error Red
    return "#e2e8f0"; // Default neutral grey
  }};

  &:focus {
    outline: none;
    border-color: #2f496e;
    box-shadow: 0 0 0 2px rgba(47, 73, 110, 0.1);
  }
`;

export const Button = styled.button`
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: none;
  background-color: #2f496e;
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
  font-family: var(--font-ubuntu-mono); 

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
  &:hover:not(:disabled) {
    opacity: 0.9;
  }
`;

export const GenderGroup = styled.div`
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
`;

export const GenderOption = styled.div`
  flex: 1;
  padding: 10px;
  text-align: center;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid ${({ $active }) => ($active ? "#2f496e" : "#e2e8f0")};
  background: ${({ $active }) => ($active ? "#2f496e" : "white")};
  color: ${({ $active }) => ($active ? "white" : "#475569")};
`;

export const PasswordHintList = styled.ul`
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  font-size: 11px;
  margin-bottom: 15px;
  padding-left: 0;
  list-style: none;
`;

export const PasswordHintItem = styled.li`
  color: ${({ $valid }) => ($valid ? "#16a34a" : "#94a3b8")}; /* Green if valid, grey if not */
  font-weight: ${({ $valid }) => ($valid ? "600" : "400")};
  display: flex;
  align-items: center;
  
  &:before {
    content: "${({ $valid }) => ($valid ? "✓" : "○")}";
    margin-right: 4px;
  }
`;

export const SuggestionBox = styled.div`
  position: absolute;
  background: white;
  width: 100%;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 10;
  top: 45px; /* Position below input */
  border: 1px solid #e2e8f0;
`;

export const SuggestionItem = styled.div`
  padding: 10px 16px;
  cursor: pointer;
  font-size: 14px;
  &:hover { background: #f1f5f9; }
  &:first-child { border-radius: 10px 10px 0 0; }
  &:last-child { border-radius: 0 0 10px 10px; }
`;
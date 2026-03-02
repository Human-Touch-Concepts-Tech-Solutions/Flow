import styled from "styled-components";

export const PageWrapper = styled.div`
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f9fafb;
`;


export const Card = styled.div`
  width: 100%;
  max-width: 420px;
  background: #ffffff;
  padding: 32px;
  border-radius: 12px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08);
`;


export const Title = styled.h1`
  font-size: 1.4rem;
  font-weight: 600;
  text-align: center;
  margin-bottom: 8px;
 
  font-family:var(--font-geist-sans);
  text-transform: capitalize;
  letter-spacing: 1px;
`;

export const Subtitle = styled.p`
  font-size: 0.9rem;
  color: #6b7280;
  text-align: center;
  margin-bottom: 24px;
  font-family:var(--font-ubuntu-mono);
`;



export const EmailText = styled.span`
  font-weight: 500;
  color: #111827;
`;

export const AdminInput = styled.input`
  width: 100%;
  height: 50px;
  padding: 0 15px;
  border-radius: 8px;
  border: 1px solid #d1d5db;
  font-size: 1.1rem;
  margin-bottom: 20px;
  text-align: center;
  font-family:var(--font-ubuntu-mono);
  letter-spacing: 4px;
  &:focus {
    border-color: var(--lightblue);
    outline: none;
    box-shadow: 0 0 0 2px var(--darkblue);
  }
`;


export const ErrorText = styled.p`
  color: #dc2626;
  font-size: 0.85rem;
  text-align: center;
  margin-bottom: 12px;
`;

export const Button = styled.button`
  width: 100%;
  height: 44px;
  background: var(--darkblue);
  color: white;
  border-radius: 8px;
  font-weight: 500;
  border: none;
  font-family:var(--font-ubuntu-mono);
  cursor: pointer;
  transition: 0.2s;
  &:hover { background: var(--lightblue); }
  &:disabled { opacity: 0.6; cursor: not-allowed; }
`;

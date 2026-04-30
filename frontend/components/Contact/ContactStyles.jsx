import styled from "styled-components";

export const ContactContainer = styled.div`
  min-height: 100vh;
  background: #f8fafc;
  padding: 4rem 2rem; 
  display: flex;
  justify-content: center;
  align-items: center;

  @media (max-width: 768px) {
    padding: 2rem 1rem;
  }
`;

export const ContactCard = styled.div`
  width: 100%;
  max-width: 1100px;
  background: white;
  border-radius: 20px;
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  overflow: hidden;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);

  @media (max-width: 900px) {
    grid-template-columns: 1fr;
  }
`;

export const Sidebar = styled.div`
  background: var(--darkblue); 
  color: white;
  padding: 3rem;
  display: flex;
  flex-direction: column;
  justify-content: space-between;

  h2 {
    font-size: 2rem;
    margin-bottom: 1rem;
    font-family: var(--font-geist-sans);
    letter-spacing:1px;
  }

  p {
    opacity: 0.9;
    line-height: 1.6;
    margin-bottom: 2rem;
    font-family: var(--font-geist-mono);
  }
  .back-link {
    background: transparent;
    border: none;
    color: white;
    cursor: pointer;
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 2rem;
    font-size: 0.9rem;
    opacity: 0.8;
    transition: opacity 0.2s;

    &:hover {
      opacity: 1;
    }
  }

  .copyright {
    font-size: 0.8rem;
    opacity: 0.7;
    font-family: var(--font-geist-mono);
  }

`;

export const InfoItem = styled.div`
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
  font-size: 1rem;
   font-family: var(--font-geist-mono);

  .icon {
    font-size: 1.2rem;
    color: #93c5fd;
  }
`;

export const FormSection = styled.div`
  padding: 3rem;

  h3 {
    font-size: 1.5rem;
    color: #1e293b;
    margin-bottom: 2rem;
     font-family: var(--font-geist-sans);
  }
`;

export const FormGrid = styled.form`
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
   font-family: var(--font-geist-mono);

  .full {
    grid-column: span 2;
  }

  @media (max-width: 600px) {
    grid-template-columns: 1fr;
    .full { grid-column: span 1; }
  }
`;

export const InputGroup = styled.div`
  display: flex;
  flex-direction: column;
  gap: 0.5rem;

  label {
    font-size: 0.875rem;
    font-weight: 600;
    color: #64748b;
  }

  input, textarea, select {
    padding: 0.75rem;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    font-size: 1rem;
    transition: all 0.2s;
    font-family: inherit;

    &:focus {
      outline: none;
      border-color: #2f496e;
      box-shadow: 0 0 0 3px rgba(47, 73, 110, 0.1);
    }
  }
`;

export const SubmitButton = styled.button`
  background: #2f496e;
  color: white;
  padding: 1rem 2rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, background 0.2s;
  margin-top: 1rem;
  font-family: var(--font-geist-mono);

  &:hover {
    background: #1e2e46;
    transform: translateY(-1px);
  }

  &:active {
    transform: translateY(0);
  }
`;
export const HeaderFlex = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;

  h3 {
    margin-bottom: 0 !important;
  }

  @media (max-width: 600px) {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
`;

export const ReturnBtn = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f1f5f9;
  color: #2f496e;
  border: 1px solid #e2e8f0;
  padding: 0.6rem 1rem;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  font-family: var(--font-geist-mono);

  &:hover {
    background: #e2e8f0;
    border-color: #cbd5e1;
  }
`;
"use client";
import styled from "styled-components";
import { FiX } from "react-icons/fi";

const PanelContainer = styled.div`
  /* Logic: If open, take 50% width. If closed, take 0% width. */
  width: ${props => props.$isOpen ? '50%' : '0px'};
  min-width: ${props => props.$isOpen ? '400px' : '0px'};
  height: 100vh;
  background: #ffffff;
  border-left: ${props => props.$isOpen ? '1px solid #e2e8f0' : 'none'};
  display: flex;
  flex-direction: column;
  z-index: 1000;
  
  /* Smoothly slide the width and the transform */
  transition: all 0.5s cubic-bezier(0.4, 0, 0.2, 1);
  transform: ${props => props.$isOpen ? 'translateX(0)' : 'translateX(100%)'};
  overflow: hidden; /* Crucial: hides content as it shrinks */

  @media (max-width: 1024px) {
    width: 100%;
    position: fixed;
    inset: 0;
    transform: ${props => props.$isOpen ? 'translateX(0)' : 'translateX(100%)'};
  }
`;

const ContentArea = styled.div`
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  min-width: 400px; /* Keeps content from squishing during animation */
  background: white; /* Ensure background is solid */
  color: #1e293b;
  .preview-html-root {
    font-family: inherit;
    line-height: 1.6;
    color: #1e293b;
  }
`;

export default function PreviewPanel({ data, onClose }) {
  const isOpen = !!data;

  return (
    <PanelContainer $isOpen={isOpen}>
      <div style={{ 
        padding: '15px', 
        borderBottom: '1px solid #e2e8f0', 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        background: '#fff',
        minWidth: '400px'
      }}>
        <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: '600' }}>
          {data?.title || "Preview"}
        </h3>
        <FiX 
          onClick={onClose} 
          style={{ cursor: 'pointer', fontSize: '1.2rem', color: '#64748b' }} 
        />
      </div>
      
      <ContentArea>
        {data && (
          <div 
            className="preview-html-root"
            /* FIXED: Now checks both htmlContent AND content */
            dangerouslySetInnerHTML={{ __html: data.htmlContent || data.content || "" }} 
          />
        )}
      </ContentArea>
    </PanelContainer>
  );
}
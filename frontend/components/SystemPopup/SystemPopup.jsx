"use client";
import styled, { keyframes } from "styled-components";
import { FiX } from "react-icons/fi";

const fadeIn = keyframes`
  from { opacity: 0; }
  to { opacity: 1; }
`;

const slideDown = keyframes`
  from { transform: translateY(-20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
`;

/* This is the invisible shield that blocks the chat interface */
const ModalOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(15, 23, 42, 0.5); /* Dimmed background */
  backdrop-filter: blur(3px); /* Optional: blurs the chat behind it */
  display: flex;
  align-items: flex-start; /* Keeps popup at the top */
  justify-content: center;
  padding-top: 50px;
  z-index: 10000; /* Higher than everything else */
  animation: ${fadeIn} 0.3s ease-out;
`;

const NotificationContainer = styled.div`
  position: relative; /* Changed from fixed because parent is now the overlay */
  width: 95%;
  max-width: 550px;
  background: #ffffff;
  color: #1e293b;
  border-radius: 12px;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
  border: 1px solid #e2e8f0;
  animation: ${slideDown} 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  overflow: hidden;
`;

const ContentWrapper = styled.div`
  padding: 24px;
  position: relative;
`;

const CloseButton = styled.button`
  position: absolute;
  top: 12px;
  right: 12px;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  color: #64748b;
  cursor: pointer;
  padding: 6px;
  border-radius: 8px;
  display: flex;
  transition: all 0.2s;
  &:hover {
    background: #fee2e2;
    color: #ef4444;
  }
`;

const DynamicHtmlArea = styled.div`
  width: 100%;
  .backend-html-root {
    font-size: 0.95rem;
    line-height: 1.6;
    
    button {
       /* Just in case you don't use the action-btn class, 
          this makes standard buttons look decent */
       cursor: pointer;
    }
  }
`;

export default function SystemPopup({ isOpen, data, onClose }) {
  // If not open or no content, don't show the overlay or the popup
  if (!isOpen || !data || !data.htmlContent) return null;

  return (
    /* The Overlay captures all clicks so the chat underneath is "dead" */
    <ModalOverlay onClick={(e) => e.stopPropagation()}>
      <NotificationContainer onClick={(e) => e.stopPropagation()}>
        <ContentWrapper>
          <CloseButton onClick={onClose} aria-label="Close notification">
            <FiX size={18} />
          </CloseButton>

          <DynamicHtmlArea>
            <div 
              className="backend-html-root"
              dangerouslySetInnerHTML={{ __html: data.htmlContent }} 
            />
          </DynamicHtmlArea>
        </ContentWrapper>
      </NotificationContainer>
    </ModalOverlay>
  );
}
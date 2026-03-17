"use client";
import styled from "styled-components";

const FullScreenOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: #ffffff;
  z-index: 20000; /* Higher than popups and panels */
  display: ${props => props.$isOpen ? 'flex' : 'none'};
  flex-direction: column;
`;

export default function PresentationView({ data, onClose }) {
  if (!data) return null;

  return (
    <FullScreenOverlay $isOpen={!!data}>
      {/* The backend sends the HTML/Canvas/SVG code to be rendered here */}
      <div 
        style={{ flex: 1, width: '100%' }}
        dangerouslySetInnerHTML={{ __html: data.htmlContent }} 
      />
    </FullScreenOverlay>
  );
}
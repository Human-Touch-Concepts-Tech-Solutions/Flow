"use client";
import styled from "styled-components";

export const Container = styled.footer`
  width: 100%;
  flex-shrink: 0;
  display: flex;
  justify-content: center;
  align-items: center;
  height: fit-content;
  padding: 8px;
 

  background: white;
  border-top: 1px solid #f0f0f0; /* Added a subtle line for professional separation */
`;

export const Content = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  width: 100%;
  max-width: 800px; /* Ensures the text doesn't stretch too wide on huge screens */
`;

export const DisclaimerText = styled.p`
  margin: 0;
  color: #666; /* Muted gray color for a professional look */
  font-size: clamp(0.75rem, 2vw, 0.9rem); /* Responsive font size */
  text-align: center;
  line-height: 1.5;
  font-family: sans-serif;
   font-family: var(--font-ubuntu-mono);
   letter-spacing: 0.05em;
  
  /* Smooth transition if you decide to add hover states later */
  transition: color 0.3s ease;

  &:hover {
    color: #333;
  }
`;
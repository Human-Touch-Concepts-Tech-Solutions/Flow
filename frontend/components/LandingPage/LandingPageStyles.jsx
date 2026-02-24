"use client";
import styled, { keyframes, css }  from "styled-components";





export const Background = styled.div`
  min-height: 100vh; /* Changed from height to min-height */
  width: 100%;
  display: flex;
  flex-direction: column; /* Stack Nav on top of Content */
  background: #ffffff;
  overflow-x: hidden;
`;

export const Content = styled.div`
flex: 1; /* Takes up remaining space */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center; /* Keeps content vertically centered in the remaining space */
  text-align: center;
  gap: clamp(10px, 2%, 18px);
  max-width: 520px;
  margin: 0 auto; /* Center horizontally */
  padding: 20px;
  
  /* On very small screens, add space at the bottom so it doesn't touch the edge */
  padding-bottom: 60px;

    h2 {
    color: #2f496e;
    font-family: var(--font-geist-sans);
    text-transform: uppercase;
    font-weight: 900;
    font-size: clamp(22px, 6vw, 28px);
    letter-spacing: 0.2rem;
    line-height: 1.3;
    margin-top: 5px;
  }

  p {
    color: #4b5563;
    font-family: var(--font-ubuntu-mono);
    font-size: clamp(16px, 4vw, 18px);
    font-style: italic;
    letter-spacing: 0.5px;
    line-height: 1.6;
    font-weight: 700;
  }
`;


export const Logo = styled.img`
  width: clamp(150px, 45%, 300px);
  height: auto;
  margin-bottom: clamp(5px, 5%, 10px);

`
;

export const CTA = styled.button`
  margin-top: clamp(5px, 5%, 15px);
  padding: 12px 28px;
  font-size: 16px;
  font-family: var(--font-ubuntu-mono);
  border-radius: 50px;
  border: none;
  cursor: pointer;

  display: flex;
  align-items: center;
  gap: 10px;

  background: #2f496e;
  color: #ffffff;
  transition: all 0.25s ease;

  &:hover {
    background: #1f3552;
    transform: translateY(-1px);
  }

  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }

  svg {
    font-size: 18px;
  }

`
;
// Add these to your existing imports
export const TopNav = styled.nav`
width: 100%;
  padding: 20px clamp(20px, 5%, 50px);
  display: flex;
  justify-content: flex-end;
  align-items: center;
  z-index: 10;
  /* No more position: absolute; this prevents lapping */

  @media (max-width: 480px) {
    padding: 15px 20px;
  }
`;

export const PricingLink = styled.button`
  background: transparent;
  border: 1px solid #e2e8f0;
  padding: 8px 20px;
  border-radius: 50px;
  color: #2f496e;
  font-family: var(--font-ubuntu-mono);
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s ease;

  &:hover {
    background: #f8fafc;
    border-color: #2f496e;
    transform: translateY(-1px);
  }

  svg {
    font-size: 16px;
  }

  @media (max-width: 480px) {
    font-size: 13px;
    padding: 6px 15px;
  }
`;
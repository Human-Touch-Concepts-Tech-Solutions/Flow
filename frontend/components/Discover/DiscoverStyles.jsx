"use client";
import styled, { keyframes } from "styled-components";

const slideDown = keyframes`
  from { transform: translateY(-100%); }
  to { transform: translateY(0); }
`;

export const DiscoverWrapper = styled.div`
  background: #ffffff;
  color: #2f496e;
`;

export const Nav = styled.nav`
  position: sticky;
  top: 0;
  background: white;
  border-bottom: 1px solid #e2e8f0;
  z-index: 100;
  padding: 15px 0;
`;

export const NavContainer = styled.div`
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  letter-spacing: 0.09rem;
`;

export const Logo = styled.img`height: 50px;`;

export const NavLinkContainer = styled.div`
  display: flex;
  gap: 30px;
  align-items: center;
  font-family: var(--font-geist-mono);
  @media (max-width: 768px) { display: none; }

  .get-started {
    background: #2f496e;
    color: white;
    padding: 8px 20px;
    border-radius: 50px;
    text-decoration: none;
      &:hover {
    background: #1f3552;
    transform: translateY(-1px);
  }
     
  }
`;

export const NavLink = styled.a`
  cursor: pointer;
  font-weight: 600;
  color: var( --darkblue);
  
  &:hover { color: #1f3552;transform: translateY(-1px); }
`;

export const MenuButton = styled.button`
  display: none;
  background: none;
  border: none;
  font-size: 24px;
  
  @media (max-width: 768px) { display: block; }
`;

export const MobileMenu = styled.div`
  position: absolute;
  top: 100%;
  left: 0;
  width: 100%;
  background: white;
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  box-shadow: 0 10px 15px rgba(0,0,0,0.05);
  animation: ${slideDown} 0.3s ease-out;
  
  .get-started {
    text-align: center;
    background: #2f496e;
    color: white;
    padding: 12px;
    border-radius: 8px;
    text-decoration: none;
  }
`;

export const Section = styled.section`
  max-width: 1100px;
  margin: 0 auto;
  padding: 80px 20px;
  
  /* Change props.light to props.$light */
  background: ${props => props.$light ? "#f8fafc" : "white"};
  
  h1, h2 { 
    font-weight: 600; 
    margin-bottom: 20px; 
    color: var(--darkblue); /* Ensuring visibility against the light background */
  font-family: var(--font-geist-sans);
  letter-spacing: 1px
  }
  
  p { 
    line-height: 1.6; 
    font-family: var(--font-geist-mono); 
  }
`;

export const Grid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-top: 40px;
  
`;

export const Card = styled.div`
  padding: 30px;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  transition: 0.3s;
  &:hover { border-color: #2f496e; }
  h3 { margin: 15px 0 10px; font-family: var(--font-geist-sans); }
 
`;

export const FAQItem = styled.div`
  margin-bottom: 30px;
  h4 { font-weight: 700; color: #2f496e;font-family: var(--font-geist-sans); }
`;

export const StartBox = styled.div`
  text-align: center;
  padding: 40px 20px;
  background: #2f496e;
  color: white;
  font-family: var(--font-geist-sans);
 
  .cta {
    display: inline-flex;
    align-items: center;
    gap: 10px;
    margin-top: 20px;
    background: white;
    color: #2f496e;
    padding: 15px 35px;
    border-radius: 50px;
    text-decoration: none;
    font-weight: 800;
    transition: 0.8s ease ;
     &:hover {
    padding: 15px 25px;
    transform: translateY(-2px);
  }
   
    
  }
`;
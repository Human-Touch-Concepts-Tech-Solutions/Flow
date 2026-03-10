"use client";
import styled from "styled-components";

export const PageContainer = styled.div`
  max-width: 800px;
  margin: 40px auto;
  padding: 0 20px;
font-family: var(--font-geist-sans);
`;

export const TitleSection = styled.div`
  margin-bottom: 40px;
  h1 { font-size: 2rem; color: #000000; margin: 0; }
  p { color: #666; margin-top: 8px; }
`;

export const Section = styled.section`
  margin-bottom: 40px;
`;

export const SectionTitle = styled.h2`
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 1.1rem;
  /* Use the $ prefix here */
  color: ${props => props.$danger ? "#d93025" : "#444"}; 
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
`;

export const SettingCard = styled.button`
  width: 100%;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px;
  background: white;
  border: 1px solid #f0f0f0;
  border-radius: 12px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;

  &:hover {
    background: #fafafa;
    border-color: #ddd;
    transform: translateY(-1px);
  }

  svg { color: #888; }
`;

export const IconWrapper = styled.div`
  width: 40px;
  height: 40px;
  background: #f0f7ff;
  border-radius: 10px;
  display: flex;
  justify-content: center;
  align-items: center;
  svg { color: var(--lightblue) !important; font-size: 1.2rem; }
`;

export const SettingInfo = styled.div`
  flex: 1;
  h3 { font-size: 1rem; margin: 0; color: #333; }
  p { font-size: 0.85rem; color: #777; margin: 4px 0 0; }
`;

export const Toggle = styled.div`
  width: 44px;
  height: 24px;
  background: ${props => props.$active ? "var(--lightblue)" : "#ccc"}; // Added $
  border-radius: 20px;
  position: relative;
  cursor: pointer;
  transition: background 0.3s;

  &::after {
    content: "";
    position: absolute;
    width: 18px;
    height: 18px;
    background: white;
    border-radius: 50%;
    top: 3px;
    left: ${props => props.$active ? "23px" : "3px"}; // Added $
    transition: left 0.3s;
  }
`;

export const DangerCard = styled.div`
  width: 100%;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px;
  background: white;
  border: 1px solid #fce8e6;
  border-radius: 12px;
  margin-bottom: 12px;
  transition: all 0.2s;

  &:hover { 
    background: #fff8f7; 
    border-color: #f5c2c1; 
  }

  button {
    background: #d93025;
    color: white;
    border: none;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
    &:hover { background: #b21f16; }
  }
`;

export const LoadingWrapper = styled.div`
  display: flex;
  justify-content: center;
  padding: 100px;
`;
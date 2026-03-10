"use client";
import styled from "styled-components";

export const PageContainer = styled.div`
  max-width: 900px;
  margin: 40px auto;
  padding: 0 20px;
  animation: fadeIn 0.5s ease;

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
  }
`;

export const ProfileHeader = styled.div`
  display: flex;
  align-items: center;
  gap: 25px;
  padding-bottom: 30px;
  border-bottom: 1px solid #eee;
  margin-bottom: 40px;

  @media (max-width: 600px) {
    flex-direction: column;
    text-align: center;
  }
`;

export const AvatarCircle = styled.div`
  width: 100px;
  height: 100px;
  background: linear-gradient(135deg, var(--lightblue),var(--darkblue));
  color: white;
  border-radius: 50%;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 3rem;
  font-weight: bold;
  box-shadow: 0 4px 12px rgba(0, 123, 255, 0.2);
  font-family: var(--font-geist-sans); 
  letter-spacing: 0.2rem;
`;

export const HeaderInfo = styled.div`
  flex: 1;
   font-family: var(--font-geist-sans); 
  h1 { margin: 0; font-size: 1.8rem; color: #333; text-transform: capitalize; }
  p { margin: 5px 0 0; color: rgb(136, 136, 136); font-size: 0.9rem; letter-spacing: 1px; text-transform: uppercase; } 
`;

export const EditButton = styled.button`
  display: flex;
  align-items: center;
  gap: 8px;
font-family: var(--font-geist-sans); 
  padding: 10px 20px;
  border-radius: 8px;
  border: 1px solid #ddd;
  background: white;
  cursor: pointer;
  transition: all 0.2s;
  &:hover { background: #f8f9fa; border-color: #bbb; }
`;

export const InfoGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 25px;
`;

export const InfoCard = styled.div`
  background: #fff;
  padding: 20px;
  border-radius: 12px;
  border: 1px solid #f0f0f0;
font-family: var(--font-geist-sans); 

  label {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 0.85rem;
    color: #666;
    margin-bottom: 10px;
  }

  input {
    width: 100%;
    padding: 10px;
    border: 1px solid transparent;
    background: #f9f9f9;
    border-radius: 6px;
    font-size: 1rem;
    color: #333;
    &:focus { border-color: #007bff; outline: none; background: white; }
    &:disabled { cursor: not-allowed; background: #f5f5f5; }
  }

  small { color: #aaa; font-size: 0.75rem; margin-top: 5px; display: block; }
`;

export const Badge = styled.span`
  padding: 5px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
  background: ${props => props.active ? "#e6f4ea" : "#fce8e6"};
  color: ${props => props.active ? "#1e7e34" : "#d93025"};
`;

export const LoadingWrapper = styled.div`
  display: flex;
  justify-content: center;
  padding: 100px;
  color: #666;
`;
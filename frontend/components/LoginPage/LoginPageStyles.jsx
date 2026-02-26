"use client";

import styled from "styled-components";

export const Background = styled.main`
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: radial-gradient(
    circle at center,
    #ffffff 0%,
    #f4f6fa 40%,
    #e6e9f0 100%
  );
`;

export const Content = styled.div`
  width: 100%;
  max-width: 420px;
  padding: 40px 30px;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.08);

  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
  text-align: center;


  h2{
  
    color: var(--darkblue);
    letter-spacing: 0.2rem;
    font-family: var(--font-geist-sans);
  }
  p{
 
    font-family: var(--font-ubuntu-mono);
  }
`;

export const Logo = styled.img`
  width: 150px;
  height: auto;
  margin-bottom: 8px;
`;

export const Input = styled.input`
  width: 100%;
  padding: 12px 14px;
  border-radius: 10px;
  border: 1px solid #d1d5db;
  font-size: 14px;
  font-family: var(--font-geist-mono);
  outline: none;

  &:focus {
    border-color: var(--darkblue);
  }
`;

export const Button = styled.button`
  width: 100%;
  margin-top: 10px;
  padding: 12px;
  border-radius: 10px;
  border: none;
  cursor: pointer;
  font-family: var(--font-ubuntu-mono);

  display: flex;
  justify-content: center;
  align-items: center;
  gap: 10px;

  background: var(--darkblue);
  color: #ffffff;
  font-size: 15px;

  &:hover {
    background: #1f3552;
  }

  &:disabled {
    opacity: 0.7;
    cursor: not-allowed;
  }
`;

export const BackLink = styled.span`
  margin-top: 12px;
  font-size: 14px;
  color: var(--darkblue);
  cursor: pointer;
  font-family: var(--font-ubuntu-mono);

  &:hover {
    text-decoration: underline;
  }
`;

export const Divider = styled.div`
  width: 100%;
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--darkblue);
  font-size: 14px;
  font-family: var(--font-ubuntu-mono);
  margin: 10px 0;

  &::before,
  &::after {
    content: "";
    flex: 1;
    height: 1px;
    background: #e2e8f0;
  }
`;

export const OAuthButton = styled.button`
  width: 100%;
  padding: 12px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  cursor: pointer;
  font-family: var(--font-ubuntu-mono);
  text-transform: capitalize;

  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;

  background: ${({ $apple }) => ($apple ? "#000000" : "#ffffff")};
  color: ${({ $apple }) => ($apple ? "#ffffff" : "#111827")};

  font-size: 14px;
  transition: all 0.25s ease;

  &:hover {
    background: ${({ $apple }) => ($apple ? "#111111" : "#f8fafc")};
  }

  svg {
    font-size: 18px;
  }
`;

export const SignupText = styled.p`
  margin-top: 16px;
  font-size: 14px;
  color: var(--darkblue);

  span {
    margin-left: 6px;
    color: var(--darkblue);
    cursor: pointer;
    font-weight: 500;

    &:hover {
      text-decoration: underline;
    }
  }
`;

export const ForgotPasswordLink = styled.span`
  width: 100%;
  text-align: right;
  font-size: 13px;
  color: #ff0202;
  cursor: pointer;
  margin-top: -6px;
  font-family: var(--font-ubuntu-mono);
  text-transform: capitalize;

  &:hover {
    text-decoration: underline;
    color: var(--darkblue);
  }
`;

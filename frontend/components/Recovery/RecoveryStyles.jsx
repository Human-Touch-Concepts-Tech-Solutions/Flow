import styled, {keyframes} from "styled-components";
import { FiRefreshCw } from "react-icons/fi";

export const Background = styled.div`
  min-height: 100vh;
    background: radial-gradient(
    circle at center,
    #ffffff 0%,
    #f4f6fa 40%,
    #e6e9f0 100%
  );
  display: flex; align-items: center; justify-content: center; padding: 20px;
`;

export const Card = styled.div`
  background: white; border-radius: 16px; padding: 40px 32px;
  width: 100%; max-width: 420px; box-shadow: 0 20px 40px rgba(0, 0, 0, 0.377);
`;

export const Header = styled.div` display: flex; align-items: center; margin-bottom: 24px; font-family: var(--font-geist-sans); letter-spacing: 1px; color: var(--darkblue); `;

export const BackButton = styled.button`
  background: none; border: none; font-size: 1.5rem; cursor: pointer; color: #4a5568;
  &:hover { color: #000000; }
`;

export const Title = styled.h1` font-size: 1.75rem; font-weight: 700; color: #1a202c; margin: 0; `;

export const Subtitle = styled.p` color: #718096; text-align: center; margin-bottom: 32px;  font-family: var(--font-ubuntu-mono);`;

export const InputGroup = styled.div` margin-bottom: 24px; position: relative; `;

export const Label = styled.label` display: block; margin-bottom: 8px; font-weight: 500; color: #2d3748; font-family: var(--font-geist-sans);`;

export const Input = styled.input`
  width: 100%; padding: 14px 16px; border: 1px solid #e2e8f0; border-radius: 12px;
  &:focus { border-color: var(--darkblue); outline: none; box-shadow: 0 0 0 3px rgba(102,126,234,0.1); }
`;

export const SubmitButton = styled.button`
  width: 100%; padding: 14px; background: var(--lightblue); color: white; border: none;
  border-radius: 12px; font-weight: 600; cursor: pointer;
  &:disabled { background: #cbd5e0; cursor: not-allowed; }
`;

export const ErrorMessage = styled.p` color: #e53e3e; font-size: 0.9rem; text-align: center; margin-top: 10px; font-family:var(--font-geist-sans); `;

export const SuccessMessage = styled.p` color: #38a169; font-size: 0.9rem; text-align: center; margin-bottom: 10px; font-family: var(--font-geist-sans);`;

export const FooterLink = styled.p`
  text-align: center; margin-top: 24px; color: var(--lightblue);  cursor: pointer; font-weight: 500; font-family: var(--font-ubuntu-mono);
  &:hover { text-decoration: underline; }
`;

export const PasswordToggle = styled.button`
  position: absolute; right: 16px; top: 14px; background: none; border: none; color: #718096; cursor: pointer;
`;

export const PasswordHintList = styled.ul` list-style: none; padding: 0; margin-top: 8px; `;

export const PasswordHintItem = styled.li`
  font-size: 0.8rem; color: ${props => props.$valid ? "#38a169" : "#718096"};
  &:before { content: "${props => props.$valid ? "✓ " : "○ "}"; }
`;

export const LogoWrapper = styled.div`
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
  img {
    width: 100px;
    height: auto;
  }
`;

export const TimerText = styled.p`
  font-size: 0.85rem;
  color: ${props => props.$warning ? "#e53e3e" : "#718096"};
  text-align: center;
  margin-top: 10px;
  font-family: var(--font-ubuntu-mono);
`;

const rotate = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

// Update your icon usage or add this class to your global styles
// Or simply use it in the Resend button's icon:
export const StyledResendIcon = styled(FiRefreshCw)`
  &.spin {
    animation: ${rotate} 1s linear infinite;
  }
`;
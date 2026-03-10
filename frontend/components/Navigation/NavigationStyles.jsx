import styled, { keyframes } from "styled-components";

const spin = keyframes`
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
`;

export const NavbarContainer = styled.nav`
  position: sticky; /* Sticky is safer than relative for top bars */
  top: 0;
  flex-shrink: 0;
  width: 100%;
  height: 70px;
  background: #ffffff;
  border-bottom: 1px solid #f3f4f6;
  z-index: 1000;
`;
export const NavbarContent = styled.div`
  max-width: 1400px;
  margin: 0 auto;
  padding: 0 20px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
`;

export const NavRightGroup = styled.div`
  display: flex;
  align-items: center;
  gap: 15px;
  flex: 1;
  justify-content: space-between;

  @media (min-width: 1024px) {
    justify-content: flex-end;
    gap: 25px;
  }
`;

export const LogoWrapper = styled.div`
  cursor: pointer;
  position: relative;
  width: 140px;
  height: 40px;

  &.desktop-only {
    display: none;
    @media (min-width: 1024px) { display: block; }
  }
`;

export const StatusBadge = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f0f9ff;
  color: var(--darkblue);
  padding: 6px 14px;
  border-radius: 50px;
  font-size: 0.8rem;
  font-weight: 600;
  font-family:var(--font-geist-sans);

  .spin-icon { animation: ${spin} 2s linear infinite; }
  
  @media (max-width: 500px) {
    span { display: flex; }
  }
`;

export const CreditsDisplay = styled.div`
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f0f9ff;
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--darkblue);
  font-family: var(--font-geist-sans);

  .coin-icon { color: var(--darkblue); font-size: 1.1rem; }
  strong {color: var(--darkblue); font-size: 0.9rem; }
`;

export const AddCreditsButton = styled.button`
  background: var(--darkblue);
  color: white;
  border: none;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  font-weight: bold;
  &:hover { background: #1f3552;; }
`;

/* PROFILE DROPDOWN DESIGN */
export const ProfileSection = styled.div`
  position: relative;
  font-family: var(--font-geist-sans);
  display: none;
  @media (min-width: 1024px) {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 5px 10px;
    border-radius: 10px;
    cursor: pointer;
    &:hover { background: #f9fafb; }
  }
`;

export const ProfileAvatar = styled.div`
  width: 35px;
  height: 35px;
  border-radius: 50%;
  background: var(--gray);
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--darkblue);
  border: 1px solid var(--darkblue);
 
`;

export const ProfileName = styled.span`
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--darkblue);
   text-transform: capitalize;
`;

export const ProfileDropdown = styled.div`
  position: absolute;
  top: 55px;
  right: 0;
  width: 220px;
  background: white;
  border: 1px solid #f3f4f6;
  border-radius: 12px;
  box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
  padding: 10px;
  z-index: 1000;

  .dropdown-header {
    padding: 10px;
    display: flex;
    flex-direction: column;
    strong { font-size: 0.9rem; color: #000000;  text-transform: capitalize;}
    span { font-size: 0.75rem; color: #4d535e; text-transform: capitalize; letter-spacing: 0.05em; margin-top: 2px;font-weight: 600;   }
  }

  hr { border: 0; border-top: 1px solid #f3f4f6; margin: 8px 0; }
`;

export const DropdownItem = styled.div`
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px;
  border-radius: 8px;
  font-size: 0.9rem;
  color: #4b5563;
  &:hover { background:#f0f9ff; color: #111827; }
  &.logout { color: red; &:hover { background: #ff00001c; } }
`;

/* MOBILE SIDEBAR */
export const MobileMenuButton = styled.button`
  background: none;
  border: none;
  font-size: 1.6rem;
  cursor: pointer;
  display: flex;
  color: #374151;
  
  @media (min-width: 1024px) { display: none; }
  
`;

export const NotificationIcon = styled.div`
  position: relative;
  cursor: pointer;
  display: flex;
  align-items: center;
  font-size: 1.5rem;
  color: var(--darkblue);
  padding: 5px;
  
  &:hover { color: var(--grey); }
`;

export const NotificationBadge = styled.span`
  position: absolute;
  top: -2px;
  right: -2px;
  background: #ff0000; /* Red color */
  color: white;
  font-size: 0.70rem;
  font-weight: bold;
  width: 17px;
  height: 17px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid white;
 font-family: var(--font-geist-sans);
`;

export const MobileMenuOverlay = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(2px);
  z-index: 1500;
  display: ${props => (props.$visible ? "block" : "none")};
`;

export const MobileMenu = styled.div`
  position: fixed;
  top: 0;
  left: 0;
  height: 100vh;
  width: 280px;
  background: white;
  z-index: 1600;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 20px;
  font-family: var(--font-geist-sans);
  transition: transform 0.3s ease-in-out;
  transform: ${props => (props.$isOpen ? "translateX(0)" : "translateX(-100%)")};

  .sidebar-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    border-bottom: 1px solid #f3f4f6;
    padding-bottom: 20px;
  }

  .close-btn {
    background: #f9fafb;
    border: none;
    width: 35px;
    height: 35px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.2rem;
    cursor: pointer;
  }

  .mobile-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 15px;
    border-radius: 10px;
    font-weight: 500;
    color: #374151;
    margin-bottom: 5px;
    cursor: pointer;
    &:hover { background: #f3f4f6; }
    &.logout { color: red; border-top: 1px solid #f3f4f6; margin-top: 10px; }
  }
`;

export const MobileUserInfo = styled.div`
  padding: 16px 20px;
  border-top: 1px solid ${({ theme }) => theme.borderColor || '#eee'};
  margin-top: auto; /* Pushes it to the bottom of the menu */
  display: flex;
  flex-direction: column;
  gap: 4px;
`;

export const MobileUserLabel = styled.span`
  font-size: 0.75rem;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  font-weight: 600;
`;

export const MobileUserName = styled.span`
  font-size: 0.95rem;
  color: #1e293b;
  font-weight: 500;
`;
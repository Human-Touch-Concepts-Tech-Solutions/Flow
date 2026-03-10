"use client";

import { useState } from "react";
import { useUser } from "@/providers/UserProvider";
import { authenticatedFetch } from "@/lib/api";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { FiMenu, FiX, FiLogOut, FiUser, FiSettings, FiDollarSign, FiCreditCard, FiBell } from "react-icons/fi";
import { AiOutlineLoading3Quarters } from "react-icons/ai";
import { FaCoins } from "react-icons/fa6";
import {
  NavbarContainer,
  NavbarContent,
  LogoWrapper,
  StatusBadge,
  CreditsDisplay,
  ProfileSection,
  ProfileAvatar,
  ProfileName,
  ProfileDropdown,
  DropdownItem,
  MobileMenuButton,
  MobileMenu,
  AddCreditsButton,
  NavRightGroup,
  MobileMenuOverlay,
  MobileUserInfo,
  MobileUserLabel,
  MobileUserName,
  NotificationIcon, // New
  NotificationBadge // New
} from "./NavigationStyles";

export default function Navigation() {
  const router = useRouter();
  const { user, isLoading } = useUser();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  
  // Replace this with real data from your user object later
  const notificationCount = 10; // Placeholder for unread notifications count

  const credits = user?.credits?.balance ?? 0;
  const userName = user ? `${user.first_name} ${user.last_name || ""}` : "User";
  const planName = user?.subscription?.plan ?? "Free Account";

  const handleLogout = async () => {
    try {
      await authenticatedFetch("/auth/logout", { method: "POST" });
    } catch (err) {
      console.error("Server-side logout failed", err);
    } finally {
      localStorage.removeItem("access_token");
      localStorage.removeItem("refresh_token");
      router.push("/account/login");
    }
  };

  const goToBilling = () => {
    router.push("/account/portal/billing");
    setIsMobileMenuOpen(false);
  };

  return (
    <NavbarContainer>
      <NavbarContent>
        <LogoWrapper 
  className="desktop-only" 
  onClick={() => {
    // Option A: Just refresh the server components
    router.push("/account/portal/ChatInterface"); 
    
    // Option B: Full hard reload if you really need to wipe state
    // window.location.reload(); 
  }}
>
  <Image src="/logo.svg" alt="Logo" fill style={{ objectFit: "contain" }} priority />
</LogoWrapper>

        <NavRightGroup>
          <MobileMenuButton onClick={() => setIsMobileMenuOpen(true)}>
            <FiMenu />
          </MobileMenuButton>

          {/* New Notification Icon */}
          

          <StatusBadge>
            <AiOutlineLoading3Quarters className="spin-icon" />
            <span>In Production</span>
          </StatusBadge>

          

          <CreditsDisplay title="Click + to refill credits">
            <FaCoins className="coin-icon" />
            <strong>{isLoading ? "---" : credits.toLocaleString()}</strong>
            <AddCreditsButton onClick={goToBilling}>+</AddCreditsButton>
          </CreditsDisplay>

          <NotificationIcon onClick={() => router.push("/account/notifications")}>
            <FiBell />
            {notificationCount > 0 && <NotificationBadge>{notificationCount}</NotificationBadge>}
          </NotificationIcon>

          <ProfileSection
            onMouseEnter={() => setIsProfileOpen(true)}
            onMouseLeave={() => setIsProfileOpen(false)}
          >
            <ProfileAvatar>
              <FiUser size={20} />
            </ProfileAvatar>
            <ProfileName>{isLoading ? "Loading..." : userName}</ProfileName>

            {isProfileOpen && !isLoading && (
              <ProfileDropdown>
                <div className="dropdown-header">
                  <strong>{userName}</strong>
                  <span>{planName}</span>
                </div>
                <hr />
                <DropdownItem onClick={goToBilling}>
                  <FiCreditCard /> <span>Billing & Credits</span>
                </DropdownItem>
                <DropdownItem onClick={() => router.push("/account/portal/profile")}>
                  <FiUser /> <span>Profile</span>
                </DropdownItem>
                <DropdownItem onClick={() => router.push("/account/portal/settings")}>
                  <FiSettings /> <span>Settings</span>
                </DropdownItem>
                <DropdownItem onClick={handleLogout} className="logout">
                  <FiLogOut /> <span>Logout</span>
                </DropdownItem>
              </ProfileDropdown>
            )}
          </ProfileSection>
        </NavRightGroup>
      </NavbarContent>

      <MobileMenuOverlay $visible={isMobileMenuOpen} onClick={() => setIsMobileMenuOpen(false)} />
      <MobileMenu $isOpen={isMobileMenuOpen}>
        {/* ... Mobile Menu content ... */}
        <div className="menu-top-section">
          <div className="sidebar-header">
            <div style={{ position: 'relative', width: '120px', height: '30px' }}>
              <Image src="/logo.svg" alt="Logo" fill style={{ objectFit: "contain" }} />
            </div>
            <button className="close-btn" onClick={() => setIsMobileMenuOpen(false)}>
              <FiX />
            </button>
          </div>
        </div>

        <div className="menu-bottom-section">
          <div className="mobile-item" onClick={() => { router.push("/account/notifications"); setIsMobileMenuOpen(false); }}>
            <FiBell /> Notifications ({notificationCount})
          </div>
          <div className="mobile-item" onClick={goToBilling}>
            <FiDollarSign /> Billing & Credits
          </div>
          <div className="mobile-item" onClick={() => { router.push("/account/portal/profile"); setIsMobileMenuOpen(false); }}>
            <FiUser /> Profile
          </div>
          <div className="mobile-item" onClick={() => { router.push("/account/portal/settings"); setIsMobileMenuOpen(false); }}>
            <FiSettings /> Settings
          </div>
          <div className="mobile-item logout" onClick={handleLogout}>
            <FiLogOut /> Logout
          </div>
          
          {user && (
            <MobileUserInfo>
              <MobileUserLabel>Logged in as</MobileUserLabel>
              <MobileUserName>{userName}</MobileUserName>
            </MobileUserInfo>
          )}
        </div>
      </MobileMenu>
    </NavbarContainer>
  );
}
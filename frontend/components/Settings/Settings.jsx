import React, { useState } from 'react';
import { useUser } from '@/providers/UserProvider';
import { FiLock, FiBell, FiShield, FiMoon, FiTrash2, FiChevronRight } from 'react-icons/fi';
import * as S from './SettingsStyles';

export default function Settings() {
  const { user, loading } = useUser();
  const [notifications, setNotifications] = useState(true);
  const [darkMode, setDarkMode] = useState(false);

  if (loading) return <S.LoadingWrapper>Loading Settings...</S.LoadingWrapper>;

  return (
    <S.PageContainer>
      <S.TitleSection>
        <h1>Settings</h1>
        <p>Manage your security and application preferences.</p>
      </S.TitleSection>

      <S.Section>
        <S.SectionTitle><FiShield /> Security</S.SectionTitle>
        <S.SettingCard onClick={() => console.log("Change Password Clicked")}>
          <S.IconWrapper><FiLock /></S.IconWrapper>
          <S.SettingInfo>
            <h3>Change Password</h3>
            <p>Update your password to keep your account secure.</p>
          </S.SettingInfo>
          <FiChevronRight />
        </S.SettingCard>
      </S.Section>

      <S.Section>
        <S.SectionTitle><FiBell /> Preferences</S.SectionTitle>
        <S.SettingCard as="div">
          <S.IconWrapper><FiBell /></S.IconWrapper>
          <S.SettingInfo>
            <h3>In-App Notifications</h3>
            <p>Receive alerts about credits and task updates.</p>
          </S.SettingInfo>
          <S.Toggle 
            $active={notifications} 
            onClick={() => setNotifications(!notifications)} 
            />
        </S.SettingCard>

        <S.SettingCard as="div">
          <S.IconWrapper><FiMoon /></S.IconWrapper>
          <S.SettingInfo>
            <h3>Dark Mode</h3>
            <p>Switch between light and dark themes (Coming Soon).</p>
          </S.SettingInfo>
          <S.Toggle 
                $active={darkMode} 
                onClick={() => setDarkMode(!darkMode)} 
                />
        </S.SettingCard>
      </S.Section>

      <S.Section>
        <S.SectionTitle $danger><FiTrash2 /> Danger Zone</S.SectionTitle>
        <S.DangerCard>
    <S.SettingInfo>
      <h3>Delete Account</h3>
      <p>Permanently remove your account and all associated data. This action cannot be undone.</p>
    </S.SettingInfo>
    {/* This is now perfectly valid because the parent is a div */}
    <button onClick={() => console.log("Account deletion process started")}>
      Delete
    </button>
  </S.DangerCard>
      </S.Section>
    </S.PageContainer>
  );
}
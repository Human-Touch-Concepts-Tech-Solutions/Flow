import React, { useState } from 'react';
import { useUser } from '@/providers/UserProvider'; // Adjust path to your provider
import { FiUser, FiMail, FiBriefcase, FiEdit2, FiCheck } from 'react-icons/fi';
import * as S from './ProfileStyles';

export default function Profile() {
  const { user, loading } = useUser();
  const [isEditing, setIsEditing] = useState(false);

  if (loading) return <S.LoadingWrapper>Loading Profile...</S.LoadingWrapper>;
  if (!user) return <S.LoadingWrapper>No user data found.</S.LoadingWrapper>;

  return (
    <S.PageContainer>
      <S.ProfileHeader>
        <S.AvatarCircle>
          {user.first_name?.charAt(0)}{user.last_name?.charAt(0)}
        </S.AvatarCircle>
        <S.HeaderInfo>
          <h1>{user.first_name} {user.last_name}</h1>
          <p>{user.role?.toUpperCase()} ACCOUNT</p>
        </S.HeaderInfo>
        <S.EditButton onClick={() => setIsEditing(!isEditing)}>
          {isEditing ? <><FiCheck /> Save</> : <><FiEdit2 /> Edit Profile</>}
        </S.EditButton>
      </S.ProfileHeader>

      <S.InfoGrid>
        <S.InfoCard>
          <label><FiUser /> Full Name</label>
          <input 
            type="text" 
            defaultValue={`${user.first_name} ${user.last_name}`} 
            disabled={!isEditing} 
          />
        </S.InfoCard>

        <S.InfoCard>
          <label><FiMail /> Email Address</label>
          <input type="email" defaultValue={user.email} disabled />
          <small>Email cannot be changed</small>
        </S.InfoCard>

        <S.InfoCard>
          <label><FiBriefcase /> Profession</label>
          <input 
            type="text" 
            defaultValue={user.profession || "Not Specified"} 
            disabled={!isEditing} 
          />
        </S.InfoCard>

        <S.InfoCard>
          <label>Account Status</label>
          <S.Badge active={user.is_active}>{user.is_active ? "Active" : "Inactive"}</S.Badge>
        </S.InfoCard>
      </S.InfoGrid>
    </S.PageContainer>
  );
}
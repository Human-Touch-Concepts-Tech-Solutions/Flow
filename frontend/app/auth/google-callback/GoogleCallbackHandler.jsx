"use client";
import { useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';

export default function GoogleCallbackHandler() {
  const searchParams = useSearchParams();
  const router = useRouter();

  useEffect(() => {
    const accessToken = searchParams.get('access_token');
    const refreshToken = searchParams.get('refresh_token');
    const sessionId = searchParams.get('session_id');
    
    if (accessToken && refreshToken) {
      // 1. Store tokens (localStorage or cookies)
      localStorage.setItem('access_token', accessToken);
      localStorage.setItem('refresh_token', refreshToken);
      localStorage.setItem('chat_session_id', sessionId);
      
      // 2. Redirect to dashboard/chat
      router.push(`/account/portal/ChatInterface/${sessionId}`);
    } else {
      // Handle error
      router.push('/login?error=oauth_failed');
    }
  }, [searchParams, router]);

  return <div>Processing Google Login...</div>;
}
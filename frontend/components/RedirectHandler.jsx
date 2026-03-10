"use client";
import { useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { useUser } from "@/providers/UserProvider";

export default function RedirectHandler() {
  const pathname = usePathname();
  const router = useRouter();
  const { user } = useUser();

  useEffect(() => {
    if (!user) return;

    // Logic: If user is Admin, but path is NOT admin, rewrite the URL
    if (user.role === 'admin' && pathname.includes('/account/portal/') && !pathname.includes('/admin/')) {
      const adminPath = pathname.replace('/account/portal/', '/account/portal/admin/');
      router.replace(adminPath); // This replaces the current history with the admin path
    }
  }, [pathname, user]);

  return null; // This component renders nothing
}
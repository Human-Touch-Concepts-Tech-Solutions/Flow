import { UserProvider } from "@/providers/UserProvider";
import ProtectedRoute from "@/components/ProtectedRoute/ProtectedRoute";
import RedirectHandler from "@/components/RedirectHandler";
export default function PortalLayout({ children }) {
  return (
    <UserProvider>
      <ProtectedRoute>
        <RedirectHandler />
        {/* All portal pages now have 'user' data and are behind a login wall */}
        {children}
      </ProtectedRoute>
    </UserProvider>
  );
}
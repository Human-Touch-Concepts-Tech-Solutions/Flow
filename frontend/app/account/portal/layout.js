import { UserProvider } from "@/providers/UserProvider";
import ProtectedRoute from "@/components/ProtectedRoute/ProtectedRoute";

export default function PortalLayout({ children }) {
  return (
    <UserProvider>
      <ProtectedRoute>
        {/* All portal pages now have 'user' data and are behind a login wall */}
        {children}
      </ProtectedRoute>
    </UserProvider>
  );
}
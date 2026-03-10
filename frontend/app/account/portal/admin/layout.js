import AdminProtectedRoute from "@/components/AdminProtectedRoutes/AdminProtectedRoute";

export default function AdminLayout({ children }) {
  return (
    <AdminProtectedRoute>
      {/* This only shows if the user is logged in AND is an admin */}
      {children}
    </AdminProtectedRoute>
  );
}
import { Navigate, Route, Routes } from 'react-router-dom'
import ProtectedRoute from './components/common/ProtectedRoute'
import AppLayout from './components/layout/AppLayout'
import FacesPage from './pages/FacesPage'
import LoginPage from './pages/LoginPage'
import RecordsPage from './pages/RecordsPage'
import SourceDetailPage from './pages/SourceDetailPage'
import SourceListPage from './pages/SourceListPage'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <AppLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/sources" replace />} />
        <Route path="sources" element={<SourceListPage />} />
        <Route path="sources/:id" element={<SourceDetailPage />} />
        <Route path="faces" element={<FacesPage />} />
        <Route path="records" element={<RecordsPage />} />
      </Route>
    </Routes>
  )
}

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout';
import SalesDashboard from './pages/SalesDashboard';
import OperationsDashboard from './pages/OperationsDashboard';
import CombinedView from './pages/CombinedView';
import DataQuality from './pages/DataQuality';
import InsightsPage from './pages/InsightsPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Navigate to="/sales" replace />} />
          <Route path="sales" element={<SalesDashboard />} />
          <Route path="operations" element={<OperationsDashboard />} />
          <Route path="combined" element={<CombinedView />} />
          <Route path="data-quality" element={<DataQuality />} />
          <Route path="insights" element={<InsightsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

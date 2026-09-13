import { Routes, Route } from 'react-router-dom';
import { Sidebar } from './components/Sidebar';
import Dashboard from './pages/Dashboard';
import Sales from './pages/Sales';
import Customers from './pages/Customers';
import Products from './pages/Products';
import Regions from './pages/Regions';
import Employees from './pages/Employees';
import Forecast from './pages/Forecast';
import Churn from './pages/Churn';
import RFM from './pages/RFM';
import DataQuality from './pages/DataQuality';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

function App() {
  return (
    <div className="flex min-h-screen bg-[var(--color-canvas)]">
      <Sidebar />
      <main className="flex-1 p-6 max-w-[1400px]">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/sales" element={<Sales />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/products" element={<Products />} />
          <Route path="/regions" element={<Regions />} />
          <Route path="/employees" element={<Employees />} />
          <Route path="/forecast" element={<Forecast />} />
          <Route path="/churn" element={<Churn />} />
          <Route path="/rfm" element={<RFM />} />
          <Route path="/data-quality" element={<DataQuality />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/settings" element={<Settings />} />
        </Routes>
      </main>
    </div>
  );
}

export default App;

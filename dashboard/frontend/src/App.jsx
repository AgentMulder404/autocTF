import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import Dashboard from './pages/Dashboard'
import Targets from './pages/Targets'
import Scans from './pages/Scans'
import Vulnerabilities from './pages/Vulnerabilities'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/targets" element={<Targets />} />
        <Route path="/scans" element={<Scans />} />
        <Route path="/vulnerabilities" element={<Vulnerabilities />} />
      </Routes>
    </Layout>
  )
}

export default App

import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import CropPage from './pages/CropPage'
import FertilizerPage from './pages/FertilizerPage'
import DiseasePage from './pages/DiseasePage'
import './App.css'

function App() {
  return (
    <>
      <Navbar />
      <main className="page-content">
        <Routes>
          <Route path="/"           element={<CropPage />} />
          <Route path="/fertilizer" element={<FertilizerPage />} />
          <Route path="/disease"    element={<DiseasePage />} />
        </Routes>
      </main>
    </>
  )
}

export default App
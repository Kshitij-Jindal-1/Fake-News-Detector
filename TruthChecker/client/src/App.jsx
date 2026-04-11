import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import HomePage from './pages/HomePage'
import FakeNewsPage from './pages/FakeNewsPage'

const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/community" element={<FakeNewsPage />} />
      </Routes>
    </Router>
  )
}

export default App

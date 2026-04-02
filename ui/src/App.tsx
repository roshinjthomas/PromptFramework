import { NavLink, Route, Routes } from 'react-router-dom'
import ChatPage from './pages/ChatPage'
import EvaluationPage from './pages/EvaluationPage'

function App() {
  const navLinkClass = ({ isActive }: { isActive: boolean }) =>
    `px-4 py-3 text-sm font-medium transition-colors duration-150 ${
      isActive ? 'tab-active' : 'tab-inactive'
    }`

  return (
    <div className="flex flex-col h-full">
      {/* Navbar */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-screen-xl mx-auto px-4 flex items-center justify-between h-14">
          <div className="flex items-center gap-3">
            <span className="text-blue-600 font-bold text-lg">RAG Chatbot</span>
            <span className="text-gray-400 text-xs">Customer Service Framework</span>
          </div>

          {/* Tab navigation */}
          <nav className="flex gap-1">
            <NavLink to="/" end className={navLinkClass}>
              Chat
            </NavLink>
            <NavLink to="/evaluation" className={navLinkClass}>
              Evaluation
            </NavLink>
          </nav>
        </div>
      </header>

      {/* Page content */}
      <main className="flex-1 overflow-hidden">
        <Routes>
          <Route path="/" element={<ChatPage />} />
          <Route path="/evaluation" element={<EvaluationPage />} />
        </Routes>
      </main>
    </div>
  )
}

export default App

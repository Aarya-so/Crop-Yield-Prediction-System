import { NavLink } from 'react-router-dom'
import './Navbar.css'

const links = [
  { to: '/',            label: 'Yield',         icon: '📊' },
  { to: '/fertilizer',  label: 'Fertilizer',    icon: '🧪' },
  { to: '/crop',        label: 'Crop',          icon: '🌾' },
  // { to: '/disease',     label: 'Disease',       icon: '🔬' }, 
  
]

export default function Navbar() {
  return (
    <nav className="navbar">
      <span className="navbar-brand">🌿 AgriSense</span>
      <div className="navbar-links">
        {links.map(({ to, label, icon }) => (
          <NavLink
            key={to}
            to={to}
            end
            className={({ isActive }) =>
              'nav-item' + (isActive ? ' nav-item--active' : '')
            }
          >
            <span className="nav-icon">{icon}</span>
            <span className="nav-label">{label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  )
}
import React from 'react'
import { Link, useLocation } from 'react-router-dom'
import styled from 'styled-components'
import { assets } from '../assets/assets'
import { UserButton, useClerk, useUser } from '@clerk/clerk-react'
import { useTheme } from '../context/ThemeContext'

// Styled Components
const NavContainer = styled.nav`
  position: sticky;
  top: 0;
  z-index: 50;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 16px;
  background: var(--glass-bg);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--glass-border);
  transition: all 0.3s ease;

  @media (min-width: 768px) { padding: 16px 32px; }
  @media (min-width: 1024px) { padding: 16px 58px; }
`;

const LogoImage = styled.img`
  width: 156px;
  height: 32px;
  /* Invert colors in light mode so white text becomes black */
  filter: ${props => props.theme === 'light' ? 'invert(1) brightness(0.2)' : 'none'};
  transition: filter 0.3s ease;
`;

const NavLink = styled(Link)`
  font-size: 0.875rem;
  font-weight: 500;
  transition: color 0.2s ease;
  color: ${props => props.$active 
    ? (props.$isAlert ? '#ef4444' : '#52C41A') 
    : 'var(--text-secondary)'};

  &:hover {
    color: ${props => props.$isAlert ? '#f87171' : 'var(--text-primary)'};
  }
`;

const ThemeButton = styled.button`
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.3s ease;

  &:hover {
    border-color: #52C41A;
    transform: scale(1.05);
  }
`;

const LoginButton = styled.button`
  background: #52C41A;
  color: black;
  padding: 8px 32px;
  border-radius: 9999px; /* full rounded */
  font-weight: 600;
  transition: all 0.3s ease;
  cursor: pointer;

  &:hover {
    filter: brightness(1.1);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(82, 196, 26, 0.3);
  }
`;

const Navbar = () => {
  const { user } = useUser();
  const { openSignIn } = useClerk();
  const location = useLocation();
  const { theme, toggleTheme } = useTheme();

  const isActive = (path) => location.pathname === path;

  return (
    <NavContainer>
      {/* Logo */}
      <Link to="/">
        <LogoImage src={assets.logo} alt="TruthCheck" theme={theme} />
      </Link>

      {/* Navigation Links */}
      <div className='hidden md:flex items-center gap-6'>
        <NavLink to="/" $active={isActive('/')}>
          Home
        </NavLink>
        <NavLink to="/community" $active={isActive('/community')}>
          👥 Community Fact-Checker
        </NavLink>
      </div>

      {/* Right side: Theme Toggle + Auth */}
      <div className='flex flex-row items-center gap-4'>
        {/* Mobile Menu Link */}
        <Link 
          to="/community" 
          className='md:hidden text-xs text-red-400 hover:text-red-300'
        >
          👥 Community
        </Link>

        {/* Theme Toggle */}
        <ThemeButton
          onClick={toggleTheme}
          title={`Switch to ${theme === 'dark' ? 'light' : 'dark'} mode`}
        >
          <span className='theme-toggle-icon text-base'>
            {theme === 'dark' ? '☀️' : '🌙'}
          </span>
        </ThemeButton>
        
        {!user ? (
          <LoginButton onClick={openSignIn}>
            Login
          </LoginButton>
        ) : (
          <UserButton/>
        )}
      </div>
    </NavContainer>
  )
}

export default Navbar

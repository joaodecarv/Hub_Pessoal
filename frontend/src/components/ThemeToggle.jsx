import { useState } from 'react'
import { Sun, Moon } from 'lucide-react'

// index.html sets data-theme before React mounts; this only flips and persists it.
function ThemeToggle(){
    const [theme, setTheme] = useState(document.documentElement.dataset.theme)
    const isDark = theme === 'dark'

    function toggle(){
        const next = isDark ? 'light' : 'dark'
        document.documentElement.dataset.theme = next
        try { localStorage.setItem('hub-theme', next) } catch { /* private mode: theme just won't persist */ }
        setTheme(next)
    }

    return (
        <button className="theme-toggle" onClick={toggle} aria-pressed={isDark}
                aria-label={isDark ? 'Mudar para tema claro' : 'Mudar para tema escuro'}>
            {isDark ? <Sun size={18} aria-hidden="true" /> : <Moon size={18} aria-hidden="true" />}
            <span className="nav-label">{isDark ? 'Tema claro' : 'Tema escuro'}</span>
        </button>
    )
}

export default ThemeToggle

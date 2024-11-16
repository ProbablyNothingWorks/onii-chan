// src/app/page.tsx
'use client';

import {
  Box,
  CssBaseline,
  ThemeProvider,
  createTheme,
  Fab
} from '@mui/material';
import { useState } from 'react';
import styles from './page.module.css';
import { Mint } from '@/app/component/Mint';
import { Description } from '@/app/component/Description';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

export default function Home() {
  const [darkMode, setDarkMode] = useState(true);

  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light'
    }
  });

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className={styles.page}>
        <main className={styles.main}>
          <Box
            display='grid'
            gridTemplateColumns='1fr 1fr'
            gap={2}
            overflow='auto'
          >
            <Description />
            <Mint />
          </Box>
        </main>
        <Fab
          color='primary'
          aria-label='toggle theme'
          onClick={toggleDarkMode}
          style={{
            position: 'fixed',
            bottom: '16px',
            right: '16px'
          }}
        >
          {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
        </Fab>
      </div>
    </ThemeProvider>
  );
}

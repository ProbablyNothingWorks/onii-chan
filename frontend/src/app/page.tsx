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
import { Tabs, Tab } from '@mui/material';
import { Mint } from '@/app/component/Mint';
import { Tip } from '@/app/component/Tip';
import { Description } from '@/app/component/Description';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';

export default function Home() {
  const [darkMode, setDarkMode] = useState(true);
  const [currentTab, setCurrentTab] = useState(0);  // Add this line

  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light'
    }
  });

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setCurrentTab(newValue);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className={styles.page}>
        <main className={styles.main}>
          <Box display='flex' flexDirection='column' width='100%'>
            <Tabs
              value={currentTab}
              onChange={handleTabChange}
              centered
              sx={{ mb: 3 }}
            >
              <Tab label="Mint" />
              <Tab label="Tip" />
            </Tabs>
            
            <Box display='flex'>
              <Description />
              {currentTab === 0 ? <Mint /> : <Tip />}
            </Box>
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

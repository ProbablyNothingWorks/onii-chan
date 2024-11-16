// src/app/page.tsx
'use client';

import {
  Box,
  CssBaseline,
  ThemeProvider,
  createTheme,
  Fab,
  IconButton
} from '@mui/material';
import { useState } from 'react';
import styles from './page.module.css';
import { Tabs, Tab } from '@mui/material';
import { Mint } from '@/app/component/Mint';
import { Tip } from '@/app/component/Tip';
import { TipETH } from '@/app/component/TipETH';
import { Description } from '@/app/component/Description';
import Brightness4Icon from '@mui/icons-material/Brightness4';
import Brightness7Icon from '@mui/icons-material/Brightness7';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';


export default function Home() {
  const [darkMode, setDarkMode] = useState(true);
  const [currentTab, setCurrentTab] = useState(0);
  const [isRightPanelOpen, setIsRightPanelOpen] = useState(false);

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

  const toggleRightPanel = () => {
    setIsRightPanelOpen(!isRightPanelOpen);
  };

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <div className={styles.page}>
        <main className={styles.main}>
          <Box display='flex' flexDirection='column' width='100%' position='relative'>
            {/* Description takes full width */}
            <Description />
              
           
            {/* Overlay panel */}
            <Box 
              sx={{ 
                position: 'fixed',
                top: 0,
                right: 0,
                height: '100vh',
                backgroundColor: theme.palette.background.paper,
                boxShadow: isRightPanelOpen ? '-4px 0 8px rgba(0, 0, 0, 0.1)' : 'none',
                transition: 'all 0.3s ease',
                transform: isRightPanelOpen ? 'translateX(0)' : 'translateX(100%)',
                width: '500px',
                overflowY: 'auto',
                zIndex: 1000,
              }}
            >
              <Box sx={{ 
                width: '100%',
                height: '100%',
                p: 3,
              }}>
                <Tabs
                  value={currentTab}
                  onChange={handleTabChange}
                  centered
                  sx={{ mb: 3 }}
                >
                  <Tab label="Mint" />
                  <Tab label="Tip Token" />
                  <Tab label="Tip ETH" />
                </Tabs>
                
                {currentTab === 0 ? <Mint /> : 
                 currentTab === 1 ? <Tip /> : <TipETH />}
              </Box>
            </Box>
          </Box>
        </main>

        <Fab
          color='primary'
          aria-label='toggle theme'
          onClick={toggleDarkMode}
          style={{
            position: 'fixed',
            bottom: '64px',
            left: '16px'
          }}
        >
          {darkMode ? <Brightness7Icon /> : <Brightness4Icon />}
        </Fab>

        <Fab
          color='primary'
          aria-label='toggle panel'
          onClick={toggleRightPanel}
          style={{
            position: 'fixed',
            bottom: '64px',
            right: '16px'
          }}
        >
          {isRightPanelOpen ? <ChevronRightIcon /> : <ChevronLeftIcon />}
        </Fab>
      </div>
    </ThemeProvider>
  );
}
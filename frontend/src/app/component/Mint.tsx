'use client';
import {
  Box,
  InputLabel,
  MenuItem,
  Select,
  FormControl,
  FormHelperText,
  SelectChangeEvent,
  Button
} from '@mui/material';
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useState } from 'react';
import { useAccount } from 'wagmi';

export const Mint = () => {
  const { status } = useAccount();
  const [model, setModel] = useState('shizuku-local');
  const [voice, setVoice] = useState('1');

  const handleModelChange = (event: SelectChangeEvent) => {
    setModel(event.target.value);
  };

  const handleVoiceChange = (event: SelectChangeEvent) => {
    setVoice(event.target.value);
  };

  return (
    <Box>
      <Box width='500px'>
        <video
          src={`video/${model}-${voice}.mp4`}
          autoPlay
          controls
          muted
          style={{
            height: '300px',
            width: '500px',
            position: 'sticky',
            top: '100px',
            borderRadius: 16,
            marginBottom: 16
          }}
        />
        <FormControl sx={{ m: 1, minWidth: 120, margin: 0, mr: 2, mb: 2 }}>
          <InputLabel id='demo-simple-select-helper-label'>Model</InputLabel>
          <Select
            labelId='demo-simple-select-helper-label'
            id='demo-simple-select-helper'
            value={model}
            label='Model'
            onChange={handleModelChange}
          >
            <MenuItem value={'shizuku-local'}>shizuku-local</MenuItem>
            <MenuItem value={'other_unit_90001'}>other_unit_90001</MenuItem>
            <MenuItem value={'player_unit_00003'}>player_unit_00003</MenuItem>
            <MenuItem value={'mashiro'}>mashiro</MenuItem>
          </Select>
        </FormControl>
        <FormControl sx={{ m: 1, minWidth: 120, margin: 0 }}>
          <InputLabel id='demo-simple-select-helper-label'>Voice</InputLabel>
          <Select
            labelId='demo-simple-select-helper-label'
            id='demo-simple-select-helper'
            value={voice}
            label='Voice'
            onChange={handleVoiceChange}
          >
            <MenuItem value={1}>1</MenuItem>
            <MenuItem value={2}>2</MenuItem>
            <MenuItem value={3}>3</MenuItem>
          </Select>
        </FormControl>
        <Box>
          {status === 'connected' ? (
            <Button
              variant='contained'
              onClick={() => {
                console.log(model, voice);
              }}
            >
              Mint
            </Button>
          ) : (
            <ConnectButton />
          )}
        </Box>
      </Box>
    </Box>
  );
};

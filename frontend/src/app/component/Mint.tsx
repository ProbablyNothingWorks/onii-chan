'use client';
import {
  Box,
  InputLabel,
  MenuItem,
  Select,
  FormControl,
  FormHelperText,
  SelectChangeEvent,
  Button,
  TextField,
  CircularProgress
} from '@mui/material';
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useState } from 'react';
import { useAccount, useWriteContract } from 'wagmi';
import { abi } from '../../abi';
import { useSnackbar } from 'notistack';

export const Mint = () => {
  const { data: hash, writeContract, isPending } = useWriteContract();
  const { address, status } = useAccount();

  const [model, setModel] = useState('shizuku-local');
  const [voice, setVoice] = useState('1');
  const [prompt, setPrompt] = useState('');
  const { enqueueSnackbar } = useSnackbar();
  console.log(status);
  const handleModelChange = (event: SelectChangeEvent) => {
    setModel(event.target.value);
  };

  const handleVoiceChange = (event: SelectChangeEvent) => {
    setVoice(event.target.value);
  };

  const handlePromptChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    setPrompt(event.target.value);
  };

  return (
    <Box>
      <Box width='500px' style={{ position: 'sticky', top: '50px' }}>
        <video
          src={`video/${model}-${voice}.mp4`}
          autoPlay
          controls
          muted
          style={{
            height: '300px',
            width: '500px',
            borderRadius: 16,
            marginBottom: 16
          }}
        />
        <TextField
          label='Prompt'
          multiline
          onChange={handlePromptChange}
          sx={{ mb: 3 }}
          fullWidth
        />
        <Box display='flex'>
          <FormControl
            sx={{ flex: 1, m: 1, minWidth: 120, margin: 0, mr: 2, mb: 2 }}
          >
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
          <FormControl sx={{ flex: 1, m: 1, minWidth: 120, margin: 0 }}>
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
        </Box>
        <Box display='flex' justifyContent='center'>
          {status === 'connected' ? (
            <Button
              variant='contained'
              onClick={() => {
                const data = {
                  model,
                  voice,
                  prompt
                };
                try {
                  writeContract({
                    abi,
                    address: '0x9fA0DA29B88cc1479D28CEaD5a12fF498528a9D0',
                    functionName: 'createOnii',
                    args: [address, null, JSON.stringify(data)]
                  });
                  enqueueSnackbar({ message: 'Minted', variant: 'success' });
                } catch (e) {}
              }}
            >
              {isPending ? (
                <CircularProgress color='inherit' size={16} />
              ) : (
                'Mint'
              )}
            </Button>
          ) : (
            <ConnectButton />
          )}
        </Box>
      </Box>
    </Box>
  );
};

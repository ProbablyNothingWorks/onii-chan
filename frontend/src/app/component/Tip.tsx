'use client';
import {
  Box,
  TextField,
  Button
} from '@mui/material';
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useState } from 'react';
import { useAccount } from 'wagmi';

export const Tip = () => {
  const { status } = useAccount();
  const [nftId, setNftId] = useState('');
  const [tokenAddress, setTokenAddress] = useState('');
  const [amount, setAmount] = useState('');
  const [message, setMessage] = useState('');

  return (
    <Box>
      <Box 
        width='500px'
        sx={{
          position: 'sticky',
          top: '50px',
        }}
      >
        <img
          src="/tips.png"
          alt="But please tip"
          style={{
            height: '300px',
            width: '500px',
            borderRadius: 8,
            marginBottom: 8,
            objectFit: 'cover',
          }}
        />
        
        <TextField
          fullWidth
          label="NFT ID"
          value={nftId}
          onChange={(e) => setNftId(e.target.value)}
          sx={{ mb: 2 }}
        />
        
        <TextField
          fullWidth
          label="Tip ERC20 Address"
          value={tokenAddress}
          onChange={(e) => setTokenAddress(e.target.value)}
          sx={{ mb: 2 }}
        />
        
        <TextField
          fullWidth
          label="Tip ERC20 Amount"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          sx={{ mb: 2 }}
        />
        
        <TextField
          fullWidth
          label="Message"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          multiline
          rows={4}
          sx={{ mb: 2 }}
        />

        <Box>
          {status === 'connected' ? (
            <Button
              variant='contained'
              onClick={() => {
                console.log(nftId, tokenAddress, amount, message);
              }}
            >
              Tip
            </Button>
          ) : (
            <ConnectButton />
          )}
        </Box>
      </Box>
    </Box>
  );
};
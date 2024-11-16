'use client';
import {
  Box,
  TextField,
  Button,
  CircularProgress,
  Link
} from '@mui/material';
import { ConnectButton } from '@rainbow-me/rainbowkit';
import { useState } from 'react';
import { 
  useAccount,
  useWaitForTransactionReceipt,
  useWriteContract
} from 'wagmi';
import { abi } from '../../abi';
import { useSnackbar } from 'notistack';
import { shortenAddress } from '@/util/shortenAddress';

export const TipETH = () => {
  const { data: hash, writeContract, isPending } = useWriteContract();
  const { status, chain } = useAccount();
  const { isLoading: isConfirming, isSuccess: isConfirmed } =
    useWaitForTransactionReceipt({
      hash
    });
  const { enqueueSnackbar } = useSnackbar();
  const [nftId, setNftId] = useState('');
  const [amount, setAmount] = useState('');
  const [message, setMessage] = useState('');

  return (
    <Box>
      <Box 
        width='400px'
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
            width: '400px',
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
          label="ETH Amount"
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
              disabled={isPending || isConfirming}
              onClick={async () => {
                if (!nftId || !amount) {
                  enqueueSnackbar('Please fill in all required fields', { variant: 'error' });
                  return;
                }

                try {
                  console.log('Sending ETH tip with params:', {
                    nftId: BigInt(nftId),
                    amount: BigInt(amount),
                    message
                  });

                  writeContract({
                    abi,
                    address: '0x9fA0DA29B88cc1479D28CEaD5a12fF498528a9D0',
                    functionName: 'tipEth',
                    args: [BigInt(nftId), BigInt(amount), message],
                    value: BigInt(amount)
                  });
                } catch (error) {
                  console.error('Error sending ETH tip:', error);
                  enqueueSnackbar(
                    error instanceof Error ? error.message : 'Failed to send ETH tip',
                    { variant: 'error' }
                  );
                }
              }}
            >
              {isPending || isConfirming ? (
                <CircularProgress color='inherit' size={16} />
              ) : (
                'Tip ETH'
              )}
            </Button>
          ) : (
            <ConnectButton />
          )}
        </Box>
        
        {isConfirmed && hash && (
          <Link
            href={`${chain?.blockExplorers.default.url}/tx/${hash}`}
          >
            {`${shortenAddress(hash)}`}
          </Link>
        )}
      </Box>
    </Box>
  );
};
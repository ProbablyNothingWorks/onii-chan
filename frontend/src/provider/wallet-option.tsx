'use client';
import * as React from 'react';
import { Connector, useConnect } from 'wagmi';
import { Button } from '@mui/material';
export const WalletOptions = () => {
  const { connectors, connect } = useConnect();

  return (
    <>
      {connectors.slice(0, 1).map((connector) => (
        <button key={connector.uid} onClick={() => connect({ connector })}>
          <Button variant='contained'>{connector.name}</Button>
        </button>
      ))}
    </>
  );
};

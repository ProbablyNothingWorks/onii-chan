'use client';
import * as React from 'react';
import { Connector, useConnect } from 'wagmi';

export const WalletOptions = () => {
  const { connectors, connect } = useConnect();

  return connectors.map((connector) => (
    <button key={connector.uid} onClick={() => connect({ connector })}>
      {connector.name}
    </button>
  ));
};
